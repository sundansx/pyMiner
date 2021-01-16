# pimax_bs_manager - Pimax HTC Base Station manager for Windows

threading/systray code from:
https://github.com/mann1x/pimax_bs_manager
Thanks a lot to mannix for posting is work and all the previous contributors!

Usage:
- Just run the executable or the Python script (tested on 3.7.4) 
- Status console via system tray menu, log output and status display with autoscroll
- Status is available on the hover text on the system tray icon (just move the mouse over it and you'll get HS and BS status)
- The status panel windows includes th following buttons:
  - Copy to clipboard: will copy the logs in the window to your clipboard
  - Miner Debug: miner forced on and debug output printed.  somewhat broken.
  - BS Switch mode: nothing..don't push at this point
  - Miner Off: Turn off miner. broken
  - Miner On: Force Miner On
  - Close: hide the window, pause the dashboard updates


Command line switches:
- "--debug_logs", "Enable DEBUG level logs"
- "--version", show version  number in a toast notification

Config File (remove comments):
[Miner]
3D_THRESHOLD = 15  ;Threshhold of GPU % usage that determines if a game is active.  coinmining uses cuda/compute and will not trigger this.
APP_PATH = W:\temp\ethMining\ethminer.exe ; path to ethminer
WORKER_NAME = <Name> ;  this is the name of the miner computer.  only used if app cannot determine this from COMPUTERNAME env var
ADDRESS = <user Ethereum address>;  your mining address 0xnnnnnnnnnnnnnnnnnnnnnnn
COMPUTE = cuda ; cuda or opencl lib used for mining.  amd = opencl, nvidia = cuda or opencl
POOL_ADDR = eu1.ethermine.org:4444;  pool address and port

Limitations:
- Tested only on Windows 10

Requirements:
- A miner program of your own.  Designed to be used with latest etherminer on windows 10.
- Python dependencies: on top of the original dependencies there's infi.systray for the Windows System Tray

Single executable available with ini and ico file in a ZIP file:
- Built with "build.bat" file

Support:
- you can submit an issue on this github

Todo:
- Algorithm for detecting an active game needs to be opomized.  It enumerates the resource usage list via WMI right now and uses too much processor

# Changelog:
- v1.5.2
    - Fix: Removed verify write from BLE commands
    - New: additional debug messages
- v1.5.1
    - New: Dump USB HID in logs if run with debug_logs flag
    - Fix: small fixes for the dashboard
- v1.5.0
    - New: added "--version" switch to display version number in a toast notification
    - New: (almost) complete code refactoring
    - New: Classes for main and Base Stations to avoid use of global vars and de-duplication
    - New: Discovery runs in its own thread, retries 20 times until all BS are found
    - New: console log window is now renamed as status panel, includes now status information
    - New: improved console log window with colored levels
    - New: hints in logs for troubleshooting if too many connection errors are logged over a short period
    - New: Basestation mode "Auto" defaults to Ping, "Idle" execute last command and idles
    - New: The status panel windows includes buttons to send Wakeup, Standby, Change mode, Run Discovery, switch Headset to Debug mode
    - Fix: standby is sent when headset switches off and at exit program
    - Fix: improved error messages management
    - Fix: many more fixes thanks to refactoring
    - Note: added some code the manage the Valve BS v2, still not working
 - v1.4.0
    - Fix: bleak python library used properly
- v1.3.1
    - Fix: Console log window centered on screen 
    - New: Exceptions handling for main thread with Windows 10 toast notifications
- v1.3
    - Fix: Too many small fixes and enhancements to list 
    - New: Console log output with autoscroll and copy to clipboard
    - New: DEBUG log level can be enable via command line switch
    - New: Separate threads for BS loops
    - New: Proper logging output
    - New: Standby command issued to BS when HS is On>Off
    - New: BS Timeout configurable in .ini
    - New: Added version info to executable
- v1.2
    - Fix: Switch to using LightHouse DB json file from Pimax runtime folder 
    - New: version in system tray
    - New: BS status for Discovered, Wakeup, Pinging, Errors
- v1.1
    - Fix: HeadSet status not updated properly from On to Off
    - Executable: added icon
