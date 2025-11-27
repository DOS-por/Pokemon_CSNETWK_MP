import random

# ---------- MOVE NAME GENERATION ----------
NORMAL_MOVE_NAMES = ["Strike", "Hit", "Slash"]
SPECIAL_SUFFIXES = ["Blast", "Ball"]

def generate_normal_move_name():
    return random.choice(NORMAL_MOVE_NAMES)

def generate_special_move_name(pokemon_type: str):
    suffix = random.choice(SPECIAL_SUFFIXES)
    return f"{pokemon_type} {suffix}"

# ---------- MOVE CLASS ----------
class Move:
    """Randomized Pokemon move"""
    def __init__(self, category: str, pokemon_type: str = None):
        self.category = category

        # Naming rules
        if category == "normal":
            self.name = generate_normal_move_name()
        elif category == "special":
            if pokemon_type is None:
                raise ValueError("Special moves require pokemon_type")
            self.name = generate_special_move_name(pokemon_type)

        # Random stats
        self.power = random.randint(20, 120)
        self.max_uses = random.randint(5, 25)
        self.current_uses = self.max_uses

    def use(self):
        if self.current_uses > 0:
            self.current_uses -= 1
            return True
        return False

    def __str__(self):
        return (f"{self.name} ({self.category}) | "
                f"Power: {self.power}, "
                f"Uses: {self.current_uses}/{self.max_uses}")

# ---------- RANDOM MOVE GENERATOR ----------
def generate_random_moves(pokemon_type: str):
    """
    Generate 2 normal moves and 2 special moves for a Pokemon.
    """
    normal_moves = [Move("normal") for _ in range(2)]
    special_moves = [Move("special", pokemon_type) for _ in range(2)]
    return normal_moves, special_moves
