import maya.cmds as cmds

def highlight_ngons():
    # Get the currently selected polygon objects
    selected_objects = cmds.ls(selection=True, dag=True, type="transform")
    
    if not selected_objects:
        cmds.warning("No objects selected. Please select a polygon mesh.")
        return

    # Clear any previous selection
    cmds.select(clear=True)

    # Define a counter for the total N-gons found
    total_ngons = 0

    # Loop through each selected object to find N-gons
    for obj in selected_objects:
        # Get the shape node of the object to ensure it's a mesh
        shapes = cmds.listRelatives(obj, shapes=True)
        if not shapes or not cmds.objectType(shapes[0], isType="mesh"):
            cmds.warning(f"{obj} is not a polygon object.")
            continue

        # Get all faces in the object
        face_count = cmds.polyEvaluate(obj, face=True)
        n_gon_faces = []

        for i in range(face_count):
            # Get vertex count for each face using polyInfo
            face_info = cmds.polyInfo(f"{obj}.f[{i}]", faceToVertex=True)
            if face_info:
                vertex_count = len(face_info[0].split()) - 2  # -2 to exclude "FACE" and index
                # If the face has more than 4 vertices, it's an N-gon
                if vertex_count > 4:
                    n_gon_faces.append(f"{obj}.f[{i}]")
                    total_ngons += 1

        # Highlight the N-gons for this object
        if n_gon_faces:
            cmds.select(n_gon_faces, add=True)
            print(f"Highlighted {len(n_gon_faces)} N-gon faces in {obj}.")
        else:
            print(f"No N-gons found in {obj}.")

    # If no N-gons were found in any objects, show a message
    if total_ngons == 0:
        cmds.warning("No N-gons found in the selected objects.")
    else:
        cmds.warning(f"{total_ngons} N-gon faces highlighted in the selected objects.")

# Run the function
highlight_ngons()
