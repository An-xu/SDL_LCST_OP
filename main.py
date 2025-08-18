import sys
import os
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QComboBox, QLineEdit, QGroupBox, QTabWidget, QFileDialog, QListWidget, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap
import pyfirmata
from Functions.motor_control import control_motor
from Functions.initialize_board import initialize_board
import threading
from Functions.valves_control import create_valve_control_section
from Functions.peltier_control import initialize_pids, set_pid_output_limits, start_monitoring, stop_monitoring
from Functions.temp_reader import SerialReader
from Functions.temperature_sweep import start_temperature_sweep
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from matplotlib.legend_handler import HandlerLine2D
import matplotlib

# Initialize hardware-related variables
board = None
motor_pins = {      # Define motor pins as in your original script
    'motor1': {'dir': 22, 'step': 23, 'enable': 24},
    'motor2': {'dir': 25, 'step': 26, 'enable': 27},
    'motor3': {'dir': 28, 'step': 29, 'enable': 30}
}
mdd3a_pins = {}
valve_group_pins = {
    'Group1': [35, 34, 33, 32, 31],
    'Group2': [40, 39, 38, 37, 36],
    'Group3': [45, 44, 43, 42, 41],
}

port = None

def find_arduino_port():
    """
    Searches through available serial ports to find an Arduino.
    Returns the port name if found, None otherwise.
    """
    arduino_ports = [
        '/dev/cu.usbmodem',  # Common prefix for Arduino on macOS
        '/dev/ttyUSB',       # Common prefix for Arduino on Linux
        'COM'                # Common prefix for Arduino on Windows
    ]
    for port in serial.tools.list_ports.comports():
        for prefix in arduino_ports:
            if port.device.startswith(prefix):
                return port.device
    return None

def initialize_hardware():
    global board, motor_pins, mdd3a_pins, valve_group_pins
    port = find_arduino_port()
    if port:
        board, motor_pins, mdd3a_pins, valve_group_pins = initialize_board(port)
        it = pyfirmata.util.Iterator(board)
        it.start()
        # Initialize photodiode pins and other components as in your original script
    else:
        print("Arduino not found. Please check your connections.")

class MotorControlWidget(QGroupBox):
    def __init__(self, motor_id):
        super().__init__(f"Motor {motor_id}")
        self.motor_id = motor_id
        self.init_ui()
        self.disable_motor()  # Disable motor on initialization

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.mode_var = QComboBox()
        modes = [('Clockwise Slow', '1-slow'), ('Clockwise Fast', '1-fast'),
                 ('Counter-Clockwise Slow', '0-slow'), ('Counter-Clockwise Fast', '0-fast')]
        for text, value in modes:
            self.mode_var.addItem(text, value)
        layout.addWidget(self.mode_var)

        volume_label = QLabel("Enter volume (uL):")
        layout.addWidget(volume_label)
        self.volume_entry = QLineEdit()
        layout.addWidget(self.volume_entry)

        self.start_button = QPushButton("Go")
        self.start_button.clicked.connect(self.start_motor)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def disable_motor(self):
        motor = motor_pins[self.motor_id]
        if 'enable_pin' in motor:
            motor['enable_pin'].write(1)  # Set enable pin to HIGH to disable the motor
        # print(f"Motor {self.motor_id} disabled")

    def start_motor(self):
        mode = self.mode_var.currentData()
        volume = float(self.volume_entry.text()) if self.volume_entry.text() else 0
        direction, speed = mode.split('-')
        motor = motor_pins[self.motor_id]
        
        # Enable the motor before starting
        if 'enable_pin' in motor:
            motor['enable_pin'].write(0)  # Set enable pin to LOW to enable the motor
        
        threading.Thread(target=control_motor, args=(motor, int(direction), speed, volume)).start()

