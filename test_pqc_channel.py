import threading
import time
import unittest

from client_pqc import PQCClient
from server_pqc import PQCServer


class TestPQCSecureChannel(unittest.TestCase):
    """
    Comprehensive integration tests for the post-quantum secure communication channel.
    Tests the complete lifecycle: Kyber768 KEM, ML-DSA-65 signatures, encryption, transmission, and decryption.
    """

    def test_full_communication_lifecycle(self):
        """
        Test the complete post-quantum secure communication lifecycle:
        1. Server startup
        2. Client connection and PQC key exchange (Kyber768 + ML-DSA-65)
        3. Encrypted message transmission
        4. Server message reception and decryption
        5. Graceful shutdown
        """
        server = None
        server_thread = None
        client = None
        message_event = threading.Event()

        try:
            # Setup: Start server in background thread
            server = PQCServer(
                host="localhost", port=12346, message_received_event=message_event
            )
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()

            # Allow server time to initialize
            time.sleep(0.5)

            # Execution: Connect client
            client = PQCClient(host="localhost", port=12346)
            connection_successful = client.connect()
            self.assertTrue(connection_successful, "Client should connect successfully")

            # Send test message
            test_message = "This is a quantum-resistant secret test message."
            send_successful = client.send_message(test_message)
            self.assertTrue(send_successful, "Message should be sent successfully")

            # Wait for server to receive and decrypt the message
            message_received = message_event.wait(timeout=3)
            self.assertTrue(
                message_received, "Server should receive message within timeout"
            )

            # Assertion: Verify server received and decrypted the message correctly
            self.assertEqual(
                server.last_received_message,
                test_message,
                "Server should receive and decrypt the exact message sent by client",
            )

            # Send exit command to gracefully close connection
            message_event.clear()
            client.send_message("exit")
            message_event.wait(timeout=3)

            # Verify exit message was also received
            self.assertEqual(
                server.last_received_message,
                "exit",
                "Server should receive the exit command",
            )

        finally:
            # Teardown: Clean up resources
            if client:
                client.disconnect()

            if server:
                server.stop()

            if server_thread:
                server_thread.join(timeout=2.0)

    def test_multiple_messages(self):
        """
        Test sending multiple messages in sequence to verify the encryption
        nonce randomization and message integrity across multiple transmissions
        in a post-quantum context.
        """
        server = None
        server_thread = None
        client = None
        message_event = threading.Event()

        try:
            # Setup server
            server = PQCServer(
                host="localhost", port=12347, message_received_event=message_event
            )
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            # Connect client
            client = PQCClient(host="localhost", port=12347)
            self.assertTrue(client.connect(), "Client should connect")

            # Send multiple messages
            messages = [
                "First PQC message",
                "Second message with quantum resistance",
                "Third message with special chars!@#$%^&*()",
            ]

            for msg in messages:
                message_event.clear()
                self.assertTrue(client.send_message(msg), f"Should send: {msg}")
                message_received = message_event.wait(timeout=3)
                self.assertTrue(
                    message_received,
                    f"Server should receive message within timeout: {msg}",
                )
                self.assertEqual(
                    server.last_received_message, msg, f"Server should receive: {msg}"
                )

            # Clean exit
            message_event.clear()
            client.send_message("exit")
            message_event.wait(timeout=3)

        finally:
            if client:
                client.disconnect()
            if server:
                server.stop()
            if server_thread:
                server_thread.join(timeout=2.0)

    def test_connection_failure_handling(self):
        """
        Test that the PQC client handles connection failures gracefully when
        no server is running.
        """
        # Attempt to connect to non-existent server
        client = PQCClient(host="localhost", port=19998)
        connection_successful = client.connect()

        # Should fail gracefully
        self.assertFalse(
            connection_successful, "Connection should fail when server is not available"
        )
        self.assertFalse(client.connected, "Client should not be marked as connected")


def run_tests():
    """
    Run the test suite with verbose output.
    """
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
