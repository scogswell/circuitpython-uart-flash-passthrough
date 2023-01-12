import usb_cdc
import supervisor #lol
usb_cdc.enable(console=True, data=True)
supervisor.runtime.autoreload = False 