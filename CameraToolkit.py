import maya.cmds as cmds

def camera_switcher_ui():
    if cmds.window("cameraSwitcherWindow", exists=True):
        cmds.deleteUI("cameraSwitcherWindow", window=True)

    # Create a new window for the camera switcher tool
    window = cmds.window("cameraSwitcherWindow", title="Camera Switcher Tool", widthHeight=(300, 200), sizeable=True)
    cmds.columnLayout(adjustableColumn=True)

    # Refresh button to reload the camera list
    cmds.button(label="Refresh Camera List", command=lambda x: populate_camera_list())
    
    # Camera list with a default item
    global camera_list_ui
    camera_list_ui = cmds.textScrollList(numberOfRows=10, allowMultiSelection=False, selectCommand=lambda: switch_to_selected_camera())
    
    # Populate the camera list initially
    populate_camera_list()
    
    cmds.showWindow(window)

def populate_camera_list():
    """Populates the textScrollList with the names of all cameras in the scene."""
    cameras = cmds.listCameras()
    
    # Clear any existing items in the list
    cmds.textScrollList(camera_list_ui, edit=True, removeAll=True)
    
    # Add each camera to the list
    for cam in cameras:
        cmds.textScrollList(camera_list_ui, edit=True, append=cam)

def switch_to_selected_camera():
    """Switches the viewport to the selected camera from the list."""
    selected_camera = cmds.textScrollList(camera_list_ui, query=True, selectItem=True)
    if selected_camera:
        cmds.lookThru(selected_camera[0])

# Run the camera switcher UI
camera_switcher_ui()
