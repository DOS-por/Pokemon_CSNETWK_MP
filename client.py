import threading
import time
from typing import Optional
import os

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
from battle.pokemon import PokemonDatabase, Pokemon
from battle.battle_logic import Battle
from battle.damage import calculate_damage
from chat.chat_handler import ChatHandler
from ui import cli
from config import POKEMON_DATA_FILE
from battle.move import Move


class PokeProtocolClient:
    """Main client for PokeProtocol"""

    def __init__(self, player_name: str, role: str):
        self.player_name = player_name
        self.role = role
        self.running = False

        # Network
        self.udp_client: Optional[UDPClient] = None
        self.reliability: Optional[ReliabilityLayer] = None

        # Protocol
        self.state_machine = StateMachine()
        self.chat_handler = ChatHandler()

        # Game data
        self.pokemon_db: Optional[PokemonDatabase] = None
        self.my_pokemon: Optional[Pokemon] = None
        self.opponent_pokemon: Optional[Pokemon] = None
        self.opponent_name: Optional[str] = None
        self.battle: Optional[Battle] = None

        # Pending attack verification
        self.pending_attack = None  # {'turn_number', 'damage', 'next_turn_player', 'acks': set()}

        self.input_thread: Optional[threading.Thread] = None
        self.input_lock = threading.Lock()

    # -------------------- Network / Start -------------------- #
    def start(self, host: str, port: int):
        """Start UDP client and reliability layer"""
        try:
            # Load Pokemon DB
            csv_path = os.path.join(os.path.dirname(__file__), POKEMON_DATA_FILE)
            self.pokemon_db = PokemonDatabase(csv_path)
            cli.print_success(f"Loaded {self.pokemon_db.count()} Pokemon")

            # UDP client
            self.udp_client = UDPClient(host, port)
            if not self.udp_client.start():
                cli.print_error("Failed to start UDP client")
                return False

            # Reliability
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
        self.running = False
        if self.reliability:
            self.reliability.stop()
        if self.udp_client:
            self.udp_client.stop()
        cli.print_info("Client stopped")

    def send_message(self, message):
        if not self.udp_client or not self.udp_client.peer_address:
            return False
        self.reliability.send_reliable(message.encode(), self.udp_client.peer_address)
        return True

    # -------------------- Message Handling -------------------- #
    def _handle_message(self, data: bytes, address: tuple):
        """Dispatch incoming messages to handlers"""
        message = decode_message(data)
        if not message:
            return

        msg_type = message.type

        if msg_type == "HELLO":
            self._handle_hello(message, address)
        elif msg_type == "HELLO_ACK":
            self._handle_hello_ack(message)
        elif msg_type == "POKEMON_SELECT":
            self._handle_pokemon_select(message)
        elif msg_type == "POKEMON_SELECT_ACK":
            self._handle_pokemon_select_ack(message)
        elif msg_type == "READY":
            self._handle_ready(message)
        elif msg_type == "READY_ACK":
            self._handle_ready_ack(message)
        elif msg_type == "BATTLE_START":
            self._handle_battle_start(message)
        elif msg_type == "ATTACK":
            self._handle_attack(message)
        elif msg_type == "ATTACK_ACK":
            self._handle_attack_ack(message)
        elif msg_type == "BATTLE_RESULT":
            self._handle_battle_result(message)
        elif msg_type == "CHAT_MESSAGE":
            self._handle_chat_message(message)
        elif msg_type == "DISCONNECT":
            self._handle_disconnect(message)

    # -------------------- Handlers -------------------- #
    def _handle_hello(self, message, address):
        self.opponent_name = message.get("player_name")
        self.udp_client.set_peer(address[0], address[1])
        ack = create_hello_ack(self.player_name)
        self.send_message(ack)
        self.state_machine.transition(ConnectionState.CONNECTED, f"Connected to {self.opponent_name}")
        cli.print_success(f"Connected to {self.opponent_name}")

    def _handle_hello_ack(self, message):
        self.opponent_name = message.get("player_name")
        self.state_machine.transition(ConnectionState.CONNECTED, f"Connected to {self.opponent_name}")
        cli.print_success(f"Connected to {self.opponent_name}")

    def _handle_pokemon_select(self, message):
        num = message.get_int("pokemon_number")
        self.opponent_pokemon = self.pokemon_db.get_by_number(num)
        cli.print_info(f"{self.opponent_name} selected {self.opponent_pokemon.name}")
        ack = create_pokemon_select_ack()
        self.send_message(ack)

    def _handle_pokemon_select_ack(self, message):
        cli.print_success("Opponent acknowledged your Pokemon selection")

    def _handle_ready(self, message):
        ack = create_ready_ack()
        self.send_message(ack)
        self.state_machine.transition(ConnectionState.READY, "Both players ready")
        if self.role == "HOST":
            self._start_battle()

    def _handle_ready_ack(self, message):
        self.state_machine.transition(ConnectionState.READY, "Both players ready")
        cli.print_success("Opponent is ready!")

    def _handle_battle_start(self, message):
        first_player = message.get("first_player")
        if not self.battle:
            self._create_battle()
        self.battle.start_battle()
        self.state_machine.transition(ConnectionState.BATTLE_ACTIVE, "Battle started")
        cli.print_success(f"Battle started! {first_player} goes first")

    def _handle_attack(self, message):
        attacker = message.get("attacker")
        move_type = message.get("move_type")
        damage_sent = message.get_int("damage")
        turn_number = message.get_int("turn_number")
        next_turn_player = message.get("next_turn_player")

        if not self.battle:
            cli.print_error("Battle not initialized")
            return

        if attacker == self.player_name:
            attacker_pokemon = self.my_pokemon
            defender_pokemon = self.opponent_pokemon
        else:
            attacker_pokemon = self.opponent_pokemon
            defender_pokemon = self.my_pokemon

        local_damage, _ = calculate_damage(
            attacker_pokemon, defender_pokemon,
            power=60,
            move_type=move_type
        )

        agreed_damage = max(local_damage, damage_sent) if local_damage != damage_sent else damage_sent
        defender_pokemon.take_damage(agreed_damage)
        cli.print_info(f"{attacker} attacked with {move_type} for {agreed_damage} damage!")

        ack_msg = create_attack_ack(defender_pokemon.current_hp)
        self.send_message(ack_msg)

        self.pending_attack = {
            'turn_number': turn_number,
            'damage': agreed_damage,
            'next_turn_player': next_turn_player,
            'acks': set([self.player_name])
        }

        cli.clear_screen()
        self.display_battle_state()

    def _handle_attack_ack(self, message):
        defender_hp = message.get_int("defender_hp")
        sender = message.get("sender", "opponent")
        if not self.pending_attack:
            cli.print_error("Received ACK with no pending attack")
            return

        self.pending_attack['acks'].add(sender)
        if len(self.pending_attack['acks']) >= 2:
            if defender_hp != self.my_pokemon.current_hp:
                cli.print_info(f"[Warning] HP mismatch! Local: {self.my_pokemon.current_hp}, Opponent: {defender_hp}")
                self.my_pokemon.current_hp = max(self.my_pokemon.current_hp, defender_hp)

            # Sync turn count
            self.battle.turn_count = self.pending_attack['turn_number']

            # Sync turn phase based on next_turn_player
            next_player = self.pending_attack['next_turn_player']
            if next_player == self.battle.player1_name:
                self.battle.phase = self.battle.__class__.BattlePhase.PLAYER1_TURN
            else:
                self.battle.phase = self.battle.__class__.BattlePhase.PLAYER2_TURN

            self.pending_attack = None

            if self.my_pokemon.is_fainted():
                result_msg = create_battle_result(self.opponent_name, self.player_name)
                self.send_message(result_msg)


    def _handle_battle_result(self, message):
        winner = message.get("winner")
        loser = message.get("loser")
        cli.print_battle_result(winner, loser)
        self.state_machine.transition(ConnectionState.BATTLE_ENDED, f"{winner} wins!")

    def _handle_chat_message(self, message):
        sender = message.get("sender")
        text = message.get("message")
        sticker = message.get("sticker") if message.get("sticker") else None
        chat_msg = self.chat_handler.receive_message(sender, text, sticker)
        print(f"\n{chat_msg}")

    def _handle_disconnect(self, message):
        player = message.get("player_name")
        reason = message.get("reason", "Unknown")
        cli.print_info(f"{player} disconnected: {reason}")
        self.state_machine.transition(ConnectionState.DISCONNECTED, "Peer disconnected")
        self.running = False

    # -------------------- Battle helpers -------------------- #
    def _create_battle(self):
        if not self.my_pokemon or not self.opponent_pokemon:
            cli.print_error("Cannot create battle: Missing Pokemon")
            return
        self.battle = Battle(self.player_name, self.opponent_name, self.my_pokemon, self.opponent_pokemon)

    def _start_battle(self):
        self._create_battle()
        self.battle.start_battle()
        start_msg = create_battle_start(self.battle.get_current_turn_player())
        self.send_message(start_msg)
        self.state_machine.transition(ConnectionState.BATTLE_ACTIVE, "Battle started")

    def execute_attack(self, move: Move):
        if not self.battle or not self.battle.is_player_turn(self.player_name):
            cli.print_error("Not your turn!")
            return

        if not move.use():
            cli.print_error(f"{move.name} has no remaining uses!")
            return

        result = self.battle.execute_attack(self.player_name, move)

        if result['success']:
            next_turn_player = (
                self.opponent_name
                if self.battle.get_current_turn_player() == self.player_name
                else self.player_name
            )

            attack_msg = create_attack(
                attacker=self.player_name,
                move_type=move.move_type,
                damage=result['damage'],
                turn_number=self.battle.turn_count + 1,
                next_turn_player=next_turn_player
            )
            self.send_message(attack_msg)

    def display_battle_state(self):
        """Show current battle state in CLI"""
        if not self.battle:
            return

        state = {
            'player1': {
                'name': self.player_name,
                'hp': self.my_pokemon.current_hp,
                'pokemon': {
                    'name': self.my_pokemon.name,
                    'type1': self.my_pokemon.type1,
                    'type2': self.my_pokemon.type2
                }
            },
            'player2': {
                'name': self.opponent_name,
                'hp': self.opponent_pokemon.current_hp,
                'pokemon': {
                    'name': self.opponent_pokemon.name,
                    'type1': self.opponent_pokemon.type1,
                    'type2': self.opponent_pokemon.type2
                }
            },
            'turn': self.battle.get_current_turn_player()
        }

        cli.print_battle_state(state)

    # -------------------- Pokémon selection / ready -------------------- #
    def select_pokemon(self):
        options = self.pokemon_db.get_random_pokemon(6)
        cli.print_pokemon_selection(options)
        choice = cli.get_number_input("Select your Pokemon", 1, len(options))
        self.my_pokemon = options[choice - 1]
        cli.print_success(f"You selected {self.my_pokemon.name}!")
        select_msg = create_pokemon_select(self.my_pokemon.pokedex_number, self.my_pokemon.name)
        self.send_message(select_msg)
        self.state_machine.transition(ConnectionState.POKEMON_SELECTION, "Pokemon selected")
        return True

    def send_ready(self):
        ready_msg = create_ready()
        self.send_message(ready_msg)
        cli.print_waiting("Waiting for opponent to be ready...")

    # -------------------- Connection helpers -------------------- #
    def wait_for_connection(self, timeout: float = 30.0):
        """Wait until the client is connected to a peer"""
        start_time = time.time()
        while self.running and self.state_machine.get_state() != ConnectionState.CONNECTED:
            if time.time() - start_time > timeout:
                cli.print_error("Timeout waiting for peer to connect")
                return False
            time.sleep(0.1)
        return True
    
    # -------------------- Connection helpers -------------------- #
    def connect_to_peer(self, peer_host: str, peer_port: int):
        """Set peer address and send HELLO message to initiate connection"""
        if not self.udp_client:
            cli.print_error("UDP client not started")
            return False

        self.udp_client.set_peer(peer_host, peer_port)

        from protocol.messages import create_hello
        hello_msg = create_hello(self.player_name, self.role)
        self.send_message(hello_msg)

        self.state_machine.transition(ConnectionState.CONNECTING, "Sent HELLO")
        cli.print_waiting("Waiting for HELLO_ACK...")
        return True


