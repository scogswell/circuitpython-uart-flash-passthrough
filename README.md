 # circuitpython-uart-flash-passthrough
 A USB-to-UART passthrough program for Circuitpython that allows flashing
 of ESP co-processor modules 

 This is designed for the ILabs Challenger RP2040 Wifi/BLE boards 
 Which use an ESP32C3 or other ESP32 chip as a wifi/BLE coprocessor. 

 This means you can re-flash the ESP32C3 without having to flash the RP2040
 with the Arduino passthrough program.  
 https://ilabs.se/pass-through-sketch-for-wifi-enabled-challenger-boards/

 If not in `FLASH_MODE` (`FLASH_MODE=False`), the program echos characters from 
 the usb connection to the ESP32 co-processor so you can type AT commands
 (e.g. AT+GMR) directly at the ESP32 to see that it's working as intended.  

 In `FLASH_MODE` (`FLASH_MODE=True`), the ESP32 chip is put into download mode so you can 
 flash it using esptool or the ESP Web Flasher.
 You need --before no_reset as part of the esptool command: 

 `esptool.py --port /dev/ttyACM1 --baud 115200 --before no_reset write_flash 0 factory_MINI-1.bin`
 
 This is because the Circuitpython USB_CDC module does not support setting RTS/DTR
 status that esptool normally uses to put the chip into download program mode.  
 https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html 
  
 This program also translates `\r` characters on USB input into `\r\n` sequences 
 since the espressif AT command set (and probably others) expect `\r\n`
 to terminate commands, but the "screen" terminal program on MacOS and Linux
 outputs `\r` by default.  Rather than try and figure out how to fix screen 
 it's easier to just do it here.  It's disabled with a boolean flag below.  
 If FLASH_MODE is enabled end-of-line translation and local echo are disabled.  

 The neopixel is used for status: 
 * white: no USB connected 
 * blue: USB connected, idle
 * green: reading bytes from USB 
 * red: reading bytes from UART   

 Your circuitpython board needs these libraries in /lib
 ``` 
 adafruit_bus_device
 adafruit_pixelbuf.mpy
 neopixel.mpy    
 ```
 Download them from https://circuitpython.org/libraries

 Note that for this to work you MUST have this in `boot.py` on 
 circuitpython, to enable the usb_cdc connection:

 ```
import usb_cdc
usb_cdc.enable(console=True, data=True)
```
 Note that if you change `boot.py` you must reset the board with the reset
 button or power cycle to take effect.  

 This will make a *second* USB device different from the circuitpython REPL
 console.   ie - console is `/dev/ttyACM0` and the passthrough port is `/dev/ttyACM1`
 (on Linux, names will be different on different systems).  You want to connect
 your terminal program to the passthrough port, e.g:
 		`screen /dev/ttyACM1`   
 on MacOS.  

 Steven Cogswell January 2023 https://github.com/scogswell

 References: 
 https://learn.adafruit.com/adafruit-feather-m4-express-atsamd51/circuitpython-uart-serial
 https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
 https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/AT_Command_Set/Basic_AT_Commands.html