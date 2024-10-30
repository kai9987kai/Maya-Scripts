import maya.cmds as cmds

def apply_direct_noise_shader():
    """
    Creates a Lambert shader with a noise texture directly connected to its color
    and applies it to selected objects.
    """
    # Check for selected objects
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.confirmDialog(title='No Selection', message='Please select one or more objects to apply the noise shader.', button=['OK'], defaultButton='OK')
        return

    # Create a noise texture node
    noise_texture = cmds.shadingNode('noise', asTexture=True, name='directNoiseTexture')

    # Adjust noise settings for maximum variation
    cmds.setAttr(f"{noise_texture}.ratio", 0.2)      # Low smoothness for high variation
    cmds.setAttr(f"{noise_texture}.frequency", 20.0) # High frequency for finer noise

    # Create and connect a place2dTexture node for UV mapping
    place2d = cmds.shadingNode('place2dTexture', asUtility=True, name='place2dDirectNoise')
    cmds.connectAttr(f"{place2d}.outUV", f"{noise_texture}.uvCoord", force=True)
    cmds.connectAttr(f"{place2d}.outUvFilterSize", f"{noise_texture}.uvFilterSize", force=True)

    # Create a Lambert shader
    shader = cmds.shadingNode('lambert', asShader=True, name='directNoiseShader')
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='directNoiseSG')

    # Connect noise texture directly to shader's color
    cmds.connectAttr(f"{noise_texture}.outColor", f"{shader}.color", force=True)

    # Connect shader to shading group
    cmds.connectAttr(f"{shader}.outColor", f"{shading_group}.surfaceShader", force=True)

    # Assign shader to selected objects
    cmds.sets(selection, edit=True, forceElement=shading_group)

    print(f"Applied direct noise shader to selected objects: {selection}")

# Run the script to apply the direct noise shader to selected objects
apply_direct_noise_shader()
