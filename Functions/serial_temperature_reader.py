
import serial
import time
import re

# Replace 'COM3' with the port where your Arduino is connected
serial_port = '/dev/cu.usbmodem1101'
baud_rate = 57600  # In sync with your Arduino's baud rate

# Set up the serial connection
ser = serial.Serial(serial_port, baud_rate)

def read_serial_data():
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline()
                try:
                    decoded_line = line.decode('utf-8').rstrip()
                except UnicodeDecodeError:
                    # In case of decode error, use 'latin1' or 'ignore' errors
                    decoded_line = line.decode('utf-8', errors='ignore').rstrip()
                
                # Use regular expression to find sensor number and temperature
                match = re.search(r"Sensor (\d)Object = ([\d.]+)\*C", decoded_line)
                if match:
                    sensor_number = match.group(1)
                    temperature = match.group(2)
                    print(f"Sensor {sensor_number}: {temperature}°C")
                
                time.sleep(0.1)  # Add a short delay to reduce CPU usage
        except KeyboardInterrupt:
            print("Interrupted by user, closing connection.")
            ser.close()
            break

if __name__ == '__main__':
    read_serial_data()
