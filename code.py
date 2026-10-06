import time
import board
import busio
import digitalio
import sdcardio
import storage
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

print("test starting")

# --------------------------------------------------
# Matrix pin assignments
# --------------------------------------------------

# Five rows
row_pins = [
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
    board.GP6,
]

# Four columns
column_pins = [
    board.GP7,
    board.GP8,
    board.GP9,
    board.GP14,
]


# --------------------------------------------------
# Set up matrix rows
# --------------------------------------------------

rows = []

for pin in row_pins:
    row = digitalio.DigitalInOut(pin)
    row.direction = digitalio.Direction.OUTPUT

    # Rows remain HIGH when inactive
    row.value = True

    rows.append(row)


# --------------------------------------------------
# Set up matrix columns
# --------------------------------------------------

columns = []

for pin in column_pins:
    column = digitalio.DigitalInOut(pin)
    column.direction = digitalio.Direction.INPUT
    column.pull = digitalio.Pull.UP

    columns.append(column)


# --------------------------------------------------
# Button mapping
# --------------------------------------------------

# Maps matrix positions to logical button numbers.
#
# R1:   1   2   3   4
# R2:   5   6   7   8
# R3:   9  10  11  12
# R4:  13  14  15  16
# R5:  17  18  19  20

button_map = [
    [1,  2,  3,  4],
    [5,  6,  7,  8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
    [17, 18, 19, 20],
]


# --------------------------------------------------
# SD card
# --------------------------------------------------

spi = busio.SPI(
    board.GP10,
    MOSI=board.GP11,
    MISO=board.GP12
)

cs = digitalio.DigitalInOut(board.GP13)

sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

print("SD card mounted.")


# --------------------------------------------------
# Load macros
# --------------------------------------------------

macros = {}

with open("/sd/macros.txt", "r") as file:

    for raw_line in file:

        line = raw_line.strip()

        # Ignore blank lines
        if not line:
            continue

        # Ignore comments
        if line.startswith("#"):
            continue

        parts = line.split("|", 2)

        if len(parts) != 3:
            print("Ignoring malformed line:", line)
            continue

        try:
            button_number = int(parts[0].strip())

        except ValueError:
            print("Invalid button number:", line)
            continue

        action_type = parts[1].strip().upper()
        value = parts[2].strip()

        macros[button_number] = (
            action_type,
            value
        )


print("Loaded macros:")
print(macros)


# --------------------------------------------------
# USB keyboard
# --------------------------------------------------

keyboard = Keyboard(usb_hid.devices)

layout = KeyboardLayoutUS(keyboard)


# --------------------------------------------------
# Key-name conversion
# --------------------------------------------------

key_aliases = {
    "CTRL": "CONTROL",
    "CMD": "COMMAND",
    "WIN": "WINDOWS",
    "ESC": "ESCAPE",
    "RETURN": "ENTER",
    "DEL": "DELETE",
}


def get_keycode(name):

    name = name.strip().upper()

    if name in key_aliases:
        name = key_aliases[name]

    try:
        return getattr(Keycode, name)

    except AttributeError:
        print("Unknown key:", name)
        return None


# --------------------------------------------------
# Perform macro
# --------------------------------------------------

def run_macro(button_number):

    if button_number not in macros:
        print(
            "No macro assigned to button",
            button_number
        )
        return

    action_type, value = macros[button_number]

    print(
        "Button",
        button_number,
        "->",
        action_type,
        value
    )

    # --------------------------
    # TEXT
    # --------------------------

    if action_type == "TEXT":

        layout.write(value)

    # --------------------------
    # Single key
    # --------------------------

    elif action_type == "KEY":

        keycode = get_keycode(value)

        if keycode is not None:
            keyboard.send(keycode)

    # --------------------------
    # Hotkey
    # --------------------------

    elif action_type == "HOTKEY":

        names = value.split("+")

        keycodes = []

        for name in names:

            keycode = get_keycode(name)

            if keycode is None:
                return

            keycodes.append(keycode)

        keyboard.send(*keycodes)

    # --------------------------
    # Unknown action
    # --------------------------

    else:

        print(
            "Unknown action type:",
            action_type
        )


# --------------------------------------------------
# Matrix state
# --------------------------------------------------

last_states = [
    [False for _ in column_pins]
    for _ in row_pins
]


print("Macropad ready.")


# --------------------------------------------------
# Main loop
# --------------------------------------------------

while True:

    # Scan one row at a time
    for row_index, row in enumerate(rows):

        # Activate current row
        row.value = False

        # Brief settling time
        time.sleep(0.001)

        # Check each column
        for column_index, column in enumerate(columns):

            pressed = not column.value

            previous_state = last_states[
                row_index
            ][
                column_index
            ]

            # Run macro only on a NEW press
            if pressed and not previous_state:

                button_number = button_map[
                    row_index
                ][
                    column_index
                ]

                run_macro(button_number)

            # Store current state
            last_states[
                row_index
            ][
                column_index
            ] = pressed

        # Deactivate this row
        row.value = True

    time.sleep(0.005)