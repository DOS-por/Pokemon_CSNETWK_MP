"""
Terminal CLI for Pokemon Battle System
"""
import os
import sys
from typing import Optional
import config


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str):
    """Print formatted header"""
    width = 60
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def print_section(title: str):
    """Print section title"""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print('─' * 60)


def print_pokemon_display(pokemon, player_name: str):
    """
    Display Pokemon information in battle format
    
    Args:
        pokemon: Pokemon object
        player_name: Owner's name
    """
    hp_bar = create_hp_bar(pokemon.current_hp, pokemon.max_hp, 20)
    hp_percent = pokemon.get_hp_percentage()
    
    types = f"{pokemon.type1}/{pokemon.type2}" if pokemon.type2 else pokemon.type1
    
    print(f"\n{player_name}'s {pokemon.name} ({types})")
    print(f"HP: {hp_bar} {pokemon.current_hp}/{pokemon.max_hp} ({hp_percent:.1f}%)")
    print(f"ATK: {pokemon.attack}  DEF: {pokemon.defense}  SPD: {pokemon.speed}")


def create_hp_bar(current_hp: int, max_hp: int, length: int = 20) -> str:
    """
    Create ASCII HP bar
    
    Args:
        current_hp: Current HP
        max_hp: Maximum HP
        length: Length of bar in characters
    
    Returns:
        HP bar string
    """
    if max_hp <= 0:
        filled = 0
    else:
        filled = int((current_hp / max_hp) * length)
    
    empty = length - filled
    
    # Color based on HP percentage
    hp_percent = (current_hp / max_hp * 100) if max_hp > 0 else 0
    
    if hp_percent > 50:
        bar = "█" * filled + "░" * empty
    elif hp_percent > 25:
        bar = "▓" * filled + "░" * empty
    else:
        bar = "▒" * filled + "░" * empty
    
    return f"[{bar}]"


def print_battle_state(battle_state: dict):
    """
    Display current battle state
    
    Args:
        battle_state: Battle state dictionary
    """
    clear_screen()
    print_header("⚔️  POKEMON BATTLE  ⚔️")
    
    p1 = battle_state['player1']
    p2 = battle_state['player2']
    
    # Player 1 (left side)
    print(f"\n{p1['name']}")
    print(f"  {p1['pokemon']['name']} - {p1['pokemon']['type1']}", end='')
    if p1['pokemon']['type2']:
        print(f"/{p1['pokemon']['type2']}", end='')
    print()
    
    hp_bar1 = create_hp_bar(p1['pokemon']['hp'], p1['pokemon']['max_hp'], 20)
    print(f"  HP: {hp_bar1} {p1['pokemon']['hp']}/{p1['pokemon']['max_hp']}")
    
    print("\n          VS")
    
    # Player 2 (right side)
    print(f"\n{p2['name']}")
    print(f"  {p2['pokemon']['name']} - {p2['pokemon']['type1']}", end='')
    if p2['pokemon']['type2']:
        print(f"/{p2['pokemon']['type2']}", end='')
    print()
    
    hp_bar2 = create_hp_bar(p2['pokemon']['hp'], p2['pokemon']['max_hp'], 20)
    print(f"  HP: {hp_bar2} {p2['pokemon']['hp']}/{p2['pokemon']['max_hp']}")
    
    # Turn info
    print(f"\n{'─' * 60}")
    print(f"Turn {battle_state['turn_count']} - {battle_state['current_turn']}'s turn")
    print('─' * 60)


def print_pokemon_selection(pokemon_list):
    """
    Display Pokemon selection menu
    
    Args:
        pokemon_list: List of Pokemon objects
    """
    print_section("Select Your Pokemon")
    
    for i, pokemon in enumerate(pokemon_list, 1):
        types = f"{pokemon.type1}/{pokemon.type2}" if pokemon.type2 else pokemon.type1
        print(f"{i}. {pokemon.name} ({types}) - HP: {pokemon.hp}, ATK: {pokemon.attack}, DEF: {pokemon.defense}, SPATK: {pokemon.sp_attack}, SPDEF: {pokemon.sp_defense},SPEED: {pokemon.speed}")


