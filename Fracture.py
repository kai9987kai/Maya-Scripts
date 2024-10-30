import maya.cmds as cmds
import random
import math

def simple_fracture(object_name):
    """
    Simple fracture of an object using a single cutting plane.

    Parameters:
    - object_name (str): The name of the object to fracture.

    Returns:
    - list: List containing the fractured piece.
    """
    print("Starting simple fracture process...")

    # Step 1: Validate the selected object
    if not cmds.objExists(object_name):
        cmds.confirmDialog(title='Error', message=f"Object '{object_name}' does not exist.", button=['OK'], defaultButton='OK')
        return

    if cmds.objectType(object_name) != 'transform':
        cmds.confirmDialog(title='Error', message=f"Object '{object_name}' is not a transform node.", button=['OK'], defaultButton='OK')
        return

    shapes = cmds.listRelatives(object_name, shapes=True, noIntermediate=True)
    if not shapes or cmds.objectType(shapes[0]) != 'mesh':
        cmds.confirmDialog(title='Error', message=f"Object '{object_name}' does not have a mesh shape.", button=['OK'], defaultButton='OK')
        return

    # Step 2: Duplicate the object to preserve the original
    fractured_obj = cmds.duplicate(object_name, name=f"{object_name}_fractured")[0]
    print(f"Duplicated object: {fractured_obj}")

    # Step 3: Delete history to ensure clean Boolean operations
    cmds.delete(fractured_obj, ch=True)
    print(f"Deleted history on: {fractured_obj}")

    # Step 4: Get the center of the object in global space
    try:
        center = cmds.objectCenter(fractured_obj, gl=True)
        print(f"Object center: {center}")
    except Exception as e:
        print(f"Failed to get object center: {e}")
        cmds.delete(fractured_obj)
        return

    # Step 5: Get bounding box of the object
    try:
        bbox = cmds.exactWorldBoundingBox(fractured_obj)
        min_x, min_y, min_z, max_x, max_y, max_z = bbox
        print(f"Bounding box: {bbox}")
    except Exception as e:
        print(f"Failed to get bounding box: {e}")
        cmds.delete(fractured_obj)
        return

    # Step 6: Create the cutting plane aligned to the Y-axis
    try:
        # Determine plane size based on bounding box
        size = max((max_x - min_x), (max_z - min_z)) * 2

        # Create a cutting plane
        plane = cmds.polyPlane(
            width=size,
            height=size,
            sx=1,
            sy=1,
            ax=(0, 1, 0),  # Y-axis
            ch=False,
            name="fracturePlane_1"
        )[0]

        # Position the plane at the center
        cmds.setAttr(f"{plane}.translateX", center[0])
        cmds.setAttr(f"{plane}.translateY", center[1])
        cmds.setAttr(f"{plane}.translateZ", center[2])
        print(f"Created cutting plane: {plane}")
    except Exception as e:
        print(f"Failed to create cutting plane: {e}")
        cmds.delete(fractured_obj)
        return

    # Step 7: Perform Boolean difference
    try:
        # Select the fractured object and the cutting plane
        cmds.select([fractured_obj, plane], replace=True)
        print(f"Selected objects for Boolean operation: {fractured_obj}, {plane}")

        # Perform Boolean difference
        bool_result = cmds.polyBoolOp(op=2, ch=False)  # op=2 is difference
        print(f"Boolean operation result: {bool_result}")

        if not bool_result:
            print("Boolean operation failed. No pieces created.")
            cmds.delete(plane)
            cmds.delete(fractured_obj)
            return

        new_piece = bool_result[0]
        print(f"Created new piece: {new_piece}")
    except Exception as e:
        print(f"Boolean operation failed: {e}")
        cmds.delete(plane)
        cmds.delete(fractured_obj)
        return

    # Step 8: Delete the cutting plane and the original fractured object
    cmds.delete(plane)
    cmds.delete(fractured_obj)
    print(f"Deleted cutting plane: {plane}")
    print(f"Deleted original fractured object: {fractured_obj}")

    # Step 9: Rename the fractured piece for clarity
    fractured_piece = cmds.rename(new_piece, f"{object_name}_fractured_piece1")
    print(f"Renamed fractured piece to: {fractured_piece}")

    return [fractured_piece]

# Usage Example:
selection = cmds.ls(selection=True)
if selection:
    fractured_piece = simple_fracture(selection[0])
    print("\nFractured piece:", fractured_piece)
else:
    cmds.confirmDialog(title='Error', message='No objects selected. Please select an object to fracture.', button=['OK'], defaultButton='OK')
