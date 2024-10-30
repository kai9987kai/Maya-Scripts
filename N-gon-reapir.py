import maya.cmds as cmds
import maya.api.OpenMaya as om
import sys
import numpy as np

# Increase recursion limit for large meshes
sys.setrecursionlimit(10000)

def get_mesh_dag_path(mesh_name):
    """
    Retrieves the DAG path of the mesh, ensuring it includes the shape node.
    Returns both the DAG path and MFnMesh function set.
    """
    try:
        selection_list = om.MSelectionList()
        selection_list.add(mesh_name)
        dag_path = selection_list.getDagPath(0)
        
        # Check if the node is a transform node
        if dag_path.node().hasFn(om.MFn.kTransform):
            # Extend to shape node
            if dag_path.extendToShapeDirectly():
                mesh_fn = om.MFnMesh(dag_path)
            else:
                cmds.error("Transform node '{}' has no valid mesh shape.".format(mesh_name))
                return None, None
        elif dag_path.node().hasFn(om.MFn.kMesh):
            mesh_fn = om.MFnMesh(dag_path)
        else:
            cmds.error("Node '{}' is neither a transform nor a mesh.".format(mesh_name))
            return None, None
        
        return dag_path, mesh_fn
    except Exception as e:
        cmds.error("Mesh '{}' not found or invalid. Error: {}".format(mesh_name, e))
        return None, None

def detect_and_fill_holes(mesh_name):
    """
    Detects holes in the mesh and fills them using constrained Delaunay triangulation.
    """
    # Convert mesh to poly (ensure it's triangulated)
    try:
        cmds.select(mesh_name, replace=True)
        cmds.polyTriangulate(mesh_name, constructionHistory=False)
    except Exception as e:
        cmds.error("Failed to triangulate mesh '{}'. Error: {}".format(mesh_name, e))
        return False

    # Get mesh DAG path and function set
    dag_path, mesh_fn = get_mesh_dag_path(mesh_name)
    if dag_path is None or mesh_fn is None:
        return False

    # Create edge iterator in world space
    edge_iter = om.MItMeshEdge(dag_path)
    boundary_edges = []

    while not edge_iter.isDone():
        if edge_iter.onBoundary():
            edge_id = edge_iter.index()
            boundary_edges.append(edge_id)
        edge_iter.next()

    if not boundary_edges:
        print("No holes detected in the mesh.")
        return True

    print("Detected {} boundary edges. Filling holes...".format(len(boundary_edges)))

    # Get boundary edge loops
    boundary_edges_set = set(boundary_edges)
    edge_to_vertex = {}
    edge_iter.reset()
    
    while not edge_iter.isDone():
        edge_id = edge_iter.index()
        vtx1 = edge_iter.vertexId(0)
        vtx2 = edge_iter.vertexId(1)
        edge_to_vertex[edge_id] = (vtx1, vtx2)
        edge_iter.next()

    # Build edge adjacency
    vertex_to_edges = {}
    for edge_id in boundary_edges:
        vtx1, vtx2 = edge_to_vertex[edge_id]
        vertex_to_edges.setdefault(vtx1, []).append(edge_id)
        vertex_to_edges.setdefault(vtx2, []).append(edge_id)

    # Extract boundary loops
    boundary_loops = []
    visited_edges = set()
    
    for edge_id in boundary_edges:
        if edge_id in visited_edges:
            continue
            
        loop = []
        current_edge = edge_id
        visited_edges.add(current_edge)
        vtx1, vtx2 = edge_to_vertex[current_edge]
        loop.append(vtx1)
        loop.append(vtx2)
        current_vertex = vtx2
        
        while True:
            edges = vertex_to_edges.get(current_vertex, [])
            next_edge = None
            for e in edges:
                if e != current_edge and e in boundary_edges_set:
                    next_edge = e
                    break
            if next_edge is None or next_edge in visited_edges:
                break
            visited_edges.add(next_edge)
            vtx1, vtx2 = edge_to_vertex[next_edge]
            next_vertex = vtx2 if vtx1 == current_vertex else vtx1
            loop.append(next_vertex)
            current_edge = next_edge
            current_vertex = next_vertex
        boundary_loops.append(loop)

    # Fill each hole using constrained Delaunay triangulation
    for loop in boundary_loops:
        try:
            # Get unique vertex IDs in the loop
            unique_vertices = []
            seen = set()
            for vtx_id in loop:
                if vtx_id not in seen:
                    unique_vertices.append(vtx_id)
                    seen.add(vtx_id)

            # Get positions of vertices in the loop
            positions = []
            for vtx_id in unique_vertices:
                point = mesh_fn.getPoint(vtx_id, om.MSpace.kWorld)
                positions.append([point.x, point.y, point.z])

            # Project loop onto a best-fit plane
            if len(positions) >= 3:  # Need at least 3 points for a plane
                positions_np = np.array(positions)
                plane_normal, plane_point = best_fit_plane(positions_np)
                projected_positions = project_points_to_plane(positions_np, plane_normal, plane_point)

                # Create new faces using triangulation
                new_faces = triangulate_loop(projected_positions, unique_vertices)
                
                # Add the new faces to the mesh
                for face in new_faces:
                    try:
                        cmds.polyCreateFacet(
                            mesh_name,
                            point=[mesh_fn.getPoint(i, om.MSpace.kWorld) for i in face]
                        )
                    except Exception as e:
                        cmds.warning("Failed to create face: {}".format(e))
                        continue

                print("Successfully filled hole with {} new faces".format(len(new_faces)))
            else:
                cmds.warning("Not enough vertices to fill hole (minimum 3 required)")
                
        except Exception as e:
            cmds.warning("Failed to process boundary loop: {}".format(e))
            continue

    # Clean up the mesh after hole filling
    try:
        cmds.polyMergeVertex(mesh_name, distance=0.001)
        cmds.polyNormal(mesh_name, normalMode=2)  # Conform normals
        cmds.polyTriangulate(mesh_name)  # Re-triangulate after filling
    except Exception as e:
        cmds.warning("Post-processing failed: {}".format(e))

    return True

