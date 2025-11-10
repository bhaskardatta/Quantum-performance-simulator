import os
import socket

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class ClassicalClient:
    """
    A secure TCP client implementing ECDH key exchange and AES-GCM encryption.
    Designed to work with ClassicalServer for secure message transmission.
    """

    def __init__(self, host="localhost", port=12345):
        self.host = host
        self.port = port
        self.client_socket = None
        self.aesgcm = None
        self.connected = False

    def connect(self):
        """
        Connect to the server and perform ECDH key exchange.
        Returns True on success, False on failure.
        """
        try:
            # Create socket and connect
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"[CLIENT] Connected to {self.host}:{self.port}")

            # Perform key exchange
            aes_key = self._perform_key_exchange()
            if not aes_key:
                self.disconnect()
                return False

            # Initialize AES-GCM cipher
            self.aesgcm = AESGCM(aes_key)
            self.connected = True
            print("[CLIENT] Secure channel established")
            return True

        except Exception as e:
            print(f"[CLIENT][ERROR] Connection failed: {e}")
            self.disconnect()
            return False

    def _perform_key_exchange(self):
        """
        Perform ECDH key exchange with the server.
        Returns the derived AES-256 key or None on failure.
        """
        try:
            # Receive server's public key
            server_key_length_bytes = self._receive_exact(4)
            if not server_key_length_bytes:
                return None

            server_key_length = int.from_bytes(server_key_length_bytes, byteorder="big")
            server_public_bytes = self._receive_exact(server_key_length)
            if not server_public_bytes:
                return None

            print("[CLIENT] Received server public key")

            # Deserialize server's public key
            server_public_key = serialization.load_pem_public_key(server_public_bytes)

            # Generate client's ECDH key pair
            client_private_key = ec.generate_private_key(ec.SECP384R1())
            client_public_key = client_private_key.public_key()

            # Serialize client's public key
            client_public_bytes = client_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            # Send client's public key (length + data)
            key_length = len(client_public_bytes)
            self.client_socket.sendall(key_length.to_bytes(4, byteorder="big"))
            self.client_socket.sendall(client_public_bytes)
            print("[CLIENT] Sent public key")

            # Compute shared secret
            shared_secret = client_private_key.exchange(ec.ECDH(), server_public_key)

            # Derive AES key using HKDF
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,  # AES-256
                salt=None,
                info=b"handshake data",
            ).derive(shared_secret)

            print("[CLIENT] Key exchange completed")
            return derived_key

        except Exception as e:
            print(f"[CLIENT][ERROR] Key exchange failed: {e}")
            return None

    def send_message(self, message):
        """
        Encrypt and send a message to the server.
        Returns True on success, False on failure.
        """
        if not self.connected or not self.aesgcm:
            print("[CLIENT][ERROR] Not connected to server")
            return False

        try:
            # Generate random nonce (96 bits for GCM)
            nonce = os.urandom(12)

            # Encrypt message
            plaintext = message.encode("utf-8")
            ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)

            # Send message using protocol: nonce_length | nonce | ciphertext_length | ciphertext
            nonce_length = len(nonce)
            self.client_socket.sendall(nonce_length.to_bytes(4, byteorder="big"))
            self.client_socket.sendall(nonce)

            ciphertext_length = len(ciphertext)
            self.client_socket.sendall(ciphertext_length.to_bytes(4, byteorder="big"))
            self.client_socket.sendall(ciphertext)

            print(f"[CLIENT] Sent encrypted message: {message}")
            return True

        except Exception as e:
            print(f"[CLIENT][ERROR] Failed to send message: {e}")
            return False

    def _receive_exact(self, num_bytes):
        """
        Receive exactly num_bytes from the socket.
        Returns the data or None if connection closed.
        """
        data = b""
        while len(data) < num_bytes:
            chunk = self.client_socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def disconnect(self):
        """
        Close the connection to the server.
        """
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
                print("[CLIENT] Disconnected from server")
            except Exception as e:
                print(f"[CLIENT][ERROR] Error closing socket: {e}")
        self.client_socket = None
        self.aesgcm = None


def main():
    """
    Main entry point for interactive client execution.
    """
    client = ClassicalClient()

    try:
        if not client.connect():
            print("[CLIENT] Failed to establish connection")
            return

        print("[CLIENT] Type messages to send (type 'exit' to quit):")

        while True:
            message = input("> ")
            if not message:
                continue

            if not client.send_message(message):
                print("[CLIENT] Failed to send message")
                break

            if message.lower() == "exit":
                break

    except KeyboardInterrupt:
        print("\n[CLIENT] Interrupted by user")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
