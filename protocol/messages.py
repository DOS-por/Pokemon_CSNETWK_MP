"""
Protocol message encoding and decoding
Messages follow key: value\n format as per PokeProtocol RFC
"""
from typing import Dict, Optional, Any
import config


class ProtocolMessage:
    """Represents a protocol message with key-value pairs"""
    
    def __init__(self, msg_type: str):
        """
        Initialize message with type
        
        Args:
            msg_type: Message type (HELLO, ATTACK, etc.)
        """
        self.type = msg_type
        self.fields: Dict[str, str] = {}
        self.sequence: Optional[int] = None
    
    def set(self, key: str, value: Any) -> 'ProtocolMessage':
        """
        Set a field value (chainable)
        
        Args:
            key: Field name
            value: Field value
        
        Returns:
            Self for chaining
        """
        self.fields[key] = str(value)
        return self
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get a field value
        
        Args:
            key: Field name
            default: Default value if key not found
        
        Returns:
            Field value or default
        """
        return self.fields.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get field as integer"""
        try:
            return int(self.fields.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get field as float"""
        try:
            return float(self.fields.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def encode(self) -> bytes:
        """
        Encode message to bytes in key: value\n format
        Note: sequence number is added by reliability layer
        
        Returns:
            Encoded message bytes
        """
        lines = [f"type: {self.type}"]
        
        for key, value in self.fields.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")  # Empty line at end
        message = "\n".join(lines)
        
        return message.encode('utf-8')
    
    def __str__(self) -> str:
        """String representation"""
        return f"ProtocolMessage({self.type}, {self.fields})"


def decode_message(data: bytes) -> Optional[ProtocolMessage]:
    """
    Decode bytes into ProtocolMessage
    
    Args:
        data: Raw message bytes
    
    Returns:
        ProtocolMessage or None if invalid
    """
    try:
        decoded = data.decode('utf-8', errors='ignore')
        lines = decoded.strip().split('\n')
        
        if not lines:
            return None
        
        msg_type = None
        sequence = None
        fields = {}
        
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if key == 'type':
                msg_type = value
            elif key == 'seq':
                try:
                    sequence = int(value)
                except ValueError:
                    pass
            else:
                fields[key] = value
        
        if not msg_type:
            return None
        
        message = ProtocolMessage(msg_type)
        message.fields = fields
        message.sequence = sequence
        
        return message
        
    except Exception as e:
        if config.DEBUG_MODE:
            print(f"[ERROR] Failed to decode message: {e}")
        return None


# Message builder helper functions

def create_hello(player_name: str, role: str = config.ROLE_JOINER) -> ProtocolMessage:
    """Create HELLO message"""
    return ProtocolMessage(config.MSG_TYPE_HELLO) \
        .set("player_name", player_name) \
        .set("role", role)


def create_hello_ack(player_name: str) -> ProtocolMessage:
    """Create HELLO_ACK message"""
    return ProtocolMessage(config.MSG_TYPE_HELLO_ACK) \
        .set("player_name", player_name) \
        .set("status", "OK")


def create_pokemon_select(pokemon_number: int, pokemon_name: str) -> ProtocolMessage:
    """Create POKEMON_SELECT message"""
    return ProtocolMessage(config.MSG_TYPE_POKEMON_SELECT) \
        .set("pokemon_number", pokemon_number) \
        .set("pokemon_name", pokemon_name)


def create_pokemon_select_ack() -> ProtocolMessage:
    """Create POKEMON_SELECT_ACK message"""
    return ProtocolMessage(config.MSG_TYPE_POKEMON_SELECT_ACK) \
        .set("status", "OK")


def create_ready() -> ProtocolMessage:
    """Create READY message"""
    return ProtocolMessage(config.MSG_TYPE_READY) \
        .set("status", "READY")


def create_ready_ack() -> ProtocolMessage:
    """Create READY_ACK message"""
    return ProtocolMessage(config.MSG_TYPE_READY_ACK) \
        .set("status", "OK")


def create_battle_start(first_player: str) -> ProtocolMessage:
    """Create BATTLE_START message"""
    return ProtocolMessage(config.MSG_TYPE_BATTLE_START) \
        .set("first_player", first_player)


def create_attack(attacker: str, move_type: str, damage: int,
                  turn_number: int, next_turn_player: str) -> ProtocolMessage:
    return ProtocolMessage(config.MSG_TYPE_ATTACK) \
        .set("attacker", attacker) \
        .set("move_type", move_type) \
        .set("damage", damage) \
        .set("turn_number", turn_number) \
        .set("next_turn_player", next_turn_player)



def create_attack_ack(defender_hp: int) -> ProtocolMessage:
    """Create ATTACK_ACK message"""
    return ProtocolMessage(config.MSG_TYPE_ATTACK_ACK) \
        .set("defender_hp", defender_hp) \
        .set("status", "OK")


def create_battle_result(winner: str, loser: str) -> ProtocolMessage:
    """Create BATTLE_RESULT message"""
    return ProtocolMessage(config.MSG_TYPE_BATTLE_RESULT) \
        .set("winner", winner) \
        .set("loser", loser)


def create_battle_end(reason: str = "NORMAL") -> ProtocolMessage:
    """Create BATTLE_END message"""
    return ProtocolMessage(config.MSG_TYPE_BATTLE_END) \
        .set("reason", reason)


def create_chat_message(sender: str, message: str, 
                       sticker: Optional[str] = None) -> ProtocolMessage:
    """Create CHAT_MESSAGE"""
    msg = ProtocolMessage(config.MSG_TYPE_CHAT_MESSAGE) \
        .set("sender", sender) \
        .set("message", message)
    
    if sticker:
        msg.set("sticker", sticker)
    
    return msg


def create_chat_ack() -> ProtocolMessage:
    """Create CHAT_ACK message"""
    return ProtocolMessage(config.MSG_TYPE_CHAT_ACK) \
        .set("status", "OK")


def create_disconnect(player_name: str, reason: str = "USER_QUIT") -> ProtocolMessage:
    """Create DISCONNECT message"""
    return ProtocolMessage(config.MSG_TYPE_DISCONNECT) \
        .set("player_name", player_name) \
        .set("reason", reason)


def create_error(error_code: str, error_message: str) -> ProtocolMessage:
    """Create ERROR message"""
    return ProtocolMessage(config.MSG_TYPE_ERROR) \
        .set("error_code", error_code) \
        .set("error_message", error_message)


# Message validation

def validate_message(message: ProtocolMessage) -> tuple[bool, str]:
    """
    Validate message has required fields
    
    Returns:
        (is_valid, error_message)
    """
    msg_type = message.type
    
    # Required fields for each message type
    required_fields = {
        config.MSG_TYPE_HELLO: ["player_name", "role"],
        config.MSG_TYPE_HELLO_ACK: ["player_name"],
        config.MSG_TYPE_POKEMON_SELECT: ["pokemon_number", "pokemon_name"],
        config.MSG_TYPE_READY: [],
        config.MSG_TYPE_BATTLE_START: ["first_player"],
        config.MSG_TYPE_ATTACK: ["attacker", "move_type", "damage", "turn_number", "next_turn_player"],
        config.MSG_TYPE_ATTACK_ACK: ["defender_hp"],
        config.MSG_TYPE_BATTLE_RESULT: ["winner", "loser"],
        config.MSG_TYPE_CHAT_MESSAGE: ["sender", "message"],
        config.MSG_TYPE_DISCONNECT: ["player_name"],
    }
    
    if msg_type not in required_fields:
        return True, ""  # Unknown type, assume valid
    
    for field in required_fields[msg_type]:
        if field not in message.fields or not message.fields[field]:
            return False, f"Missing required field: {field}"
    
    return True, ""
