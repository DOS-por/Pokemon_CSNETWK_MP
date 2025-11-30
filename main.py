"""
Main entry point for PokeProtocol
Command-line interface for host/joiner/spectator modes
"""
import sys
import os
import time
import threading
import socket
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from network.udp_client import UDPClient
from network.reliability import ReliabilityLayer
from protocol.messages import (
    decode_message, create_hello, create_hello_ack,
    create_pokemon_select, create_pokemon_select_ack,
    create_ready, create_ready_ack, create_battle_start,
    create_attack, create_attack_ack, create_battle_result,
    create_chat_message, create_disconnect
)
from protocol.state_machine import StateMachine, ConnectionState
from battle.database import PokemonDatabase
from battle.pokemon import Pokemon
from battle.battle_logic import Battle, BattlePhase
from battle.move import Move
from chat.chat_handler import ChatHandler
from ui import cli


class PokeProtocolClient:
    """Main client for PokeProtocol"""
    
    def __init__(self, player_name: str, role: str):
        """
        Initialize client
        
        Args:
            player_name: Player's name
            role: HOST, JOINER, or SPECTATOR
        """
        self.player_name = player_name
        self.role = role
        self.running = False
        
        # Network components
        self.udp_client: Optional[UDPClient] = None
        self.reliability: Optional[ReliabilityLayer] = None
        
        # Protocol components
        self.state_machine = StateMachine()
        self.chat_handler = ChatHandler()
        
        # Game data
        self.pokemon_db: Optional[PokemonDatabase] = None
        self.my_pokemon: Optional[Pokemon] = None
        self.opponent_pokemon: Optional[Pokemon] = None
        self.opponent_name: Optional[str] = None
        self.battle: Optional[Battle] = None
        
        # Input thread
        self.input_thread: Optional[threading.Thread] = None
        self.input_lock = threading.Lock()

        self.spectators = []  # List of (host, port) tuples
        self.is_spectator = (role == config.ROLE_SPECTATOR)
    
    def start(self, host: str, port: int):
        """Start the client"""
        try:
            # Load Pokemon database
            csv_path = os.path.join(os.path.dirname(__file__), config.POKEMON_DATA_FILE)
            self.pokemon_db = PokemonDatabase(csv_path)
            cli.print_success(f"Loaded {self.pokemon_db.count()} Pokemon")
            
            # Start UDP client
            self.udp_client = UDPClient(host, port)
            if not self.udp_client.start():
                cli.print_error("Failed to start UDP client")
                return False
            
            # Start reliability layer
            self.reliability = ReliabilityLayer(self.udp_client.send)
            self.reliability.set_message_callback(self._handle_message)
            self.reliability.start()
            
            # Start receiving
            self.udp_client.start_receiving(self.reliability.handle_received)
            
            self.running = True
            cli.print_success(f"Client started on {host}:{port}")
            
            return True
            
        except Exception as e:
            cli.print_error(f"Failed to start client: {e}")
            return False
    
    def stop(self):
        """Stop the client"""
        self.running = False
        
        if self.reliability:
            self.reliability.stop()
        
        if self.udp_client:
            self.udp_client.stop()
        
        cli.print_info("Client stopped")
    
    def connect_to_peer(self, peer_host: str, peer_port: int):
        """Connect to peer"""
        self.udp_client.set_peer(peer_host, peer_port)
        
        # Send HELLO
        hello_msg = create_hello(self.player_name, self.role)
        self.send_message(hello_msg)
        
        self.state_machine.transition(ConnectionState.CONNECTING, "Sent HELLO")
        cli.print_waiting("Waiting for HELLO_ACK...")

    def wait_for_connection(self):
        """Wait for peer to connect (host mode)"""
        self.state_machine.transition(ConnectionState.CONNECTING, "Waiting for HELLO")
        cli.print_waiting("Waiting for opponent to connect...")
    
    def send_message(self, message):
        """Send protocol message"""
        if not self.udp_client or not self.udp_client.peer_address:
            return False
        
        data = message.encode()
        self.reliability.send_reliable(data, self.udp_client.peer_address)
        return True
    
    def send_to_spectators(self, message):
        BROADCAST_IP = "255.255.255.255"
        PORT = 6000

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        sock.sendto(message.encode(), (BROADCAST_IP, PORT))

    def _handle_message(self, data: bytes, address: tuple):
        """Handle received message"""
        message = decode_message(data)
        if not message:
            return
        
        msg_type = message.type
        
        if config.DEBUG_MODE:
            print(f"[RECEIVED] {msg_type} from {address}")
        
        # Handle different message types
        if msg_type == config.MSG_TYPE_HELLO:
            self._handle_hello(message, address)
        elif msg_type == config.MSG_TYPE_HELLO_ACK:
            self._handle_hello_ack(message)
        elif msg_type == config.MSG_TYPE_POKEMON_SELECT:
            self._handle_pokemon_select(message)
        elif msg_type == config.MSG_TYPE_POKEMON_SELECT_ACK:
            self._handle_pokemon_select_ack(message)
        elif msg_type == config.MSG_TYPE_READY:
            self._handle_ready(message)
        elif msg_type == config.MSG_TYPE_READY_ACK:
            self._handle_ready_ack(message)
        elif msg_type == config.MSG_TYPE_BATTLE_START:
            self._handle_battle_start(message)
        elif msg_type == config.MSG_TYPE_ATTACK:
            self._handle_attack(message)
        elif msg_type == config.MSG_TYPE_ATTACK_ACK:
            self._handle_attack_ack(message)
        elif msg_type == config.MSG_TYPE_BATTLE_RESULT:
            self._handle_battle_result(message)
        elif msg_type == config.MSG_TYPE_CHAT_MESSAGE:
            self._handle_chat_message(message)
        elif msg_type == config.MSG_TYPE_DISCONNECT:
            self._handle_disconnect(message)
    
    def _handle_hello(self, message, address):
        """Handle HELLO message from either a joiner or a spectator"""

        role = message.get("role")

        if role == config.ROLE_SPECTATOR:
            # Add spectator to the list
            self.spectators.append(address)
            ack = create_hello_ack(self.player_name)
            self.reliability.send_reliable(ack.encode(), address)
            cli.print_info(f"Spectator connected: {address}")

            # Optionally send them the current battle state if available
            if self.battle:
                from protocol.messages import create_battle_state
                state_msg = create_battle_state(self.battle.get_battle_state())
                self.reliability.send_reliable(state_msg.encode(), address)

        else:
            # Handle normal opponent (joiner)
            self.opponent_name = message.get("player_name")
            self.udp_client.set_peer(address[0], address[1])

            # Send HELLO_ACK back to opponent
            ack = create_hello_ack(self.player_name)
            self.send_message(ack)

            self.state_machine.transition(ConnectionState.CONNECTED,
                                        f"Connected to {self.opponent_name}")
            cli.print_success(f"Connected to {self.opponent_name}")
    
    def _handle_hello_ack(self, message):
        """Handle HELLO_ACK message"""
        self.opponent_name = message.get("player_name")
        self.state_machine.transition(ConnectionState.CONNECTED, f"Connected to {self.opponent_name}")
        cli.print_success(f"Connected to {self.opponent_name}")
    
    def _handle_pokemon_select(self, message):
        """Handle POKEMON_SELECT message"""
        pokemon_num = message.get_int("pokemon_number")
        pokemon_name = message.get("pokemon_name")
        
        self.opponent_pokemon = self.pokemon_db.get_by_number(pokemon_num)
        if self.opponent_pokemon:
            cli.print_info(f"{self.opponent_name} selected {pokemon_name}")
        
        # Send ACK
        ack = create_pokemon_select_ack()
        self.send_message(ack)
    
    def _handle_pokemon_select_ack(self, message):
        """Handle POKEMON_SELECT_ACK message"""
        cli.print_success("Opponent acknowledged your Pokemon selection")
    
    def _handle_ready(self, message):
        """Handle READY message"""
        # Send ACK
        ack = create_ready_ack()
        self.send_message(ack)
        
        self.state_machine.transition(ConnectionState.READY, "Both players ready")
        
        # Host starts battle
        if self.role == config.ROLE_HOST:
            self._start_battle()
    
    def _handle_ready_ack(self, message):
        """Handle READY_ACK message"""
        self.state_machine.transition(ConnectionState.READY, "Both players ready")
        cli.print_success("Opponent is ready!")
    
    def _handle_battle_start(self, message):
        """Handle BATTLE_START message"""
        first_player = message.get("first_player")
        
        if not self.battle:
            self._create_battle()
        
        self.battle.start_battle()
        self.state_machine.transition(ConnectionState.BATTLE_ACTIVE, "Battle started")
        
        cli.print_success(f"Battle started! {first_player} goes first")
    
    def _handle_attack(self, message):
        """Handle ATTACK message from opponent"""

        attacker = message.get("attacker")
        move_name = message.get("move_name")
        damage = message.get_int("damage")
        next_turn_player = message.get("next_turn_player")
        turn_number = message.get_int("turn_number")

        if not self.battle:
            return

        # Determine which Pokemon took damage
        if attacker == self.player_name:
            defender_pokemon = self.opponent_pokemon
        else:
            defender_pokemon = self.my_pokemon

        # Apply damage
        defender_pokemon.take_damage(damage)
        cli.print_info(f"{attacker} used {move_name} for {damage} damage!")

        # Sync turn count and next player exactly as sent
        self.battle.turn_count = turn_number
        self.battle.phase = (
            BattlePhase.PLAYER1_TURN if next_turn_player == self.battle.player1_name
            else BattlePhase.PLAYER2_TURN
        )

        # Send ACK
        ack = create_attack_ack(self.my_pokemon.current_hp, sender=self.player_name)
        self.send_message(ack)

        # Check if defender fainted
        if defender_pokemon.is_fainted():
            winner = self.opponent_name if defender_pokemon == self.my_pokemon else self.player_name
            result_msg = create_battle_result(winner, attacker)
            self.send_message(result_msg)
            self._end_battle(winner)

    def _handle_attack_ack(self, message):
        """Handle ATTACK_ACK message"""
        defender_hp = message.get_int("defender_hp")
        cli.print_info(f"Opponent HP: {defender_hp}")

        # Update opponent Pokémon HP
        if self.opponent_pokemon:
            self.opponent_pokemon.current_hp = defender_hp

        # Check if opponent fainted
        if defender_hp <= 0:
            result_msg = create_battle_result(self.player_name, self.opponent_name)
            self.send_message(result_msg)
            self._end_battle(self.player_name)

    
    def _handle_battle_result(self, message):
        """Handle BATTLE_RESULT message"""
        winner = message.get("winner")
   
        self.state_machine.transition(ConnectionState.BATTLE_ENDED, f"{winner} wins!")
    
    def _handle_chat_message(self, message):
        """Handle CHAT_MESSAGE"""
        sender = message.get("sender")
        text = message.get("message")
        sticker = message.get("sticker") if message.get("sticker") else None
        
        chat_msg = self.chat_handler.receive_message(sender, text, sticker)
        print(f"\n{chat_msg}")
    
    def _handle_disconnect(self, message):
        """Handle DISCONNECT message"""
        player = message.get("player_name")
        reason = message.get("reason", "Unknown")
        
        cli.print_info(f"{player} disconnected: {reason}")
        self.state_machine.transition(ConnectionState.DISCONNECTED, "Peer disconnected")
        self.running = False
    
    def select_pokemon(self) -> bool:
        """Pokemon selection phase"""
        # Get random Pokemon to choose from
        options = self.pokemon_db.get_random_pokemon(6)
        
        cli.print_pokemon_selection(options)
        choice = cli.get_number_input("Select your Pokemon", 1, len(options))
        
        self.my_pokemon = options[choice - 1]
        cli.print_success(f"You selected {self.my_pokemon.name}!")
        
        # Send selection to opponent
        select_msg = create_pokemon_select(self.my_pokemon.pokedex_number, self.my_pokemon.name)
        self.send_message(select_msg)
        
        self.state_machine.transition(ConnectionState.POKEMON_SELECTION, "Pokemon selected")
        
        return True
    
    def send_ready(self):
        """Send ready message"""
        ready_msg = create_ready()
        self.send_message(ready_msg)
        cli.print_waiting("Waiting for opponent to be ready...")
    
    def _start_battle(self):
        """Start battle (host only)"""
        self._create_battle()
        self.battle.start_battle()
        
        # Send BATTLE_START
        start_msg = create_battle_start(self.battle.first_player)
        self.send_message(start_msg)
        
        self.state_machine.transition(ConnectionState.BATTLE_ACTIVE, "Battle started")
    
    def _create_battle(self):
        """Create battle instance"""
        if not self.my_pokemon or not self.opponent_pokemon:
            cli.print_error("Cannot create battle: Missing Pokemon")
            return
        
        
        if self.role == config.ROLE_HOST:
            self.battle = Battle(
                self.player_name, self.opponent_name,
                self.my_pokemon, self.opponent_pokemon
            )
        elif self.role == config.ROLE_JOINER:
            self.battle = Battle(
                self.opponent_name, self.player_name,
                self.opponent_pokemon, self.my_pokemon 
            )
    
    def execute_attack(self, move: Move):
        """Execute attack on your turn and send network message"""
        if not self.battle or not self.battle.is_player_turn(self.player_name):
            cli.print_error("Not your turn!")
            return

        # Check PP
        if not move.use():
            cli.print_error(f"{move.name} has no remaining uses!")
            return

        # Execute attack
        result = self.battle.execute_attack(self.player_name, move)

        if result['success']:
            attack_msg = create_attack(
                attacker=self.player_name,
                move=move,
                damage=result['damage'],
                turn_number=result['turn_number'],
                next_turn_player=result['next_turn_player']  # crucial for syncing
            )
            self.send_message(attack_msg)
            self.send_to_spectators(attack_msg)

    def _end_battle(self, winner: str):
        """End battle"""
        cli.print_battle_result(winner, self.opponent_name if winner == self.player_name else self.player_name)
        self.state_machine.transition(ConnectionState.BATTLE_ENDED, f"{winner} wins!")
    
    def send_chat(self, message: str, sticker: str = None):
        """Send chat message"""
        chat_msg = create_chat_message(self.player_name, message, sticker)
        self.send_message(chat_msg)
        
        # Log locally
        self.chat_handler.send_message(self.player_name, message, sticker)
    
    def disconnect(self, reason: str = "USER_QUIT"):
        """Send disconnect message"""
        disconnect_msg = create_disconnect(self.player_name, reason)
        self.send_message(disconnect_msg)
        self.running = False

