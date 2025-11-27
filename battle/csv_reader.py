import csv
from pokemon import Pokemon
from move import generate_random_moves  # your move generator

class PokemonCSVReader:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.pokemon_list = []

    def load_pokemon(self):
        with open(self.csv_file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create Pokemon object
                p = Pokemon(
                    pokedex_number=int(row['pokedex_number']),
                    name=row['name'],
                    classification=row['classification'],
                    type1=row['type1'],
                    type2=row['type2'] or None,
                    hp=int(row['hp']),
                    attack=int(row['attack']),
                    defense=int(row['defense']),
                    sp_attack=int(row['sp_attack']),
                    sp_defense=int(row['sp_defense']),
                    speed=int(row['speed']),
                    base_total=int(row['base_total']),
                    abilities=row['abilities'].split(';'),  # or your format
                    type_effectiveness={}  # optionally fill from CSV
                )

                # Generate moves automatically here
                p.normal_moves, p.special_moves = generate_random_moves(p.type1)

                self.pokemon_list.append(p)

        return self.pokemon_list
