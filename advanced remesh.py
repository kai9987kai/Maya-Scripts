import maya.cmds as cmds
import maya.api.OpenMaya as om

def improve_mesh_to_quads():
    # Get the currently selected polygon objects
    selected_objects = cmds.ls(selection=True, type='transform')
    
    if not selected_objects:
        cmds.warning("No objects selected. Please select a polygon mesh.")
        return

    for obj in selected_objects:
        shapes = cmds.listRelatives(obj, shapes=True, noIntermediate=True)
        if not shapes or cmds.nodeType(shapes[0]) != 'mesh':
            cmds.warning(f"{obj} is not a polygon mesh.")
            continue

        print(f"Processing mesh cleanup for {obj}...")

        # Step 1: Triangulate the mesh to ensure no N-gons or malformed geometry
        cmds.polyTriangulate(obj, constructionHistory=False)
        print("Mesh triangulated.")

        # Step 2: Quadrangulate the mesh to convert triangles into quads where possible
        cmds.polyQuad(obj, angle=180)
        print("Quadrangulation applied.")

        # Step 3: Apply polySmooth to relax the mesh
        cmds.polySmooth(obj, mth=0, dv=1, c=1, kb=1, ksb=1, khe=1, kt=1, kmb=1, suv=1, peh=0, ps=0.1, ro=1, ch=0)
        print("Edge flow optimized with polySmooth.")

        # Step 4: Check for N-gons and highlight them for possible manual cleanup
        ngons = find_ngons(obj)
        if ngons:
            cmds.select(ngons, replace=True)
            cmds.warning(f"{len(ngons)} N-gon faces detected. Highlighted for review.")
        else:
            print("No N-gons detected. Mesh is clean with quads.")

    print("Mesh improvement to quads and reasonable edge flow completed.")

def find_ngons(mesh_name):
    """
    Identifies and returns a list of faces that are N-gons (non-quad and non-triangle) in the mesh.
    """
    dag_path, mesh_fn = get_mesh_dag_path(mesh_name)
    if dag_path is None or mesh_fn is None:
        return []

    face_iter = om.MItMeshPolygon(dag_path)
    n_gons = []

    while not face_iter.isDone():
        if face_iter.polygonVertexCount() > 4:
            n_gons.append(f"{mesh_name}.f[{face_iter.index()}]")
        face_iter.next()

    return n_gons

def get_mesh_dag_path(mesh_name):
    """
    Retrieves the DAG path of the mesh and verifies it's a mesh.
    """
    try:
        selection_list = om.MSelectionList()
        selection_list.add(mesh_name)
        dag_path = selection_list.getDagPath(0)
        
        if dag_path.node().hasFn(om.MFn.kTransform):
            dag_path.extendToShape()
        
        if not dag_path.node().hasFn(om.MFn.kMesh):
            cmds.error(f"Node '{mesh_name}' is not a mesh.")
            return None, None

        mesh_fn = om.MFnMesh(dag_path)
        return dag_path, mesh_fn
    except Exception as e:
        cmds.error(f"Mesh '{mesh_name}' not found or invalid. Error: {e}")
        return None, None

# Execute the function
improve_mesh_to_quads()
