from simple_pid import PID
import threading
import time

def initialize_pids():
    return {i: PID(1.0, 0.1, 0.05, setpoint=25) for i in range(5)}

def set_pid_output_limits(pids):
    for pid in pids.values():
        pid.output_limits = (-0, 0.2)

def start_monitoring(sensor_number, monitoring_events, pids, board, mdd3a_pins, temp_labels):
    if not monitoring_events[sensor_number].is_set():
        monitoring_events[sensor_number].set()
        thread = threading.Thread(target=monitor_temperature, args=(sensor_number, monitoring_events, pids, board, mdd3a_pins, temp_labels))
        thread.start()
        print(f"Monitoring started for sensor {sensor_number + 1}.")

def stop_monitoring(sensor_number, monitoring_events, board, mdd3a_pins):
    if monitoring_events[sensor_number].is_set():
        monitoring_events[sensor_number].clear()
        disable_peltier(sensor_number+1, board, mdd3a_pins)
        print(f"Monitoring stopped and Peltier disabled for sensor {sensor_number + 1}.")

def monitor_temperature(sensor_number, monitoring_events, pids, board, mdd3a_pins, temp_labels):
    pid = pids[sensor_number]
    try:
        while monitoring_events[sensor_number].is_set():
            current_temp_str = temp_labels[sensor_number].cget("text").split(": ")[1].strip().split(' ')[0]
            current_temp = float(current_temp_str)
            control = pid(current_temp)
            action = control > 0
            pwm_value = abs(control)
            board_name = f'board{sensor_number + 1}'
            control_peltier(board, mdd3a_pins, board_name, heat=action, pwm=True, pwm_duty_cycle=pwm_value)
            time.sleep(1)
    except Exception as e:
        print(f"Error in monitoring temperature for sensor {sensor_number + 1}: {e}")

def disable_peltier(board_name, board, mdd3a_pins):
    try:
        board_name = f'board{board_name}'
        control_peltier(board, mdd3a_pins, board_name, heat=None, pwm=False, pwm_duty_cycle=0)
    except Exception as e:
        print(f"Error in disabling peltier {board_name}: {e}")

def control_peltier(board,mdd3a_pins,board_name, heat, pwm=False, pwm_duty_cycle=1.0):
    """
    Control the Peltier module for heating or cooling, with optional PWM.
    :param board: PyFirmata/Arduino board instance.
    :param mdd3a_pins: Dictionary with control pin mappings.
    :param board_name: Name of the MDD3A board to control.
    :param heat: True for heating, False for cooling, None for off.
    :param pwm: Use PWM if True.
    :param pwm_duty_cycle: Duty cycle for PWM (0.0 to 1.0), default 1.0 for full power.
    """
    inputA = mdd3a_pins[board_name]['inputA']
    inputB = mdd3a_pins[board_name]['inputB']

    pwm_value = pwm_duty_cycle if pwm else 1

    if heat is None:
        inputA.write(0)
        inputB.write(0)
    elif heat:
        inputA.write(pwm_value)
        inputB.write(0)
    else:
        inputA.write(0)
        inputB.write(pwm_value)
