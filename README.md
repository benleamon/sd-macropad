# sd-macropad
Code, documentation, and 3D files for a hand-wired, 4x5 macropad. 

## Hardware 

### Wiring: 
Matrix GPIO Assignments: 
| Matrix line | RP2040 GPIO |
|---|---:|
| R1 | GP2 |
| R2 | GP3 |
| R3 | GP4 |
| R4 | GP5 |
| R5 | GP6 |
| C1 | GP7 |
| C2 | GP8 |
| C3 | GP9 |
| C4 | GP14 |

MicroSD Modlule: 
| SD module | RP2040 |
|---|---:|
| VCC | 5V |
| GND | GND |
| SCK | GP10 |
| MOSI | GP11 |
| MISO | GP12 |
| CS | GP13 |

Use FAT32 for the MicroSD card. 

### Storage Layout: 

#### RP2040 internal storage
CircuitPython exposes the RP2040's internal flash as:
CIRCUITPY

The important files are:
```
CIRCUITPY/
├── code.py
└── lib/
    └── adafruit_hid/
        ├── keyboard.mpy
        ├── keyboard_layout_us.mpy
        ├── keycode.mpy
        ├── keyboard_layout_jp.py
        └── ...
```

`keyboard_layout_jp.py` is required only for JIS profiles.

#### microSD card
The physical SD card contains the user configuration:
```
SD CARD/
├── config.json
└── profiles/
    ├── home.json
    ├── work.json
    └── ...
```

Inside CircuitPython, the physical card is mounted at: `/sd`

Important
A folder manually created at: `CIRCUITPY/sd/` is not the physical SD card.
The firmware mounts the physical SD read-only from CircuitPython's side, while the connected computer can edit the card over USB.

## Set Up 

### Setting up the RP2040

The macros and configuration live on the SD card, so replacing the RP2040 does **not** require recreating all profiles.

A new RP2040-Zero-compatible board needs:

- CircuitPython;
- `code.py`;
- the Adafruit HID library;
- the JIS layout module if required;
- the existing SD card.

#### 1. Install CircuitPython

Use CircuitPython 10.x for the RP2040-Zero-compatible board.

With the RP2040 disconnected:

1. Hold the BOOT button.
2. Connect USB.
3. Release BOOT.
4. A drive called `RPI-RP2` should appear.
5. Copy the CircuitPython `.uf2` file onto `RPI-RP2`.
6. Wait for the board to reboot.
7. `CIRCUITPY` should appear.

---

#### 2. Install the Adafruit HID library

Download/use a CircuitPython library bundle matching the installed major version.

For CircuitPython 10.x this will look similar to:

```text
adafruit-circuitpython-bundle-10.x-mpy-YYYYMMDD
```

Open its:

```text
lib/
```

folder and copy:

```text
adafruit_hid/
```

to:

```text
CIRCUITPY/lib/
```

Do not copy the entire library bundle to the microcontroller.

---

#### 3. Install JIS support

If JIS profiles will be used, copy:

```text
keyboard_layout_jp.py
```

to:

```text
CIRCUITPY/lib/adafruit_hid/
```

The resulting structure should resemble:

```text
CIRCUITPY/
├── code.py
└── lib/
    └── adafruit_hid/
        ├── keyboard.mpy
        ├── keyboard_layout_us.mpy
        ├── keycode.mpy
        ├── keyboard_layout_jp.py
        └── ...
```

---

#### 4. Install the firmware

Copy the project's current:

```text
code.py
```

to the root of:

```text
CIRCUITPY
```

CircuitPython automatically restarts when `code.py` is saved.

---

### Fn Key
Fn key can be changed in `config.json`. 

### Adding new profiles: 
Make sure that in addition to the profile.json file, you update the profile order in config.json, as well as possibly the default profile. 

Minimal profile example: 
```
{
  "schema_version": 1,

  "profile": {
    "name": "QGIS",
    "layout": "us"
  },

  "normal": {},

  "fn": {}
}
```

### Japanese Support
Go to https://github.com/koyaaaaaan/adafruit_hidJP/tree/main/circuitpython7.x_after/adafruit_hid. 
Add keyboard_laoyout_jp.py to the lib/adafruit_hit folder in the CIRCUITPY directory. 

### Updating a profile 
- Edit the macros (either by removing the SD card or using it on your computer). 
- Use fn 5 to reload the macros. 

