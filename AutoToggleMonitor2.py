#pip3 install monitorcontrol
#pip3 install pywin32
from time import time,sleep

from monitorcontrol import get_monitors, InputSource, PowerMode
from win32gui import EnumWindows,GetWindowRect, IsWindowVisible,GetClassName
from win32process import GetWindowThreadProcessId, GetModuleFileNameEx
from win32api import OpenProcess,CloseHandle,EnumDisplayMonitors
from win32con import PROCESS_QUERY_INFORMATION


def second_monitor_set_power_mode(powermode:PowerMode) -> None:
    monitors = get_monitors()
    if (len(monitors)<2):
        return
    monitor = monitors[1]
    with monitor:
        while True:
            monitor.set_power_mode(powermode)
            sleep(5)
            if monitor.get_power_mode() == powermode:
                break



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

def in_screen(left,top,right,bottom,rect,offset):

    def between(val,min,max):
        return val > min and val <max
    def in_rectangle(x,y,rect,offset):
        return between(x,rect[0]+offset, rect[2]+offset) and between(y,rect[1],rect[3])

    
    points = [(left,top),(right,top),(right, bottom),(left,bottom)]

    for point in points:
        if in_rectangle(*point,rect,offset):
            return True
    return False    

def enumwindow_callback(hwnd,power_mode:list):

    ignore = [ "TextInputHost.exe",
        "explorer.exe",
        "ApplicationFrameHost.exe"
    ]

    global rect
    window_rect = GetWindowRect(hwnd)

    if in_screen(*window_rect,rect,-10) or in_screen(*rect,window_rect,10) and IsWindowVisible(hwnd):
        c = GetClassName(hwnd)
        tid,pid = GetWindowThreadProcessId(hwnd)
        name = process_name(pid)[-1]
        if not name in ignore or c == "CabinetWClass":
            power_mode[0] = PowerMode.on
            power_mode[1] = name

def get_second_monitor():
    monitors = EnumDisplayMonitors(None,None)
    if (len(monitors) < 2):
        return 0,(0,0,0,0)
    return (monitors[1][0].handle,monitors[1][2])

def main():
    print("AutoToggleMonitor2 by COB")
    print("(it turns on/off DVI monitor if it contains no window)")

    global handle,rect
    handle,rect =  get_second_monitor()
    print(f"Second monitor handle {handle}, rectangle {rect}")

    prev_power_mode = 0
    monitor_power_mode = 0
    start_time = time()
    while True:
        enum_result = [PowerMode.standby,""]
        EnumWindows(enumwindow_callback,enum_result)
        power_mode, found_process = enum_result

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
                        second_monitor_set_power_mode(power_mode)
                        break
                    except:
                        sleep(1)
                monitor_power_mode = power_mode
                print("Monitor turned " + ("ON" if power_mode == PowerMode.on else "OFF"))

        prev_power_mode = power_mode

if __name__ == "__main__":
    main()