def best_fit_plane(points):
    """
    Computes the best-fit plane for a set of 3D points using SVD.
    """
    # Center the points
    centroid = np.mean(points, axis=0)
    centered_points = points - centroid
    
    # Compute SVD
    _, _, vh = np.linalg.svd(centered_points)
    normal = vh[2]  # The normal is the last right singular vector
    
    return normal, centroid

def project_points_to_plane(points, normal, point_on_plane):
    """
    Projects points onto a plane defined by normal and point.
    """
    normal = normal / np.linalg.norm(normal)
    vectors = points - point_on_plane
    distances = np.dot(vectors, normal)
    projections = points - np.outer(distances, normal)
    return projections

def triangulate_loop(points_3d, vertex_indices):
    """
    Performs 2D triangulation of points after converting to a local coordinate system.
    """
    if len(points_3d) < 3:
        raise ValueError("Need at least 3 points for triangulation")

    # Find the best-fit plane normal
    normal, centroid = best_fit_plane(points_3d)
    
    # Create a local coordinate system
    z_axis = normal
    y_axis = np.array([0.0, 1.0, 0.0])
    if np.abs(np.dot(z_axis, y_axis)) > 0.9:
        y_axis = np.array([1.0, 0.0, 0.0])
    x_axis = np.cross(y_axis, z_axis)
    x_axis /= np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    
    # Project points onto the plane and convert to 2D
    local_points = []
    for p in points_3d:
        v = p - centroid
        x = np.dot(v, x_axis)
        y = np.dot(v, y_axis)
        local_points.append([x, y])
    
    # Simple ear clipping triangulation
    local_points = np.array(local_points)
    triangles = []
    indices = list(range(len(local_points)))
    
    while len(indices) >= 3:
        for i in range(len(indices)):
            i0 = indices[i]
            i1 = indices[(i + 1) % len(indices)]
            i2 = indices[(i + 2) % len(indices)]
            
            p0 = local_points[i0]
            p1 = local_points[i1]
            p2 = local_points[i2]
            
            # Check if triangle is counter-clockwise
            v1 = p1 - p0
            v2 = p2 - p0
            if np.cross(v1, v2) <= 0:
                continue
                
            # Check if triangle contains any other points
            valid = True
            for j in indices:
                if j in (i0, i1, i2):
                    continue
                p = local_points[j]
                if point_in_triangle(p, p0, p1, p2):
                    valid = False
                    break
            
            if valid:
                triangles.append([vertex_indices[i0], vertex_indices[i1], vertex_indices[i2]])
                indices.pop((i + 1) % len(indices))
                break
        else:
            break  # No valid ear found
            
    return triangles

def point_in_triangle(p, a, b, c):
    """
    Determines if point p is inside triangle abc.
    """
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    
    d1 = sign(p, a, b)
    d2 = sign(p, b, c)
    d3 = sign(p, c, a)
    
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    
    return not (has_neg and has_pos)

def main():
    """
    Main function to execute hole filling on the selected mesh.
    """
    # Get selected mesh
    selection = cmds.ls(selection=True, transforms=True)
    if not selection:
        cmds.error("Please select a mesh before running the script.")
        return

    mesh_name = selection[0]
    
    # Start an undo chunk
    cmds.undoInfo(openChunk=True)
    
    try:
        # Fill holes in the mesh
        if detect_and_fill_holes(mesh_name):
            print("Mesh processing completed successfully.")
    except Exception as e:
        cmds.error("Error processing mesh: {}".format(e))
    finally:
        # Close the undo chunk
        cmds.undoInfo(closeChunk=True)

if __name__ == "__main__":
    main()
