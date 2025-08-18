import threading
import time
import datetime
import os
from .peltier_control import control_peltier, stop_monitoring

def start_temperature_sweep(sensor_index, start_temps, end_temps, step_sizes, hold_times, pids, monitoring_events, temp_labels, analog_labels, board, mdd3a_pins):
    try:
        start_temp = float(start_temps[sensor_index].text())
        end_temp = float(end_temps[sensor_index].text())
        step_size = float(step_sizes[sensor_index].text())
        hold_time = float(hold_times[sensor_index].text())

        threading.Thread(target=temperature_sweep, args=(sensor_index, start_temp, end_temp, step_size, hold_time, pids, monitoring_events, temp_labels, analog_labels, board, mdd3a_pins)).start()

    except ValueError as e:
        print(f"Invalid input for temperature sweep parameters on sensor {sensor_index+1}: {e}")

def temperature_sweep(sensor_index, start_temp, end_temp, step, hold_time_minutes, pids, monitoring_events, temp_labels, analog_labels, board, mdd3a_pins):
    # Create a new folder for this run
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"Data/Sensor{sensor_index + 1}_{current_time}"
    os.makedirs(folder_name, exist_ok=True)

    temp_log_file = open(os.path.join(folder_name, f"temperature_log_sensor_{sensor_index + 1}.txt"), "a")
    uv_log_file = open(os.path.join(folder_name, f"uv_log_sensor_{sensor_index + 1}.txt"), "a")

    try:
        current_temp = start_temp
        pids[sensor_index].setpoint = start_temp

        while current_temp <= end_temp and monitoring_events[sensor_index].is_set():
            pids[sensor_index].setpoint = current_temp
            print(f"Sensor {sensor_index + 1} set to {current_temp}°C")
            temp_log_file.write(f"{datetime.datetime.now()}: Set Sensor {sensor_index + 1} to {current_temp}°C\n")

            stable_time_start = None
            while monitoring_events[sensor_index].is_set():
                current_reading = float(temp_labels[sensor_index].text().split(": ")[1].strip().split(' ')[0])
                
                # Control Peltier
                control = pids[sensor_index](current_reading)
                action = control > 0
                pwm_value = abs(control)
                board_name = f'board{sensor_index + 1}'
                control_peltier(board, mdd3a_pins, board_name, heat=action, pwm=True, pwm_duty_cycle=pwm_value)

                if abs(current_reading - current_temp) <= 0.5:
                    if stable_time_start is None:
                        stable_time_start = time.time()
                    elif time.time() - stable_time_start >= 10:
                        temp_log_file.write(f"{datetime.datetime.now()}: Temperature {current_temp}°C stabilized for 10 seconds\n")
                        break
                else:
                    stable_time_start = None

                uv_reading = analog_labels[f'analog{sensor_index + 1}'].text().split(": ")[1]
                uv_log_file.write(f"{datetime.datetime.now()}: UV Sensor {sensor_index + 1} Reading: {uv_reading}\n")
                uv_log_file.flush()
                time.sleep(3)

            if not monitoring_events[sensor_index].is_set():
                break

            hold_time_seconds = hold_time_minutes * 60
            print(f"Holding {current_temp}°C for {hold_time_minutes} minutes...")
            temp_log_file.write(f"{datetime.datetime.now()}: Holding {current_temp}°C for {hold_time_minutes} minutes\n")

            hold_start_time = time.time()
            while time.time() - hold_start_time < hold_time_seconds and monitoring_events[sensor_index].is_set():
                current_reading = float(temp_labels[sensor_index].text().split(": ")[1].strip().split(' ')[0])
                
                # Control Peltier during hold time
                control = pids[sensor_index](current_reading)
                action = control > 0
                pwm_value = abs(control)
                board_name = f'board{sensor_index + 1}'
                control_peltier(board, mdd3a_pins, board_name, heat=action, pwm=True, pwm_duty_cycle=pwm_value)

                uv_reading = analog_labels[f'analog{sensor_index + 1}'].text().split(": ")[1]
                uv_log_file.write(f"{datetime.datetime.now()}: UV Sensor {sensor_index + 1} Reading: {uv_reading}\n")
                uv_log_file.flush()
                current_hold_temp = float(temp_labels[sensor_index].text().split(": ")[1].strip().split(' ')[0])
                temp_log_file.write(f"{datetime.datetime.now()}: Real-time Hold Temp: {current_hold_temp}°C\n")
                temp_log_file.flush()
                time.sleep(3)
                
                if not monitoring_events[sensor_index].is_set():
                    break

            current_temp += step

        if monitoring_events[sensor_index].is_set():
            print(f"Temperature sweep completed for sensor {sensor_index + 1}.")
            temp_log_file.write(f"{datetime.datetime.now()}: Temperature sweep completed for sensor {sensor_index + 1}.\n")
        else:
            temp_log_file.write(f"{datetime.datetime.now()}: Temperature sweep stopped for sensor {sensor_index + 1}.\n")
    finally:
        # Stop monitoring and disable Peltier after sweep
        stop_monitoring(sensor_index, monitoring_events, board, mdd3a_pins)
        temp_log_file.close()
        uv_log_file.close()