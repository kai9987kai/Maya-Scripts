import maya.cmds as cmds

# Define the golden ratio
GOLDEN_RATIO = 1.618

# Function to apply golden ratio scaling to selected objects
def apply_golden_ratio():
    # Get all selected objects in the scene
    selected_objects = cmds.ls(selection=True)
    
    if not selected_objects:
        cmds.warning("No objects selected. Please select objects to scale.")
        return
    
    for obj in selected_objects:
        # Get the current scale values
        current_scale_x = cmds.getAttr(f"{obj}.scaleX")
        current_scale_y = cmds.getAttr(f"{obj}.scaleY")
        current_scale_z = cmds.getAttr(f"{obj}.scaleZ")
        
        # Apply the golden ratio to each axis
        new_scale_x = current_scale_x * GOLDEN_RATIO
        new_scale_y = current_scale_y * GOLDEN_RATIO
        new_scale_z = current_scale_z * GOLDEN_RATIO
        
        # Set the new scale values
        cmds.setAttr(f"{obj}.scaleX", new_scale_x)
        cmds.setAttr(f"{obj}.scaleY", new_scale_y)
        cmds.setAttr(f"{obj}.scaleZ", new_scale_z)
        
    print("Golden ratio scaling applied to selected objects.")

# Execute the function
apply_golden_ratio()
