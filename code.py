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


# --------------------------------------------------
# Buttons
# --------------------------------------------------

button_pins = [
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
]

buttons = []

for pin in button_pins:
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    buttons.append(button)


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

        # Ignore blank lines and comments
        if not line or line.startswith("#"):
            continue

        parts = line.split("|", 2)

        if len(parts) != 3:
            print("Ignoring malformed line:", line)
            continue

        button_number = int(parts[0].strip())
        action_type = parts[1].strip().upper()
        value = parts[2].strip()

        macros[button_number] = (action_type, value)


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
}


def get_keycode(name):
    name = name.strip().upper()

    if name in key_aliases:
        name = key_aliases[name]

    return getattr(Keycode, name)


# --------------------------------------------------
# Perform macro
# --------------------------------------------------

def run_macro(button_number):

    if button_number not in macros:
        print("No macro assigned to button", button_number)
        return

    action_type, value = macros[button_number]

    print(
        "Button",
        button_number,
        "→",
        action_type,
        value
    )

    if action_type == "TEXT":
        layout.write(value)

    elif action_type == "KEY":
        keyboard.send(get_keycode(value))

    elif action_type == "HOTKEY":
        names = value.split("+")
        keycodes = [get_keycode(name) for name in names]

        keyboard.send(*keycodes)

    else:
        print("Unknown action type:", action_type)


# --------------------------------------------------
# Main loop
# --------------------------------------------------

last_states = [button.value for button in buttons]

while True:

    for index, button in enumerate(buttons):

        current_state = button.value

        # HIGH → LOW means newly pressed
        if last_states[index] and not current_state:
            run_macro(index + 1)

        last_states[index] = current_state

    time.sleep(0.01)
    