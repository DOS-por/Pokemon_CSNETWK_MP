"""
Pokemon damage calculation formulas
Based on simplified Pokemon battle mechanics
"""
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pokemon import Pokemon


def calculate_damage(attacker: 'Pokemon', defender: 'Pokemon', 
                     move_power: int = 50, move_type: str = None,
                     is_special: bool = False) -> int:
    """
    Calculate damage using simplified Pokemon formula
    
    Simplified formula:
    Damage = ((2 * Level / 5 + 2) * Power * A / D / 50 + 2) * Modifier
    
    For this implementation:
    - Level is assumed to be 50 for all Pokemon
    - A = attacker's Attack or Sp. Attack
    - D = defender's Defense or Sp. Defense
    - Modifier includes STAB, Type effectiveness, and random factor
    
    Args:
        attacker: Attacking Pokemon
        defender: Defending Pokemon
        move_power: Base power of the move (default 50)
        move_type: Type of the move (defaults to attacker's type1)
        is_special: Whether the move is special (uses Sp. Attack/Defense)
    
    Returns:
        Calculated damage amount
    """
    level = 50
    
    # Determine attack and defense stats
    if is_special:
        attack_stat = attacker.sp_attack
        defense_stat = defender.sp_defense
    else:
        attack_stat = attacker.attack
        defense_stat = defender.defense
    
    # Prevent division by zero
    if defense_stat <= 0:
        defense_stat = 1
    
    # Base damage calculation
    base_damage = ((2 * level / 5 + 2) * move_power * attack_stat / defense_stat / 50 + 2)
    
    # Calculate modifiers
    modifier = 1.0
    
    # STAB (Same Type Attack Bonus) - 1.5x if move type matches attacker's type
    if move_type is None:
        move_type = attacker.type1
    
    if move_type.lower() == attacker.type1.lower() or \
       (attacker.type2 and move_type.lower() == attacker.type2.lower()):
        modifier *= 1.5
    
    # Type effectiveness
    type_effectiveness = get_type_effectiveness(move_type, defender)
    modifier *= type_effectiveness
    
    # Random factor (0.85 to 1.0)
    random_factor = random.uniform(0.85, 1.0)
    modifier *= random_factor
    
    # Calculate final damage
    damage = int(base_damage * modifier)
    
    # Ensure at least 1 damage if attack connects
    return max(1, damage)


def get_type_effectiveness(attack_type: str, defender: 'Pokemon') -> float:
    """
    Get type effectiveness multiplier
    
    Args:
        attack_type: Type of the attacking move
        defender: Defending Pokemon
    
    Returns:
        Effectiveness multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
    """
    attack_type = attack_type.lower()
    
    # Get effectiveness from defender's type chart
    # The CSV contains how much damage this Pokemon takes from each type
    effectiveness = defender.type_effectiveness.get(attack_type, 1.0)
    
    return effectiveness


def calculate_critical_hit(base_damage: int) -> int:
    """
    Calculate critical hit damage (2x damage)
    Critical hit chance is 1/24 (~4.17%)
    
    Args:
        base_damage: Base damage before critical
    
    Returns:
        Damage after critical calculation
    """
    if random.randint(1, 24) == 1:
        return base_damage * 2
    return base_damage


def calculate_damage_with_critical(attacker: 'Pokemon', defender: 'Pokemon',
                                   move_power: int = 50, move_type: str = None,
                                   is_special: bool = False) -> tuple[int, bool]:
    """
    Calculate damage with critical hit chance
    
    Returns:
        tuple: (damage, is_critical)
    """
    base_damage = calculate_damage(attacker, defender, move_power, move_type, is_special)
    
    # Check for critical hit
    if random.randint(1, 24) == 1:
        return base_damage * 2, True
    
    return base_damage, False


def get_move_power_by_type(pokemon_type: str) -> int:
    """
    Get default move power based on Pokemon type
    This is a simplified version - in real Pokemon, moves have different powers
    
    Returns:
        Base power of the move
    """
    # Standard move powers by type (simplified)
    type_powers = {
        'normal': 50,
        'fire': 55,
        'water': 55,
        'electric': 55,
        'grass': 55,
        'ice': 55,
        'fighting': 60,
        'poison': 50,
        'ground': 60,
        'flying': 55,
        'psychic': 55,
        'bug': 50,
        'rock': 60,
        'ghost': 55,
        'dragon': 60,
        'dark': 55,
        'steel': 55,
        'fairy': 55
    }
    
    return type_powers.get(pokemon_type.lower(), 50)


def is_move_special(move_type: str) -> bool:
    """
    Determine if a move type is special or physical
    
    Physical: Normal, Fighting, Flying, Poison, Ground, Rock, Bug, Ghost, Steel
    Special: Fire, Water, Electric, Grass, Ice, Psychic, Dragon, Dark, Fairy
    
    Returns:
        True if special, False if physical
    """
    special_types = {
        'fire', 'water', 'electric', 'grass', 'ice',
        'psychic', 'dragon', 'dark', 'fairy'
    }
    
    return move_type.lower() in special_types


def format_effectiveness(multiplier: float) -> str:
    """Format type effectiveness for display"""
    if multiplier == 0:
        return "No effect!"
    elif multiplier < 0.5:
        return "Not very effective..."
    elif multiplier < 1.0:
        return "Not very effective"
    elif multiplier == 1.0:
        return ""
    elif multiplier < 2.0:
        return "It's super effective!"
    else:
        return "It's super effective!!"