class TemperatureControlWidget(QWidget):
    def __init__(self, board, mdd3a_pins):
        super().__init__()
        self.board = board
        self.mdd3a_pins = mdd3a_pins
        self.pids = initialize_pids()
        set_pid_output_limits(self.pids)
        self.monitoring_events = {i: threading.Event() for i in range(5)}
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        self.temp_labels = {}
        self.start_temps = {}
        self.end_temps = {}
        self.step_sizes = {}
        self.hold_times = {}
        self.analog_labels = {}

        for i in range(5):
            row = i
            current_temp_label = QLabel(f"Current Temp {i+1}: -- °C")
            layout.addWidget(current_temp_label, row, 0)
            self.temp_labels[i] = current_temp_label

            start_label = QLabel("Start Temp (°C):")
            layout.addWidget(start_label, row, 1)
            start_entry = QLineEdit()
            layout.addWidget(start_entry, row, 2)
            self.start_temps[i] = start_entry

            end_label = QLabel("End Temp (°C):")
            layout.addWidget(end_label, row, 3)
            end_entry = QLineEdit()
            layout.addWidget(end_entry, row, 4)
            self.end_temps[i] = end_entry

            step_label = QLabel("Step (°C):")
            layout.addWidget(step_label, row, 5)
            step_entry = QLineEdit()
            layout.addWidget(step_entry, row, 6)
            self.step_sizes[i] = step_entry

            hold_label = QLabel("Hold Time (mins):")
            layout.addWidget(hold_label, row, 7)
            hold_entry = QLineEdit()
            layout.addWidget(hold_entry, row, 8)
            self.hold_times[i] = hold_entry

            sweep_button = QPushButton(f"Start {i+1}")
            sweep_button.clicked.connect(lambda checked, i=i: self.start_temperature_sweep(i))
            layout.addWidget(sweep_button, row, 9)

            disable_button = QPushButton(f"Disable {i+1}")
            disable_button.clicked.connect(lambda checked, i=i: self.stop_monitoring(i))
            layout.addWidget(disable_button, row, 10)

        # Add analog labels
        for i in range(5):
            analog_label = QLabel(f"Analog Reading {i+1}: --")
            layout.addWidget(analog_label, 5, i)
            self.analog_labels[f'analog{i+1}'] = analog_label

        self.setLayout(layout)

    def start_temperature_sweep(self, i):
        if not self.monitoring_events[i].is_set():
            self.monitoring_events[i].set()
            start_temperature_sweep(i, 
                                    self.start_temps,
                                    self.end_temps,
                                    self.step_sizes,
                                    self.hold_times,
                                    self.pids,
                                    self.monitoring_events,
                                    self.temp_labels,
                                    self.analog_labels,
                                    self.board,
                                    self.mdd3a_pins)
        else:
            print(f"Temperature sweep already in progress for sensor {i + 1}")

    def stop_monitoring(self, i):
        stop_monitoring(i, self.monitoring_events, self.board, self.mdd3a_pins)


class ValveControlWidget(QWidget):
    def __init__(self, board):
        super().__init__()
        self.board = board
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        for group_id, pins in valve_group_pins.items():
            group_layout = QVBoxLayout()
            group_layout.addWidget(QLabel(group_id))
            for i, pin in enumerate(pins, start=1):
                button = QPushButton(f"Valve {i}")
                button.setCheckable(True)
                button.clicked.connect(lambda checked, p=pin: self.toggle_valve(p, checked))
                group_layout.addWidget(button)
            layout.addLayout(group_layout)
        self.setLayout(layout)

    def toggle_valve(self, pin, state):
        if self.board:
            try:
                # Try to get the existing pin object
                valve_pin = self.board.get_pin(f'd:{pin}:o')
            except pyfirmata.pyfirmata.PinAlreadyTakenError:
                # If the pin is already taken, it's likely set up correctly, so we can use it
                valve_pin = self.board.digital[pin]
            
            valve_pin.write(1 if state else 0)
            print(f"Valve {pin} {'opened' if state else 'closed'}")
        else:
            print(f"Cannot toggle valve {pin}. Board not available.")

