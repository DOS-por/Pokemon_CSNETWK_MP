import math
from battle.move import Move

# type_effectiveness.py
import json

# Full type chart (Gen VI onward)
TYPE_CHART = {
    "Normal":   {"Rock":0.5, "Ghost":0.0, "Steel":0.5},
    "Fire":     {"Grass":2.0, "Ice":2.0, "Bug":2.0, "Steel":2.0,
                 "Fire":0.5, "Water":0.5, "Rock":0.5, "Dragon":0.5},
    "Water":    {"Fire":2.0, "Ground":2.0, "Rock":2.0,
                 "Water":0.5, "Grass":0.5, "Dragon":0.5},
    "Electric": {"Water":2.0, "Flying":2.0,
                 "Electric":0.5, "Grass":0.5, "Dragon":0.5,
                 "Ground":0.0},
    "Grass":    {"Water":2.0, "Ground":2.0, "Rock":2.0,
                 "Fire":0.5, "Grass":0.5, "Poison":0.5, "Flying":0.5,
                 "Bug":0.5, "Dragon":0.5, "Steel":0.5},
    "Ice":      {"Grass":2.0, "Ground":2.0, "Flying":2.0, "Dragon":2.0,
                 "Fire":0.5, "Water":0.5, "Ice":0.5, "Steel":0.5},
    "Fighting": {"Normal":2.0, "Ice":2.0, "Rock":2.0, "Dark":2.0, "Steel":2.0,
                 "Poison":0.5, "Flying":0.5, "Psychic":0.5, "Bug":0.5, "Fairy":0.5,
                 "Ghost":0.0},
    "Poison":   {"Grass":2.0, "Fairy":2.0,
                 "Poison":0.5, "Ground":0.5, "Rock":0.5, "Ghost":0.5,
                 "Steel":0.0},
    "Ground":   {"Fire":2.0, "Electric":2.0, "Poison":2.0, "Rock":2.0, "Steel":2.0,
                 "Grass":0.5, "Bug":0.5, "Flying":0.0},
    "Flying":   {"Grass":2.0, "Fighting":2.0, "Bug":2.0,
                 "Electric":0.5, "Rock":0.5, "Steel":0.5},
    "Psychic":  {"Fighting":2.0, "Poison":2.0,
                 "Psychic":0.5, "Steel":0.5, "Dark":0.0},
    "Bug":      {"Grass":2.0, "Psychic":2.0, "Dark":2.0,
                 "Fire":0.5, "Fighting":0.5, "Flying":0.5, "Poison":0.5,
                 "Ghost":0.5, "Steel":0.5, "Fairy":0.5},
    "Rock":     {"Fire":2.0, "Ice":2.0, "Flying":2.0, "Bug":2.0,
                 "Fighting":0.5, "Ground":0.5, "Steel":0.5},
    "Ghost":    {"Psychic":2.0, "Ghost":2.0,
                 "Dark":0.5, "Normal":0.0},
    "Dragon":   {"Dragon":2.0,
                 "Steel":0.5, "Fairy":0.0},
    "Dark":     {"Psychic":2.0, "Ghost":2.0,
                 "Fighting":0.5, "Dark":0.5, "Fairy":0.5},
    "Steel":    {"Ice":2.0, "Rock":2.0, "Fairy":2.0,
                 "Fire":0.5, "Water":0.5, "Electric":0.5, "Steel":0.5},
    "Fairy":    {"Fighting":2.0, "Dragon":2.0, "Dark":2.0,
                 "Fire":0.5, "Poison":0.5, "Steel":0.5},
}

def get_type_effectiveness(move_type: str, defender_types: list) -> float:
    move_type = move_type.capitalize()
    multiplier = 1.0
    if move_type not in TYPE_CHART:
        return 1.0
    for d_type in defender_types:
        if not d_type:  # skip None
            continue
        d_type = d_type.capitalize()
        multiplier *= TYPE_CHART[move_type].get(d_type, 1.0)
    return multiplier

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
    category = move.category

    if category == "special":
        base_attack = attacker.sp_attack
        base_defense = defender.sp_defense
    else:
        base_attack = attacker.attack
        base_defense = defender.defense

    if base_defense <= 0:
        base_defense = 1

    # Base damage formula
    damage = (move.power * base_attack
          * get_type_effectiveness(move.move_type, [defender.type1, defender.type2])
          ) / base_defense

    return math.floor(damage)