# motor_control.py
from pyfirmata import ArduinoMega, util, OUTPUT
import time

# Initialize the board and motors
def initialize_board(port):
    board = ArduinoMega(port)
    motor_pins = {
        # 'motor1': {'dir': 23, 'step': 22, 'enable': 44},
        # 绿色direction， 蓝色step，白色enable
        'motor1': {'dir': 22, 'step': 23, 'enable': 24},
        # 'motor2': {'dir': 25, 'step': 24, 'enable': 46},
        'motor2': {'dir': 25, 'step': 26, 'enable': 27},
        # 'motor3': {'dir': 27, 'step': 26, 'enable': 48}
        'motor3': {'dir': 28, 'step': 29, 'enable': 30}
    }

    for motor in motor_pins.values():
        motor['dir_pin'] = board.get_pin(f'd:{motor["dir"]}:o')
        motor['step_pin'] = board.get_pin(f'd:{motor["step"]}:o')
        motor['enable_pin'] = board.get_pin(f'd:{motor["enable"]}:o')
        motor['enable_pin'].write(0)

    mdd3a_pins = {
        'board5': {'inputA': board.get_pin('d:13:p'), 'inputB': board.get_pin('d:12:p')},
        'board4': {'inputA': board.get_pin('d:11:p'), 'inputB': board.get_pin('d:10:p')},
        'board3': {'inputA': board.get_pin('d:9:p'), 'inputB': board.get_pin('d:8:p')},
        'board2': {'inputA': board.get_pin('d:7:p'), 'inputB': board.get_pin('d:6:p')},
        'board1': {'inputA': board.get_pin('d:5:p'), 'inputB': board.get_pin('d:4:p')},
    }

    # photodiode_pins = {
    #     'photodiode1': {'analog': board.get_pin('a:0:i')},
    #     'photodiode2': {'analog': board.get_pin('a:1:i')},
    #     'photodiode3': {'analog': board.get_pin('a:2:i')},
    #     'photodiode4': {'analog': board.get_pin('a:3:i')},
    #     'photodiode5': {'analog': board.get_pin('a:4:i')},
    # }
    # Air valve pin setup
    valve_group_pins = {
        'Group1': [35, 34, 33, 32, 31],
        'Group2': [40, 39, 38, 37, 36],
        'Group3': [45, 44, 43, 42, 41],
    }

    for group in valve_group_pins.values():
        for pin in group:
            board.get_pin(f'd:{pin}:o').mode = OUTPUT

    return board, motor_pins, mdd3a_pins,valve_group_pins