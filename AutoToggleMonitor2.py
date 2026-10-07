#pip3 install monitorcontrol
#pip3 install pywin32
from time import time

from monitorcontrol import PowerMode, VCPError, get_monitors
from win32api import CloseHandle, EnumDisplayMonitors, OpenProcess
from win32con import PROCESS_QUERY_INFORMATION
from win32gui import EnumWindows, GetClassName, GetWindowRect, IsWindowVisible
from win32process import GetModuleFileNameEx, GetWindowThreadProcessId
from pywintypes import error



cancelable_turn_off = False

monitor = None
def get_second_monitor():
    global monitor
    if monitor is None:
        monitors = get_monitors()
        if (len(monitors)<2):
            return
        monitor = monitors[1]
    return monitor

def second_monitor_set_power_mode(powermode:PowerMode) -> None:
    monitor = get_second_monitor()
    if monitor is None:
        return
    with monitor:
        monitor.set_power_mode(powermode)

def second_monitor_get_power_mode() -> PowerMode:
    monitor = get_second_monitor()
    if monitor is None:
        return PowerMode.standby
    with monitor:
        return monitor.get_power_mode()



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
    _, monitor_rect = get_second_monitor_handle_and_rect()
    try:
        window_rect = GetWindowRect(hwnd)
    except error:
        return

    if in_screen(*window_rect,monitor_rect,-10) or in_screen(*monitor_rect,window_rect,10) and IsWindowVisible(hwnd):
        c = GetClassName(hwnd)
        _,pid = GetWindowThreadProcessId(hwnd)
        name = process_name(pid)[-1]
        if not name in ignore or c == "CabinetWClass":
            power_mode[0] = PowerMode.on
            power_mode[1] = name

def get_second_monitor_handle_and_rect():
    monitors = EnumDisplayMonitors(None,None)
    if (len(monitors) < 2):
        return 0,(0,0,0,0)
    return (monitors[1][0].handle,monitors[1][2])

    
TURNED_ON = 1
WAITING_FOR_TURN_ON = 2
ON = 3
TURNED_OFF = 4
WAITING_FOR_TURN_OFF = 5
OFF = 6

def main():
    def log_mode(power_mode):
        print("power_mode : PowerMode." + ("on" if power_mode == PowerMode.on else "standby"))

    print("AutoToggleMonitor2 by COB")
    print("(it turns on/off 2nd monitor depending on the presence of a window or not)")

    handle,rect =  get_second_monitor_handle_and_rect()
    print(f"Second monitor handle {handle}, rectangle {rect}")

    prev_power_mode = 0

    if second_monitor_get_power_mode() == PowerMode.on:
        state = ON
    else:
        state = OFF
    
    toggled_time = 0
    while True:
        enum_result = [PowerMode.standby,""]
        EnumWindows(enumwindow_callback,enum_result)
        power_mode, found_process = enum_result

        if state == ON:
            if power_mode == PowerMode.standby:
                state = TURNED_OFF
                toggled_time = time()

        elif state == TURNED_OFF:
            if power_mode == PowerMode.on:
                state = ON
            elif time() - toggled_time > 5:
                state = WAITING_FOR_TURN_OFF
                toggled_time = time()
                try:
                    second_monitor_set_power_mode(PowerMode.standby)
                except VCPError:
                    toggled_time += 3

        elif state == WAITING_FOR_TURN_OFF:
            if cancelable_turn_off and power_mode == PowerMode.on:
                state = TURNED_ON
            elif time() - toggled_time > 5 :
                if second_monitor_get_power_mode() != PowerMode.standby:
                    state = TURNED_OFF
                else:
                    state = OFF

        elif state == OFF:
            if power_mode == PowerMode.on:
                state = TURNED_ON

        elif state == TURNED_ON:
            toggled_time = time()
            try:
                second_monitor_set_power_mode(PowerMode.on)
            except VCPError:
                toggled_time += 3
            state = WAITING_FOR_TURN_ON

        elif state == WAITING_FOR_TURN_ON:
            if time() - toggled_time > 5 and second_monitor_get_power_mode() != PowerMode.on:
                state = TURNED_ON
            else:
                state = ON

        if power_mode != prev_power_mode:
            if power_mode == PowerMode.on:
                print(f"Detected a window from process {found_process}")
            log_mode(power_mode)
        prev_power_mode = power_mode

if __name__ == "__main__":
    main()
