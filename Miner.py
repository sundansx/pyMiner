#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import asyncio
import atexit
import binascii
import configparser
import datetime
import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime
from datetime import timedelta
import traceback
import subprocess as sp
import win32con
import win32gui
import win32process
import win32api

import pywinusb.hid as hid
import wx
import wx.lib
import wx.lib.newevent
import wx.lib.colourdb
import wx.dataview as dv
import checkGPU
#from bleak import BleakClient
from bleak import _logger as logger
#from bleak import discover
from infi.systray import SysTrayIcon
from win10toast import ToastNotifier


LogMsgEvent, EVT_LOG_MSG = wx.lib.newevent.NewEvent()


class MainObj:

    def __init__(self):
        """
        Init function will initialize the instance with default runtime values
        :rtype: object
        """
        self.version = "1.3.1"

        self.threeDThresh = None
        self.minerAppPath = None
        self.workerName = None
        self.coinAddr = None
        self.compute = None
        self.poolAddr1 = None
        self.poolAddr2 = None
        self.poolAddr3 = None
        self.gpuCheckPasses = None
        self.respTimeout = None
        self.workTimeout = None
        self.preMineTask = None
        self.postMineTask = None
        self.minerProc = 0

        self.sleep_time_sec = None
        self.debug_logs = False

        self.tray_icon = "Miner_on.ico"
        self.logformat = "%(asctime)s %(levelname)s (%(module)s): %(message)s"

        self.gpu_label = 'GPU'
        self.toomanynoted = False
        self.quit_main = False

        self.systray = None
        self.gputhr = None
        self.logthr = None
        self.toaster = None

        self.mode = "Auto"

        self.panelupdate = "Initializing"
        self.panelstatus = [(0, ("Dashboard", "Status", self.panelupdate)), (1, ("", "", ""))]
        self.paneldata = [[str(k)] + list(v) for k, v in self.panelstatus]

    def set_threads(self, _systray, _gputhr, _logthr):
        """
        Set infi.systray, Miner thread and basestations threads in main instance
        :type _logthr: object
        :param _gputhr:
        :type _systray: object
        """
        self.systray = _systray
        self.gputhr = _gputhr
        self.logthr = _logthr

    def settoaster(self, _toaster):
        """
        Set toaster object in main instance
        :type _toaster: object
        """
        self.toaster = _toaster

    def get_quit_main(self):
        """
        Return quit main value from main instance
        :return:
        """
        return self.quit_main

    def get_dashboard_except(self):
        self.panelstatus = [(0, ("Dashboard", "Status", self.panelupdate)), (1, ("", "", ""))]
        self.paneldata = [[str(k)] + list(v) for k, v in self.panelstatus]
        return self.paneldata

    def toast_err(self, _msg):
        """
        Function to display the error message as a Windows 10 toast notification
        :param _msg:
        """
        self.toaster.show_toast("Miner",
                           _msg,
                           icon_path=maininst.tray_icon,
                           duration=5,
                           threaded=True)
        while self.toaster.notification_active(): time.sleep(0.1)

    def load_configuration(self, _toaster):
        """
        Load configuration file
        :param _toaster:
        """
        try:
            config = configparser.ConfigParser()
            config.read('configuration.ini')
            logging.info("Miner path: " + config['Miner']['APP_PATH'])
            miner = config["Miner"]
            self.threeDThresh = miner.get('3D_THRESHOLD')
            self.minerAppPath = miner.get('APP_PATH')
            self.workerName = os.getenv('COMPUTERNAME')
            if (self.workerName == ""):
                self.workerName = miner.get('WORKER_NAME')
            self.coinAddr = miner.get('ADDRESS')
            self.poolAddr1 = miner.get('POOL1')
            self.poolAddr2 = miner.get('POOL2')
            self.poolAddr3 = miner.get('POOL3')
            computeStr = miner.get('COMPUTE', 'cuda')
            if (computeStr == 'cuda'):
                self.compute = '-U'
                logging.info(f"Using cuda compute library")
            else:
                self.compute = '-G'
                logging.info(f"Using openCL compute library")
            self.respTimeout = miner.get('ETHM_RESP_TIMEOUT', "30")
            self.workTimeout = miner.get('ETHM_WORK_TIMEOUT', "300")
            self.gpuCheckPasses = miner.get('GPU_CHECK_PASSES', '3')
            self.sleep_time_sec = miner.get('CHECK_SLEEP', '5')
            logging.info(f"gpu Check passes: {self.gpuCheckPasses}")
            logging.info(f"gpu Check sleep: {self.sleep_time_sec} sec")
            logging.info(f"Will run or quit this miner when 3D threshold is {self.threeDThresh}: {self.minerAppPath}")
            self.preMineTask = miner.get('PREMINE_TASK')
            self.postMineTask = miner.get('POSTMINE_TASK')
            logging.info(f"will run pre-mine task: \'{self.preMineTask}\'")
            logging.info(f"will run post-mine task: \'{self.postMineTask}\'")

        except Exception as err:
            if not self.quit_main:
                self.toast_err("Load configuration file exception: " + str(err))
                self.quit_main = True

    def setMinerState(self, cmd):
        try:
            if (cmd == 'Off'):
                logging.debug("stopping miner")
                self.minerProc.kill()
                if (self.postMineTask != None):
                    logging.info(f"starting post-mine task.")
                    #m = re.search("(^.*)\\\\.*\.exe",self.postMineTask)
                    #postMineStr = m.group(1)
                    postMineProc = sp.run(self.postMineTask, creationflags=sp.CREATE_NEW_CONSOLE | sp.SW_HIDE, stdin=sp.PIPE, stderr=sp.PIPE, stdout=sp.PIPE)
                    logging.info(f"post mine result: {postMineProc.stdout.decode().rstrip()}")
            elif (cmd == 'On'):
                logging.debug("starting miner")
                #m = re.search("(^.*)\\\\.*\.exe",self.minerAppPath)
                #minerWD = m.group(1)
                if (self.preMineTask != None):
                    logging.info(f"starting pre-mine task.")
                    #m = re.search("(^.*)\\\\.*\.exe",self.preMineTask)
                    #preMineStr = m.group(1)
                    preMineProc = sp.run(self.preMineTask, creationflags=sp.CREATE_NEW_CONSOLE | sp.SW_HIDE, stdin=sp.PIPE, stderr=sp.PIPE, stdout=sp.PIPE)                    
                    logging.info(f"pre mine result: {preMineProc.stdout.decode().rstrip()}")
                if (self.poolAddr1 != None):
                    poolStr1 = f" -P stratum1+tcp://{self.coinAddr}.{self.workerName}@{self.poolAddr1} "
                else:
                    poolStr1 = ""
                if (self.poolAddr2 != None):
                    poolStr2 = f" -P stratum1+tcp://{self.coinAddr}.{self.workerName}@{self.poolAddr2} "
                else:
                    poolStr2 = ""
                if (self.poolAddr3 != None):
                    poolStr3 = f" -P stratum1+tcp://{self.coinAddr}.{self.workerName}@{self.poolAddr3} "
                else:
                    poolStr3 = ""
                minerPathStr = f"{self.minerAppPath} {self.compute} --report-hashrate --response-timeout {self.respTimeout}" \
                               f" --work-timeout {self.workTimeout}{poolStr1}{poolStr2}{poolStr3}"
                logging.info(f"running {minerPathStr}")
                self.minerProc = sp.Popen(minerPathStr, creationflags=sp.CREATE_NEW_CONSOLE | sp.SW_HIDE)
                time.sleep(3)
                hwnd = self.get_hwnds_for_pid(self.minerProc.pid)
                win32gui.ShowWindow(hwnd[0], win32con.SW_MINIMIZE)
            else:
                raise Exception("Unknown Miner state")
        except Exception as err:
                logging.error(f"Error: Failed to turn {cmd} Miner\n" + str(err))
                logging.error(traceback.print_exc())

    
    def setMinerOn(self):
        """
        Start Ethminer
        """
        self.setMinerState("On")

    def setMinerOff(self):
        """
        Stop EthMiner
        """
        self.setMinerState("Off")
 
    def setmode(self):
        """
        Set mode for Ethminer to set icon state
        """
        if self.mode == "Auto":
            _mode = "Idle"
        else:
            _mode = "Auto"
        self.mode = _mode
        logging.info("Set BS mode to " + str(_mode))
        self.mode = _mode

    def get_hwnds_for_pid(self, pid):
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
            return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds

    def getFileProperties(self, fname):
    #Read all properties of the given file return them as a dictionary.
    
        propNames = ('Comments', 'InternalName', 'ProductName',
            'CompanyName', 'LegalCopyright', 'ProductVersion',
            'FileDescription', 'LegalTrademarks', 'PrivateBuild',
            'FileVersion', 'OriginalFilename', 'SpecialBuild')

        props = {'FixedFileInfo': None, 'StringFileInfo': None, 'FileVersion': None}

        try:
            # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
            fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
            props['FixedFileInfo'] = fixedInfo
            props['FileVersion'] = "%d.%d.%d.%d" % (fixedInfo['FileVersionMS'] / 65536,
                    fixedInfo['FileVersionMS'] % 65536, fixedInfo['FileVersionLS'] / 65536,
                    fixedInfo['FileVersionLS'] % 65536)

            # \VarFileInfo\Translation returns list of available (language, codepage)
            # pairs that can be used to retreive string info. We are using only the first pair.
            lang, codepage = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')[0]

            # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
            # two are language/codepage pair returned from above

            strInfo = {}
            for propName in propNames:
                strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage, propName)
                ## print str_info
                strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

            props['StringFileInfo'] = strInfo
            return props
        except:
            pass


