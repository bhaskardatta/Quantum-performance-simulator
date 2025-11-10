import os
import socket

from oqs import oqs
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class PQCClient:
    """
    A secure TCP client implementing Kyber768 KEM and ML-DSA-65 signatures for quantum-resistant key exchange,
    with AES-GCM encryption for data transmission.
    Designed to work with PQCServer for secure message transmission.
    """

    def __init__(self, host="localhost", port=12346):
        self.host = host
        self.port = port
        self.client_socket = None
        self.aesgcm = None
        self.connected = False

    def connect(self):
        """
        Connect to the server and perform post-quantum key exchange.
        Returns True on success, False on failure.
        """
        try:
            # Create socket and connect
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"[PQC CLIENT] Connected to {self.host}:{self.port}")

            # Perform post-quantum key exchange
            aes_key = self._perform_pqc_key_exchange()
            if not aes_key:
                self.disconnect()
                return False

            # Initialize AES-GCM cipher
            self.aesgcm = AESGCM(aes_key)
            self.connected = True
            print("[PQC CLIENT] Secure channel established")
            return True

        except Exception as e:
            print(f"[PQC CLIENT][ERROR] Connection failed: {e}")
            self.disconnect()
            return False

    def _perform_pqc_key_exchange(self):
        """
        Perform post-quantum key exchange using Kyber768 KEM and ML-DSA-65 signatures.
        Returns the derived AES-256 key or None on failure.
        """
        try:
            # Initialize Kyber768 KEM and ML-DSA-65 signature
            with oqs.KeyEncapsulation("Kyber768") as kem:
                with oqs.Signature("ML-DSA-65") as sig:
                    # Generate client's signature keypair
                    client_sig_public_key = sig.generate_keypair()

                    # Receive server's signature public key
                    server_sig_key_length_bytes = self._receive_exact(4)
                    if not server_sig_key_length_bytes:
                        return None

                    server_sig_key_length = int.from_bytes(
                        server_sig_key_length_bytes, byteorder="big"
                    )
                    server_sig_public_key = self._receive_exact(server_sig_key_length)
                    if not server_sig_public_key:
                        return None

                    print("[PQC CLIENT] Received server signature public key")

                    # Send client's signature public key
                    sig_key_length = len(client_sig_public_key)
                    self.client_socket.sendall(
                        sig_key_length.to_bytes(4, byteorder="big")
                    )
                    self.client_socket.sendall(client_sig_public_key)
                    print("[PQC CLIENT] Sent signature public key")

                    # Generate client's KEM keypair
                    client_kem_public_key = kem.generate_keypair()

                    # Sign the KEM public key
                    kem_signature = sig.sign(client_kem_public_key)

                    # Send KEM public key length
                    kem_pk_length = len(client_kem_public_key)
                    self.client_socket.sendall(
                        kem_pk_length.to_bytes(4, byteorder="big")
                    )

                    # Send KEM public key
                    self.client_socket.sendall(client_kem_public_key)

                    # Send signature length
                    signature_length = len(kem_signature)
                    self.client_socket.sendall(
                        signature_length.to_bytes(4, byteorder="big")
                    )

                    # Send signature
                    self.client_socket.sendall(kem_signature)

                    print("[PQC CLIENT] Sent KEM public key and signature")

                    # Receive ciphertext length
                    ciphertext_length_bytes = self._receive_exact(4)
                    if not ciphertext_length_bytes:
                        return None

                    ciphertext_length = int.from_bytes(
                        ciphertext_length_bytes, byteorder="big"
                    )

                    # Receive ciphertext
                    ciphertext = self._receive_exact(ciphertext_length)
                    if not ciphertext:
                        return None

                    # Receive signature length
                    signature_length_bytes = self._receive_exact(4)
                    if not signature_length_bytes:
                        return None

                    signature_length = int.from_bytes(
                        signature_length_bytes, byteorder="big"
                    )

                    # Receive signature
                    ciphertext_signature = self._receive_exact(signature_length)
                    if not ciphertext_signature:
                        return None

                    print("[PQC CLIENT] Received ciphertext and signature")

                    # Verify the signature on the ciphertext
                    is_valid = sig.verify(
                        ciphertext, ciphertext_signature, server_sig_public_key
                    )
                    if not is_valid:
                        print("[PQC CLIENT][ERROR] Signature verification failed")
                        return None

                    print("[PQC CLIENT] Server signature verified")

                    # Decapsulate to get shared secret
                    shared_secret_client = kem.decap_secret(ciphertext)

                    # Use shared secret as AES key (Kyber768 produces 32-byte shared secret)
                    aes_key = shared_secret_client[:32]  # Ensure 32 bytes for AES-256

                    print("[PQC CLIENT] Key exchange completed")
                    return aes_key

        except Exception as e:
            print(f"[PQC CLIENT][ERROR] Key exchange failed: {e}")
            return None

    def send_message(self, message):
        """
        Encrypt and send a message to the server.
        Returns True on success, False on failure.
        """
        if not self.connected or not self.aesgcm:
            print("[PQC CLIENT][ERROR] Not connected to server")
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

            print(f"[PQC CLIENT] Sent encrypted message: {message}")
            return True

        except Exception as e:
            print(f"[PQC CLIENT][ERROR] Failed to send message: {e}")
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
                print("[PQC CLIENT] Disconnected from server")
            except Exception as e:
                print(f"[PQC CLIENT][ERROR] Error closing socket: {e}")
        self.client_socket = None
        self.aesgcm = None


def main():
    """
    Main entry point for interactive client execution.
    """
    client = PQCClient()

    try:
        if not client.connect():
            print("[PQC CLIENT] Failed to establish connection")
            return

        print("[PQC CLIENT] Type messages to send (type 'exit' to quit):")

        while True:
            message = input("> ")
            if not message:
                continue

            if not client.send_message(message):
                print("[PQC CLIENT] Failed to send message")
                break

            if message.lower() == "exit":
                break

    except KeyboardInterrupt:
        print("\n[PQC CLIENT] Interrupted by user")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