def main():
    """Main entry point"""
    cli.print_welcome()
    
    # Get player name
    player_name = cli.get_user_input("Enter your name")
    
    # Select role
    role_choice = cli.print_menu("Select role", [
        "Host (create game)",
        "Join (connect to game)",
        "Spectator (watch game)"
    ])
    
    roles = [config.ROLE_HOST, config.ROLE_JOINER, config.ROLE_SPECTATOR]
    role = roles[role_choice]
    
    # Get network configuration
    if role == config.ROLE_HOST:
        port = cli.get_number_input("Enter port to host on", 1024, 65535)
        client = PokeProtocolClient(player_name, role)
        if not client.start(config.DEFAULT_HOST, port):
            return
        cli.print_connection_info(role, config.DEFAULT_HOST, port)
        client.wait_for_connection()
        # Wait for connection
        while client.running and client.state_machine.get_state() == ConnectionState.CONNECTING:
            time.sleep(0.5)
        if not client.running:
            return
        # Pokemon selection
        client.select_pokemon()
        cli.print_waiting("Waiting for opponent to select Pokemon...")
        while client.running and not client.opponent_pokemon:
            time.sleep(0.5)
        client.send_ready()
        # Wait for battle to start
        while client.running and client.state_machine.get_state() != ConnectionState.BATTLE_ACTIVE:
            time.sleep(0.5)

    elif role == config.ROLE_JOINER:  # JOINER
        peer_host = cli.get_user_input("Enter host IP")
        peer_port = cli.get_number_input("Enter host port", 1024, 65535)
        local_port = cli.get_number_input("Enter your local port", 1024, 65535)
        
        client = PokeProtocolClient(player_name, role)
        
        if not client.start(config.DEFAULT_HOST, local_port):
            return
        
        cli.print_connection_info(role, config.DEFAULT_HOST, local_port, peer_host, peer_port)
        client.connect_to_peer(peer_host, peer_port)
        
        # Wait for connection
        while client.running and client.state_machine.get_state() == ConnectionState.CONNECTING:
            time.sleep(0.5)
        
        if not client.running:
            return
        
        # Pokemon selection
        client.select_pokemon()
        cli.print_waiting("Waiting for opponent to select Pokemon...")
        
        while client.running and not client.opponent_pokemon:
            time.sleep(0.5)
        
        client.send_ready()
        
        # Wait for battle to start
        while client.running and client.state_machine.get_state() != ConnectionState.BATTLE_ACTIVE:
            time.sleep(0.5)

    else:  # SPECTATOR
        PORT = 6000

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind to all interfaces on the given UDP port
        sock.bind(("0.0.0.0", PORT))

        print(f"Listening for UDP broadcasts on port {PORT}...")

        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Received from {addr}: {data.decode()}")
    
    # Battle loop
    while client.running and client.battle and client.battle.is_active():
        cli.print_battle_state(client.battle.get_battle_state())
        
        if client.battle.is_player_turn(client.player_name):
            action = cli.print_menu("Your turn", [
                "Attack",
                "Chat",
                "View Battle Log",
                "Forfeit"
            ])
            
            if action == 0:  # Attack
                # Show all available moves
                moves = client.my_pokemon.moves
                move_names = [str(m) for m in moves]  # __str__ gives nice formatting
                
                move_choice = cli.print_menu("Choose a move", move_names)
                chosen_move = moves[move_choice]
                
                # Execute attack using the chosen move
                client.execute_attack(chosen_move)
                client.battle.switch_turn()
            elif action == 1:  # Chat
                msg = cli.get_user_input("Message")
                client.send_chat(msg)
            elif action == 2:  # Battle log
                if client.battle:
                    cli.print_battle_log(client.battle.get_battle_log())
                    cli.pause()
            elif action == 3:  # Forfeit
                if cli.confirm_action("Are you sure you want to forfeit?"):
                    client.disconnect("FORFEIT")
                    break
        else:
            cli.print_waiting(f"Waiting for {client.opponent_name}'s turn...")
            time.sleep(1)

    # Check if the result has been processed on a previous network tick
        if client.state_machine.get_state() == ConnectionState.BATTLE_ENDED:
            break  # Exit the loop immediately to preserve the final result printout
    
    cli.print_goodbye()
    client.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        cli.print_error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
