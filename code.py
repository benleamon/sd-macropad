import time
import json

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
# Optional Japanese keyboard layout
# --------------------------------------------------

try:
    from adafruit_hid.keyboard_layout_jp import KeyboardLayoutJP
except ImportError:
    KeyboardLayoutJP = None


# --------------------------------------------------
# Constants
# --------------------------------------------------

CONFIG_PATH = "/sd/config.json"
PROFILE_DIR = "/sd/profiles"

SUPPORTED_SCHEMA_VERSION = 1


# --------------------------------------------------
# Matrix pin assignments
# --------------------------------------------------

# 5 rows
ROW_PINS = [
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
    board.GP6,
]

# 4 columns
COLUMN_PINS = [
    board.GP7,
    board.GP8,
    board.GP9,
    board.GP14,
]


# --------------------------------------------------
# Physical matrix -> logical button numbers
# --------------------------------------------------

BUTTON_MAP = [
    [1,  2,  3,  4],
    [5,  6,  7,  8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
    [17, 18, 19, 20],
]


# --------------------------------------------------
# Matrix setup
# --------------------------------------------------

rows = []

for pin in ROW_PINS:
    row = digitalio.DigitalInOut(pin)
    row.direction = digitalio.Direction.OUTPUT
    row.value = True
    rows.append(row)


columns = []

for pin in COLUMN_PINS:
    column = digitalio.DigitalInOut(pin)
    column.direction = digitalio.Direction.INPUT
    column.pull = digitalio.Pull.UP
    columns.append(column)


# --------------------------------------------------
# SD card
# --------------------------------------------------

spi = busio.SPI(
    board.GP10,
    MOSI=board.GP11,
    MISO=board.GP12,
)

cs = digitalio.DigitalInOut(board.GP13)

sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)

storage.mount(vfs, "/sd")

print("SD card mounted.")


# --------------------------------------------------
# USB keyboard
# --------------------------------------------------

keyboard = Keyboard(usb_hid.devices)

layout_us = KeyboardLayoutUS(keyboard)

if KeyboardLayoutJP is not None:
    layout_jis = KeyboardLayoutJP(keyboard)
else:
    layout_jis = None


# --------------------------------------------------
# Runtime state
# --------------------------------------------------

config = {}

profile_order = []
fn_button = 20

active_profile_id = None
active_profile_name = None

active_layout_name = "us"
active_layout = layout_us

active_macros = {
    "normal": {},
    "fn": {},
}


# --------------------------------------------------
# JSON helpers
# --------------------------------------------------

def load_json(path):
    with open(path, "r") as file:
        return json.load(file)


def check_schema(data, path):
    version = data.get("schema_version")

    if version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported schema_version in {}: {}".format(
                path,
                version
            )
        )


# --------------------------------------------------
# Global configuration
# --------------------------------------------------

def load_config():

    global config
    global profile_order
    global fn_button

    data = load_json(CONFIG_PATH)

    check_schema(data, CONFIG_PATH)

    profile_order = data.get(
        "profile_order",
        []
    )

    if not profile_order:
        raise ValueError(
            "profile_order cannot be empty"
        )

    fn_button = int(
        data.get("fn_button", 20)
    )

    if fn_button < 1 or fn_button > 20:
        raise ValueError(
            "fn_button must be between 1 and 20"
        )

    config = data

    print("Profiles:", profile_order)
    print("Fn button:", fn_button)


# --------------------------------------------------
# Keyboard layouts
# --------------------------------------------------

def select_layout(name):

    name = name.strip().lower()

    if name in (
        "us",
        "ansi",
    ):
        return "us", layout_us

    if name in (
        "jis",
        "jp",
        "ja",
    ):

        if layout_jis is None:
            raise RuntimeError(
                "JIS layout requested, but "
                "keyboard_layout_jp.py is not installed."
            )

        return "jis", layout_jis

    raise ValueError(
        "Unknown keyboard layout: {}".format(name)
    )


# --------------------------------------------------
# Profile loading
# --------------------------------------------------

def load_profile(profile_id):

    global active_profile_id
    global active_profile_name
    global active_layout_name
    global active_layout
    global active_macros

    profile_id = profile_id.strip().lower()

    path = "{}/{}.json".format(
        PROFILE_DIR,
        profile_id
    )

    data = load_json(path)

    check_schema(data, path)

    profile_info = data.get(
        "profile",
        {}
    )

    profile_name = profile_info.get(
        "name",
        profile_id
    )

    layout_name = profile_info.get(
        "layout",
        "us"
    )

    (
        selected_layout_name,
        selected_layout,
    ) = select_layout(layout_name)

    normal_macros = data.get(
        "normal",
        {}
    )

    fn_macros = data.get(
        "fn",
        {}
    )

    active_profile_id = profile_id
    active_profile_name = profile_name

    active_layout_name = selected_layout_name
    active_layout = selected_layout

    active_macros = {
        "normal": normal_macros,
        "fn": fn_macros,
    }

    print("------------------------------")
    print("Profile:", active_profile_name)
    print("Profile ID:", active_profile_id)
    print("Layout:", active_layout_name)
    print("------------------------------")


