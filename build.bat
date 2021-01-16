call setpy 37
pyinstaller --onefile miner.py --hidden-import pkg_resources --hidden-import infi.systray --hidden-import bleak --icon=miner_on.ico --version-file miner_version_info.txt --noconsole
copy configuration.ini dist
copy Miner_off.ico dist
copy Miner_on.ico dist
copy dist\*.* W:\temp\ethMining