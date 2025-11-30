from battle.move import Move, generate_moves_for_type
from battle.pokemon import Pokemon


class PokemonCSVReader:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.pokemon_list = []

    def load_pokemon(self):
        import csv
        with open(self.csv_file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create Pokemon object
                p = Pokemon(
                    pokedex_number=int(row['pokedex_number']),
                    name=row['name'],
                    type1=row['type1'],
                    type2=row['type2'] or None,
                    hp=int(row['hp']),
                    attack=int(row['attack']),
                    defense=int(row['defense']),
                    sp_attack=int(row['sp_attack']),
                    sp_defense=int(row['sp_defense']),
                    speed=int(row['speed']),
                    base_total=int(row['base_total']),
                    abilities=row['abilities'].split(';'),
                    type_effectiveness={}
                )

                # --- Generate moves automatically ---
                p.moves = []
                for t in [p.type1, p.type2] if p.type2 else [p.type1]:
                    physical_move, special_move = generate_moves_for_type(t, p.attack, p.sp_attack)
                    p.moves.extend([physical_move, special_move])

                self.pokemon_list.append(p)

        return self.pokemon_list