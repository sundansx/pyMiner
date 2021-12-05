# pyMiner - python miner manager for Windows

threading/systray code based on.  (thanks):
https://github.com/mann1x/pimax_bs_manager
Thanks a lot to mannix for posting is work and all the previous contributors!

Usage:
- Just run the miner.exe executable or the Python script (tested on 3.7.3)
- run minerWatchdog.exe to run it under a watchdog...if miner crashes, minerWatchdog will restart it.
- Status console via system tray menu, log output and status display with autoscroll
- Status is available on the hover text on the system tray icon (just move the mouse over it and you'll get gaming  status).  icon is yellow when making money (mining) and greyed out when gaming (losing money)
- The status panel windows includes th following buttons:
  - Copy to clipboard: will copy the logs in the window to your clipboard
  - Miner Debug: miner forced on and debug output printed.  somewhat broken.
  - Exclude: Add current application to excludelist.txt
  - Miner Off: Turn off miner. broken
  - Miner On: Force Miner On
  - Close: hide the window, pause the dashboard updates


Command line switches:
- "--debug_logs", "Enable DEBUG level logs"
- "--debug", same as above
- "--version", show version  number in a toast notification

Config File (remove comments):
[Miner]
3D_THRESHOLD = 15  - Threshhold of GPU % usage that determines if a game is active.  coinmining uses cuda/compute and will not trigger this.

APP_PATH = W:\temp\ethMining\ethminer.exe - path to ethminer or nbminer (see 1.3.4 release notes)

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

QUERY_MINER_SEC = 10 - number of seconds between ethminer queries to help limit cpu usage.  granularity is 5 seconds.

Limitations:
- Tested only on Windows 10

Requirements:
- A miner program of your own.  Designed to be used with latest etherminer and nbminer on windows 10.
- Python dependencies: on top of the original dependencies there's infi.systray for the Windows System Tray.  exe file release has dependencies bundled

Single executable available with ini and ico file in a ZIP file:
- Built with "build.bat" file

Support:
- you can submit an issue on this github

Todo:
- Add thread to monitor the ethminer application for activity and presence.  requests module to ethminer web interface?

# Changelog:
- v1.3.6
    - Added QUERY_MINER_SEC to set the delay between ethminer queries.  CPU use to high at default because it does not keep the connection open.
    - Fixed nbminer using 3rd server every time.
- v1.3.5
    - Fixed bug with writing game list and using it shortly after.
    - Added "open game files" that will open your excludelist.txt and gamelist.txt in your system text editor (notepad on most) for inspection
- v1.3.4
    - Added an exclusion list.  This can be added to manually or it can be added to by pressing the exclude button on the interface while the detected app is active.
    - Added nbminer.  Just add nbminer exe in the APP_PATH and it will be detected.  (note:  nbminer will not run in watchdog mode, it is turned off)
    - Added detecting hashrate not zero for ethminer (nbminer has a different method) and will restart the miner if it detects a hashrate of 0.
    - Added minerWatchdog.exe.  Run this instead to restart the miner.exe if it crashes for some reason.
    - Made the status window smaller and resizeable (but not scalable).
- v1.3.3 
    - added code to filter for "dwm.exe"/desktop window manager.  In VR that can cause large 3d loads, but never goes away
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
