import maya.cmds as cmds
import maya.mel as mel

def improve_edge_flow_script():
    # Get the currently selected polygon objects
    selected_objects = cmds.ls(selection=True, type='transform')

    if not selected_objects:
        cmds.warning("No objects selected. Please select a polygon mesh.")
        return

    # Loop through each selected object
    for obj in selected_objects:
        # Ensure the object is a polygon mesh
        shapes = cmds.listRelatives(obj, shapes=True, noIntermediate=True)
        if not shapes or cmds.nodeType(shapes[0]) != 'mesh':
            cmds.warning(f"{obj} is not a polygon mesh.")
            continue

        print(f"Improving edge flow in {obj}...")

        # Call the function to improve edge flow
        improve_edge_flow(obj)

    cmds.warning("Edge flow improvement completed.")

def improve_edge_flow(mesh):
    # Step 1: Duplicate the mesh for processing
    temp_mesh = cmds.duplicate(mesh, name=f"{mesh}_temp")[0]

    # Step 2: Apply smoothing to relax the vertices
    # Use polySmooth with appropriate settings
    cmds.polySmooth(temp_mesh, mth=0, sdt=0, ovb=1, ofb=3, ofc=0, ost=0, ocr=0, dv=1, bnr=1, c=1, kb=1, ksb=1, khe=0, kt=1, kmb=1, suv=1, peh=0, ps=0.1, ro=1, ch=0)

    # Step 3: Retopologize the mesh to improve edge flow
    # Note: The 'polyRetopo' command may not be available in all versions of Maya
    if cmds.pluginInfo('retopo', query=True, loaded=True):
        print(f"Retopologizing {temp_mesh}...")
        cmds.polyRetopo(temp_mesh, targetFaceCount=cmds.polyEvaluate(temp_mesh, face=True), symmetryType=0, smoothingIterations=1)
    else:
        print("Retopo plugin not available. Using alternative methods.")
        # Alternative method: Use the Quadrangulate command to clean up topology
        cmds.select(temp_mesh)
        mel.eval('Quadrangulate;')

    # Step 4: Shrinkwrap the original mesh onto the processed mesh to preserve shape
    shrinkwrap_deformer = cmds.deformer(mesh, type='shrinkWrap')[0]
    cmds.setAttr(f"{shrinkwrap_deformer}.projection", 0)  # Closest point
    cmds.setAttr(f"{shrinkwrap_deformer}.targetInflation", 0)
    cmds.connectAttr(f"{temp_mesh}.worldMesh[0]", f"{shrinkwrap_deformer}.targetGeom", force=True)

    # Step 5: Cleanup temporary objects
    cmds.delete(temp_mesh)
    cmds.delete(mesh, constructionHistory=True)

    # Optional: Apply a final smoothing pass to enhance edge flow
    cmds.polySmooth(mesh, divisions=1, continuity=1.0)

    print(f"Edge flow improved for {mesh}.")

# Run the function
improve_edge_flow_script()
