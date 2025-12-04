"""
Asynchronous UDP-based chat system with reliable delivery
Runs independently from the battle state machine
"""
import threading
import queue
import time
import base64
import os
from typing import Optional, Callable, Dict, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import config


class MessageType(Enum):
    """Message type enum"""
    CHAT_MESSAGE = "CHAT_MESSAGE"
    BATTLE_MESSAGE = "BATTLE_MESSAGE"


class ChatContentType(Enum):
    """Chat content type enum"""
    TEXT = "TEXT"
    STICKER = "STICKER"


@dataclass
class ChatMessage:
    """
    Represents a chat message
    
    Attributes:
        message_type: Type of message (CHAT_MESSAGE)
        sender_name: Name of the sender
        content_type: TEXT or STICKER
        message_text: Optional text content
        sticker_data: Optional Base64 encoded sticker data
        sequence_number: Sequence number for reliability
    """
    message_type: MessageType
    sender_name: str
    content_type: ChatContentType
    message_text: Optional[str] = None
    sticker_data: Optional[str] = None
    sequence_number: int = 0
    
    def __post_init__(self):
        """Validate message after initialization"""
        if self.content_type == ChatContentType.TEXT and not self.message_text:
            raise ValueError("TEXT messages must have message_text")
        if self.content_type == ChatContentType.STICKER and not self.sticker_data:
            raise ValueError("STICKER messages must have sticker_data")


def serialize_chat_message(msg: ChatMessage) -> str:
    """
    Serialize ChatMessage to RFC-style key: value format
    
    Args:
        msg: ChatMessage to serialize
    
    Returns:
        Serialized message string
    """
    lines = []
    lines.append(f"message_type: {msg.message_type.value}")
    lines.append(f"sender_name: {msg.sender_name}")
    lines.append(f"content_type: {msg.content_type.value}")
    
    if msg.message_text is not None:
        # Escape newlines in message text
        escaped_text = msg.message_text.replace('\n', '\\n')
        lines.append(f"message_text: {escaped_text}")
    
    if msg.sticker_data is not None:
        lines.append(f"sticker_data: {msg.sticker_data}")
    
    lines.append(f"sequence_number: {msg.sequence_number}")
    lines.append("")  # Empty line at end
    
    return "\n".join(lines)


def parse_chat_message(raw: str) -> ChatMessage:
    """
    Parse RFC-style message into ChatMessage
    
    Args:
        raw: Raw message string
    
    Returns:
        Parsed ChatMessage
    
    Raises:
        ValueError: If message format is invalid
    """
    lines = raw.strip().split('\n')
    fields = {}
    
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue
        
        # Split on first colon only
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        fields[key] = value
    
    # Validate required fields
    if 'message_type' not in fields:
        raise ValueError("Missing message_type field")
    
    if fields['message_type'] != MessageType.CHAT_MESSAGE.value:
        raise ValueError(f"Invalid message_type: {fields['message_type']}")
    
    if 'sender_name' not in fields:
        raise ValueError("Missing sender_name field")
    
    if 'content_type' not in fields:
        raise ValueError("Missing content_type field")
    
    # Parse content type
    try:
        content_type = ChatContentType(fields['content_type'])
    except ValueError:
        raise ValueError(f"Invalid content_type: {fields['content_type']}")
    
    # Validate content based on type
    message_text = None
    sticker_data = None
    
    if content_type == ChatContentType.TEXT:
        if 'message_text' not in fields:
            raise ValueError("TEXT messages must have message_text")
        # Unescape newlines
        message_text = fields['message_text'].replace('\\n', '\n')
    
    elif content_type == ChatContentType.STICKER:
        if 'sticker_data' not in fields:
            raise ValueError("STICKER messages must have sticker_data")
        sticker_data = fields['sticker_data']
        if not sticker_data:
            raise ValueError("STICKER messages must have non-empty sticker_data")
    
    # Parse sequence number
    sequence_number = int(fields.get('sequence_number', 0))
    
    return ChatMessage(
        message_type=MessageType.CHAT_MESSAGE,
        sender_name=fields['sender_name'],
        content_type=content_type,
        message_text=message_text,
        sticker_data=sticker_data,
        sequence_number=sequence_number
    )


