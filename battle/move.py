class Move:
    """Represents a Pokemon move"""
    def __init__(self, name: str, category: str, move_type: str, power: int = 100, max_uses: int = 25):
        self.name = name
        self.category = category 
        self.move_type = move_type  
        self.power = power
        self.max_uses = max_uses
        self.current_uses = max_uses

    def use(self) -> bool:
        """Use the move, decrementing PP if available"""
        if self.current_uses > 0:
            self.current_uses -= 1
            return True
        return False

    def __str__(self):
        return f"{self.name} ({self.category}, {self.move_type}) | Power: {self.power}, Uses: {self.current_uses}/{self.max_uses}"


def generate_moves_for_type(pokemon_type: str):
    """
    Generate one normal and one special move for a given type.
    """
    normal_move = Move(name=f"{pokemon_type} Strike", category="normal", move_type=pokemon_type, power=60)
    special_move = Move(name=f"{pokemon_type} Blast", category="special", move_type=pokemon_type, power=60)
    return normal_move, special_move