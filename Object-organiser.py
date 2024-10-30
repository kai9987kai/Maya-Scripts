import maya.cmds as cmds

def organize_objects_in_line():
    # Get selected objects
    selected_objects = cmds.ls(selection=True)
    
    # Check if any objects are selected
    if not selected_objects:
        cmds.warning("Please select objects to organize.")
        return

    # Initialize list to store object data (name, width, parent)
    object_data = []

    # Loop through objects and gather their width info
    for obj in selected_objects:
        # Unparent object if it has a parent
        parent = cmds.listRelatives(obj, parent=True)
        if parent:
            cmds.parent(obj, world=True)
        
        # Freeze transformations
        cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True)
        
        # Get bounding box size to calculate width
        bbox = cmds.exactWorldBoundingBox(obj)
        width = bbox[3] - bbox[0]  # Calculate width along X-axis
        object_data.append((obj, width, parent))
    
    # Sort objects by width in ascending order
    object_data.sort(key=lambda x: x[1])
    
    # Set starting X position
    x_position = 0.0
    spacing = 0.5  # Small space between objects, adjust as needed
    
    # Arrange objects in a line along X-axis with Y and Z reset to 0
    for obj, width, parent in object_data:
        cmds.setAttr(f"{obj}.translateX", x_position)
        cmds.setAttr(f"{obj}.translateY", 0)
        cmds.setAttr(f"{obj}.translateZ", 0)
        
        # Update x_position based on object width plus spacing
        x_position += width + spacing

        # Reparent the object if it had a parent originally
        if parent:
            cmds.parent(obj, parent[0])

    # Optional confirmation dialog to indicate completion
    cmds.confirmDialog(title="Completed", message="Objects organized in a line along the X-axis.", button=["OK"])

# Execute the function
organize_objects_in_line()
