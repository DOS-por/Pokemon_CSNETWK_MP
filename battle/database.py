import random
from battle.csv_reader import PokemonCSVReader

class PokemonDatabase:
    def __init__(self, csv_file_path: str):
        reader = PokemonCSVReader(csv_file_path)
        self.pokemon_list = reader.load_pokemon()
        # Index for quick lookup
        self.by_number = {p.pokedex_number: p for p in self.pokemon_list}
        self.by_name = {p.name.lower(): p for p in self.pokemon_list}

    def count(self) -> int:
        return len(self.pokemon_list)

    def get_by_number(self, number: int):
        return self.by_number.get(number)

    def get_by_name(self, name: str):
        return self.by_name.get(name.lower())
    def get_random_pokemon(self, count: int = 6):
        """
        Return a random selection of Pokémon from the database.
        Args:
            count: number of Pokémon to select
        Returns:
            List of Pokémon objects
        """
        if count > len(self.pokemon_list):
            count = len(self.pokemon_list)
        return random.sample(self.pokemon_list, count)