import threading
import time
import unittest

from client_classical import ClassicalClient
from server_classical import ClassicalServer


class TestSecureChannel(unittest.TestCase):
    """
    Comprehensive integration tests for the secure classical communication channel.
    Tests the complete lifecycle: ECDH handshake, encryption, transmission, and decryption.
    """

    def test_full_communication_lifecycle(self):
        """
        Test the complete secure communication lifecycle:
        1. Server startup
        2. Client connection and ECDH key exchange
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
            server = ClassicalServer(
                host="localhost", port=12345, message_received_event=message_event
            )
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()

            # Allow server time to initialize
            time.sleep(0.5)

            # Execution: Connect client
            client = ClassicalClient(host="localhost", port=12345)
            connection_successful = client.connect()
            self.assertTrue(connection_successful, "Client should connect successfully")

            # Send test message
            test_message = "This is a secret test message."
            send_successful = client.send_message(test_message)
            self.assertTrue(send_successful, "Message should be sent successfully")

            # Wait for server to receive and decrypt the message
            message_received = message_event.wait(timeout=2)
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
            message_event.wait(timeout=2)

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
        nonce randomization and message integrity across multiple transmissions.
        """
        server = None
        server_thread = None
        client = None
        message_event = threading.Event()

        try:
            # Setup server
            server = ClassicalServer(
                host="localhost", port=12346, message_received_event=message_event
            )
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            time.sleep(0.5)

            # Connect client
            client = ClassicalClient(host="localhost", port=12346)
            self.assertTrue(client.connect(), "Client should connect")

            # Send multiple messages
            messages = [
                "First message",
                "Second message with different content",
                "Third message!@#$%^&*()",
            ]

            for msg in messages:
                message_event.clear()
                self.assertTrue(client.send_message(msg), f"Should send: {msg}")
                message_received = message_event.wait(timeout=2)
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
            message_event.wait(timeout=2)

        finally:
            if client:
                client.disconnect()
            if server:
                server.stop()
            if server_thread:
                server_thread.join(timeout=2.0)

    def test_connection_failure_handling(self):
        """
        Test that the client handles connection failures gracefully when
        no server is running.
        """
        # Attempt to connect to non-existent server
        client = ClassicalClient(host="localhost", port=19999)
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
