import zmq
import serial
import time
import sys
import json
import logging
import argparse

# ZeroMQ configuration
ZMQ_PORT = "tcp://127.0.0.1:5555"
ZMQ_TIMEOUT_MS = 1000  # Timeout for ZeroMQ receive operation

# UART configuration
BAUD_RATE = 115200
TIMEOUT_S = 5  # Timeout for serial port read operation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Logs go to stdout (captured by systemd)
        logging.StreamHandler(sys.stderr)  # Warnings and errors go to stderr
    ]
)
logging.info("PV PI Awake!")

def uart_zmq_service(uart_port="/dev/ttyAMA0"):
    """
    The main service loop. It listens for ZeroMQ requests from multiple clients,
    sends them over UART, and returns the UART response to the correct sender.
    This uses the ROUTER socket to manage multiple connections.
    """
    logging.info("ZeroMQ UART Service starting...")

    # Set up ZeroMQ context and ROUTER socket
    context = zmq.Context()
    # The ROUTER socket is crucial for handling multiple clients
    socket = context.socket(zmq.ROUTER)
    socket.bind(ZMQ_PORT)
    logging.info(f"ZeroMQ service listening on {ZMQ_PORT}")
    

    # Set up the serial port connection
    ser = None
    try:
        ser = serial.Serial(uart_port, BAUD_RATE, timeout=TIMEOUT_S)
        logging.info(f"Successfully opened serial port {uart_port} at {BAUD_RATE} baud.")

        while True:
            # Wait for a request from a client
            client_id = None
            try:
                # Use a non-blocking poll to check for new messages
                if socket.poll(ZMQ_TIMEOUT_MS):
                    # ROUTER receives a multi-part message: [client_id, delimiter, message]
                    message_parts = socket.recv_multipart()
                    client_id = message_parts[0]
                    
                    # Concatenate the rest of the message parts into a single message body.
                    request_type = message_parts[1].decode('utf-8')

                    message_bytes = b''.join(message_parts[2:])
                    message_str = message_bytes.decode('utf-8')
                    print(f"Service received request type {request_type} from client {client_id.hex()}: '{message_str}'")

                    # Send the message to the UART device
                    if request_type == "send_command":
                        try:
                            ser.write(message_bytes)
                            logging.info(f"Sent to UART: '{message_bytes}'")
                            logging.info("Waiting for response from UART device...")

                            # Wait for a response from the UART device
                            response = ser.readline()
                            response_str = response.decode('utf-8').strip()   

                            print(f"Received from UART: '{message_bytes}'")
                            # Send the response back to the correct client, stripping any newlines
                            # ROUTER sends a multi-part message: [client_id, delimiter, reply]
                            socket.send_multipart([client_id, b'', response_str.encode('utf-8')])
                        except Exception as e:
                            logging.info("UART timed out, or response received.")
                            # Send a timeout error back to the client
                            socket.send_multipart([client_id, b'', b"ERROR: UART timeout"])

            except zmq.Again:
                pass
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                if 'socket' in locals() and socket is not None:
                     # Send an error back if possible
                    socket.send_multipart([client_id, b'', f"ERROR: Internal Service Error: {e}".encode('utf-8')])
                # Attempt to restart the serial connection
                if ser and not ser.is_open:
                    logging.info("Attempting to re-open serial connection...")
                    try:
                        ser.close()
                        ser = serial.Serial(UART_PORT, BAUD_RATE, timeout=TIMEOUT_S)
                        logging.info("Serial connection re-established.")
                    except serial.SerialException:
                        logging.error("Failed to re-establish serial connection.")
                        ser = None

    except serial.SerialException as e:
        logging.error(f"Error opening serial port {UART_PORT}: {e}")
        logging.info("Exiting service. Check your port and permissions (e.g., sudo).")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Service interrupted by user. Shutting down.")
    finally:
        if ser and ser.is_open:
            ser.close()
            logging.info("Serial port closed.")
        if socket:
            socket.close()
            logging.info("ZeroMQ socket closed.")
        if context:
            context.term()
            logging.info("ZeroMQ context terminated.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="PV PI Manager CLI")
    parser.add_argument("--port", default="/dev/ttyAMA0", help="Serial port to STM32")
    args = parser.parse_args()

    uart_zmq_service(uart_port=args.port)
