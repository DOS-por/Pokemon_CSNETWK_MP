"""
Configuration file for PokeProtocol
Contains ports, timeouts, constants, and feature flags
"""

# Network Configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
BUFFER_SIZE = 4096

# Reliability Configuration
ACK_TIMEOUT = 2.0  # seconds to wait for ACK before retransmission
MAX_RETRIES = 5    # maximum retransmission attempts
SEQUENCE_START = 0
MAX_SEQUENCE = 65535

# Battle Configuration
MAX_POKEMON_TEAM = 6
DEFAULT_BATTLE_TIMEOUT = 60  # seconds per turn

# Message Types
MSG_TYPE_HELLO = "HELLO"
MSG_TYPE_HELLO_ACK = "HELLO_ACK"
MSG_TYPE_POKEMON_SELECT = "POKEMON_SELECT"
MSG_TYPE_POKEMON_SELECT_ACK = "POKEMON_SELECT_ACK"
MSG_TYPE_READY = "READY"
MSG_TYPE_READY_ACK = "READY_ACK"
MSG_TYPE_BATTLE_START = "BATTLE_START"
MSG_TYPE_ATTACK = "ATTACK"
MSG_TYPE_ATTACK_ACK = "ATTACK_ACK"
MSG_TYPE_BATTLE_RESULT = "BATTLE_RESULT"
MSG_TYPE_BATTLE_END = "BATTLE_END"
MSG_TYPE_CHAT_MESSAGE = "CHAT_MESSAGE"
MSG_TYPE_CHAT_ACK = "CHAT_ACK"
MSG_TYPE_DISCONNECT = "DISCONNECT"
MSG_TYPE_ERROR = "ERROR"
MSG_TYPE_BATTLE_STATE = "BATTLE_STATE"

# Battle States
STATE_IDLE = "IDLE"
STATE_CONNECTING = "CONNECTING"
STATE_POKEMON_SELECTION = "POKEMON_SELECTION"
STATE_READY = "READY"
STATE_BATTLE = "BATTLE"
STATE_BATTLE_END = "BATTLE_END"
STATE_DISCONNECTED = "DISCONNECTED"

# Sticker Types
STICKERS = {
    "1": "😀 Happy",
    "2": "😢 Sad",
    "3": "😠 Angry",
    "4": "👍 Thumbs Up",
    "5": "❤️ Heart",
    "6": "🔥 Fire",
    "7": "⚡ Thunder",
    "8": "💧 Water",
    "9": "🌿 Grass",
    "10": "🎉 Party"
}

# Role Types
ROLE_HOST = "HOST"
ROLE_JOINER = "JOINER"
ROLE_SPECTATOR = "SPECTATOR"

# Debug Flags
DEBUG_MODE = False
VERBOSE_LOGGING = False

# File Paths
POKEMON_DATA_FILE = "data/pokemon.csv"
