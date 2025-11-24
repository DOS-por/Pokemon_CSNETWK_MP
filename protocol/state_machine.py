"""
State machine for managing battle protocol states and transitions
"""
from enum import Enum
from typing import Optional, Callable
import config


class ConnectionState(Enum):
    """Connection states following PokeProtocol"""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    POKEMON_SELECTION = "POKEMON_SELECTION"
    READY = "READY"
    BATTLE_ACTIVE = "BATTLE_ACTIVE"
    BATTLE_ENDED = "BATTLE_ENDED"


class StateMachine:
    """
    Manages protocol state transitions
    Ensures messages are sent/received in correct order
    """
    
    def __init__(self):
        """Initialize state machine"""
        self.state = ConnectionState.DISCONNECTED
        self.callbacks = {}
        self.transition_log = []
    
    def get_state(self) -> ConnectionState:
        """Get current state"""
        return self.state
    
    def can_transition(self, to_state: ConnectionState) -> bool:
        """
        Check if transition to new state is valid
        
        Args:
            to_state: Target state
        
        Returns:
            True if transition is allowed
        """
        # Define valid transitions
        valid_transitions = {
            ConnectionState.DISCONNECTED: [
                ConnectionState.CONNECTING
            ],
            ConnectionState.CONNECTING: [
                ConnectionState.CONNECTED,
                ConnectionState.DISCONNECTED
            ],
            ConnectionState.CONNECTED: [
                ConnectionState.POKEMON_SELECTION,
                ConnectionState.DISCONNECTED
            ],
            ConnectionState.POKEMON_SELECTION: [
                ConnectionState.READY,
                ConnectionState.DISCONNECTED
            ],
            ConnectionState.READY: [
                ConnectionState.BATTLE_ACTIVE,
                ConnectionState.DISCONNECTED
            ],
            ConnectionState.BATTLE_ACTIVE: [
                ConnectionState.BATTLE_ENDED,
                ConnectionState.DISCONNECTED
            ],
            ConnectionState.BATTLE_ENDED: [
                ConnectionState.DISCONNECTED,
                ConnectionState.POKEMON_SELECTION  # For rematch
            ]
        }
        
        allowed = valid_transitions.get(self.state, [])
        return to_state in allowed
    
    def transition(self, to_state: ConnectionState, reason: str = "") -> bool:
        """
        Transition to new state
        
        Args:
            to_state: Target state
            reason: Reason for transition (for logging)
        
        Returns:
            True if transition successful
        """
        if not self.can_transition(to_state):
            if config.DEBUG_MODE:
                print(f"[STATE] Invalid transition: {self.state.value} -> {to_state.value}")
            return False
        
        old_state = self.state
        self.state = to_state
        
        # Log transition
        log_entry = f"{old_state.value} -> {to_state.value}"
        if reason:
            log_entry += f" ({reason})"
        self.transition_log.append(log_entry)
        
        if config.DEBUG_MODE:
            print(f"[STATE] {log_entry}")
        
        # Call state change callback
        self._trigger_callback(to_state, old_state)
        
        return True
    
    def register_callback(self, state: ConnectionState, callback: Callable):
        """
        Register callback for state entry
        
        Args:
            state: State to trigger on
            callback: Function to call when entering state
        """
        if state not in self.callbacks:
            self.callbacks[state] = []
        self.callbacks[state].append(callback)
    
    def _trigger_callback(self, new_state: ConnectionState, old_state: ConnectionState):
        """Trigger callbacks for state change"""
        if new_state in self.callbacks:
            for callback in self.callbacks[new_state]:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    print(f"[ERROR] State callback error: {e}")
    
    def reset(self):
        """Reset state machine to initial state"""
        self.state = ConnectionState.DISCONNECTED
        self.transition_log.clear()
    
    def get_transition_log(self) -> list:
        """Get state transition history"""
        return self.transition_log.copy()
    
    def is_connected(self) -> bool:
        """Check if in any connected state"""
        return self.state not in [
            ConnectionState.DISCONNECTED,
            ConnectionState.CONNECTING
        ]
    
    def is_in_battle(self) -> bool:
        """Check if battle is active"""
        return self.state == ConnectionState.BATTLE_ACTIVE
    
    def can_send_message(self, msg_type: str) -> bool:
        """
        Check if message type can be sent in current state
        
        Args:
            msg_type: Message type to check
        
        Returns:
            True if message can be sent
        """
        # Message types allowed per state
        allowed_messages = {
            ConnectionState.DISCONNECTED: [],
            ConnectionState.CONNECTING: [
                config.MSG_TYPE_HELLO,
                config.MSG_TYPE_HELLO_ACK
            ],
            ConnectionState.CONNECTED: [
                config.MSG_TYPE_POKEMON_SELECT,
                config.MSG_TYPE_POKEMON_SELECT_ACK,
                config.MSG_TYPE_CHAT_MESSAGE,
                config.MSG_TYPE_DISCONNECT
            ],
            ConnectionState.POKEMON_SELECTION: [
                config.MSG_TYPE_READY,
                config.MSG_TYPE_READY_ACK,
                config.MSG_TYPE_CHAT_MESSAGE,
                config.MSG_TYPE_DISCONNECT
            ],
            ConnectionState.READY: [
                config.MSG_TYPE_BATTLE_START,
                config.MSG_TYPE_CHAT_MESSAGE,
                config.MSG_TYPE_DISCONNECT
            ],
            ConnectionState.BATTLE_ACTIVE: [
                config.MSG_TYPE_ATTACK,
                config.MSG_TYPE_ATTACK_ACK,
                config.MSG_TYPE_BATTLE_RESULT,
                config.MSG_TYPE_CHAT_MESSAGE,
                config.MSG_TYPE_DISCONNECT
            ],
            ConnectionState.BATTLE_ENDED: [
                config.MSG_TYPE_BATTLE_END,
                config.MSG_TYPE_CHAT_MESSAGE,
                config.MSG_TYPE_DISCONNECT
            ]
        }
        
        # CHAT_MESSAGE and DISCONNECT can be sent in most states
        if msg_type in [config.MSG_TYPE_CHAT_MESSAGE, config.MSG_TYPE_DISCONNECT]:
            return self.is_connected()
        
        allowed = allowed_messages.get(self.state, [])
        return msg_type in allowed
