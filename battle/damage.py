from battle.move import Move

def is_move_special(move_type: str) -> bool:
    """
    Determine if a move type is considered special.
    Args:
        move_type: The type of the move (e.g., 'Fire', 'Water', 'Normal')
    Returns:
        True if the move is special, False otherwise
    """
    special_types = {
        "Fire", "Water", "Grass", "Electric",
        "Ice", "Psychic", "Dragon", "Dark"
    }
    return move_type.capitalize() in special_types


def get_type_effectiveness(attack_type: str, defender) -> float:
    attack_type = attack_type.lower()
    return defender.type_effectiveness.get(attack_type, 1.0)


def format_effectiveness(multiplier: float) -> str:
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


def calculate_damage(attacker, defender, move: Move):
    level = 50

    # Decide category automatically
    category = "special" if is_move_special(move.move_type) else "normal"

    if category == "special":
        base_attack = attacker.sp_attack
        base_defense = defender.sp_defense
    else:
        base_attack = attacker.attack
        base_defense = defender.defense

    if base_defense <= 0:
        base_defense = 1

    # Base damage formula
    base_damage = ((2 * level / 5 + 2) * move.power * base_attack / base_defense / 50 + 2)

    # STAB
    if move.move_type and (move.move_type.lower() == attacker.type1.lower() or
                      (attacker.type2 and move.move_type.lower() == attacker.type2.lower())):
        base_damage *= 1.5

    # Type effectiveness
    effectiveness = get_type_effectiveness(move.move_type, defender)
    base_damage *= effectiveness

    return max(1, int(base_damage))