## Macro language

The macro format is inspired by DuckyScript but implements only the commands supported by this firmware.

Each macro is a list of instructions executed in order.

---

### `STRING`

Types text.

```text
STRING Hello world
```

Example:

```json
"1": [
  "STRING Hello world"
]
```

---

### `STRINGLN`

Types text and presses Enter afterward.

```text
STRINGLN git status
```

Equivalent conceptually to:

```text
STRING git status
ENTER
```

---

### `DELAY`

Waits for a number of milliseconds.

```text
DELAY 500
```

Example:

```json
"2": [
  "WIN R",
  "DELAY 300",
  "STRING notepad",
  "ENTER"
]
```

---

### Keys and hotkeys

Any instruction that is not another macro command is interpreted as a keyboard key or key combination.

Examples:

```text
ENTER
TAB
ESC
CTRL C
CTRL V
CTRL SHIFT S
ALT TAB
WIN R
```

Key names are based on `adafruit_hid.Keycode`.

Useful aliases include:

| Macro name | Keycode meaning |
|---|---|
| `CTRL` | Control |
| `CMD` | GUI |
| `COMMAND` | GUI |
| `WIN` | GUI |
| `WINDOWS` | GUI |
| `ESC` | Escape |
| `RETURN` | Enter |
| `DEL` | Delete |
| `UP` | Up Arrow |
| `DOWN` | Down Arrow |
| `LEFT` | Left Arrow |
| `RIGHT` | Right Arrow |
| `PAGEUP` | Page Up |
| `PAGEDOWN` | Page Down |
| `CAPSLOCK` | Caps Lock |
| `PRINTSCREEN` | Print Screen |

Digits `0`–`9` can also be used as key names.

---

### `REM`

Adds a comment inside a macro.

```text
REM Open the save dialog
```

The comment does nothing when the macro executes.

---

### `DEFAULT_DELAY`

Adds a delay after subsequent macro instructions.

```text
DEFAULT_DELAY 100
```

The alternative spelling is also accepted:

```text
DEFAULTDELAY 100
```

Example:

```json
"3": [
  "DEFAULT_DELAY 100",
  "CTRL L",
  "STRING example.com",
  "ENTER"
]
```

---

### `REPEAT`

Repeats the previous non-comment instruction.

```text
RIGHT
REPEAT 3
```

This sends Right Arrow four times total: the original press plus three repeats.

---

## System commands

Commands specific to the macropad use the `SYSTEM` namespace.

### Next profile

```text
SYSTEM PROFILE_NEXT
```

Loads the next profile from `profile_order`.

The list wraps around.

### Previous profile

```text
SYSTEM PROFILE_PREV
```

Loads the previous profile.

### Specific profile

```text
SYSTEM PROFILE work
```

Loads:

```text
/sd/profiles/work.json
```

### Reload configuration

```text
SYSTEM RELOAD
```

Re-reads the global config and active profile from the SD card.

This is intended for applying changes made over USB.

A useful Fn setup is:

```json
"fn": {
  "18": [
    "SYSTEM PROFILE_PREV"
  ],

  "19": [
    "SYSTEM PROFILE_NEXT"
  ],

  "20": [
    "SYSTEM RELOAD"
  ]
}
```

The reload process is designed to validate the new data before replacing the currently working configuration. If the reload fails, the previous configuration remains active.

---

## Printing the macro layout

The firmware can type an ASCII summary of the currently active profile.

```text
SYSTEM PRINT_LAYOUT
```

This prints both the normal and Fn layers.

To print only one layer:

```text
SYSTEM PRINT_LAYOUT normal
```

or:

```text
SYSTEM PRINT_LAYOUT fn
```

The output contains the actual macro instructions, so there is no separate label system to maintain.

For example:

```text
Profile: Home
Layout: US
Layer: Normal

+--------------------+--------------------+--------------------+--------------------+
|CTRL C              |CTRL V              |STRING git status   |CTRL SHIFT S        |
|                    |                    |ENTER               |                    |
+--------------------+--------------------+--------------------+--------------------+
...
```

Long commands are truncated for display only. The actual macro is unchanged.

For best results, print the layout into an application using a monospaced font.

Because the layout is produced as normal keyboard input, make sure the intended text field has focus before triggering it.
