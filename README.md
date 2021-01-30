# pyMiner - python miner manager for Windows

threading/systray code from:
https://github.com/mann1x/pimax_bs_manager
Thanks a lot to mannix for posting is work and all the previous contributors!

Usage:
- Just run the executable or the Python script (tested on 3.7.3) 
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
3D_THRESHOLD = 15  - Threshhold of GPU % usage that determines if a game is active.  coinmining uses cuda/compute and will not trigger this.

APP_PATH = W:\temp\ethMining\ethminer.exe - path to ethminer

WORKER_NAME = <Name> -  this is the name of the miner computer.  only used if app cannot determine this from COMPUTERNAME env var

ADDRESS = <user Ethereum address>  -  your mining address 0xnnnnnnnnnnnnnnnnnnnnnnn

COMPUTE = cuda - cuda or opencl lib used for mining.  amd = opencl, nvidia = cuda or opencl

POOL1 = us2.ethermine.org:4444 - This is the addresss of the main mining pool

POOL2 = us1.ethermine.org:4444  - first fallback pool number

POOL3 = eu1.ethermine.org:4444  - second fallback pool

PREMINE_TASK = <pre miner task with full path and arguments (no quotes)> 

POSTMINE_TASK = <post miner task with full path and arguments (no quotes)> 

ETHM_RESP_TIMEOUT = 25  - this is the ethminer "--response timeout" passed to ethminer

ETHM_WORK_TIMEOUT = 301  - this it the ethminer "--work timeout" passed to ethminer

GPU_CHECK_PASSES = 3  - this is now many times the app has to find a game/3d app past the 3d threshold to count as active

CHECK_SLEEP = 4  - how long the gpu check loop sleeps between checks.  shorten this to find the game faster, but takes more cpu

Limitations:
- Tested only on Windows 10
- will not monitor the ethminer task

Requirements:
- A miner program of your own.  Designed to be used with latest etherminer on windows 10.
- Python dependencies: on top of the original dependencies there's infi.systray for the Windows System Tray

Single executable available with ini and ico file in a ZIP file:
- Built with "build.bat" file

Support:
- you can submit an issue on this github

Todo:
- Add thread to monitor the ethminer application for activity and presence.  requests module to ethminer web interface?

# Changelog:
- v1.3.2 
    - added app name caching.  it will check a list called gamelist.txt in root folder for a game it had previously id'ed and immediately stop the Miner.py
    - added a thread to watch the miner pid and restart it if it dies unexpectedly
- v1.3.1 
    - fixed bug with pre/post miner launch tasks.
- v1.3.0
    - added ability to run a task before and after the miner starts.  can be used for stuff like setting gpu clocks
- v1.2.0
    - added ability to use multiple pools
    - added tweaks for timing check loop
    - added ablity to change some more ethmining settings (work and response timeouts)
    - added --report-hashrate to report hashrate to pool

- v1.1.0
    - moved to WMI access via Com object as default method.  20x faster (lower processor too)
    - fixed some fault bugs
    - scans faster for 3d app
    - version 1.1 release

- v1.0.0
    - first stab.  initial release for github
