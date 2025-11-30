"""
Reliability layer for UDP with sequence numbers, ACKs, and retransmission
"""
import threading
import time
from typing import Dict, Optional, Callable, Tuple
from dataclasses import dataclass
import config


@dataclass
class PendingMessage:
    """Represents a message waiting for acknowledgment"""
    sequence: int
    data: bytes
    address: Tuple[str, int]
    sent_time: float
    retries: int = 0


class ReliabilityLayer:
    """
    Provides reliable message delivery over UDP using:
    - Sequence numbers
    - Acknowledgments
    - Retransmission with timeout
    """
    
    def __init__(self, send_callback: Callable[[bytes, Tuple[str, int]], bool]):
        """
        Initialize reliability layer
        
        Args:
            send_callback: Function to send raw data (UDP send function)
        """
        self.send_callback = send_callback
        self.sequence_number = config.SEQUENCE_START
        self.sequence_lock = threading.Lock()
        
        # Pending messages waiting for ACK
        self.pending_messages: Dict[Tuple[int, Tuple[str, int]], PendingMessage] = {}
        self.pending_lock = threading.Lock()
        
        # Received sequence numbers (for duplicate detection)
        self.received_sequences: set = set()
        self.received_lock = threading.Lock()
        
        # Callbacks for message handling
        self.message_callback: Optional[Callable] = None
        self.ack_callback: Optional[Callable] = None
        
        # Retransmission thread
        self.running = False
        self.retransmit_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the reliability layer"""
        self.running = True
        self.retransmit_thread = threading.Thread(target=self._retransmit_loop, daemon=True)
        self.retransmit_thread.start()
        
        if config.VERBOSE_LOGGING:
            print("[RELIABILITY] Started")
    
    def stop(self):
        """Stop the reliability layer"""
        self.running = False
        
        if self.retransmit_thread and self.retransmit_thread.is_alive():
            self.retransmit_thread.join(timeout=2.0)
        
        if config.VERBOSE_LOGGING:
            print("[RELIABILITY] Stopped")
    
    def get_next_sequence(self) -> int:
        """Get next sequence number"""
        with self.sequence_lock:
            seq = self.sequence_number
            self.sequence_number = (self.sequence_number + 1) % config.MAX_SEQUENCE
            return seq
    
    def send_reliable(self, data: bytes, address: Tuple[str, int], 
                     sequence: Optional[int] = None) -> int:
        """
        Send message reliably with automatic ACK handling
        
        Args:
            data: Message data to send
            address: Destination address
            sequence: Optional sequence number (auto-generated if None)
        
        Returns:
            Sequence number of sent message
        """
        if sequence is None:
            sequence = self.get_next_sequence()
        
        # Add sequence number to data
        message_with_seq = f"seq: {sequence}\n".encode() + data
        
        # Send the message
        success = self.send_callback(message_with_seq, address)
        
        if success:
            # Store in pending messages for retransmission
            with self.pending_lock:
                self.pending_messages[(sequence, address)] = PendingMessage(
                    sequence=sequence,
                    data=message_with_seq,
                    address=address,
                    sent_time=time.time()
                )
            if config.DEBUG_MODE:
                print(f"[RELIABILITY] Sent message with seq={sequence}")
        
        return sequence
    
    def send_ack(self, sequence: int, address: Tuple[str, int]):
        """
        Send acknowledgment for received message
        
        Args:
            sequence: Sequence number to acknowledge
            address: Destination address
        """
        ack_message = f"seq: {sequence}\ntype: ACK\n".encode()
        self.send_callback(ack_message, address)
        
        if config.DEBUG_MODE:
            print(f"[RELIABILITY] Sent ACK for seq={sequence}")
    
    def handle_received(self, data: bytes, address: Tuple[str, int]) -> bool:
        """
        Handle received message, check for duplicates, send ACK
        
        Args:
            data: Received message data
            address: Sender address
        
        Returns:
            True if message is new (not duplicate)
        """
        try:
            # Parse sequence number
            decoded = data.decode('utf-8', errors='ignore')
            lines = decoded.split('\n')
            
            sequence = None
            is_ack = False
            
            for line in lines:
                if line.startswith('seq:'):
                    sequence = int(line.split(':', 1)[1].strip())
                elif line.startswith('type:'):
                    # Check if this is a reliability-layer ACK (not a protocol message)
                    msg_type = line.split(':', 1)[1].strip()
                    if msg_type == 'ACK':
                        is_ack = True
            
            if sequence is None:
                # No sequence number, treat as unreliable message
                if self.message_callback:
                    self.message_callback(data, address)
                return True
            
            if is_ack:
                # This is an ACK message
                self._handle_ack(sequence, address)
                if self.ack_callback:
                    self.ack_callback(sequence, address)
                return True
            
            # Check for duplicate
            with self.received_lock:
                key = (sequence, address)
                if key in self.received_sequences:
                    # Duplicate message, send ACK but don't process
                    self.send_ack(sequence, address)
                    if config.DEBUG_MODE:
                        print(f"[RELIABILITY] Duplicate message seq={sequence} from {address}")
                    return False

                # New message, add to received set
                self.received_sequences.add(key)

                # Keep only recent sequences (prevent memory leak)
                if len(self.received_sequences) > 5000:
                    # Optionally prune oldest; simplest: clear
                    self.received_sequences.clear()
            
            # Send ACK
            self.send_ack(sequence, address)
            
            # Call message callback
            if self.message_callback:
                self.message_callback(data, address)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error handling received message: {e}")
            return False
    
    def _handle_ack(self, sequence: int, address: Tuple[str, int]):
        """Handle received ACK by removing from pending messages"""
        with self.pending_lock:
            key = (sequence, address)
            if key in self.pending_messages:
                del self.pending_messages[key]
                if config.DEBUG_MODE:
                    print(f"[RELIABILITY] Received ACK for seq={sequence}")
    
    def _retransmit_loop(self):
        """Background loop to retransmit unacknowledged messages"""
        while self.running:
            time.sleep(0.5)  # Check every 500ms

            current_time = time.time()
            to_retransmit = []
            to_remove = []

            with self.pending_lock:
                for key, msg in list(self.pending_messages.items()):
                    # key is (seq, addr)
                    elapsed = current_time - msg.sent_time

                    if elapsed > config.ACK_TIMEOUT:
                        if msg.retries < config.MAX_RETRIES:
                            to_retransmit.append(key)  # queue by key
                        else:
                            to_remove.append(key)  # remove by key
                            print(f"[WARNING] Message seq={msg.sequence} to {msg.address} failed after {config.MAX_RETRIES} retries")

            # Retransmit outside of lock
            for key in to_retransmit:
                with self.pending_lock:
                    msg = self.pending_messages.get(key)
                if not msg:
                    continue
                self.send_callback(msg.data, msg.address)
                with self.pending_lock:
                    # Update the same keyed entry
                    if key in self.pending_messages:
                        self.pending_messages[key].sent_time = current_time
                        self.pending_messages[key].retries += 1
                if config.DEBUG_MODE:
                    print(f"[RELIABILITY] Retransmitted seq={msg.sequence} to {msg.address} (retry {msg.retries + 1})")

            # Remove failed messages
            with self.pending_lock:
                for key in to_remove:
                    if key in self.pending_messages:
                        del self.pending_messages[key]
    
    def set_message_callback(self, callback: Callable[[bytes, Tuple[str, int]], None]):
        """Set callback for received messages"""
        self.message_callback = callback
    
    def set_ack_callback(self, callback: Callable[[int, Tuple[str, int]], None]):
        """Set callback for received ACKs"""
        self.ack_callback = callback
    
    def get_pending_count(self) -> int:
        """Get number of pending unacknowledged messages"""
        with self.pending_lock:
            return len(self.pending_messages)
    
    def clear_pending(self):
        """Clear all pending messages"""
        with self.pending_lock:
            self.pending_messages.clear()
