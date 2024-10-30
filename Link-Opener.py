import webbrowser
from maya import cmds

def open_web_page(url="https://www.example.com"):
    """
    Opens the specified URL in the system's default web browser.
    
    Args:
        url (str): The URL to open. Defaults to "https://www.example.com".
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    webbrowser.open(url)

def create_browser_ui():
    """
    Creates a simple Maya window with an address bar and control buttons to open URLs externally.
    """
    window_name = "ExternalBrowserWindow"
    
    # If the window already exists, delete it
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)
    
    # Create a new window
    window = cmds.window(window_name, title="External Browser", widthHeight=(400, 150))
    cmds.columnLayout(adjustableColumn=True, columnAlign="center", rowSpacing=10)
    
    # Address field
    address_field = cmds.textField(width=300, placeholderText="Enter URL here...")
    
    # Button Row
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(100, 100, 100))
    
    # Open button
    cmds.button(label="Open", width=100, command=lambda x: open_web_page(cmds.textField(address_field, query=True, text=True)))
    
    # Refresh button (reopens the same URL)
    cmds.button(label="Refresh", width=100, command=lambda x: open_web_page(cmds.textField(address_field, query=True, text=True)))
    
    # Close button
    cmds.button(label="Close", width=100, command=lambda x: cmds.deleteUI(window_name))
    
    cmds.setParent("..")  # Exit rowLayout
    
    cmds.showWindow(window)

# Execute the UI creation
create_browser_ui()
