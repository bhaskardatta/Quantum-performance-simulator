import socket
import threading

from oqs import oqs
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class PQCServer:
    """
    A secure TCP server implementing Kyber768 KEM and ML-DSA-65 signatures for quantum-resistant key exchange,
    with AES-GCM encryption for data transmission.
    Designed for testability with thread-safe operation and message tracking.
    """

    def __init__(self, host="localhost", port=12346, message_received_event=None):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.last_received_message = None
        self._lock = threading.Lock()
        self.message_received_event = message_received_event

    def start(self):
        """
        Start the server and begin listening for connections.
        Runs in the calling thread.
        """
        self.running = True
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(
                1.0
            )  # Allow periodic checking of running flag
            print(f"[PQC SERVER] Listening on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"[PQC SERVER] Connection from {address}")
                    self._handle_client(client_socket)
                except socket.timeout:
                    continue  # Check running flag and continue listening
                except Exception as e:
                    if self.running:
                        print(f"[PQC SERVER][ERROR] Accept error: {e}")

        except Exception as e:
            print(f"[PQC SERVER][ERROR] Server initialization failed: {e}")
        finally:
            self._cleanup()

    def _handle_client(self, client_socket):
        """
        Handle a single client connection with Kyber768 KEM and ML-DSA-65 authentication.
        """
        try:
            with client_socket:
                # Perform post-quantum key exchange
                aes_key = self._perform_pqc_key_exchange(client_socket)
                if not aes_key:
                    return

                aesgcm = AESGCM(aes_key)
                print("[PQC SERVER] Secure channel established")

                # Message reception loop
                while self.running:
                    try:
                        message = self._receive_encrypted_message(client_socket, aesgcm)
                        if message is None:
                            break

                        print(f"[PQC SERVER] Decrypted message: {message}")

                        # Store last received message (thread-safe)
                        with self._lock:
                            self.last_received_message = message

                        # Signal that a message has been received (for testing)
                        if self.message_received_event:
                            self.message_received_event.set()

                        if message.lower() == "exit":
                            print("[PQC SERVER] Client requested disconnect")
                            break

                    except Exception as e:
                        print(f"[PQC SERVER][ERROR] Message reception error: {e}")
                        break

        except Exception as e:
            print(f"[PQC SERVER][ERROR] Client handler error: {e}")

    def _perform_pqc_key_exchange(self, client_socket):
        """
        Perform post-quantum key exchange using Kyber768 KEM and ML-DSA-65 signatures.
        Returns the derived AES-256 key or None on failure.
        """
        try:
            # Initialize Kyber768 KEM and ML-DSA-65 signature
            with oqs.KeyEncapsulation("Kyber768") as kem:
                with oqs.Signature("ML-DSA-65") as sig:
                    # Generate server's signature keypair
                    server_sig_public_key = sig.generate_keypair()

                    # Send server's signature public key
                    sig_key_length = len(server_sig_public_key)
                    client_socket.sendall(sig_key_length.to_bytes(4, byteorder="big"))
                    client_socket.sendall(server_sig_public_key)
                    print("[PQC SERVER] Sent signature public key")

                    # Receive client's signature public key
                    client_sig_key_length_bytes = self._receive_exact(client_socket, 4)
                    if not client_sig_key_length_bytes:
                        return None

                    client_sig_key_length = int.from_bytes(
                        client_sig_key_length_bytes, byteorder="big"
                    )
                    client_sig_public_key = self._receive_exact(
                        client_socket, client_sig_key_length
                    )
                    if not client_sig_public_key:
                        return None

                    print("[PQC SERVER] Received client signature public key")

                    # Receive client's KEM public key length
                    kem_pk_length_bytes = self._receive_exact(client_socket, 4)
                    if not kem_pk_length_bytes:
                        return None

                    kem_pk_length = int.from_bytes(kem_pk_length_bytes, byteorder="big")

                    # Receive client's KEM public key
                    client_kem_public_key = self._receive_exact(
                        client_socket, kem_pk_length
                    )
                    if not client_kem_public_key:
                        return None

                    # Receive signature length
                    signature_length_bytes = self._receive_exact(client_socket, 4)
                    if not signature_length_bytes:
                        return None

                    signature_length = int.from_bytes(
                        signature_length_bytes, byteorder="big"
                    )

                    # Receive signature of KEM public key
                    kem_signature = self._receive_exact(client_socket, signature_length)
                    if not kem_signature:
                        return None

                    print("[PQC SERVER] Received client KEM public key and signature")

                    # Verify the signature on the KEM public key
                    is_valid = sig.verify(
                        client_kem_public_key, kem_signature, client_sig_public_key
                    )
                    if not is_valid:
                        print("[PQC SERVER][ERROR] Signature verification failed")
                        return None

                    print("[PQC SERVER] Client signature verified")

                    # Encapsulate shared secret using client's KEM public key
                    ciphertext, shared_secret_server = kem.encap_secret(
                        client_kem_public_key
                    )

                    # Sign the ciphertext
                    ciphertext_signature = sig.sign(ciphertext)

                    # Send ciphertext length
                    ciphertext_length = len(ciphertext)
                    client_socket.sendall(
                        ciphertext_length.to_bytes(4, byteorder="big")
                    )

                    # Send ciphertext
                    client_socket.sendall(ciphertext)

                    # Send signature length
                    signature_length = len(ciphertext_signature)
                    client_socket.sendall(signature_length.to_bytes(4, byteorder="big"))

                    # Send signature
                    client_socket.sendall(ciphertext_signature)

                    print("[PQC SERVER] Sent encapsulated ciphertext and signature")

                    # Use shared secret as AES key (Kyber768 produces 32-byte shared secret)
                    aes_key = shared_secret_server[:32]  # Ensure 32 bytes for AES-256

                    print("[PQC SERVER] Key exchange completed")
                    return aes_key

        except Exception as e:
            print(f"[PQC SERVER][ERROR] Key exchange failed: {e}")
            return None

    def _receive_encrypted_message(self, client_socket, aesgcm):
        """
        Receive and decrypt a message using the protocol: nonce_length | nonce | ciphertext_length | ciphertext.
        Returns the decrypted message string or None on failure/disconnect.
        """
        try:
            # Receive nonce length (4 bytes)
            nonce_length_bytes = self._receive_exact(client_socket, 4)
            if not nonce_length_bytes:
                return None

            nonce_length = int.from_bytes(nonce_length_bytes, byteorder="big")

            # Receive nonce
            nonce = self._receive_exact(client_socket, nonce_length)
            if not nonce:
                return None

            # Receive ciphertext length (4 bytes)
            ciphertext_length_bytes = self._receive_exact(client_socket, 4)
            if not ciphertext_length_bytes:
                return None

            ciphertext_length = int.from_bytes(ciphertext_length_bytes, byteorder="big")

            # Receive ciphertext
            ciphertext = self._receive_exact(client_socket, ciphertext_length)
            if not ciphertext:
                return None

            # Decrypt message
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")

        except Exception as e:
            print(f"[PQC SERVER][ERROR] Decryption error: {e}")
            return None

    def _receive_exact(self, sock, num_bytes):
        """
        Receive exactly num_bytes from the socket.
        Returns the data or None if connection closed.
        """
        data = b""
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def stop(self):
        """
        Gracefully stop the server.
        """
        print("[PQC SERVER] Stopping server...")
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"[PQC SERVER][ERROR] Error closing server socket: {e}")

    def _cleanup(self):
        """
        Clean up server resources.
        """
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        print("[PQC SERVER] Server stopped")


def main():
    """
    Main entry point for standalone server execution.
    """
    server = PQCServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[PQC SERVER] Interrupted by user")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
