import maya.cmds as cmds

def createWhiteModeUI():
    if cmds.window("whiteModeWindow", exists=True):
        cmds.deleteUI("whiteModeWindow", window=True)

    # Create a new window for the white-themed UI
    window = cmds.window("whiteModeWindow", title="White Mode UI Example", widthHeight=(400, 300), sizeable=True)
    cmds.columnLayout(adjustableColumn=True)

    # White theme button with black text
    cmds.button(label="White Mode Button", bgc=(1, 1, 1), h=40, w=200)
    
    # White theme text field with black text
    cmds.textField(text="White Mode Text Field", bgc=(1, 1, 1))
    
    # White theme checkbox with black text
    cmds.checkBox(label="White Mode Checkbox", h=30)
    
    # White theme option menu
    cmds.optionMenu(label="Dropdown", bgc=(1, 1, 1))
    cmds.menuItem(label="Option 1")
    cmds.menuItem(label="Option 2")
    cmds.menuItem(label="Option 3")
    
    # Color slider with white background
    cmds.colorSliderGrp(label="Color Picker", rgb=(1, 1, 1), cal=(1, 'center'), h=40)

    cmds.setParent("..")
    cmds.showWindow(window)

createWhiteModeUI()
