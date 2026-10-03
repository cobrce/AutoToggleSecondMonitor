#pip3 install monitorcontrol
#pip3 install pywin32
from time import time,sleep

from monitorcontrol import get_monitors, InputSource, PowerMode
from win32gui import EnumWindows,GetWindowRect, IsWindowVisible,GetClassName
from win32process import GetWindowThreadProcessId, GetModuleFileNameEx
from win32api import OpenProcess,CloseHandle
from win32con import PROCESS_QUERY_INFORMATION


def dvi_monitor_set_power_mode(powermode:PowerMode) -> None:
    for monitor in get_monitors():
        with monitor:
            input_source_raw: int = monitor.get_input_source()
            if ("DVI" in InputSource(input_source_raw).name):
                monitor.set_power_mode(powermode)



def process_name(pid):
    try:
        hProcess = OpenProcess(PROCESS_QUERY_INFORMATION,False,pid)
        name = str(GetModuleFileNameEx(hProcess,0)).split("\\")
        CloseHandle(hProcess)
        return name
    except:
        return [""]

def is_explorer(pid):
        return "explorer.exe" in process_name(pid)

def in_screen(left,right,top,bottom):
    def between(val,min,max):
        return val >= min and val <=max
    
    for val in [left,right,top,bottom]:
        if between(val,-1609,-10):
            return True
    return False

def enumwindow_callback(hwnd,power_mode:list):
    left,top,right,bottom = GetWindowRect(hwnd)
    
    if in_screen(*GetWindowRect(hwnd)) and IsWindowVisible(hwnd):
        c = GetClassName(hwnd)
        tid,pid = GetWindowThreadProcessId(hwnd)
        name = process_name(pid)[-1]
        if not "explorer.exe" in name or c == "CabinetWClass":
            power_mode[0] = PowerMode.on
            power_mode[1] = name
    pass

def main():
    print("AutoToggleMonitor2 by COB")
    print("(it turns on/off DVI monitor if it contains no window)")
    prev_power_mode = 0
    monitor_power_mode = 0
    start_time = time()
    while True:
        power_mode = [PowerMode.standby,""]
        EnumWindows(enumwindow_callback,power_mode)
        found_process = power_mode[1]
        power_mode = power_mode[0]
        if (power_mode != prev_power_mode):
            print("power_mode : PowerMode." + ("on" if power_mode == PowerMode.on else "standby"))
            if (power_mode == PowerMode.standby):
                start_time = time()
            else:
                print(f"Detected a window from process {found_process}")
        if (power_mode == PowerMode.on or time() - (start_time) > 5):
            if  (monitor_power_mode != power_mode):
                while True:
                    try:
                        dvi_monitor_set_power_mode(power_mode)
                        break
                    except:
                        sleep(1)
                monitor_power_mode = power_mode
                print("Monitor turned " + ("ON" if power_mode == PowerMode.on else "OFF"))

        prev_power_mode = power_mode

if __name__ == "__main__":
    main()