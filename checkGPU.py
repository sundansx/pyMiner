import wmi
import re
import psutil
import time
import traceback
import threading
import win32com.client

class gameCheck:
    def __init__(self, threshold, useCOM = True):

        self.w = wmi.WMI(find_classes=False)
        self.isGaming = False
        self.activeTasks = {}
        self.loop = 0
        self.seqCount = 0
        self.percThreshoold = threshold
        self.times = 3 #number of times - 1
        self.useCOM = useCOM
        self.debugMsg = ""
        strComputer = "."
        objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        self.objSWbemServices = objWMIService.ConnectServer(strComputer,"root\cimv2")


    def mIsGaming(self):
        pid = 0
        pName = ""
        usage = ""
        self.debugMsg = ""
        loop = 0
        gpu = None
        try:
            if (self.useCOM == True):
                gpu = self.objSWbemServices.ExecQuery("SELECT * FROM Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine")
            else:
                gpu = self.w.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
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
                    if (int(usage) > self.percThreshoold):
                        if (pid in self.activeTasks.keys()):
                            self.activeTasks[pid] = self.activeTasks[pid] + 1
                        else:
                            self.activeTasks[pid] = 1
                        self.debugMsg = self.debugMsg + f"adding {pid}-\t{pName}: {usage}\n"
            #check keys to see if a task has exceeded for 4 passes
            if (self.loop == self.times):
                for x in self.activeTasks:
                    if (self.activeTasks[x] > self.times):
                        self.debugMsg = self.debugMsg + f"found active 3d app: ({x})\n"
                        self.isGaming = True
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
            for x in self.activeTasks:
                if (self.activeTasks[x] > self.times):
                    if (psutil.pid_exists(int(x)) == False):
                        self.debugMsg = self.debugMsg + f"Game has exited\n"
                        self.activeTasks.clear()
                        self.isGaming = False
                        break
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
    