class GPU(threading.Thread):

    def __init__(self, label, _maininst, autostart=False):
        """
        Init function will initialize the thread with default values and store reference to the main instance
        :param label:
        :param _maininst:
        :param autostart:
        """
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start_orig = self.start
        self.start = self.start_local
        self.lock = threading.Lock()
        self.lock.acquire()  # lock until variables are set
        self.maininst = _maininst
        self.label = label
        self.status_initial = "N/A"
        self.status = self.status_initial
        self.tlock = False
        self.islocked = False
        self.gameActive = False

        if autostart:
            self.start()  # automatically start thread on init
        self.setstatus("Off")

    def run(self):
        """
        Run function what will check GPU gaming state
        """
        try:
            self.lock.release()
            self.cg = checkGPU.gameCheck(int(maininst.threeDThresh), int(maininst.gpuCheckPasses))

            while True:
                time.sleep(int(maininst.sleep_time_sec))
                if maininst.get_quit_main():
                    logging.debug(self.label + " thread exiting due to quit main")
                    break
                if self.tlock:
                    logging.debug(self.label + " thread lock active")
                    self.islocked = True
                    continue
                # if maininst.disco:
                    # logging.debug(self.label + " detection paused, discovery running")
                    # self.islocked = True
                    # continue
                # if self.maininst.debug_bypass_usb:
                    # self.setstatus("DEBUG")
                    # self.islocked = False
                    # continue
                self.islocked = False
                start = time.time()
                if (self.cg.isGaming == False):
                    returnVal = self.cg.mIsGaming()
                    if (returnVal == True):
                        logging.debug(self.cg.debugMsg)
                    elif (returnVal):
                        raise Exception(self.cg.debugMsg)
                    else:
                        raise Exception(f"Unknown return val: {returnVal}")
                else:
                    returnVal = self.cg.mNotGaming()
                    if (returnVal == True):
                        logging.debug(self.cg.debugMsg)
                    elif (returnVal):
                        raise Exception(self.cg.debugMsg)
                    else:
                        raise Exception(f"Unknown return val: {returnVal}")
                if maininst.debug_logs:
                    logging.debug(f"Game Active?: {self.cg.isGaming}")
                self.gameActive = self.cg.isGaming
                if (self.gameActive == False):
                    self.setstatus("Off")
                else:
                    self.setstatus("On")
                end = time.time()
                logging.debug(f"GPU thread loop time: {end - start}")


        except Exception as err:
            logging.error("Error: %s in %s thread: %s" % (self.__class__.__name__, self.label, str(err)))
            logging.error(traceback.print_exc())

    def setlock(self, _lock):
        """
        Set thread lock
        :param _lock:
        """
        self.islocked = False
        self.tlock = _lock

    def gettray(self):
        """
        Return string to display in system tray hover text
        :return:
        """
        return f"{self.label} [{self.status}]"

    def getstatus(self):
        """
        Return string with GPU status
        :return:
        """
        return f"{self.status}"

    def setstatus(self, _status):
        """
        Set GPU status
        :param _status:
        """
        logging.debug(f"setstatus: {_status}")
        if _status == "On":
            self.gameActive = True
        elif _status == "Off":
            self.gameActive = False
        elif _status == "DEBUG":
            self.gameActive = True
        if self.status != _status:
            if _status == "On":
                logging.info(self.label + " is gaming")
                self.maininst.setMinerOff()
            elif _status == "Off":
                logging.info(self.label + " is idle")
                if self.status != self.status_initial:
                    self.maininst.setMinerOn()
            elif _status == "DEBUG":
                logging.info(self.label + " is forced On")
                self.maininst.setMinerOn()
        self.status = _status

    def isActive(self):
        """
        Return true if the GPU is gameActive or in debug mode
        :return:
        """
        return bool(self.gameActive)

    def destroy(self):
        """
        Override the destroy thread adding lock release
        """
        self.lock.release()

    def start_local(self):
        """
        Start the thread with original run and acquire the lock
        """
        self.start_orig()
        self.lock.acquire()


