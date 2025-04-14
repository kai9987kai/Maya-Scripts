import maya.cmds as cmds

def ultimate_unwrap_db5():
    """
    Advanced UV unwrapping script for the Aston Martin DB5 model in Maya.
    Processes all non-intermediate mesh parts with a workflow inspired by recent research:
    1. Initial UV projection with refined parameters.
    2. Semantic-aware seam adjustment (simulated via curvature analysis).
    3. Unfolding to minimize distortion.
    4. UV optimization to reduce stretching.
    5. Efficient UV layout with UDIM support.
    6. Checker texture application for quality inspection.

    Assumptions:
    - The scene contains only the DB5 model parts as polygonal meshes.
    - Parts are processed individually for tailored UV treatment.
    """
    # Collect all mesh shapes in the scene
    mesh_shapes = cmds.ls(type="mesh", long=True)
    if not mesh_shapes:
        cmds.warning("No mesh objects found in the scene.")
        return

    # Process each mesh part
    for shape in mesh_shapes:
        if cmds.getAttr(shape + ".intermediateObject"):
            continue  # Skip intermediate objects

        parent = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        print(f"Processing part: {parent}")

        try:
            # Step 1: Initial UV Projection with Refined Parameters
            # Use polyAutoProjection with settings optimized for car geometry
            cmds.polyAutoProjection(
                shape + ".f[*]",
                lm=0,       # Planar projection as base
                pb=0,       # No border preservation
                ibd=1,      # Ignore best distortion for speed
                cm=1,       # Create new map
                l=2,        # Layout method for better packing
                sc=1,       # Uniform scaling
                ps=0.15,    # Smaller projection size for detail preservation
                ws=0,       # Object space projection
                ch=1        # Keep construction history
            )
            print("  - Initial UV projection applied.")

            # Step 2: Simulate Semantic-Aware Seam Placement
            # Inspired by research (e.g., GraphSeam), approximate by analyzing curvature
            # Select high-curvature edges as potential seams
            cmds.select(shape)
            cmds.polySelectConstraint(mode=3, type=0x0008, orient=2, orientbound=[45, 90])
            high_curvature_edges = cmds.ls(selection=True, flatten=True)
            if high_curvature_edges:
                cmds.polyMapCut(high_curvature_edges)
                print("  - Simulated semantic seams based on curvature.")
            cmds.polySelectConstraint(mode=0)  # Reset constraints

            # Step 3: Unfold UVs to Minimize Distortion
            # Use polyUnfold for relaxation, inspired by SF3D's fast unwrapping
            cmds.polyUnfold(
                shape,
                iterations=5,      # More iterations for smoother results
                pack=False,        # Unfold without packing yet
                percentage=0.5,    # Moderate correction per iteration
                smoothing=1        # Smooth UVs to follow geometry
            )
            print("  - UVs unfolded to reduce distortion.")

            # Step 4: Optimize UVs to Reduce Stretching
            # Use polyOptimizeUV, inspired by neural UV mapping concepts
            cmds.polyOptimizeUV(
                shape,
                optimize=1,       # Minimize angle distortion
                iterations=10     # Thorough optimization
            )
            print("  - UVs optimized for minimal stretching.")

            # Step 5: Normalize and Layout UVs with UDIM Support
            # Ensure uniform texel density
            cmds.polyNormalizeUV(
                shape,
                normalizeType=1   # Stretch to fit bounds
            )
            print("  - Texel density normalized.")

            # Layout UV shells efficiently with UDIM tiling option
            cmds.polyLayoutUV(
                shape,
                layout=3,          # UDIM tiling layout
                scaleMode=1,       # Uniform scaling
                rotateForBestFit=True,
                spacing=0.02,      # Small padding between shells
                shell=True         # Process all shells
            )
            print("  - UV shells laid out with UDIM support.")

        except Exception as e:
            cmds.warning(f"Error processing {shape}: {e}")

    # Step 6: Apply Checker Texture for Quality Inspection
    checker = cmds.shadingNode('checker', asTexture=True, name="DB5_checker")
    material = cmds.shadingNode('lambert', asShader=True, name="DB5_check_mat")
    cmds.connectAttr(f"{checker}.outColor", f"{material}.color")
    for shape in mesh_shapes:
        if not cmds.getAttr(shape + ".intermediateObject"):
            parent = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
            cmds.select(parent)
            cmds.hyperShade(assign=material)
    print("Checker texture applied for inspection.")

    print("Ultimate UV unwrapping completed for Aston Martin DB5.")

# Execute the script
ultimate_unwrap_db5()
