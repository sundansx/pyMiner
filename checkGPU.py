import wmi
import re
import psutil
import time
import traceback
import threading

class gameCheck:
    def __init__(self, threshold):

        self.w = wmi.WMI(find_classes=False)
        self.isGaming = False
        self.activeTasks = {}
        self.loop = 0
        self.seqCount = 0
        self.percThreshoold = threshold
        self.times = 2 #number of times - 1

    def mIsGaming(self):
        pid = 0
        pName = ""
        usage = ""
        loop = 0
        try:
            gpu = self.w.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
            #enumerate gpu loads
            for task in gpu:
                if (task.name.find('engtype_Graphics') > -1 or task.name.find('engtype_3D') > -1):
                    m = re.search("^pid_([0-9]+)_luid.+",task.name)
                    pid = m.group(1)
                    pName = psutil.Process(int(pid)).name()
                    usage = task.UtilizationPercentage
                    if (int(usage) > self.percThreshoold):
                        if (pid in self.activeTasks.keys()):
                            self.activeTasks[pid] = self.activeTasks[pid] + 1
                        else:
                            self.activeTasks[pid] = 1
                        print(threading.get_ident())
                        print(f"adding {pid}-\t{pName}: {usage}")
                        #print(task.name)
            #check keys to see if a task has exceeded for 4 passes
            if (self.loop == self.times):
                for x in self.activeTasks:
                    if (self.activeTasks[x] > self.times):
                        print(f"found active 3d app: ({x})")
                        #self.activeTasks.clear
                        self.isGaming = True
                        return
                self.activeTasks.clear()
                self.loop = 0
            else:
                self.loop = self.loop + 1
        except Exception as err:    
            #self.activeTasks.clear
            print(f"Caught an exception:\n {err}")
            traceback.print_exc()

    def mNotGaming(self):
        try:
            for x in self.activeTasks:
                if (self.activeTasks[x] > self.times):
                    if (psutil.pid_exists(int(x)) == False):
                        #print(f"Game has exited")
                        self.activeTasks.clear()
                        self.isGaming = False
                        break
        except Exception as err:  
            print(f"Caught an exception:\n {err}")
            traceback.print_exc()
        
if __name__ == "__main__":
    g = gameCheck(15)
    while True:
        print(f"Isgaming: {g.isGaming}")
        if (g.isGaming == False):
            start = time.time()
            g.mIsGaming()
            end = time.time()
            print(f"loop time: {end - start}")
        else:
            g.mNotGaming()
        time.sleep(5)
    