class WxLogHandler(logging.Handler):

    def __init__(self, get_log_dest_func):
        """
        Logging handler to redirect messages to the wxPython window
        :param get_log_dest_func:
        """
        logging.Handler.__init__(self)
        self._get_log_dest_func = get_log_dest_func
        self.level = logging.DEBUG

    def flush(self):
        pass

    def emit(self, record):
        """
        This function will forward the event message to the destination window
        :param record:
        """
        try:
            msg = self.format(record)
            event = LogMsgEvent(message=msg, levelname=record.levelname, levelno=record.levelno)

            log_dest = self._get_log_dest_func()

            def after_func(get_log_dest_func=self._get_log_dest_func, event=event):
                _log_dest = get_log_dest_func()
                if _log_dest:
                    wx.PostEvent(_log_dest, event)

            wx.CallAfter(after_func)

        except Exception as err:
            sys.stderr.write("Error: %s failed while emitting a log record (%s): %s\n" % (
                self.__class__.__name__, repr(record), str(err)))


class LevelFilter(object):
    def __init__(self, level):
        """
        Filter for log level
        :param level:
        """
        self.level = level

    def filter(self, record):
        """
        Filter will forward only records with a level greater or equal self.level
        :type record: object
        """
        return record.levelno >= self.level


class LogWnd(wx.Frame):

    def __init__(self):
        """
        wxPython logging window
        """
        #import wx.lib.inspection
        #wx.lib.inspection.InspectionTool().Show()

        try:
            frame_style = wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
            frame_style = frame_style & ~ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)

            wx.lib.colourdb.updateColourDB()

            self.wxorange = wx.Colour("ORANGE RED")
            self.wxdarkgreen = wx.Colour("DARK GREEN")

            wx.Frame.__init__(self, None,
                              title="Miner panel", style=frame_style)

            self.Bind(EVT_LOG_MSG, self.on_log_msg)

            self.Bind(wx.EVT_CLOSE, self.oncloseevt)

            self.SetIcon(wx.Icon("Miner_on.ico"))

            (self.display_width_, self.display_height_) = wx.GetDisplaySize()

            frame_width = self.display_width_ * 90 / 100
            frame_height = self.display_height_ * 85 / 100
            self.SetSize(wx.Size(frame_width, frame_height))

            panel_width = self.GetClientSize().GetWidth()-2
            panel_height = self.GetClientSize().GetHeight()-46

            status_width = 500
            text_width = panel_width - status_width
            text_height = panel_height
            if text_width < 1:
                text_width = 100

            value_width = panel_width - text_width
            unit_width = value_width/10
            c0_width = int(unit_width*2)
            c1_width = int(unit_width*2)
            if c0_width < 120:
                c0_width = 120
            if c1_width < 120:
                c1_width = 120
            c2_width = int(unit_width*6)
            delta = (c0_width+c1_width+c2_width)-value_width
            if delta > 10:
                c2_width = c2_width - delta
            if c2_width < 260:
                c2_width = 260

            status_width = c0_width + c1_width + c2_width

            self.dvc = dv.DataViewCtrl(self,
                                       style=wx.BORDER_THEME
                                       | dv.DV_ROW_LINES # nice alternating bg colors
                                       #| dv.DV_HORIZ_RULES
                                       | dv.DV_VERT_RULES
                                       | dv.DV_MULTIPLE
                                       | dv.DV_NO_HEADER
                                       , size=(status_width, text_height)
                                       )

            self.model = StatusModel(getpaneldata())

            self.dvc.AssociateModel(self.model)

            c0 = self.dvc.AppendTextColumn("Item " + str(c0_width) + " " + str(value_width),  1, width=c0_width, align=wx.ALIGN_RIGHT, mode=dv.DATAVIEW_CELL_INERT)
            c1 = self.dvc.AppendTextColumn("Characteristic " + str(c1_width),   2, width=c1_width, align=wx.ALIGN_RIGHT, mode=dv.DATAVIEW_CELL_INERT)
            c2 = self.dvc.AppendTextColumn("Value " + str(c2_width-4),   3, width=c2_width-4, align=wx.ALIGN_LEFT, mode=dv.DATAVIEW_CELL_INERT)

            for c in self.dvc.Columns:
                c.Sortable = False
                c.Reorderable = False

            log_font = wx.Font(9, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.FONTWEIGHT_NORMAL)

            panel = wx.Panel(self, wx.ID_ANY)

            style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH2

            self.text = wx.TextCtrl(panel, wx.ID_ANY, size=(text_width, text_height),
                                    style=style)
            self.text.SetFont(log_font)

            sizer = wx.BoxSizer(wx.VERTICAL)
            wbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            wbox.Add(self.text, 0, wx.ALL | wx.EXPAND | wx.LEFT, 0)
            wbox.Add(self.dvc, 0, wx.ALL | wx.EXPAND | wx.RIGHT, 0)

            self.closebtn = wx.Button(panel, wx.ID_ANY, 'Close')
            self.closebtn.Bind(wx.EVT_BUTTON, self.onclosebutton)
            self.Bind(wx.EVT_BUTTON, self.onclosebutton, self.closebtn)
            self.copybtn = wx.Button(panel, wx.ID_ANY, label="Copy to clipboard")
            self.copybtn.Bind(wx.EVT_BUTTON, self.oncopybutton)
            self.Bind(wx.EVT_BUTTON, self.oncopybutton, self.copybtn)
            self.debugbtn = wx.Button(panel, wx.ID_ANY, label="Miner Debug")
            self.debugbtn.Bind(wx.EVT_BUTTON, self.ondebugbutton)
            self.Bind(wx.EVT_BUTTON, self.ondebugbutton, self.debugbtn)
            self.bsmodebtn = wx.Button(panel, wx.ID_ANY, label="BS Switch mode")
            self.bsmodebtn.Bind(wx.EVT_BUTTON, self.onbsmodebutton)
            self.Bind(wx.EVT_BUTTON, self.onbsmodebutton, self.bsmodebtn)
            self.wakeupbtn = wx.Button(panel, wx.ID_ANY, label="Miner On")
            self.wakeupbtn.Bind(wx.EVT_BUTTON, self.onwakeupbutton)
            self.Bind(wx.EVT_BUTTON, self.onwakeupbutton, self.wakeupbtn)
            self.standbybtn = wx.Button(panel, wx.ID_ANY, label="Miner Off")
            self.standbybtn.Bind(wx.EVT_BUTTON, self.onstandbybutton)
            self.Bind(wx.EVT_BUTTON, self.onstandbybutton, self.standbybtn)

            hbox.Add(self.copybtn, 1, wx.ALL | wx.ALIGN_CENTER, 5)
            hbox.Add(self.debugbtn, 1, wx.ALL | wx.ALIGN_CENTER, 5)
            hbox.Add(self.bsmodebtn, 1, wx.ALL | wx.ALIGN_CENTER, 5)
            hbox.Add(self.standbybtn, 1, wx.ALL | wx.ALIGN_CENTER, 5)
            hbox.Add(self.wakeupbtn, 1, wx.ALL | wx.ALIGN_CENTER, 5)
            hbox.Add(self.closebtn, 1, wx.ALL | wx.ALIGN_CENTER, 5)
            sizer.Add(wbox, flag=wx.ALL | wx.EXPAND)
            sizer.Add(hbox, 1, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
            panel.SetSizer(sizer)
            panel.Layout()
            panel.Fit()

            self.CenterOnScreen()
            self.dataObj = None

            self.Raise()

        except Exception as err:
            toast_err("Status panel error: " + str(err))

    def oncloseevt(self, e):
        """
        The close button will hide the window without destroying it to keep the logging messages flowing in
        :param e:
        """
        e.Veto()
        self.Show(False)
        self.Hide()

    def onclosebutton(self, e):
        """
        The close button will hide the window without destroying it to keep the logging messages flowing in
        :param e:
        """
        self.Show(False)
        self.Hide()

    def oncopybutton(self, e):
        """
        The copy button will fill the clipboard with the logging messages in the window
        :param e:
        """
        self.dataObj = wx.TextDataObject()
        self.dataObj.SetText(self.text.GetValue())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(self.dataObj)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard", "Error")

    def ondebugbutton(self, e):
        pass

    def onwakeupbutton(self, e):
        maininst.setMinerOn()

    def onstandbybutton(self, e):
        maininst.setMinerOff()

    def onbsmodebutton(self, e):
        maininst.setmode()

    def on_log_msg(self, e):
        """
        This function is triggered by the bind for the EVT_LOG_MSG event.
        Autoscroll is enabled if vertical scrollbar is near the bottom
        :param e:
        """
        try:
            msg = re.sub("\r\n?", "\n", e.message)

            if e.levelno >= 40:
                self.text.SetDefaultStyle(wx.TextAttr(wx.RED))
            elif e.levelno >= 30:
                self.text.SetDefaultStyle(wx.TextAttr(self.wxorange))
            elif e.levelno >= 20:
                self.text.SetDefaultStyle(wx.TextAttr(wx.BLACK))
            elif e.levelno >= 10:
                self.text.SetDefaultStyle(wx.TextAttr(self.wxdarkgreen))

            # msg = msg + " sc=" + str(self.text.GetScrollPos(wx.VERTICAL))

            sbrng = self.text.GetScrollRange(wx.VERTICAL)
            sbpos = self.text.GetScrollPos(wx.VERTICAL)+self.text.GetVirtualSize().GetHeight()
            sboldpos = self.text.GetScrollPos(wx.VERTICAL)

            current_pos = self.text.GetInsertionPoint()
            end_pos = self.text.GetLastPosition()

            # autoscroll = (current_pos == end_pos)

            if sbrng-sbpos <= 10:
                # msg = msg + " YESASB"
                reposition = False
                autoscroll = True
            else:
                current_pos = self.text.GetScrollPos(wx.VERTICAL)
                # msg = msg + " NOASB"
                reposition = True
                autoscroll = False

            if autoscroll:
                # msg = msg + " YESA"
                self.text.AppendText("%s\n" % msg)
                if reposition:
                    self.text.SetScrollPos(wx.VERTICAL, self.text.GetScrollRange(wx.VERTICAL), True)
            else:
                # msg = msg + " NOA"
                self.text.Freeze()
                (selection_start, selection_end) = self.text.GetSelection()
                self.text.SetEditable(True)
                self.text.SetInsertionPoint(end_pos)
                self.text.WriteText("%s\n" % msg)
                self.text.SetEditable(False)
                self.text.SetInsertionPoint(current_pos)
                self.text.SetSelection(selection_start, selection_end)
                self.text.Thaw()
                if reposition:
                    self.text.SetScrollPos(wx.VERTICAL, sboldpos, True)
                else:
                    self.text.SetScrollPos(wx.VERTICAL, self.text.GetScrollRange(wx.VERTICAL), True)
                #self.text.Refresh()

        except Exception as err:
            sys.stderr.write(
                "Error: %s failed while responding to a log message: %s.\n" % (self.__class__.__name__, str(err)))

        if e is not None:
            e.Skip(True)


class StatusModel(dv.DataViewIndexListModel):
    def __init__(self, data):
        dv.DataViewIndexListModel.__init__(self, len(data))
        self.wxgray = wx.Colour(47, 79, 79)
        self.data = data

    def GetColumnType(self, col):
        return "string"

    # This method is called to provide the data object for a
    # particular row,col
    def GetValueByRow(self, row, col):
        return self.data[row][col]

    # Report how many columns this model provides data for.
    def GetColumnCount(self):
        return len(self.data[0])

    # Report the number of rows in the model
    def GetCount(self):
        return len(self.data)

    # Called to check if non-standard attributes should be used in the
    # cell at (row, col)
    def GetAttrByRow(self, row, col, attr):
        if col == 1:
            attr.SetColour(self.wxgray)
            attr.SetBold(True)
            attr.SetItalic(True)
            return True
        if col == 3:
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False

    def AddRow(self, value):
        # update data structure
        self.data.append(value)
        # notify views
        self.RowAppended()


class LogThread(threading.Thread):

    def __init__(self, autostart=True):
        """
        Run the log window in a thread.
        Access the frame with self.frame

        :type autostart: object
        """
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start_orig = self.start
        self.start = self.start_local
        self.frame = None  # to be defined in self.run
        self.framepnl = None
        self.status = ""
        self.lock = threading.Lock()
        self.lock.acquire()  # lock until variables are set

        if autostart:
            self.start()  # automatically start thread on init

    def run(self):
        """
        Initialize the frame with with the wxPython class and run the window MainLoop
        """
        import wx
        atexit.register(disable_asserts)

        app = wx.App(False)

        frame = LogWnd()

        # define frame and release lock
        self.frame = frame
        self.lock.release()

        app.MainLoop()

    def destroy(self):
        """
         Override the destroy adding frame destroy first
        """
        self.frame.Destroy()

    def start_local(self):
        """
        Start the thread with original run and acquire the lock
        """
        self.start_orig()
        self.lock.acquire()


def runlogthread():
    """
    Run the Logging window thread and makes the frame accessible
    :return:
    """
    lt = LogThread()  # run wx MainLoop as thread
    #frame = lt.frame  # access to wx Frame
    lt.frame.Show(False)
    return lt


def consolewin(systray):
    """
    Function for the system tray menu to show the Logging window
    :param systray:
    """
    try:
        maininst.logthr.frame.Show(True)
        maininst.logthr.frame.Raise()
    except Exception as err:
        maininst.logthr = runlogthread()
        maininst.logthr.frame.Show(True)
        maininst.logthr.frame.Raise()
        toast_err("ex=" + str(err))


def disable_asserts():
    """
    Disable wxPython error messages when destroying the windows
    """
    import wx
    wx.DisableAsserts()

def do_nothing(systray):
    """
    Function for the system tray menu to act as stub for nothing to do
    :param systray:
    """
    pass




def on_quit_callback(systray):
    """
    Function for the system tray menu to set the quit main loop and trigger the program shutdown
    :param systray:
    """
#    if maininst.bs1thr or maininst.bs2thr:
    maininst.setMinerOff()
    maininst.quit_main = True


def updatepaneldata():
    # self.status = {("ciao", "mondo"), ("ecco", "mano")}
    # self.data = [[str(k)] + list(v) for k, v in self.status]

    try:
        while True:
            if maininst.get_quit_main():
                break
            time.sleep(1)
            if logthr.frame.IsShown():

                idx = 0
                status = {}

                def addstatus( r1, r2 , r3, status, idx):
                    nstatus = {}
                    nstatus[idx] = r1, r2, r3
                    status.update(nstatus)
                    idx += 1
                    return idx

                idx = addstatus("Dashboard", "Status", maininst.panelupdate, status, idx)
                idx = addstatus("", "", "", status, idx)
                idx = addstatus("Miner", "", "", status, idx)
                idx = addstatus("", "Status", str(maininst.gputhr.getstatus()), status, idx)
                maininst.panelstatus = status
                try:
                    status = sorted(status.items())
                    maininst.paneldata = [[str(k)] + list(v) for k, v in status]
                    #time.sleep(0.2)
                    logthr.frame.model = StatusModel(maininst.paneldata)
                    logthr.frame.dvc.AssociateModel(logthr.frame.model)
                    #time.sleep(0.2)
                    maininst.panelupdate = "Updating"
                    logthr.frame.dvc.Refresh()
                    #logging.debug("Panel update=" + str(status))
                except Exception as err:
                    if not maininst.quit_main:
                        toast_err("Update panel inner thread exception: " + str(err))
                        logging.debug("Panel inner closed: " + str(err))
                        maininst.panelupdate = "Error"
                        logthr.frame.model = StatusModel(maininst.get_dashboard_except())
                        logthr.frame.dvc.AssociateModel(logthr.frame.model)
                        #logthr.frame.dvc.Refresh()
                    pass
    except Exception as err:
        if not maininst.quit_main:
            logging.debug("Panel inner exception: " + str(err))
            toast_err("Update panel thread exception: " + str(err))
            maininst.panelupdate = "Error"
            logthr.frame.model = StatusModel(maininst.get_dashboard_except())
            logthr.frame.dvc.AssociateModel(logthr.frame.model)
            #logthr.frame.dvc.Refresh()


def getpaneldata():
    return maininst.paneldata

def toast_err(_msg):
    """
    Function to display the error message as a Windows 10 toast notification
    :param _msg:
    """
    toaster.show_toast("Miner",
                       _msg,
                       icon_path=maininst.tray_icon,
                       duration=5,
                       threaded=True)
    while toaster.notification_active():
        time.sleep(0.1)


def main(_logger):
    """
    Main loop for the program
    :param _logger:
    """
    try:
        parser = argparse.ArgumentParser()
#        parser.add_argument("--debug_ignore_usb", help="Disable the USB search for Miner", action="store_true")
        parser.add_argument("--debug_logs", help="Enable DEBUG level logs", action="store_true")
        parser.add_argument("--version", help="Print version", action="store_true")

        args = parser.parse_args()

#        maininst.debug_bypass_usb = args.debug_ignore_usb
        maininst.debug_logs = args.debug_logs

        if args.version:
            toast_err("Version: " + str(maininst.version))
            sys.exit()

        if maininst.debug_logs:
            maininst.MIN_LEVEL = logging.DEBUG
            os.environ["BLEAK_LOGGING"] = "True"
        else:
            maininst.MIN_LEVEL = logging.INFO
            os.environ["BLEAK_LOGGING"] = "False"

        logging.basicConfig(format=maininst.logformat, level=maininst.MIN_LEVEL)
        log_formatter = logging.Formatter("%(asctime)s %(levelname)s (%(module)s): %(message)s", "%H:%M:%S")
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(log_formatter)
        h.setLevel(maininst.MIN_LEVEL)

        wx_handler = WxLogHandler(lambda: logthr.frame)
        wx_handler.setFormatter(log_formatter)
        wx_handler.setLevel(maininst.MIN_LEVEL)
        wx_handler.addFilter(LevelFilter(maininst.MIN_LEVEL))
        logging.getLogger().addHandler(wx_handler)

        _logger.addHandler(h)
        _logger = logging.getLogger(__name__)

        menu_options = (('Status panel', None, consolewin),
                        ('Version ' + maininst.version, None, do_nothing)
                        )
        with SysTrayIcon(maininst.tray_icon, "Initializing...", menu_options, on_quit=on_quit_callback) as systray:
            try:
                logging.info("Miner Version: " + maininst.version)
                maininst.settoaster(toaster)
                maininst.load_configuration(toaster)
                maininst.setMinerOn()
                if maininst.get_quit_main():
                    raise Exception("Exiting due to configuration file load error")
                logging.info("Configuration loaded")

                gputhr = GPU(maininst.gpu_label, maininst)
                maininst.set_threads(systray, gputhr, logthr)
                logging.debug("Threads initialized")

                tray_label = gputhr.gettray()
                systray.update(hover_text=tray_label)

                logging.info("Starting threads")
                gputhr.start()

                updatethr = threading.Thread(target=updatepaneldata, args=())
                updatethr.start()

                #maininst.disco = False

                logging.debug("Threads started")

                while True:
                    if maininst.quit_main:
                        logging.debug("Quit main_loop, waiting for threads exiting")
                        timeref = time.time()
                        while gputhr.is_alive() :
                            time.sleep(0.1)
                            if time.time() - timeref > 5:
                                break
                        logging.debug("Quit main_loop, systray status=" + str(maininst.quit_main))
                        break

                    tray_label = gputhr.gettray()
                    trayStr = ""
                    if (gputhr.gettray().find("[On]") == -1):
                        maininst.tray_icon = "Miner_on.ico"
                    else:
                        maininst.tray_icon = "Miner_off.ico"
                    systray.update(icon=maininst.tray_icon)
                    systray.update(hover_text=tray_label)
                    if not gputhr.is_alive():
                        raise Exception(gputhr.label + " thread has crashed!")

                    time.sleep(1)

            except Exception as err:
                if not maininst.quit_main:
                    toast_err("Main thread loop exception: " + str(err))
                    logging.error(traceback.print_exc())
                systray.shutdown()
                sys.exit()

    except Exception as err:
        if not maininst.quit_main:
            toast_err("Main thread exception: " + str(err))
            logging.error(traceback.print_exc())
        systray.shutdown()
        sys.exit()


if __name__ == "__main__":
    toaster = ToastNotifier()
    maininst = MainObj()
    logthr = runlogthread()
    main(logger)