# --------------------------------------------------
# Profile switching
# --------------------------------------------------

def get_profile_index():

    try:
        return profile_order.index(
            active_profile_id
        )

    except ValueError:
        return 0


def next_profile():

    index = get_profile_index()

    index = (
        index + 1
    ) % len(profile_order)

    load_profile(
        profile_order[index]
    )


def previous_profile():

    index = get_profile_index()

    index = (
        index - 1
    ) % len(profile_order)

    load_profile(
        profile_order[index]
    )


def reload_configuration():

    current_profile = active_profile_id

    load_config()

    if (
        current_profile is not None
        and current_profile in profile_order
    ):
        target_profile = current_profile

    else:
        target_profile = config.get(
            "default_profile",
            profile_order[0]
        )

        if target_profile not in profile_order:
            target_profile = profile_order[0]

    load_profile(target_profile)

    print("Configuration reloaded.")


# --------------------------------------------------
# Ducky-style key names
# --------------------------------------------------

KEY_ALIASES = {
    "CTRL": "CONTROL",

    "CMD": "GUI",
    "COMMAND": "GUI",

    "WIN": "GUI",
    "WINDOWS": "GUI",

    "ESC": "ESCAPE",
    "RETURN": "ENTER",
    "DEL": "DELETE",

    "UP": "UP_ARROW",
    "DOWN": "DOWN_ARROW",
    "LEFT": "LEFT_ARROW",
    "RIGHT": "RIGHT_ARROW",

    "PAGEUP": "PAGE_UP",
    "PAGEDOWN": "PAGE_DOWN",

    "CAPSLOCK": "CAPS_LOCK",
    "PRINTSCREEN": "PRINT_SCREEN",
}


DIGIT_NAMES = {
    "0": "ZERO",
    "1": "ONE",
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINE",
}


def get_keycode(name):

    name = name.strip().upper()

    if name in KEY_ALIASES:
        name = KEY_ALIASES[name]

    if name in DIGIT_NAMES:
        name = DIGIT_NAMES[name]

    try:
        return getattr(Keycode, name)

    except AttributeError:
        return None


# --------------------------------------------------
# Send key / hotkey
# --------------------------------------------------

def send_key_command(command):

    tokens = command.split()

    keycodes = []

    for token in tokens:

        keycode = get_keycode(token)

        if keycode is None:
            print(
                "Unknown key:",
                token
            )
            return

        keycodes.append(keycode)

    if keycodes:
        keyboard.send(*keycodes)


# --------------------------------------------------
# Macropad-specific commands
# --------------------------------------------------

def run_system_command(argument):

    parts = argument.strip().split(
        " ",
        1
    )

    if not parts:
        return

    command = parts[0].upper()

    if len(parts) > 1:
        value = parts[1].strip()
    else:
        value = ""

    if command == "PROFILE_NEXT":
        next_profile()

    elif command == "PROFILE_PREV":
        previous_profile()

    elif command == "PROFILE":

        if not value:
            print(
                "SYSTEM PROFILE requires a profile ID"
            )
            return

        load_profile(
            value.lower()
        )

    elif command == "RELOAD":
        reload_configuration()

    else:
        print(
            "Unknown SYSTEM command:",
            argument
        )


# --------------------------------------------------
# Execute one macro instruction
# --------------------------------------------------

def execute_instruction(line):

    line = line.strip()

    if not line:
        return

    parts = line.split(
        " ",
        1
    )

    command = parts[0].upper()

    if len(parts) > 1:
        argument = parts[1]
    else:
        argument = ""

    # DuckyScript comment
    if command == "REM":
        return

    # Type text
    if command == "STRING":

        try:
            active_layout.write(argument)

        except Exception as error:
            print(
                "Could not type STRING:",
                error
            )

        return

    # Type text and press Enter
    if command == "STRINGLN":

        try:
            active_layout.write(argument)
            keyboard.send(
                Keycode.ENTER
            )

        except Exception as error:
            print(
                "Could not type STRINGLN:",
                error
            )

        return

    # Delay in milliseconds
    if command == "DELAY":

        try:
            milliseconds = int(argument)

        except ValueError:
            print(
                "Invalid DELAY:",
                argument
            )
            return

        time.sleep(
            milliseconds / 1000
        )

        return

    # Our macropad-specific namespace
    if command == "SYSTEM":

        run_system_command(
            argument
        )

        return

    # Otherwise interpret the entire line
    # as a key / hotkey command:
    #
    # ENTER
    # CTRL C
    # CTRL SHIFT S
    # ALT TAB

    send_key_command(line)


