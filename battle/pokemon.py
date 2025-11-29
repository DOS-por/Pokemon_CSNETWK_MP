class Pokemon:
    """Represents a Pokemon with its stats and abilities"""
    
    def __init__(
        self,
        pokedex_number: int,
        name: str,
        type1: str,
        type2: str,
        hp: int,
        attack: int,
        defense: int,
        sp_attack: int,
        sp_defense: int,
        speed: int,
        base_total: int,
        abilities: list,
        type_effectiveness: dict
    ):
        self.pokedex_number = pokedex_number
        self.name = name
        
        # Types
        self.type1 = type1
        self.type2 = type2 or None
        
        # Base stats
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.sp_attack = sp_attack
        self.sp_defense = sp_defense
        self.speed = speed
        self.base_total = base_total
        
        # Battle HP
        self.max_hp = hp
        self.current_hp = hp
        
        # Abilities & effectiveness
        self.abilities = abilities
        self.type_effectiveness = type_effectiveness

        # ----- Move Slots -----
        self.normal_moves = []   # 2 random normal moves
        self.special_moves = []  # 2 random special moves
    
    
    # ----- Battle Utility Methods -----

    def take_damage(self, damage: int) -> int:
        actual_damage = min(damage, self.current_hp)
        self.current_hp -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal
    
    def is_fainted(self) -> bool:
        return self.current_hp <= 0
    
    def reset_hp(self):
        self.current_hp = self.max_hp
    
    def get_hp_percentage(self) -> float:
        return (self.current_hp / self.max_hp) * 100
    
    def __str__(self):
        type_str = f"{self.type1}/{self.type2}" if self.type2 else self.type1
        return (f"{self.name} (#{self.pokedex_number}) - {type_str}\n"
                f"HP: {self.current_hp}/{self.max_hp} | "
                f"ATK: {self.attack} | DEF: {self.defense} | SPD: {self.speed}")
