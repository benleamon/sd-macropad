import time
import board
import busio
import digitalio
import sdcardio
import storage
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS


# -------------------------
# Button
# -------------------------

button = digitalio.DigitalInOut(board.GP2)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP


# -------------------------
# SD card
# -------------------------

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


# -------------------------
# Load macro
# -------------------------

with open("/sd/test.txt", "r") as f:
    button1_text = f.read().rstrip("\r\n")

print("Loaded button 1:")
print(button1_text)


# -------------------------
# USB keyboard
# -------------------------

keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)


# -------------------------
# Main loop
# -------------------------

last_button_state = button.value

while True:
    current_button_state = button.value

    # Detect new press
    if last_button_state and not current_button_state:
        print("Button 1 pressed")
        layout.write(button1_text)

    last_button_state = current_button_state
    time.sleep(0.01)