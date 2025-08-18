import time
import threading
import tkinter as tk
import threading
import time

# Global variables for thread management
motor_thread_lock = threading.Lock()
motor_thread_active = False
# Volume in grams dispensed per step
VOLUME_PER_STEP_MOTOR1 = 2.4
VOLUME_PER_STEP_MOTOR2 = 2.4
VOLUME_PER_STEP_MOTOR3 = 2.4

# Constants for motor control
ENABLE_SETTLING_TIME = 0.5  # 100ms settling time after enabling motor
DISABLE_DELAY = 0.5  # 100ms delay before disabling motor

def rotate_stepper(motor, direction, delay, steps):
    try:
        # Enable the motor
        if 'enable_pin' in motor:
            motor['enable_pin'].write(0)  # Set enable pin to LOW to enable the motor
            time.sleep(ENABLE_SETTLING_TIME)

        motor['dir_pin'].write(direction)
        time.sleep(0.5)
        steps = int(steps)
        for _ in range(steps):
            motor['step_pin'].write(1)
            time.sleep(delay / 1000000.0)  # Convert microseconds to seconds
            motor['step_pin'].write(0)
            time.sleep(delay / 1000000.0)

        time.sleep(DISABLE_DELAY)
    finally:
        # Disable the motor
        if 'enable_pin' in motor:
            motor['enable_pin'].write(1)  # Set enable pin to HIGH to disable the motor
        global motor_thread_active
        with motor_thread_lock:
            motor_thread_active = False  # Reset flag when done
def control_motor(motor, direction, speed, volume_g):
    global motor_thread_active
    delay = 2000 if speed == 'slow' else 1000  # speed control
    if motor['dir'] == 22:
        steps = int(volume_g / VOLUME_PER_STEP_MOTOR1)
    elif motor['dir'] == 25:
        steps = int(volume_g / VOLUME_PER_STEP_MOTOR2)
    elif motor['dir'] == 28:
        steps = int(volume_g / VOLUME_PER_STEP_MOTOR3)
    
    # Ensure only one thread is active at a time
    with motor_thread_lock:
        if not motor_thread_active:
            motor_thread = threading.Thread(target=rotate_stepper, args=(motor, direction, delay, steps))
            motor_thread.start()
            motor_thread_active = True
        else:
            print("Motor command is already in process.")

def create_motor_section(root, motor_id, row, column, motor_pins):
    frame = tk.LabelFrame(root, text=motor_id.capitalize(), padx=10, pady=10)
    frame.grid(row=row, column=column, columnspan=1, padx=10, pady=5, sticky="nw")
    mode_var = tk.StringVar()
    volume_var = tk.DoubleVar()

    # Motor control buttons
    modes = [('Clockwise Slow', 1, 'slow'), ('Clockwise Fast', 1, 'fast'),
             ('Counter-Clockwise Slow', 0, 'slow'), ('Counter-Clockwise Fast', 0, 'fast')]
    for text, direction, speed in modes:
        b = tk.Radiobutton(frame, text=text, variable=mode_var, value=f'{direction}-{speed}')
        b.pack(anchor=tk.W)

    volume_label = tk.Label(frame, text="Enter volume (uL):")
    volume_label.pack()
    volume_entry = tk.Entry(frame, textvariable=volume_var)
    volume_entry.pack()

    def start_motor():
        with motor_thread_lock:
            if not motor_thread_active:
                mode_value = mode_var.get().split('-')
                if len(mode_value) == 2:
                    direction, speed = mode_value
                    volume_g = volume_var.get()
                    motor = motor_pins[motor_id]
                    threading.Thread(target=control_motor, args=(motor, int(direction), speed, float(volume_g))).start()
            else:
                print("Motor command is already in process.")

    start_button = tk.Button(frame, text="Go", command=start_motor)
    start_button.pack()
