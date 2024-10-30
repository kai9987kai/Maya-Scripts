import maya.cmds as cmds
import platform
import os
import datetime

def get_system_info():
    info = {}
    info["Operating System"] = platform.system()
    info["OS Version"] = platform.version()
    info["Architecture"] = platform.machine()
    info["Processor"] = platform.processor()
    info["Node Name"] = platform.node()
    info["Boot Time"] = datetime.datetime.fromtimestamp(os.path.getctime("/")).strftime("%Y-%m-%d %H:%M:%S")
    return info

def get_maya_info():
    info = {}
    info["Maya Version"] = cmds.about(version=True)
    info["Maya API Version"] = cmds.about(api=True)
    info["Current Scene"] = cmds.file(query=True, sceneName=True) or "Untitled"
    info["Running Directory"] = os.getcwd()
    return info

def create_gui():
    if cmds.window("systemInfoWindow", exists=True):
        cmds.deleteUI("systemInfoWindow", window=True)
    
    window = cmds.window("systemInfoWindow", title="System and Maya Information", widthHeight=(400, 350))
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="System Information", align="center", height=20, backgroundColor=(0.4, 0.4, 0.4))
    for key, value in get_system_info().items():
        cmds.text(label=f"{key}: {value}", align="left")

    cmds.separator(height=10, style='in')
    
    cmds.text(label="Maya Configuration", align="center", height=20, backgroundColor=(0.4, 0.4, 0.4))
    for key, value in get_maya_info().items():
        cmds.text(label=f"{key}: {value}", align="left")

    cmds.separator(height=10, style='in')

    cmds.button(label="Refresh", command=lambda x: refresh_info())
    cmds.showWindow(window)

def refresh_info():
    system_info = get_system_info()
    maya_info = get_maya_info()

    index = 0
    for key, value in system_info.items():
        cmds.text(f"system_label_{index}", edit=True, label=f"{key}: {value}")
        index += 1

    for key, value in maya_info.items():
        cmds.text(f"maya_label_{index}", edit=True, label=f"{key}: {value}")
        index += 1

create_gui()
