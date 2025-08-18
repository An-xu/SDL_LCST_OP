import serial
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal

class SerialReader(QThread):
    temperature_updated = pyqtSignal(int, float)
    analog_updated = pyqtSignal(int, int)

    def __init__(self, port, baud_rate):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.running = True
        self.ser = None
        self.reconnect_delay = 2  # seconds between reconnection attempts

    def connect_serial(self):
        """Attempt to connect to the serial port with retry logic"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries and self.running:
            try:
                # Close any existing connection
                self.close_port()
                
                # Wait before attempting to connect
                time.sleep(self.reconnect_delay)
                
                # Try to open new connection
                self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
                print(f"Successfully connected to {self.port}")
                return True
                
            except serial.SerialException as e:
                print(f"Connection attempt {retry_count + 1} failed: {e}")
                retry_count += 1
        
        return False

    def run(self):
        while self.running:
            try:
                if not self.ser or not self.ser.is_open:
                    if not self.connect_serial():
                        continue

                if self.ser.in_waiting > 0:
                    try:
                        line = self.ser.readline().decode('utf-8', errors='replace').strip()
                    except UnicodeDecodeError:
                        try:
                            line = self.ser.readline().decode('ascii', errors='ignore').strip()
                        except Exception as decode_error:
                            print(f"Decoding error: {decode_error}")
                            continue

                    if line:  # Only process non-empty lines
                        try:
                            temp_match = re.search(r"Sensor (\d)Object = ([\d.]+)\*C", line)
                            analog_match = re.search(r"Analog Reading (\d) = (\d+)", line)
                            
                            if temp_match:
                                sensor_number = int(temp_match.group(1))
                                temperature = float(temp_match.group(2))
                                self.temperature_updated.emit(sensor_number, temperature)
                            if analog_match:
                                sensor_number = int(analog_match.group(1))
                                analog_value = int(analog_match.group(2))
                                self.analog_updated.emit(sensor_number, analog_value)
                        except Exception as parse_error:
                            print(f"Error parsing line '{line}': {parse_error}")
                            continue

            except serial.SerialException as e:
                print(f"Serial connection error: {e}")
                # Try to reconnect on error
                self.connect_serial()
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(self.reconnect_delay)

        self.close_port()

    def stop(self):
        """Stop the reader thread safely"""
        print("Stopping SerialReader...")
        self.running = False
        self.close_port()
        self.wait()
        print("SerialReader stopped")

    def close_port(self):
        """Safely close the serial port"""
        try:
            if self.ser:
                if self.ser.is_open:
                    self.ser.flush()
                    self.ser.close()
                    print(f"Closed serial port {self.port}")
                self.ser = None
        except Exception as e:
            print(f"Error closing serial port: {e}")
