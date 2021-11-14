rem personal call to setup for Python 3.7 on a system with multiple python versions installed.  comment out.
call setpy 37
del /q dist
pyinstaller --onefile miner.py --hidden-import pkg_resources --hidden-import infi.systray --hidden-import bleak --icon=miner_on.ico --version-file miner_version_info.txt --noconsole

pyinstaller --onefile minerWatchdog.py --hidden-import pkg_resources --noconsole

copy configuration.example.ini dist
copy configuration.ini dist
copy Miner_off.ico dist
copy Miner_on.ico dist
REM personal copy, can remove for your build
copy dist\*.* W:\temp\ethMining
cd dist
for /f %%i in ('sigcheck -nobanner -n miner.exe') do set VER=%%i
echo building Version %VER% zip file
e:\Utils\7zip\7z.exe a pyMiner_v%VER%.zip configuration.example.ini miner.exe Miner_off.ico Miner_on.ico minerWatchdog.exe
cd ..