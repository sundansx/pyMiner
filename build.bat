rem personal call to setup for Python 3.7 on a system with multiple python versions installed.  comment out.
rem call setpy 37
pyinstaller --onefile miner.py --hidden-import pkg_resources --hidden-import infi.systray --hidden-import bleak --icon=miner_on.ico --version-file miner_version_info.txt --noconsole
copy configuration.ini dist
copy Miner_off.ico dist
copy Miner_on.ico dist
REM personal copy, can remove for your build
rem copy dist\*.* W:\temp\ethMining