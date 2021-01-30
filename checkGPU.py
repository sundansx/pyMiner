import wmi
import re
import psutil
import time
import traceback
import threading
import win32com.client
from os import path

class gameCheck:
    def __init__(self, threshold, times = 3, gameListFile = "gamelist.txt", useCOM = True):

        self.w = wmi.WMI(find_classes=False)
        self.isGaming = False
        self.activeTasks = {}
        self.loop = 0
        self.seqCount = 0
        self.percThreshold = threshold
        self.times = times #number of times - 1
        #self.delaySec = delaySec
        self.useCOM = useCOM
        self.debugMsg = ""
        strComputer = "."
        objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        self.objSWbemServices = objWMIService.ConnectServer(strComputer,"root\cimv2")
        self.gameListFile = gameListFile
        self.gameList = []
        self.activeGamePID = None
        self.readGameFile()
        self.isListDirty = False

    def readGameFile(self):
        if (path.exists(self.gameListFile)):
            fh = open(self.gameListFile,"r")
            self.gameList = fh.readlines()
            for c,item in enumerate(self.gameList):
                self.gameList[c] = item.rstrip() 
            fh.close()
            self.isListDirty = False
        

    def isOnList(self, newItem):
        if (self.isListDirty == True):
            self.readGameFile()
        for item in self.gameList:
            if (newItem == item):
                return True
        return False
        
    def mIsGaming(self):
        pid = 0
        pName = ""
        usage = ""
        self.debugMsg = ""
        #self.loop = 0
        gpu = None
        try:
            if (self.useCOM == True):
                gpu = self.objSWbemServices.ExecQuery("SELECT * FROM Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine")
            else:
                gpu = self.w.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
            #search for cached game
            for task in gpu:
                m = re.search("^pid_([0-9]+)_luid.+",task.name)
                pid = m.group(1)
                if (psutil.pid_exists(int(pid))):
                    pName = psutil.Process(int(pid)).name()
                else:
                    continue
                if (self.isOnList(pName) == True):
                    self.debugMsg = self.debugMsg + f"found cached 3d app: ({pName}:{pid})"
                    self.isGaming = True
                    self.activeGamePID = pid
                    return True
            #enumerate gpu loads
            for task in gpu:
                if (task.name.find('engtype_Graphics') > -1 or task.name.find('engtype_3D') > -1):
                    m = re.search("^pid_([0-9]+)_luid.+",task.name)
                    pid = m.group(1)
                    if (psutil.pid_exists(int(pid))):
                        pName = psutil.Process(int(pid)).name()
                    else:
                        pName = "Expired Task"
                    usage = task.UtilizationPercentage
                    if (int(usage) > self.percThreshold):
                        if (pid in self.activeTasks.keys()):
                            self.activeTasks[pid] = self.activeTasks[pid] + 1
                        else:
                            self.activeTasks[pid] = 1
                        self.debugMsg = self.debugMsg + f"adding {pid}-\t{pName}: {usage}"
            #check keys to see if a task has exceeded for self.time passes
            if (self.loop == self.times):
                for x in self.activeTasks:
                    if (self.activeTasks[x] > self.times):
                        self.debugMsg = self.debugMsg + f"found active 3d app: ({x})\n"
                        fh = open(self.gameListFile,"a")
                        gameList = fh.write(psutil.Process(int(x)).name() + '\n') 
                        fh.close()
                        self.isGaming = True
                        self.isListDirty = True
                        self.activeTasks.clear()
                        self.activeGamePID = x
                        return True
                self.activeTasks.clear()
                self.loop = 0
            else:
                self.loop = self.loop + 1
                return True
            return True
        except Exception as err:    
            self.debugMsg = self.debugMsg + f"Caught an exception:\n {err}:\n"
            self.debugMsg = self.debugMsg + traceback.format_exc()
            return False

    def mNotGaming(self):
        self.debugMsg = ""
        try:
            if (psutil.pid_exists(int(self.activeGamePID)) == False):
                self.debugMsg = self.debugMsg + f"Game has exited\n"
                #self.activeTasks.clear()
                self.isGaming = False

            # for x in self.activeTasks:
                # if (self.activeTasks[x] > self.times):
                    # if (psutil.pid_exists(int(x)) == False):
                        # self.debugMsg = self.debugMsg + f"Game has exited\n"
                        # self.activeTasks.clear()
                        # self.isGaming = False
                        # break
            return True
        except Exception as err:  
            self.debugMsg = self.debugMsg + f"Caught an exception:\n {err}:\n {traceback.format_exc()}"
            return False
        
if __name__ == "__main__":
    g = gameCheck(15)
    while True:
        print(f"Isgaming: {g.isGaming}")
        if (g.isGaming == False):
            start = time.time()
            g.mIsGaming()
            print(g.debugMsg, end='')
            end = time.time()
            print(f"loop time: {end - start}")
        else:
            g.mNotGaming()
            print(g.debugMsg, end='')
        time.sleep(3)
    