class AsyncChatManager:
    """
    Manages asynchronous chat communication
    Runs independently from battle state machine
    """
    
    def __init__(self, sender_name: str, send_callback: Callable[[bytes, Tuple[str, int]], int],
                 sticker_dir: str = "stickers"):
        """
        Initialize async chat manager
        
        Args:
            sender_name: Name of this user
            send_callback: Function to send raw data (returns sequence number)
            sticker_dir: Directory to save received stickers
        """
        self.sender_name = sender_name
        self.send_callback = send_callback
        self.sticker_dir = sticker_dir
        
        # Create sticker directory if it doesn't exist
        os.makedirs(self.sticker_dir, exist_ok=True)
        
        # Queues for async communication
        self.send_queue: queue.Queue = queue.Queue()
        self.receive_queue: queue.Queue = queue.Queue()
        
        # Threads
        self.running = False
        self.send_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.message_received_callback: Optional[Callable[[ChatMessage], None]] = None
        
        # Chat history
        self.chat_history = []
        self.history_lock = threading.Lock()
    
    def start(self):
        """Start async chat manager"""
        self.running = True
        
        # Start send thread
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        
        # Start process thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        print("[ASYNC_CHAT] Started")
    
    def stop(self):
        """Stop async chat manager"""
        self.running = False
        
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=2.0)
        
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=2.0)
        
        print("[ASYNC_CHAT] Stopped")
    
    def send_text(self, text: str):
        """
        Send text message (non-blocking)
        
        Args:
            text: Text message to send
        """
        msg = ChatMessage(
            message_type=MessageType.CHAT_MESSAGE,
            sender_name=self.sender_name,
            content_type=ChatContentType.TEXT,
            message_text=text
        )
        self.send_queue.put(msg)
    
    def send_sticker(self, file_path: str) -> bool:
        """
        Send sticker image (non-blocking)
        
        Args:
            file_path: Path to sticker image file
        
        Returns:
            True if sticker is queued for sending
        """
        try:
            # Validate file size
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10 MB
                print(f"[ERROR] Sticker file too large: {file_size} bytes (max 10 MB)")
                return False
            
            # Read and encode file
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Create sticker message
            msg = ChatMessage(
                message_type=MessageType.CHAT_MESSAGE,
                sender_name=self.sender_name,
                content_type=ChatContentType.STICKER,
                sticker_data=base64_data
            )
            
            self.send_queue.put(msg)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to send sticker: {e}")
            return False
    
    def _send_loop(self):
        """Background thread for sending messages"""
        while self.running:
            try:
                # Get message from queue with timeout
                msg = self.send_queue.get(timeout=0.5)
                
                # Serialize message
                serialized = serialize_chat_message(msg)
                data = serialized.encode('utf-8')
                
                # Send via reliability layer (will add sequence number)
                # The send_callback should handle addressing to peers/spectators
                seq = self.send_callback(data, None)  # None means broadcast to all
                
                # Add to local history
                msg.sequence_number = seq
                with self.history_lock:
                    self.chat_history.append(msg)
                
                if config.DEBUG_MODE:
                    print(f"[ASYNC_CHAT] Sent message seq={seq}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Error in send loop: {e}")
    
    def handle_received_data(self, data: bytes, address: Tuple[str, int]):
        """
        Handle received chat data (call from network layer)
        
        Args:
            data: Received data bytes
            address: Sender address
        """
        self.receive_queue.put((data, address))
    
    def _process_loop(self):
        """Background thread for processing received messages"""
        while self.running:
            try:
                # Get received data from queue with timeout
                data, address = self.receive_queue.get(timeout=0.5)
                
                # Try to parse as chat message
                try:
                    decoded = data.decode('utf-8', errors='ignore')
                    
                    # Check if this is a chat message
                    if 'message_type: CHAT_MESSAGE' not in decoded:
                        continue  # Not a chat message, ignore
                    
                    msg = parse_chat_message(decoded)
                    
                    # Add to history
                    with self.history_lock:
                        self.chat_history.append(msg)
                    
                    # Handle based on content type
                    if msg.content_type == ChatContentType.TEXT:
                        self._display_text_message(msg)
                    elif msg.content_type == ChatContentType.STICKER:
                        self._handle_sticker_message(msg)
                    
                    # Call callback if set
                    if self.message_received_callback:
                        self.message_received_callback(msg)
                    
                except ValueError as e:
                    # Not a valid chat message, ignore
                    if config.DEBUG_MODE:
                        print(f"[DEBUG] Not a chat message: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Error in process loop: {e}")
    
    def _display_text_message(self, msg: ChatMessage):
        """Display text message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] [{msg.sender_name}]: {msg.message_text}")
    
    def _handle_sticker_message(self, msg: ChatMessage):
        """Handle received sticker message"""
        try:
            # Decode Base64 data
            image_data = base64.b64decode(msg.sticker_data)
            
            # Save to file
            filename = f"sticker_{msg.sequence_number}.png"
            filepath = os.path.join(self.sticker_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Display message
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] [{msg.sender_name}] sent a sticker (file: {filepath})")
            
        except Exception as e:
            print(f"[ERROR] Failed to save sticker: {e}")
    
    def set_message_callback(self, callback: Callable[[ChatMessage], None]):
        """Set callback for received messages"""
        self.message_received_callback = callback
    
    def get_chat_history(self, count: Optional[int] = None):
        """
        Get chat history
        
        Args:
            count: Number of recent messages (None for all)
        
        Returns:
            List of ChatMessage objects
        """
        with self.history_lock:
            if count is None:
                return self.chat_history.copy()
            return self.chat_history[-count:]
    
    def clear_history(self):
        """Clear chat history"""
        with self.history_lock:
            self.chat_history.clear()
