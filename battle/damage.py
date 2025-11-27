"""
Pokemon damage calculation formulas
Simplified mechanics integrated with Move objects
Supports stat boosts and type effectiveness
"""
import random

def calculate_damage(attacker, defender, move, stat_boosts=None) -> int:
    """
    Calculate damage using simplified Pokemon formula.

    Args:
        attacker: Pokemon object using the move
        defender: Pokemon object being attacked
        move: Move object being used
        stat_boosts: Optional dict of temporary stat boosts
                     e.g., {'attack': 1, 'defense': 0, 'special_attack': 2, 'special_defense': 0}

    Returns:
        Calculated damage as integer
    """
    level = 50

    # Determine which stats to use
    if move.category == "special":
        base_attack = attacker.sp_attack
        base_defense = defender.sp_defense
        attack_key = 'special_attack'
        defense_key = 'special_defense'
    else:
        base_attack = attacker.attack
        base_defense = defender.defense
        attack_key = 'attack'
        defense_key = 'defense'

    # Apply stat boosts if provided
    boost_multiplier = { -6: 0.25, -5: 0.28, -4: 0.33, -3: 0.4, -2: 0.5,
                         -1: 0.66, 0: 1.0, 1: 1.5, 2: 2.0, 3: 2.5, 4: 3.0,
                         5: 3.5, 6: 4.0 }

    if stat_boosts:
        base_attack *= boost_multiplier.get(stat_boosts.get(attack_key, 0), 1.0)
        base_defense *= boost_multiplier.get(stat_boosts.get(defense_key, 0), 1.0)

    # Prevent division by zero
    if base_defense <= 0:
        base_defense = 1

    # Base damage formula
    base_damage = ((2 * level / 5 + 2) * move.power * base_attack / base_defense / 50 + 2)

    # Determine move type for STAB and type effectiveness
    move_type = "normal" if move.category == "normal" else move.name.split()[0]

    # STAB (Same Type Attack Bonus)
    if move_type.lower() == attacker.type1.lower() or \
       (attacker.type2 and move_type.lower() == attacker.type2.lower()):
        base_damage *= 1.5

    # Type effectiveness
    effectiveness = get_type_effectiveness(move_type, defender)
    base_damage *= effectiveness

    # Random factor (0.85 to 1.0)
    base_damage *= random.uniform(0.85, 1.0)

    return max(1, int(base_damage))


def get_type_effectiveness(attack_type: str, defender) -> float:
    """
    Get type effectiveness multiplier from defender's type chart.

    Args:
        attack_type: Type of the attacking move
        defender: Pokemon object being attacked

    Returns:
        Effectiveness multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
    """
    attack_type = attack_type.lower()
    return defender.type_effectiveness.get(attack_type, 1.0)


def format_effectiveness(multiplier: float) -> str:
    """Format type effectiveness for display."""
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
