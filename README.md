# Self-Driving Laboratory for LCST Optimization

**An Automated System for Optimizing the Lower Critical Solution Temperature of Thermoresponsive Polymers**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.7.1-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Data Analysis](#data-analysis)
- [Citation](#citation)


## 🔬 Overview

This Self-Driving Laboratory (SDL) is an automated experimental platform designed to optimize the Lower Critical Solution Temperature (LCST) of thermoresponsive polymers. The system integrates hardware automation with intelligent data analysis to accelerate materials discovery and characterization.

**Key Capabilities:**
- Automated liquid handling and sample preparation
- Precise temperature control with Peltier heating/cooling
- Real-time transmittance measurements for LCST determination
- Intelligent data analysis and visualization
- Autonomous experimental design and execution

## ✨ Features

### 🤖 Hardware Automation
- **3 Stepper Motors**: Precise liquid dispensing (2.4 μL resolution per step)
- **5 Temperature Sensors**: Multi-zone temperature monitoring and control
- **15 Valves**: Automated sample routing (3 groups × 5 valves)
- **Photodiode Sensors**: Real-time transmittance measurements for LCST detection
- **Peltier Controllers**: PID-controlled heating/cooling systems

### 💻 Software Features
- **Real-time Monitoring**: Live temperature and transmittance readings
- **Automated Sweeps**: Programmable temperature ramping protocols
- **Data Logging**: Timestamped experimental data storage
- **Advanced Analytics**: LCST calculation with statistical analysis
- **Interactive GUI**: PyQt6-based control interface
- **Remote Control**: Arduino-based hardware communication

### 📊 Analysis Tools
- **Temperature Calibration**: Set vs. actual temperature analysis
- **LCST Determination**: Automated 50% transmission point calculation
- **Data Visualization**: Interactive plots with error bars and statistics


## 🔧 Hardware Requirements

### Electronics
- **Arduino Mega 2560** 
- **5× Temperature Sensor Modules** 
- **5× Peltier Cooling/Heating Elements**
- **5× Motor Drivers** (for Peltier control)
- **3× Stepper Motor Drivers** (for pumps)
- **5× Photodiode Sensors** 

### Mechanical Components
- **3× Stepper Motors** 
- **15× Valves** 
- **Temperature-controlled sample holders**
- **Fluidic connections and tubing**

### Power Supply
- **12V DC Supply**

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Arduino IDE (for firmware upload)
- Compatible operating system (Windows, macOS, Linux)

### Software Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/SDL_LCST_OP.git
   cd SDL_LCST_OP
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Hardware Connection**
   - Connect Arduino Mega to your computer via USB
   - Upload the appropriate Firmata firmware to Arduino
   - Wire components according to pin assignments
   - Verify all sensor and actuator connections
   - Test power supplies and safety systems

4. **Launch the Application**
   ```bash
   python main.py
   ```

### Arduino Setup
1. Install Arduino IDE
2. Upload Firmata sketch to Arduino Mega
3. Verify COM port connection
4. Test hardware communication

## 📖 Usage

### Starting the System

1. **Hardware Initialization**
   - Power on all hardware components
   - Connect Arduino to computer
   - Launch the application with `python main.py`

2. **Control Panel Operations**
   - **Motor Control**: Set volume and direction for liquid dispensing
   - **Temperature Control**: Configure sweep parameters (start, end, step, hold time)
   - **Valve Control**: Manual control of sample routing valves

### Running Experiments

#### Temperature Sweep Protocol
1. Navigate to the **Control Panel** tab
2. For each sensor, configure:
   - **Start Temperature**: Initial temperature (°C)
   - **End Temperature**: Final temperature (°C)
   - **Step Size**: Temperature increment (°C)
   - **Hold Time**: Duration at each temperature (minutes)
3. Click **Start** to begin automated sweep
4. Monitor real-time progress and data logging

#### Data Collection
- Temperature and UV data are automatically logged
- Files saved in `Data/SensorX_YYYYMMDD_HHMMSS/` format
- Real-time visualization in GUI

### Data Analysis

1. **Switch to Data Analysis Tab**
2. **Select Data Folders**: Choose experimental datasets
3. **Run Analysis**: Calculate LCST from transmittance data
4. **View Results**: Interactive plots with LCST values
5. **Export Data**: Save processed results

## 📊 Data Analysis

### LCST Calculation Method
The system determines LCST by:
1. **Normalization**: UV readings normalized to 0-100% scale
2. **Interpolation**: Linear interpolation to find 50% transmission point
## 📚 Citation

If you use this system in your research, please cite our paper:

```bibtex
@article{
}
```

---

*Built with ❤️ for advancing materials science through automation*