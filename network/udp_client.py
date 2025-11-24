"""
Low-level UDP client for sending and receiving messages
"""
import socket
import threading
import time
from typing import Callable, Optional, Tuple
import config


class UDPClient:
    """UDP socket wrapper for peer-to-peer communication"""
    
    def __init__(self, host: str = config.DEFAULT_HOST, port: int = config.DEFAULT_PORT):
        """
        Initialize UDP client
        
        Args:
            host: Local host address to bind to
            port: Local port to bind to
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.receive_callback: Optional[Callable] = None
        self.peer_address: Optional[Tuple[str, int]] = None
        
    def start(self) -> bool:
        """
        Start UDP client and bind to port
        
        Returns:
            True if started successfully
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # Non-blocking with timeout
            self.running = True
            
            if config.VERBOSE_LOGGING:
                print(f"[UDP] Client started on {self.host}:{self.port}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start UDP client: {e}")
            return False
    
    def stop(self):
        """Stop UDP client and close socket"""
        self.running = False
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if config.VERBOSE_LOGGING:
            print("[UDP] Client stopped")
    
    def send(self, data: bytes, address: Tuple[str, int]) -> bool:
        """
        Send data to specified address
        
        Args:
            data: Bytes to send
            address: (host, port) tuple
        
        Returns:
            True if sent successfully
        """
        if not self.socket or not self.running:
            return False
        
        try:
            self.socket.sendto(data, address)
            
            if config.VERBOSE_LOGGING:
                print(f"[UDP] Sent {len(data)} bytes to {address}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send data: {e}")
            return False
    
    def receive(self) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        """
        Receive data (non-blocking with timeout)
        
        Returns:
            (data, address) tuple or None if timeout/error
        """
        if not self.socket or not self.running:
            return None
        
        try:
            data, address = self.socket.recvfrom(config.BUFFER_SIZE)
            
            if config.VERBOSE_LOGGING:
                print(f"[UDP] Received {len(data)} bytes from {address}")
            
            return data, address
        except socket.timeout:
            return None
        except Exception as e:
            if self.running:  # Only print error if still running
                print(f"[ERROR] Failed to receive data: {e}")
            return None
    
    def start_receiving(self, callback: Callable[[bytes, Tuple[str, int]], None]):
        """
        Start receiving messages in background thread
        
        Args:
            callback: Function to call with (data, address) when message received
        """
        self.receive_callback = callback
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        
        if config.VERBOSE_LOGGING:
            print("[UDP] Started receive loop")
    
    def _receive_loop(self):
        """Background loop for receiving messages"""
        while self.running:
            result = self.receive()
            if result and self.receive_callback:
                data, address = result
                try:
                    self.receive_callback(data, address)
                except Exception as e:
                    print(f"[ERROR] Error in receive callback: {e}")
    
    def set_peer(self, host: str, port: int):
        """
        Set the peer address for this connection
        
        Args:
            host: Peer host address
            port: Peer port
        """
        self.peer_address = (host, port)
        
        if config.VERBOSE_LOGGING:
            print(f"[UDP] Peer set to {host}:{port}")
    
    def send_to_peer(self, data: bytes) -> bool:
        """
        Send data to configured peer
        
        Args:
            data: Bytes to send
        
        Returns:
            True if sent successfully
        """
        if not self.peer_address:
            print("[ERROR] No peer address configured")
            return False
        
        return self.send(data, self.peer_address)
    
    def get_local_address(self) -> Optional[Tuple[str, int]]:
        """Get local socket address"""
        if self.socket:
            return self.socket.getsockname()
        return None
    
    def is_running(self) -> bool:
        """Check if client is running"""
        return self.running and self.socket is not None
