"""
Chat message and sticker handling
"""
from typing import Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import config


@dataclass
class ChatMessage:
    """Represents a chat message"""
    sender: str
    message: str
    sticker: Optional[str]
    timestamp: datetime
    
    def __str__(self) -> str:
        """Format message for display"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        
        if self.sticker:
            sticker_display = config.STICKERS.get(self.sticker, f"[Sticker {self.sticker}]")
            if self.message:
                return f"[{time_str}] {self.sender}: {self.message} {sticker_display}"
            else:
                return f"[{time_str}] {self.sender}: {sticker_display}"
        else:
            return f"[{time_str}] {self.sender}: {self.message}"


class ChatHandler:
    """Manages chat messages and stickers"""
    
    def __init__(self):
        """Initialize chat handler"""
        self.messages: List[ChatMessage] = []
        self.message_callback: Optional[Callable[[ChatMessage], None]] = None
        self.max_messages = 100  # Keep last 100 messages
    
    def send_message(self, sender: str, message: str, 
                    sticker: Optional[str] = None) -> ChatMessage:
        """
        Create and log a chat message
        
        Args:
            sender: Sender name
            message: Message text
            sticker: Optional sticker ID
        
        Returns:
            ChatMessage object
        """
        chat_msg = ChatMessage(
            sender=sender,
            message=message,
            sticker=sticker,
            timestamp=datetime.now()
        )
        
        self.add_message(chat_msg)
        return chat_msg
    
    def receive_message(self, sender: str, message: str, 
                       sticker: Optional[str] = None) -> ChatMessage:
        """
        Receive and log a chat message
        
        Args:
            sender: Sender name
            message: Message text
            sticker: Optional sticker ID
        
        Returns:
            ChatMessage object
        """
        chat_msg = ChatMessage(
            sender=sender,
            message=message,
            sticker=sticker,
            timestamp=datetime.now()
        )
        
        self.add_message(chat_msg)
        
        # Trigger callback
        if self.message_callback:
            try:
                self.message_callback(chat_msg)
            except Exception as e:
                print(f"[ERROR] Chat callback error: {e}")
        
        return chat_msg
    
    def add_message(self, chat_msg: ChatMessage):
        """Add message to history"""
        self.messages.append(chat_msg)
        
        # Keep only last N messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self, count: Optional[int] = None) -> List[ChatMessage]:
        """
        Get recent chat messages
        
        Args:
            count: Number of recent messages (None for all)
        
        Returns:
            List of ChatMessage objects
        """
        if count is None:
            return self.messages.copy()
        return self.messages[-count:]
    
    def clear_messages(self):
        """Clear all messages"""
        self.messages.clear()
    
    def set_callback(self, callback: Callable[[ChatMessage], None]):
        """Set callback for new messages"""
        self.message_callback = callback
    
    def get_available_stickers(self) -> dict:
        """Get available stickers"""
        return config.STICKERS.copy()
    
    def format_sticker_list(self) -> str:
        """Format sticker list for display"""
        lines = ["Available Stickers:"]
        for sid, description in config.STICKERS.items():
            lines.append(f"  {sid}: {description}")
        return "\n".join(lines)
    
    def validate_sticker(self, sticker_id: str) -> bool:
        """
        Check if sticker ID is valid
        
        Args:
            sticker_id: Sticker ID to validate
        
        Returns:
            True if valid
        """
        return sticker_id in config.STICKERS
    
    def add_system_message(self, message: str):
        """
        Add a system message (not from a player)
        
        Args:
            message: System message text
        """
        chat_msg = ChatMessage(
            sender="SYSTEM",
            message=message,
            sticker=None,
            timestamp=datetime.now()
        )
        self.add_message(chat_msg)
        
        if self.message_callback:
            try:
                self.message_callback(chat_msg)
            except Exception as e:
                print(f"[ERROR] Chat callback error: {e}")


def format_chat_log(messages: List[ChatMessage], count: Optional[int] = None) -> str:
    """
    Format chat messages for display
    
    Args:
        messages: List of ChatMessage objects
        count: Number of recent messages to format (None for all)
    
    Returns:
        Formatted string
    """
    if count is not None:
        messages = messages[-count:]
    
    if not messages:
        return "No messages"
    
    return "\n".join(str(msg) for msg in messages)
