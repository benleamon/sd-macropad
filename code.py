import time
import board
import digitalio
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS


button = digitalio.DigitalInOut(board.GP2)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)

last_button_state = button.value

while True:
    current_button_state = button.value

    # Button goes from HIGH to LOW when pressed
    if last_button_state and not current_button_state:
        layout.write("Hello from the macropad!")

    last_button_state = current_button_state
    time.sleep(0.01)