def get_user_input(prompt: str, valid_options: Optional[list] = None) -> str:
    """
    Get user input with validation
    
    Args:
        prompt: Prompt message
        valid_options: List of valid options (None for any input)
    
    Returns:
        User input
    """
    while True:
        user_input = input(f"\n{prompt}: ").strip()
        
        if not user_input:
            print("Input cannot be empty. Try again.")
            continue
        
        if valid_options is None:
            return user_input
        
        if user_input.lower() in [opt.lower() for opt in valid_options]:
            return user_input
        
        print(f"Invalid option. Please choose from: {', '.join(valid_options)}")


def get_number_input(prompt: str, min_val: int = 1, max_val: int = 100) -> int:
    """
    Get numeric input with validation
    
    Args:
        prompt: Prompt message
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Integer value
    """
    while True:
        try:
            value = int(input(f"\n{prompt} ({min_val}-{max_val}): ").strip())
            if min_val <= value <= max_val:
                return value
            print(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("Please enter a valid number.")


def print_battle_log(log_entries: list, count: int = 5):
    """
    Display battle log
    
    Args:
        log_entries: List of log messages
        count: Number of recent entries to show
    """
    print_section("Battle Log")
    
    recent = log_entries[-count:] if len(log_entries) > count else log_entries
    
    for entry in recent:
        print(f"  • {entry}")


def print_chat_messages(messages, count: int = 5):
    """
    Display chat messages
    
    Args:
        messages: List of ChatMessage objects
        count: Number of recent messages to show
    """
    if not messages:
        return
    
    print_section("Chat")
    
    recent = messages[-count:] if len(messages) > count else messages
    
    for msg in recent:
        print(f"  {msg}")


def print_menu(title: str, options: list) -> int:
    """
    Display menu and get selection
    
    Args:
        title: Menu title
        options: List of menu options
    
    Returns:
        Selected option index (0-based)
    """
    print_section(title)
    
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    
    return get_number_input("Select option", 1, len(options)) - 1


def print_connection_info(role: str, host: str, port: int, peer_host: str = None, peer_port: int = None):
    """Display connection information"""
    print_section("Connection Info")
    print(f"Role: {role}")
    print(f"Local: {host}:{port}")
    if peer_host and peer_port:
        print(f"Peer: {peer_host}:{peer_port}")


def print_waiting(message: str = "Waiting for opponent..."):
    """Display waiting message"""
    print(f"\n⏳ {message}")


def print_error(message: str):
    """Display error message"""
    print(f"\n❌ ERROR: {message}")


def print_success(message: str):
    """Display success message"""
    print(f"\n✅ {message}")


def print_info(message: str):
    """Display info message"""
    print(f"\nℹ️  {message}")


def print_battle_result(winner: str, loser: str):
    """Display battle result"""
    print("\n" + "=" * 60)
    print("🏆  BATTLE RESULT  🏆".center(60))
    print("=" * 60)
    print(f"\nWINNER: {winner}")
    print(f"LOSER: {loser}")
    print("\n" + "=" * 60)


def confirm_action(prompt: str) -> bool:
    """
    Get yes/no confirmation
    
    Args:
        prompt: Confirmation prompt
    
    Returns:
        True if confirmed
    """
    response = get_user_input(f"{prompt} (y/n)", ["y", "n", "yes", "no"])
    return response.lower() in ['y', 'yes']


def print_stickers():
    """Display available stickers"""
    print_section("Available Stickers")
    for sid, description in config.STICKERS.items():
        print(f"  {sid}: {description}")


def print_welcome():
    """Display welcome screen"""
    clear_screen()
    print("=" * 60)
    print("⚡  POKEPROTOCOL - UDP POKEMON BATTLE SYSTEM  ⚡".center(60))
    print("=" * 60)
    print("\nA peer-to-peer Pokemon battle system over UDP")
    print("Featuring turn-based combat, chat, and stickers!")
    print("\n" + "=" * 60)


def print_goodbye():
    """Display goodbye message"""
    print("\n" + "=" * 60)
    print("Thanks for playing!".center(60))
    print("=" * 60)


def pause(message: str = "Press Enter to continue..."):
    """Pause and wait for user"""
    input(f"\n{message}")
