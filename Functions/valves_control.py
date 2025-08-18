# valves_control.py

import tkinter as tk

def initialize_valve_pins(board, valve_group_pins):
    """
    Initializes the valve pins as OUTPUT.
    :param board: The pyFirmata Arduino board instance.
    :param valve_group_pins: Dictionary of valve pin groups.
    """
    for group in valve_group_pins.values():
        for pin in group:
            board.digital[pin].mode = OUTPUT

def control_valve(board, pin, state):
    """
    Controls a specific air valve by writing a state to the pin.
    :param board: The pyFirmata Arduino board instance.
    :param pin: Pin number of the valve.
    :param state: State to set the valve (True for open, False for close).
    """
    board.digital[pin].write(state)

# def toggle_valve(board, valve_group_pins, group, valve_number):
#     """
#     Toggles the state of a specified valve.
#     :param board: The pyFirmata Arduino board instance.
#     :param valve_group_pins: Dictionary of valve pin groups.
#     :param group: The group name of the valve.
#     :param valve_number: The valve number in the group.
#     """
#     valve_pins = valve_group_pins[group]
#     pin = valve_pins[valve_number]
#     current_state = board.digital[pin].read()
#     new_state = not current_state
#     control_valve(board, pin, new_state)
#
# def create_valve_control_section(root, board, valve_group_pins, group_name, group_pins, row):
#     """
#     Creates a section in the GUI for valve control.
#     :param root: Tkinter root or frame.
#     :param board: The pyFirmata Arduino board instance.
#     :param valve_group_pins: Dictionary of valve pin groups.
#     :param group_name: The name of the valve group.
#     :param group_pins: The pins in the valve group.
#     :param row: The row in the GUI to place the control section.
#     """
#     frame = tk.LabelFrame(root, text=group_name, padx=10, pady=10)
#     frame.grid(row=row, column=0, columnspan=4, padx=10, pady=5, sticky="ew")
#
#     for i, pin in enumerate(group_pins):
#         btn_text = f"Valve {i+1}"
#         btn = tk.Button(frame, text=btn_text, command=lambda i=i: toggle_valve(board, valve_group_pins, group_name, i))
#         btn.grid(row=0, column=i, padx=5, pady=5)

def create_valve_control_section(root, board, valve_group_pins, group_name, group_pins, column):
    frame = tk.LabelFrame(root, text=group_name, padx=5, pady=5)
    frame.grid(row=1, column=column, columnspan=1, padx=5, pady=5, sticky="ew")

    valve_states = [tk.BooleanVar() for _ in group_pins]

    # Correcting the lambda function to properly capture the current loop variables
    for i, pin in enumerate(group_pins):
        btn_text = f"Valve {i + 1}"
        valve_state = valve_states[i]
        toggle_switch = tk.Checkbutton(frame, text=btn_text, var=valve_state,
                                       onvalue=True, offvalue=False,
                                       command=lambda pin=pin, valve_state=valve_state: toggle_valve(board, pin, valve_state.get()))
        toggle_switch.grid(row=i, column=column, padx=5, pady=5)

def toggle_valve(board, pin, state):
    """
    Controls a specific air valve by writing a state to the pin.
    :param board: The pyFirmata Arduino board instance.
    :param pin: Pin number of the valve.
    :param state: Desired state of the valve (True for open, False for close).
    """
    control_valve(board, pin, state)

