# A USB-to-UART passthrough program for Circuitpython that allows flashing
# of ESP co-processor modules
#
# This is designed for the ILabs Challenger RP2040 Wifi/BLE boards
# Which use an ESP32C3 or other ESP32 chip as a wifi/BLE coprocessor.
#
# This means you can re-flash the ESP32C3 without having to flash the RP2040
# with the Arduino passthrough program.
# https://ilabs.se/pass-through-sketch-for-wifi-enabled-challenger-boards/
#
# If not in FLASH_MODE (FLASH_MODE=False), the program echos characters from
# the usb connection to the ESP32 co-processor so you can type AT commands
# (e.g. AT+GMR) directly at the ESP32 to see that it's working as intended.
#
# In FLASH_MODE (FLASH_MODE=True), the ESP32 chip is put into download mode so you can
# flash it using esptool or the ESP Web Flasher.
# You need --before no_reset as part of the esptool command:
# esptool.py --port /dev/ttyACM1 --baud 115200 --before no_reset write_flash 0 factory_MINI-1.bin
#
# This is because the Circuitpython USB_CDC module does not support setting RTS/DTR
# status that esptool normally uses to put the chip into download program mode.
# https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
#
# This program also translates \r characters on USB input into \r\n sequences
# since the espressif AT command set (and probably others) expect \r\n
# to terminate commands, but the "screen" terminal program on MacOS and Linux
# outputs \r by default.  Rather than try and figure out how to fix screen
# it's easier to just do it here.  It's disabled with a boolean flag below.
# If FLASH_MODE is enabled end-of-line translation and local echo are disabled.
#
# The neopixel is used for status:
# white: no USB connected
# blue: USB connected, idle
# green: reading bytes from USB
# red: reading bytes from UART
#
# Your circuitpython board needs these libraries in /lib
# adafruit_bus_device
# adafruit_pixelbuf.mpy
# neopixel.mpy
# Download them from https://circuitpython.org/libraries
#
# Note that for this to work you MUST have this in boot.py on
# circuitpython, to enable the usb_cdc connection:
#
# ---the two lines below this, without the "#"
#import usb_cdc
#usb_cdc.enable(console=True, data=True)
# ---the two lines above this, without the "#"
# Note that if you change boot.py you must reset the board with the reset
# button or power cycle to take effect.
#
# This will make a *second* USB device different from the circuitpython REPL
# console.   ie - console is /dev/ttyACM0 and the passthrough port is /dev/ttyACM1
# (on Linux, names will be different on different systems).  You want to connect
# your terminal program to the passthrough port, e.g:
# 		screen /dev/ttyACM1
# on MacOS.
#
# Steven Cogswell January 2023 https://github.com/scogswell
#
# References:
# https://learn.adafruit.com/adafruit-feather-m4-express-atsamd51/circuitpython-uart-serial
# https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
# https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/AT_Command_Set/Basic_AT_Commands.html

"""CircuitPython Feather UART Passthrough with Flash Programming Capability"""
import board
import busio
import digitalio
import usb_cdc
import neopixel
import sys

# Flash Download mode.  Enable this if you're trying to re-program
# the onboard ESP32C3 with esptool or the web flasher
# https://nabucasa.github.io/esp-web-flasher/
FLASH_MODE = False

# If your terminal program (e.g. screen on MacOS) doesn't automatically
# add "\n" to "\r" then you can make this True and if you push enter
# it will send a "\r\n", which is important for things like the
# espressif AT command set which expects \r\n for the ends of lines
# and saves you trying to figure out how to reconfigure screen
# or your terminal program.
#
# If your terminal program sends "\r\n" for enter already, or you
# don't want this behaviour change ADD_SLASHN_TO_SLASHR to False
# This is automatically disabled if FLASH_MODE is set
ADD_SLASHN_TO_SLASHR = True

# Set this to True if you want to see what you're typing and the
# passthrough device does not echo it back.  Set it to false
# if you're seeing two of every character (your device is echoing already)
# This is automatically disabled if FLASH_MODE is set
LOCAL_ECHO = False

if FLASH_MODE:  # Don't translate returns or echo when programming
    ADD_SLASHN_TO_SLASHR = False
    LOCAL_ECHO = False

# For most CircuitPython boards, the little led (not the neopixel)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# The neopixel on the Feather board itself, damn that thing is bright
num_pixels = 1
pixels = neopixel.NeoPixel(board.NEOPIXEL, num_pixels, brightness=0.1, auto_write=True)