class MainWindow(QMainWindow):
    def __init__(self, board, mdd3a_pins):
        super().__init__()
        self.board = board
        self.mdd3a_pins = mdd3a_pins
        self.setWindowTitle("Automated Liquid Distribution System")
        self.serial_reader = None
        self.init_ui()
        self.start_serial_reader()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Create tab widget
        tab_widget = QTabWidget()
        
        # Create and add Control Panel tab
        control_panel_tab = QWidget()
        control_panel_layout = QVBoxLayout()
        self.setup_control_panel(control_panel_layout)
        control_panel_tab.setLayout(control_panel_layout)
        tab_widget.addTab(control_panel_tab, "Control Panel")

        # Create and add Data Analysis tab
        data_analysis_tab = QWidget()
        data_analysis_layout = QVBoxLayout()
        self.setup_data_analysis(data_analysis_layout)
        data_analysis_tab.setLayout(data_analysis_layout)
        tab_widget.addTab(data_analysis_tab, "Data Analysis")

        # Create and add Optimization Panel tab
        # optimization_panel_tab = QWidget()
        # optimization_layout = QVBoxLayout()
        # self.setup_optimization_panel(optimization_layout)
        # optimization_panel_tab.setLayout(optimization_layout)
        # tab_widget.addTab(optimization_panel_tab, "Optimization Panel")

        main_layout.addWidget(tab_widget)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_control_panel(self, layout):
        # Add logos and title
        logo_layout = QHBoxLayout()
        
        # ND logo
        nd_logo = QLabel()
        nd_image_path = os.path.join(os.path.dirname(__file__), "Figures", "logo_bw.jpg")
        if os.path.exists(nd_image_path):
            nd_image = QPixmap(nd_image_path)
            nd_image = nd_image.scaled(int(nd_image.width() * 0.18), int(nd_image.height() * 0.18), Qt.AspectRatioMode.KeepAspectRatio)
            nd_logo.setPixmap(nd_image)
        else:
            print(f"ND logo image not found at: {nd_image_path}")
            nd_logo.setText("ND Logo")
        logo_layout.addWidget(nd_logo)

        # Title
        title_label = QLabel("Automated Liquid Distribution System")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        logo_layout.addWidget(title_label, 1)  # Give it more space in the layout

        # MonsterLab logo
        monsterlab_logo = QLabel()
        monsterlab_image_path = os.path.join(os.path.dirname(__file__), "Figures", "Lab.png")
        if os.path.exists(monsterlab_image_path):
            monsterlab_image = QPixmap(monsterlab_image_path)
            monsterlab_image = monsterlab_image.scaled(int(monsterlab_image.width()*0.15), int(monsterlab_image.height()*0.15), Qt.AspectRatioMode.KeepAspectRatio)
            monsterlab_logo.setPixmap(monsterlab_image)
        else:
            print(f"MonsterLab logo image not found at: {monsterlab_image_path}")
            monsterlab_logo.setText("MonsterLab Logo")
        logo_layout.addWidget(monsterlab_logo)

        layout.addLayout(logo_layout)

        # Motor Control Section
        motor_layout = QHBoxLayout()
        for motor_id in motor_pins.keys():
            motor_widget = MotorControlWidget(motor_id)
            motor_layout.addWidget(motor_widget)
        layout.addLayout(motor_layout)

        # Temperature Control Section
        self.temp_widget = TemperatureControlWidget(self.board, self.mdd3a_pins)
        layout.addWidget(self.temp_widget)

        # Valve Control Section
        valve_widget = ValveControlWidget(self.board)
        layout.addWidget(valve_widget)


    def setup_data_analysis(self, layout):
        # Create widgets
        self.folder_list = QListWidget()
        select_folder_button = QPushButton("Select Folders")
        analyze_button = QPushButton("Analyze")
        
        # Create plot widgets
        plot_layout = QHBoxLayout()
        self.temp_plot_widget = TemperaturePlotWidget()
        self.lcst_plot_widget = LCSTPlotWidget()
        plot_layout.addWidget(self.temp_plot_widget)
        plot_layout.addWidget(self.lcst_plot_widget)

        # Connect buttons to functions
        select_folder_button.clicked.connect(self.select_folders)
        analyze_button.clicked.connect(self.analyze_data)

        # Create layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(select_folder_button)
        button_layout.addWidget(analyze_button)

        layout.addWidget(QLabel("Selected Folders:"))
        layout.addWidget(self.folder_list)
        layout.addLayout(button_layout)
        layout.addLayout(plot_layout)

    def select_folders(self):
        self.folder_list.clear()
        while True:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", QFileDialog.Option.ShowDirsOnly)
            if folder:
                self.folder_list.addItem(folder)
                reply = QMessageBox.question(self, 'Continue?', 
                                             'Do you want to select another folder?',
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    break
            else:
                break

        if self.folder_list.count() == 0:
            QMessageBox.information(self, "No Folders Selected", "No folders were selected for analysis.")

    def analyze_data(self):
        folders = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
        if not folders:
            print("No folders selected")
            return

        all_data = []
        for folder in folders:
            for file in os.listdir(folder):
                if file.startswith("temperature_log_sensor_") and file.endswith(".txt"):
                    file_path = os.path.join(folder, file)
                    sensor_data = self.parse_temperature_file(file_path)
                    all_data.append((os.path.basename(folder), sensor_data))

        self.temp_plot_widget.plot_data(all_data)
        self.lcst_plot_widget.plot_lcst_data(folders)

    def parse_temperature_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        sensor_temps = []
        real_time_temps = []
        current_temp = None

        for line in lines:
            if "Set Sensor" in line:
                current_temp = float(line.split('to')[1].strip()[:-2].strip())
            if "Real-time Hold Temp:" in line:
                temp = float(line.split(':')[-1].strip()[:-2].strip())
                if current_temp is not None:
                    sensor_temps.append(current_temp)
                    real_time_temps.append(temp)

        return pd.DataFrame({
            'Sensor Temperature': sensor_temps,
            'Real-time Temperature': real_time_temps
        })

    def start_serial_reader(self):
        port = find_arduino_port()
        if port:
            print(f"Initializing SerialReader with port: {port}")
            if hasattr(self, 'serial_reader') and self.serial_reader:
                self.serial_reader.stop()
                self.serial_reader.wait()
            
            self.serial_reader = SerialReader(port, 57600)
            self.serial_reader.temperature_updated.connect(self.update_temperature_slot)
            self.serial_reader.analog_updated.connect(self.update_analog_slot)
            self.serial_reader.start()
            print("SerialReader started")
        else:
            print("Arduino port not found. Serial reading not started.")

    def update_temperature_slot(self, sensor_number, temperature):
        try:
            label = self.temp_widget.temp_labels.get(sensor_number)
            if label:
                label.setText(f"Current Temp {sensor_number + 1}: {temperature:.2f} °C")
                # print(f"Updated temperature label: Sensor {sensor_number + 1}, Temp {temperature:.2f}")
            else:
                print(f"Temperature label not found for sensor {sensor_number + 1}")
        except Exception as e:
            print(f"Failed to update temperature label: {e}")

    def update_analog_slot(self, sensor_number, analog_value):
        try:
            label = self.temp_widget.analog_labels.get(f'analog{sensor_number + 1}')
            if label:
                label.setText(f"Analog Reading {sensor_number + 1}: {analog_value}")
                # print(f"Updated analog label: Sensor {sensor_number + 1}, Value {analog_value}")
            else:
                print(f"Analog label not found for sensor {sensor_number + 1}")
        except Exception as e:
            print(f"Failed to update analog label: {e}")

    def closeEvent(self, event):
        if self.serial_reader:
            self.serial_reader.stop()
            self.serial_reader.wait()
        event.accept()

class PlotWidget(QWidget):
    def __init__(self, title):
        super().__init__()
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        self.ax.set_title(title)
        
        # Enable tight layout to prevent clipping of labels
        self.figure.tight_layout()

class TemperaturePlotWidget(PlotWidget):
    def __init__(self):
        super().__init__('Set Temperature vs Real-time Reading Temperature')
        self.lines = []
        self.data = {}
        
        # Add a rename button
        self.rename_button = QPushButton("Rename Legend Items")
        self.rename_button.clicked.connect(self.rename_legend_items)
        self.layout().insertWidget(1, self.rename_button)  # Insert button after the toolbar

    def plot_data(self, all_data):
        self.ax.clear()
        self.lines = []
        self.data = {}

        for folder_name, df in all_data:
            summary_df = df.groupby('Sensor Temperature').agg(['mean', 'std']).reset_index()
            summary_df.columns = ['Sensor Temperature', 'Mean Temperature', 'Temperature STD']
            
            line, = self.ax.plot(summary_df['Sensor Temperature'], summary_df['Mean Temperature'], 
                                 '-o', label=folder_name)
            self.ax.fill_between(summary_df['Sensor Temperature'],
                                 summary_df['Mean Temperature'] - summary_df['Temperature STD'],
                                 summary_df['Mean Temperature'] + summary_df['Temperature STD'],
                                 alpha=0.3)
            self.lines.append(line)
            self.data[folder_name] = {'line': line, 'df': summary_df}

        self.ax.set_xlabel('Set Temperature (°C)')
        self.ax.set_ylabel('Real-time Reading Temperature (°C)')
        self.ax.legend()
        self.ax.grid(True)

        self.canvas.draw()

    def rename_legend_items(self):
        if not self.lines:
            QMessageBox.information(self, "No Data", "No data to rename. Please plot data first.")
            return

        items = [line.get_label() for line in self.lines]
        item, ok = QInputDialog.getItem(self, "Select Item to Rename", "Choose a legend item:", items, 0, False)
        if ok and item:
            new_label, ok = QInputDialog.getText(self, 'Rename Legend Item', f'Enter new label for {item}:', text=item)
            if ok and new_label:
                for line in self.lines:
                    if line.get_label() == item:
                        line.set_label(new_label)
                        self.data[new_label] = self.data.pop(item)
                        break
                self.ax.legend()
                self.canvas.draw()

class LCSTPlotWidget(PlotWidget):
    def __init__(self):
        super().__init__('Normalized Rolling Average UV Readings Across Different Conditions')
        self.lines = []
        self.data = {}
        
        # Add a rename button
        self.rename_button = QPushButton("Rename Legend Items")
        self.rename_button.clicked.connect(self.rename_legend_items)
        self.layout().insertWidget(1, self.rename_button)

    def plot_lcst_data(self, folders):
        self.ax.clear()
        colors = ['blue', 'green', 'red', 'purple', 'orange']
        self.lines = []
        self.data = {}

        for folder in folders:
            for sensor in range(1, 6):  # Assuming up to 5 sensors
                temp_file = os.path.join(folder, f'temperature_log_sensor_{sensor}.txt')
                uv_file = os.path.join(folder, f'uv_log_sensor_{sensor}.txt')
                if os.path.exists(temp_file) and os.path.exists(uv_file):
                    temp_df, uv_df = self.parse_file(temp_file, uv_file)
                    temperatures, normalized_avgs = self.compute_normalized_averages(temp_df, uv_df)
                    if normalized_avgs:
                        lcst = self.interpolate_temperature(temperatures, normalized_avgs)
                        label = f"{os.path.basename(folder)}"
                        if isinstance(lcst, float):  # Only add LCST if it's a valid number
                            label += f' (50% at {lcst:.2f}°C)'
                        color = colors[(len(self.lines) % len(colors))]
                        line, = self.ax.plot(temperatures, normalized_avgs, marker='o', 
                                           linestyle='-', color=color, label=label)
                        self.lines.append(line)
                        self.data[label] = {
                            'line': line, 
                            'temperatures': temperatures, 
                            'normalized_avgs': normalized_avgs
                        }

        self.ax.set_xlabel('Holding Temperature (°C)')
        self.ax.set_ylabel('Normalized Average UV Reading (%)')
        self.ax.grid(True)
        self.ax.axhline(y=50, color='red', linestyle='--')

        leg = self.ax.legend()
        leg.set_draggable(True)
        for legline, origline in zip(leg.get_lines(), self.lines):
            legline.set_picker(5)
            legline.set_pickradius(5)

        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.draw()

    def parse_file(self, temp_file, uv_file):
        temp_data, uv_data = [], []
        with open(temp_file, 'r') as f:
            for line in f:
                parts = line.strip().split(': ', 1)
                if len(parts) == 2:
                    temp_data.append(parts)
        temp_df = pd.DataFrame(temp_data, columns=['Time', 'Event'])
        temp_df['Time'] = pd.to_datetime(temp_df['Time'], errors='coerce')

        with open(uv_file, 'r') as f:
            for line in f:
                parts = line.strip().split(': ', 2)
                if len(parts) == 3:
                    uv_data.append(parts)
        uv_df = pd.DataFrame(uv_data, columns=['Time', 'Label', 'Value'])
        uv_df['Time'] = pd.to_datetime(uv_df['Time'], errors='coerce')
        uv_df['Value'] = pd.to_numeric(uv_df['Value'], errors='coerce')

        return temp_df, uv_df

    def compute_normalized_averages(self, temp_df, uv_df):
        holding_events = temp_df[temp_df['Event'].str.contains('Holding')]
        temperatures, normalized_avgs = [], []

        for _, row in holding_events.iterrows():
            start_time = row['Time']
            end_time = start_time + pd.Timedelta(minutes=5)
            mask = (uv_df['Time'] >= start_time) & (uv_df['Time'] <= end_time)
            filtered_uv = uv_df.loc[mask, 'Value']

            temp_value = float(row['Event'].split(' ')[1].replace('°C', ''))
            temperatures.append(temp_value)

            if not filtered_uv.empty:
                rolling_avg = filtered_uv.rolling(window=20, min_periods=1).mean()
                normalized_avgs.append(rolling_avg.mean())

        if normalized_avgs:
            max_val = max(normalized_avgs[:5])
            min_val = min(normalized_avgs[-8:])
            range_val = max_val - min_val
            normalized_avgs = [(x - min_val) / range_val * 100 for x in normalized_avgs]

        return temperatures, normalized_avgs

    def interpolate_temperature(self, temperatures, normalized_avgs):
        temps = np.array(temperatures)
        avgs = np.array(normalized_avgs)

        crossings = []
        for i in range(len(avgs)-1):
            if (avgs[i] - 50) * (avgs[i+1] - 50) <= 0:
                t1, t2 = temps[i], temps[i+1]
                v1, v2 = avgs[i], avgs[i+1]
                if v1 != v2:
                    t_50 = t1 + (t2 - t1) * (50 - v1) / (v2 - v1)
                    crossings.append((t_50, i))

        if not crossings:
            return "50% is out of the interpolation range."

        slopes = []
        for t_50, i in crossings:
            slope = abs(avgs[i+1] - avgs[i]) / (temps[i+1] - temps[i])
            slopes.append((t_50, slope))

        return max(slopes, key=lambda x: x[1])[0]

    def on_pick(self, event):
        if isinstance(event.artist, matplotlib.lines.Line2D):
            line = event.artist
            visible = not line.get_visible()
            line.set_visible(visible)
            line.set_alpha(1.0 if visible else 0.2)
            self.canvas.draw()

    def on_click(self, event):
        if event.dblclick:
            for line in self.lines:
                if line.contains(event)[0]:
                    self.rename_legend_item(line)
                    break

    def rename_legend_item(self, line):
        old_label = line.get_label()
        new_label, ok = QInputDialog.getText(self, 'Rename Legend Item', f'Enter new label for {old_label}:', text=old_label)
        if ok and new_label:
            line.set_label(new_label)
            self.data[new_label] = self.data.pop(old_label)
            self.ax.legend()
            self.canvas.draw()

    def rename_legend_items(self):
        if not self.lines:
            QMessageBox.information(self, "No Data", "No data to rename. Please plot data first.")
            return

        items = [line.get_label() for line in self.lines]
        item, ok = QInputDialog.getItem(self, "Select Item to Rename", "Choose a legend item:", items, 0, False)
        if ok and item:
            new_label, ok = QInputDialog.getText(self, 'Rename Legend Item', f'Enter new label for {item}:', text=item)
            if ok and new_label:
                for line in self.lines:
                    if line.get_label() == item:
                        line.set_label(new_label)
                        self.data[new_label] = self.data.pop(item)
                        break
                self.ax.legend()
                self.canvas.draw()

if __name__ == '__main__':
    initialize_hardware()
    app = QApplication(sys.argv)
    main_window = MainWindow(board, mdd3a_pins)
    main_window.show()
    sys.exit(app.exec())