import maya.cmds as cmds
import maya.api.OpenMaya as om

def get_mesh_dag_path(mesh_name):
    """
    Retrieves the DAG path of the mesh and verifies it's a mesh.
    """
    try:
        selection_list = om.MSelectionList()
        selection_list.add(mesh_name)
        dag_path = selection_list.getDagPath(0)

        # Extend to shape if it's a transform node
        if dag_path.node().hasFn(om.MFn.kTransform):
            dag_path.extendToShape()
        
        # Ensure it's a mesh node
        if not dag_path.node().hasFn(om.MFn.kMesh):
            cmds.error(f"Node '{mesh_name}' is not a mesh.")
            return None, None

        mesh_fn = om.MFnMesh(dag_path)
        return dag_path, mesh_fn
    except Exception as e:
        cmds.error(f"Mesh '{mesh_name}' not found or invalid. Error: {e}")
        return None, None

def highlight_triangular_faces(mesh_name):
    """
    Detects and highlights triangular faces (with 3 vertices) in the selected mesh.
    """
    dag_path, mesh_fn = get_mesh_dag_path(mesh_name)
    if dag_path is None or mesh_fn is None:
        return False

    face_iter = om.MItMeshPolygon(dag_path)
    triangular_faces = []

    while not face_iter.isDone():
        if face_iter.polygonVertexCount() == 3:  # Check if the face has 3 vertices
            triangular_faces.append(face_iter.index())
        face_iter.next()

    if not triangular_faces:
        cmds.confirmDialog(title='No Triangles', message="No triangular faces detected in the mesh.", button=['OK'], defaultButton='OK')
        return True

    # Highlight triangular faces
    cmds.select(clear=True)
    for face_id in triangular_faces:
        cmds.select(f"{mesh_name}.f[{face_id}]", add=True)
    
    cmds.confirmDialog(title='Triangles Detected', message=f"Highlighted {len(triangular_faces)} triangular faces.", button=['OK'], defaultButton='OK')
    return True

def main():
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        cmds.error("Please select a mesh before running the script.")
        return
    mesh_name = selection[0]
    cmds.undoInfo(openChunk=True)
    
    try:
        if highlight_triangular_faces(mesh_name):
            print("Triangular face detection and highlighting completed successfully.")
    except Exception as e:
        cmds.error(f"Error processing mesh: {e}")
    finally:
        cmds.undoInfo(closeChunk=True)

if __name__ == "__main__":
    main()
