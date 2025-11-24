"""
Battle logic for Pokemon combat
Handles turn-based battle flow, HP management, and win conditions
"""
from typing import Optional, Tuple
from enum import Enum
from .pokemon import Pokemon
from .damage import calculate_damage_with_critical, get_move_power_by_type, is_move_special


class BattlePhase(Enum):
    """Battle phases"""
    NOT_STARTED = "NOT_STARTED"
    PLAYER1_TURN = "PLAYER1_TURN"
    PLAYER2_TURN = "PLAYER2_TURN"
    ENDED = "ENDED"


class BattleOutcome(Enum):
    """Battle outcome"""
    ONGOING = "ONGOING"
    PLAYER1_WIN = "PLAYER1_WIN"
    PLAYER2_WIN = "PLAYER2_WIN"
    DRAW = "DRAW"
    DISCONNECT = "DISCONNECT"


class Battle:
    """Manages a Pokemon battle between two players"""
    
    def __init__(self, player1_name: str, player2_name: str,
                 player1_pokemon: Pokemon, player2_pokemon: Pokemon):
        """
        Initialize a battle
        
        Args:
            player1_name: Name of player 1
            player2_name: Name of player 2
            player1_pokemon: Player 1's Pokemon
            player2_pokemon: Player 2's Pokemon
        """
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_pokemon = player1_pokemon
        self.player2_pokemon = player2_pokemon
        
        # Reset Pokemon HP
        self.player1_pokemon.reset_hp()
        self.player2_pokemon.reset_hp()
        
        # Battle state
        self.phase = BattlePhase.NOT_STARTED
        self.turn_count = 0
        self.battle_log = []
        
        # Determine first turn based on speed
        self.first_player = self._determine_first_player()
    
    def _determine_first_player(self) -> str:
        """
        Determine which player goes first based on Pokemon speed
        
        Returns:
            Player name who goes first
        """
        if self.player1_pokemon.speed > self.player2_pokemon.speed:
            return self.player1_name
        elif self.player2_pokemon.speed > self.player1_pokemon.speed:
            return self.player2_name
        else:
            # Equal speed, random choice
            import random
            return random.choice([self.player1_name, self.player2_name])
    
    def start_battle(self):
        """Start the battle"""
        self.phase = BattlePhase.PLAYER1_TURN if self.first_player == self.player1_name \
                     else BattlePhase.PLAYER2_TURN
        
        self.log(f"Battle started between {self.player1_name}'s {self.player1_pokemon.name} "
                f"and {self.player2_name}'s {self.player2_pokemon.name}!")
        self.log(f"{self.first_player} will go first!")
    
    def execute_attack(self, attacker_name: str, move_type: Optional[str] = None) -> dict:
        """
        Execute an attack
        
        Args:
            attacker_name: Name of attacking player
            move_type: Type of move (defaults to Pokemon's type)
        
        Returns:
            Dictionary with attack results
        """
        # Validate it's the attacker's turn
        if not self.is_player_turn(attacker_name):
            return {
                'success': False,
                'error': 'Not your turn'
            }
        
        # Get attacker and defender
        if attacker_name == self.player1_name:
            attacker_pokemon = self.player1_pokemon
            defender_pokemon = self.player2_pokemon
            defender_name = self.player2_name
        else:
            attacker_pokemon = self.player2_pokemon
            defender_pokemon = self.player1_pokemon
            defender_name = self.player1_name
        
        # Determine move type
        if move_type is None:
            move_type = attacker_pokemon.type1
        
        # Calculate move power and whether it's special
        move_power = get_move_power_by_type(move_type)
        is_special_move = is_move_special(move_type)
        
        # Calculate damage
        damage, is_critical = calculate_damage_with_critical(
            attacker_pokemon, defender_pokemon, move_power, move_type, is_special_move
        )
        
        # Apply damage
        actual_damage = defender_pokemon.take_damage(damage)
        
        # Log attack
        attack_msg = f"{attacker_name}'s {attacker_pokemon.name} used {move_type.upper()} attack!"
        self.log(attack_msg)
        
        if is_critical:
            self.log("Critical hit!")
        
        self.log(f"{defender_name}'s {defender_pokemon.name} took {actual_damage} damage!")
        self.log(f"{defender_pokemon.name} HP: {defender_pokemon.current_hp}/{defender_pokemon.max_hp}")
        
        # Increment turn counter
        self.turn_count += 1
        
        # Switch turns
        self._switch_turn()
        
        # Check for battle end
        outcome = self.check_outcome()
        
        return {
            'success': True,
            'damage': actual_damage,
            'is_critical': is_critical,
            'defender_hp': defender_pokemon.current_hp,
            'defender_max_hp': defender_pokemon.max_hp,
            'attacker': attacker_name,
            'defender': defender_name,
            'move_type': move_type,
            'outcome': outcome
        }
    
    def is_player_turn(self, player_name: str) -> bool:
        """Check if it's the specified player's turn"""
        if self.phase == BattlePhase.PLAYER1_TURN:
            return player_name == self.player1_name
        elif self.phase == BattlePhase.PLAYER2_TURN:
            return player_name == self.player2_name
        return False
    
    def get_current_turn_player(self) -> Optional[str]:
        """Get the name of the player whose turn it is"""
        if self.phase == BattlePhase.PLAYER1_TURN:
            return self.player1_name
        elif self.phase == BattlePhase.PLAYER2_TURN:
            return self.player2_name
        return None
    
    def _switch_turn(self):
        """Switch to the other player's turn"""
        if self.phase == BattlePhase.PLAYER1_TURN:
            self.phase = BattlePhase.PLAYER2_TURN
        elif self.phase == BattlePhase.PLAYER2_TURN:
            self.phase = BattlePhase.PLAYER1_TURN
    
    def check_outcome(self) -> BattleOutcome:
        """
        Check if battle has ended and determine winner
        
        Returns:
            BattleOutcome enum value
        """
        p1_fainted = self.player1_pokemon.is_fainted()
        p2_fainted = self.player2_pokemon.is_fainted()
        
        if p1_fainted and p2_fainted:
            self.phase = BattlePhase.ENDED
            self.log("Both Pokemon fainted! It's a draw!")
            return BattleOutcome.DRAW
        elif p1_fainted:
            self.phase = BattlePhase.ENDED
            self.log(f"{self.player2_name} wins!")
            return BattleOutcome.PLAYER2_WIN
        elif p2_fainted:
            self.phase = BattlePhase.ENDED
            self.log(f"{self.player1_name} wins!")
            return BattleOutcome.PLAYER1_WIN
        
        return BattleOutcome.ONGOING
    
    def forfeit(self, player_name: str) -> BattleOutcome:
        """
        Handle player forfeit
        
        Args:
            player_name: Name of player who forfeited
        
        Returns:
            BattleOutcome with winner
        """
        self.phase = BattlePhase.ENDED
        
        if player_name == self.player1_name:
            self.log(f"{self.player1_name} forfeited! {self.player2_name} wins!")
            return BattleOutcome.PLAYER2_WIN
        else:
            self.log(f"{self.player2_name} forfeited! {self.player1_name} wins!")
            return BattleOutcome.PLAYER1_WIN
    
    def disconnect(self, player_name: str) -> BattleOutcome:
        """
        Handle player disconnection
        
        Args:
            player_name: Name of player who disconnected
        
        Returns:
            BattleOutcome
        """
        self.phase = BattlePhase.ENDED
        self.log(f"{player_name} disconnected!")
        return BattleOutcome.DISCONNECT
    
    def log(self, message: str):
        """Add message to battle log"""
        self.battle_log.append(message)
    
    def get_battle_log(self) -> list:
        """Get battle log"""
        return self.battle_log.copy()
    
    def get_battle_state(self) -> dict:
        """
        Get current battle state
        
        Returns:
            Dictionary with battle state information
        """
        return {
            'phase': self.phase.value,
            'turn_count': self.turn_count,
            'current_turn': self.get_current_turn_player(),
            'player1': {
                'name': self.player1_name,
                'pokemon': {
                    'name': self.player1_pokemon.name,
                    'hp': self.player1_pokemon.current_hp,
                    'max_hp': self.player1_pokemon.max_hp,
                    'type1': self.player1_pokemon.type1,
                    'type2': self.player1_pokemon.type2
                }
            },
            'player2': {
                'name': self.player2_name,
                'pokemon': {
                    'name': self.player2_pokemon.name,
                    'hp': self.player2_pokemon.current_hp,
                    'max_hp': self.player2_pokemon.max_hp,
                    'type1': self.player2_pokemon.type1,
                    'type2': self.player2_pokemon.type2
                }
            },
            'outcome': self.check_outcome().value
        }
    
    def is_active(self) -> bool:
        """Check if battle is still active"""
        return self.phase not in [BattlePhase.NOT_STARTED, BattlePhase.ENDED]
    
    def is_ended(self) -> bool:
        """Check if battle has ended"""
        return self.phase == BattlePhase.ENDED
