import cv2
import serial
import time
import numpy as np

START_MARKER = 0xFF
PORT = "/dev/ttyUSB0"
BAUDRATE = 1500000

# Initialize serial connection
with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
    time.sleep(1)  # Allow serial connection to establish

    def send_frame_to_esp32(frame):
        """Send an OpenCV frame to the ESP32 over serial."""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (64, 64))

        # Extract R, G, B channels efficiently
        r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]

        # Generate x, y coordinates
        x_coords, y_coords = np.meshgrid(
            np.arange(64, dtype=np.uint8), np.arange(64, dtype=np.uint8)
        )

        # Compute checksum
        checksum = x_coords ^ y_coords ^ r ^ g ^ b

        # Flatten arrays and interleave into packets
        packet_data = (
            np.column_stack(
                [
                    np.full(4096, START_MARKER, dtype=np.uint8),  # START_MARKER
                    x_coords.ravel(),
                    y_coords.ravel(),
                    r.ravel(),
                    g.ravel(),
                    b.ravel(),
                    checksum.ravel(),
                ]
            )
            .astype(np.uint8)
            .tobytes()
        )

        ser.write(packet_data)

    def capture_and_send():
        cap = cv2.VideoCapture(2)  # Open the default camera
        if not cap.isOpened():
            print("Error: Camera not found")
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                send_frame_to_esp32(frame)
        finally:
            cap.release()

    capture_and_send()
