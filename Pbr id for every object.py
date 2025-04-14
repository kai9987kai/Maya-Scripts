import maya.cmds as cmds
import random

def create_valid_shader(shader_name):
    """
    Creates an OpenPBR shader with the given name.
    Checks if it has a valid output attribute.
    If not, deletes it and creates an aiStandardSurface shader instead.
    Returns the valid shader name.
    """
    # Create an openPBR shader.
    shader = cmds.shadingNode("openPBR", asShader=True, name=shader_name)
    # Attempt to set a random base color (if possible; this may fail silently).
    try:
        r, g, b = random.random(), random.random(), random.random()
        cmds.setAttr(shader + ".base_color", r, g, b, type="double3")
    except Exception as e:
        cmds.warning("Could not set base_color on {}: {}".format(shader, e))
    
    # Get a list of available attributes.
    attrs = cmds.listAttr(shader)
    
    # Check if the shader node exposes a typical shading output.
    if attrs is not None and ("outColor" in attrs or "out" in attrs):
        print(f"Shader '{shader}' created successfully with attributes: {attrs}")
        return shader
    else:
        cmds.warning(f"Shader '{shader}' has no valid shading output attributes. Attributes: {attrs}")
        # Delete the incomplete shader
        cmds.delete(shader)
        # Create a fallback shader using aiStandardSurface.
        fallback_shader = cmds.shadingNode("aiStandardSurface", asShader=True, name=shader_name)
        r, g, b = random.random(), random.random(), random.random()
        cmds.setAttr(fallback_shader + ".baseColor", r, g, b, type="double3")
        print(f"Fallback shader '{fallback_shader}' (aiStandardSurface) created with baseColor: ({r:.2f}, {g:.2f}, {b:.2f})")
        return fallback_shader

def assign_unique_shaders():
    """
    Loops over each non-intermediate mesh shape in the scene,
    creates a unique shader (OpenPBR or fallback) for each,
    creates its shading group, and assigns the shader to the shape.
    """
    # Ensure the Arnold (mtoa) plugin is loaded.
    if not cmds.pluginInfo("mtoa", q=True, loaded=True):
        try:
            cmds.loadPlugin("mtoa")
            print("Loaded mtoa plugin.")
        except Exception as e:
            cmds.warning("Could not load Arnold plugin (mtoa): " + str(e))
            return

    # List all mesh shape nodes.
    mesh_shapes = cmds.ls(type="mesh", long=True)
    if not mesh_shapes:
        cmds.warning("No mesh objects found in the scene.")
        return

    for shape in mesh_shapes:
        # Skip intermediate shapes.
        if cmds.getAttr(shape + ".intermediateObject"):
            continue

        # Get parent transform.
        parents = cmds.listRelatives(shape, parent=True, fullPath=True)
        if not parents:
            continue
        parent_transform = parents[0]

        # Create a clean name for shader and shading group.
        clean_name = parent_transform.strip("|").replace("|", "_")
        shader_name = f"{clean_name}_openPBR"
        shading_group = f"{shader_name}SG"

        # Create the shader. If the shader doesn't produce a valid output,
        # the create_valid_shader function will fallback to an aiStandardSurface.
        shader = create_valid_shader(shader_name)

        # Create (or retrieve) the shading group.
        if not cmds.objExists(shading_group):
            sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group)
            print(f"Created shading group '{shading_group}'")
        else:
            sg = shading_group

        # Determine the valid output attribute.
        if cmds.attributeQuery("outColor", node=shader, exists=True):
            output_attr = "outColor"
        elif cmds.attributeQuery("out", node=shader, exists=True):
            output_attr = "out"
        else:
            cmds.warning(f"Shader '{shader}' is missing shading output even after fallback. Skipping connection.")
            continue

        full_output = f"{shader}.{output_attr}"
        try:
            # Connect shader output to shading group's surfaceShader.
            if not cmds.isConnected(full_output, sg + ".surfaceShader"):
                cmds.connectAttr(full_output, sg + ".surfaceShader", force=True)
                print(f"Connected '{full_output}' to '{sg}.surfaceShader'")
            else:
                print(f"'{full_output}' is already connected to '{sg}.surfaceShader'")
        except Exception as e:
            cmds.warning("Error connecting {} to {}: {}".format(full_output, sg + ".surfaceShader", e))
            continue

        # Finally, assign the shading group to the mesh shape.
        try:
            cmds.sets(shape, edit=True, forceElement=sg)
            connected_sg = cmds.listConnections(shape, type="shadingEngine")
            print(f"Assigned shader '{shader}' to shape '{shape}'. Connected shading group(s): {connected_sg}")
        except Exception as e:
            cmds.warning("Error assigning shader '{}' to shape '{}': {}".format(shader, shape, e))
    
    print("Completed assignment of unique shaders to all mesh shapes.")

# Run the assignment function.
assign_unique_shaders()
