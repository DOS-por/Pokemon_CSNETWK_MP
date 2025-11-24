"""
Pokemon class and data loading from CSV
"""
import csv
import os
from typing import Dict, List, Optional


class Pokemon:
    """Represents a Pokemon with its stats and abilities"""
    
    def __init__(self, data: Dict[str, str]):
        """Initialize Pokemon from CSV row data"""
        self.pokedex_number = int(data['pokedex_number'])
        self.name = data['name']
        self.japanese_name = data['japanese_name']
        self.classification = data['classfication']  # Note: typo in CSV
        
        # Types
        self.type1 = data['type1']
        self.type2 = data['type2'] if data['type2'] else None
        
        # Base stats
        self.hp = int(data['hp'])
        self.attack = int(data['attack'])
        self.defense = int(data['defense'])
        self.sp_attack = int(data['sp_attack'])
        self.sp_defense = int(data['sp_defense'])
        self.speed = int(data['speed'])
        self.base_total = int(data['base_total'])
        
        # Battle stats (current HP for battle)
        self.current_hp = self.hp
        self.max_hp = self.hp
        
        # Abilities
        self.abilities = self._parse_abilities(data['abilities'])
        
        # Type effectiveness
        self.type_effectiveness = {
            'bug': float(data['against_bug']),
            'dark': float(data['against_dark']),
            'dragon': float(data['against_dragon']),
            'electric': float(data['against_electric']),
            'fairy': float(data['against_fairy']),
            'fight': float(data['against_fight']),
            'fire': float(data['against_fire']),
            'flying': float(data['against_flying']),
            'ghost': float(data['against_ghost']),
            'grass': float(data['against_grass']),
            'ground': float(data['against_ground']),
            'ice': float(data['against_ice']),
            'normal': float(data['against_normal']),
            'poison': float(data['against_poison']),
            'psychic': float(data['against_psychic']),
            'rock': float(data['against_rock']),
            'steel': float(data['against_steel']),
            'water': float(data['against_water'])
        }
        
        # Additional info
        self.generation = int(data['generation'])
        self.is_legendary = bool(int(data['is_legendary']))
        self.height_m = float(data['height_m']) if data['height_m'] else 0.0
        self.weight_kg = float(data['weight_kg']) if data['weight_kg'] else 0.0
        self.capture_rate = int(data['capture_rate'])
        
    def _parse_abilities(self, abilities_str: str) -> List[str]:
        """Parse abilities from string format ['Ability1', 'Ability2']"""
        if not abilities_str or abilities_str == '[]':
            return []
        # Remove brackets and quotes, split by comma
        abilities_str = abilities_str.strip("[]").replace("'", "").replace('"', '')
        return [a.strip() for a in abilities_str.split(',') if a.strip()]
    
    def take_damage(self, damage: int) -> int:
        """Apply damage and return actual damage dealt"""
        actual_damage = min(damage, self.current_hp)
        self.current_hp -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal Pokemon and return actual amount healed"""
        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal
    
    def is_fainted(self) -> bool:
        """Check if Pokemon has fainted"""
        return self.current_hp <= 0
    
    def reset_hp(self):
        """Reset HP to maximum"""
        self.current_hp = self.max_hp
    
    def get_hp_percentage(self) -> float:
        """Get current HP as percentage"""
        return (self.current_hp / self.max_hp) * 100 if self.max_hp > 0 else 0
    
    def __str__(self) -> str:
        """String representation"""
        types = f"{self.type1}/{self.type2}" if self.type2 else self.type1
        return (f"{self.name} (#{self.pokedex_number}) - {types}\n"
                f"HP: {self.current_hp}/{self.max_hp} | "
                f"ATK: {self.attack} | DEF: {self.defense} | "
                f"SPD: {self.speed}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for message passing"""
        return {
            'pokedex_number': self.pokedex_number,
            'name': self.name,
            'type1': self.type1,
            'type2': self.type2 or '',
            'hp': self.hp,
            'current_hp': self.current_hp,
            'attack': self.attack,
            'defense': self.defense,
            'sp_attack': self.sp_attack,
            'sp_defense': self.sp_defense,
            'speed': self.speed
        }


class PokemonDatabase:
    """Load and manage Pokemon data from CSV"""
    
    def __init__(self, csv_path: str):
        """Load Pokemon database from CSV file"""
        self.pokemon: Dict[int, Pokemon] = {}
        self.pokemon_by_name: Dict[str, Pokemon] = {}
        self._load_csv(csv_path)
    
    def _load_csv(self, csv_path: str):
        """Load Pokemon from CSV file"""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Pokemon CSV not found: {csv_path}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pokemon = Pokemon(row)
                    self.pokemon[pokemon.pokedex_number] = pokemon
                    self.pokemon_by_name[pokemon.name.lower()] = pokemon
                except (ValueError, KeyError):
                    # Silently skip Pokemon with malformed data
                    continue
    
    def get_by_number(self, number: int) -> Optional[Pokemon]:
        """Get Pokemon by Pokedex number"""
        return self.pokemon.get(number)
    
    def get_by_name(self, name: str) -> Optional[Pokemon]:
        """Get Pokemon by name (case-insensitive)"""
        return self.pokemon_by_name.get(name.lower())
    
    def get_random_pokemon(self, count: int = 1) -> List[Pokemon]:
        """Get random Pokemon for selection"""
        import random
        available = list(self.pokemon.values())
        return random.sample(available, min(count, len(available)))
    
    def search(self, query: str) -> List[Pokemon]:
        """Search Pokemon by name (partial match)"""
        query = query.lower()
        results = []
        for pokemon in self.pokemon.values():
            if query in pokemon.name.lower():
                results.append(pokemon)
        return results
    
    def get_all(self) -> List[Pokemon]:
        """Get all Pokemon"""
        return list(self.pokemon.values())
    
    def count(self) -> int:
        """Get total number of Pokemon"""
        return len(self.pokemon)
    
    def __len__(self) -> int:
        return len(self.pokemon)