# This is the UART connection (to the device we're passing-through to)
# Note on the Feather M4 Express at 115200 bps this had to be 128 to work correctly, a 64 byte
# buffer would miss characters.  "Your mileage may vary"
#
# Note board.ESP_TX and board.ESP_RX are defined for the ILabs Challenger RP2040 wifi boards
# but are probably not what you want for other circumstances.
uart = busio.UART(board.ESP_TX, board.ESP_RX, baudrate=115200, receiver_buffer_size=2048, timeout=0.1)
# This is the USB connection (to the user's terminal program)
serial = usb_cdc.data

if board.board_id in ["challenger_rp2040_wifi" ,"challenger_rp2040_wifi_ble"]:
    print("\nDetected board",board.board_id)
    print("Performing ESP reset...",end='')
    wifi_reset = digitalio.DigitalInOut(board.WIFI_RESET)
    wifi_mode = digitalio.DigitalInOut(board.WIFI_MODE)
    wifi_reset.direction = digitalio.Direction.OUTPUT
    wifi_mode.direction = digitalio.Direction.OUTPUT
    wifi_reset.value = 0
    if FLASH_MODE:
        wifi_mode.value = 0  # 1 for passthrough, 0 for download mode
    else:
        wifi_mode.value = 1
    wifi_reset.value = 1
    print(" reset finished.")
else:
    print("\nWARNING: known board not detected. ESP reset not performed")

# Some information printed to the console (not passthrough) port
print(f"\nThis is the console output, you want to connect to the other port for Passthrough")
print(f"e.g. screen /dev/ttyACM1\n")
if FLASH_MODE:
    print("-> Flash programming mode enabled")
if ADD_SLASHN_TO_SLASHR:
    print("-> Automatically adding \\n to \\r end of line character")
else:
    print("-> Not changing end-of-line characters")
if LOCAL_ECHO:
    print("-> Echoing input locally")
else:
    print("-> Not echoing input locally")
try:
    # Show a white neopixel while waiting for USB connection
    while serial.connected == False:
        pixels[0]=(255,255,255)
except:
    print(f"Can't create the USB CDC device for passthrough")
    print(f"Make sure your boot.py has these two lines in it:\n")
    print(f"import usb_cdc")
    print(f"usb_cdc.enable(console=True, data=True)\n")
    print(f"You must also push the RESET button the board to reload boot.py if you make changes to it.\n\n")
    sys.exit()

print(f"Connected on passthrough port")
# show a blue neopixel when connected
pixels[0]=(0,0,255)
if not FLASH_MODE:
    serial.write(b"Passthrough Connected\r\n")

# Loop forever passing bytes between ports
while True:
    # If the USB connection is still active, show the blue neopixel, otherwise
    # show it as white to indicate a disconnect
    if serial.connected == True:
        pixels[0]=(0,0,255)
    else:
        pixels[0]=(255,255,255)

    # Check for incoming bytes from the USB port (user typing)
    if serial.in_waiting > 0:
        pixels[0]=(0,255,0)  # Neopixel green on user typing input received
        led.value = True     # Also light up the board led to show activity
        bbyte = serial.read(serial.in_waiting)
        # If we get a \r, also send a \n because things like the
        # espressif AT commands set want to see \r\n on the ends
        # of commands but things like "screen" on MacOS just sends
        # the \r.  This saves having to reprogram screen or your
        # terminal command.  Change behaviour by setting
        # ADD_SLASHN_TO_SLASHR True or False at the top of the program.
        if ADD_SLASHN_TO_SLASHR == True:
            for c in bbyte:
                if c.to_bytes(1,sys.byteorder) == b'\r':
                    uart.write(b'\r\n')
                else:
                    uart.write(c.to_bytes(1,sys.byteorder))
        else:
            if LOCAL_ECHO == True:
                serial.write(bbyte)  # send the byte back to the user if asked
            uart.write(bbyte)        # send the byte to the UART device
        led.value = False

    # Check for incoming bytes from the UART device (Modem, whatever)
    if uart.in_waiting > 0:
        led.value = True      # board led shows activity
        pixels[0]=(255,0,0)   # Neopixel red on UART being received
        data = uart.read(uart.in_waiting)  # read all bytes available
        if data is not None:
            led.value = True
            serial.write(data)
        led.value = False