# --------------------------------------------------
# Execute a macro
# --------------------------------------------------

def run_macro(commands):

    if not isinstance(commands, list):

        print(
            "Macro is not a list:",
            commands
        )

        return

    default_delay = 0
    previous_instruction = None

    for line in commands:

        if not isinstance(line, str):
            print(
                "Ignoring non-string macro instruction:",
                line
            )
            continue

        stripped = line.strip()

        if not stripped:
            continue

        parts = stripped.split(
            " ",
            1
        )

        command = parts[0].upper()

        if len(parts) > 1:
            argument = parts[1]
        else:
            argument = ""

        # DuckyScript-style default delay
        if command in (
            "DEFAULT_DELAY",
            "DEFAULTDELAY",
        ):

            try:
                default_delay = int(argument)

            except ValueError:
                print(
                    "Invalid DEFAULT_DELAY:",
                    argument
                )

            continue

        # Repeat previous instruction
        if command == "REPEAT":

            if previous_instruction is None:
                print(
                    "REPEAT has no previous instruction"
                )
                continue

            try:
                count = int(argument)

            except ValueError:
                print(
                    "Invalid REPEAT:",
                    argument
                )
                continue

            for _ in range(count):

                execute_instruction(
                    previous_instruction
                )

                if default_delay > 0:
                    time.sleep(
                        default_delay / 1000
                    )

            continue

        execute_instruction(
            stripped
        )

        # Comments do not become the
        # repeatable previous instruction.
        if command != "REM":
            previous_instruction = stripped

        if default_delay > 0:
            time.sleep(
                default_delay / 1000
            )


# --------------------------------------------------
# Run one logical button
# --------------------------------------------------

def run_button(
    button_number,
    layer
):

    layer_macros = active_macros.get(
        layer,
        {}
    )

    # JSON object keys are always strings.
    button_key = str(
        button_number
    )

    commands = layer_macros.get(
        button_key
    )

    if commands is None:

        print(
            "No {} macro for button {}".format(
                layer,
                button_number
            )
        )

        return

    print(
        "{} / {} / button {}".format(
            active_profile_name,
            layer,
            button_number
        )
    )

    run_macro(commands)


# --------------------------------------------------
# Matrix scanner
# --------------------------------------------------

def scan_matrix():

    states = [
        [False for _ in COLUMN_PINS]
        for _ in ROW_PINS
    ]

    for row_index, row in enumerate(rows):

        # Activate row.
        row.value = False

        time.sleep(0.001)

        for column_index, column in enumerate(
            columns
        ):

            states[
                row_index
            ][
                column_index
            ] = not column.value

        # Deactivate row.
        row.value = True

    return states


# --------------------------------------------------
# Check one logical button
# --------------------------------------------------

def button_is_pressed(
    states,
    button_number
):

    for row_index in range(
        len(BUTTON_MAP)
    ):

        for column_index in range(
            len(BUTTON_MAP[row_index])
        ):

            if (
                BUTTON_MAP[
                    row_index
                ][
                    column_index
                ]
                == button_number
            ):

                return states[
                    row_index
                ][
                    column_index
                ]

    return False


# --------------------------------------------------
# Startup
# --------------------------------------------------

load_config()

default_profile = config.get(
    "default_profile",
    profile_order[0]
)

if default_profile not in profile_order:
    default_profile = profile_order[0]

load_profile(
    default_profile
)

last_states = scan_matrix()

print("Macropad ready.")


# --------------------------------------------------
# Main loop
# --------------------------------------------------

while True:

    current_states = scan_matrix()

    # Scan the whole matrix before checking Fn.
    # This means Fn + key doesn't depend on
    # physical scan order.
    fn_pressed = button_is_pressed(
        current_states,
        fn_button
    )

    for row_index in range(
        len(ROW_PINS)
    ):

        for column_index in range(
            len(COLUMN_PINS)
        ):

            pressed = current_states[
                row_index
            ][
                column_index
            ]

            was_pressed = last_states[
                row_index
            ][
                column_index
            ]

            # Newly pressed key
            if (
                pressed
                and not was_pressed
            ):

                button_number = BUTTON_MAP[
                    row_index
                ][
                    column_index
                ]

                # Fn is a layer modifier,
                # not an ordinary macro button.
                if button_number == fn_button:
                    continue

                if fn_pressed:
                    layer = "fn"
                else:
                    layer = "normal"

                run_button(
                    button_number,
                    layer
                )

    last_states = current_states

    time.sleep(0.005)