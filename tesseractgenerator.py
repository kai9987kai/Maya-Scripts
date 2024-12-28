import maya.cmds as cmds
import random
import math
import os

# Global variables
tesseract_group = None
tesseract_curves = []
animation_running = False

# Function to create a shader with transparency and glow
def create_holographic_shader(transparency, glow_intensity):
    shader = cmds.shadingNode("lambert", asShader=True, name="HolographicShader")
    shader_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shader + "SG")
    cmds.connectAttr(shader + ".outColor", shader_sg + ".surfaceShader")
    cmds.setAttr(shader + ".transparency", transparency, transparency, transparency, type="double3")
    cmds.setAttr(shader + ".glowIntensity", glow_intensity)
    return shader_sg

# Function to project 4D vertices into 3D space
def project_to_3d(vertices_4d, angle_xw, angle_yw, angle_zw, w_slice):
    vertices_3d = []
    for v in vertices_4d:
        x, y, z, w = v
        # Apply 4D rotation in the XW plane
        x_new = x * math.cos(angle_xw) - w * math.sin(angle_xw)
        w_new = x * math.sin(angle_xw) + w * math.cos(angle_xw)
        # Apply 4D rotation in the YW plane
        y_new = y * math.cos(angle_yw) - w_new * math.sin(angle_yw)
        w_new = y * math.sin(angle_yw) + w_new * math.cos(angle_yw)
        # Apply 4D rotation in the ZW plane
        z_new = z * math.cos(angle_zw) - w_new * math.sin(angle_zw)
        w_new = z * math.sin(angle_zw) + w_new * math.cos(angle_zw)
        # Apply W slicing (only vertices close to the slice are projected)
        if abs(w_new - w_slice) < 0.5:
            vertices_3d.append([x_new, y_new, z_new])
    return vertices_3d

# Function to create or update the tesseract
def update_tesseract(angle_xw, angle_yw, angle_zw, w_slice, num_slices, random_colors, edge_thickness, transparency, glow_intensity):
    global tesseract_group, tesseract_curves

    # Delete previous tesseract if it exists
    if tesseract_group and cmds.objExists(tesseract_group):
        cmds.delete(tesseract_group)

    # Create a new group for the tesseract
    tesseract_group = cmds.group(empty=True, name="Tesseract")
    tesseract_curves = []

    # Create a holographic shader
    shader_sg = create_holographic_shader(transparency, glow_intensity)

    # Define the 16 vertices of a tesseract in 4D space
    vertices_4d = [
        [-1, -1, -1, -1],
        [-1, -1, -1, 1],
        [-1, -1, 1, -1],
        [-1, -1, 1, 1],
        [-1, 1, -1, -1],
        [-1, 1, -1, 1],
        [-1, 1, 1, -1],
        [-1, 1, 1, 1],
        [1, -1, -1, -1],
        [1, -1, -1, 1],
        [1, -1, 1, -1],
        [1, -1, 1, 1],
        [1, 1, -1, -1],
        [1, 1, -1, 1],
        [1, 1, 1, -1],
        [1, 1, 1, 1]
    ]

    # Define the edges of the tesseract
    edges = [
        (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6),
        (3, 7), (4, 5), (4, 6), (5, 7), (6, 7), (8, 9), (8, 10),
        (8, 12), (9, 11), (9, 13), (10, 11), (10, 14), (11, 15),
        (12, 13), (12, 14), (13, 15), (14, 15), (0, 8), (1, 9),
        (2, 10), (3, 11), (4, 12), (5, 13), (6, 14), (7, 15)
    ]

    # Create multiple slices of the tesseract
    for i in range(num_slices):
        slice_offset = (i / (num_slices - 1)) * 2 - 1 if num_slices > 1 else w_slice
        vertices_3d = project_to_3d(vertices_4d, angle_xw, angle_yw, angle_zw, slice_offset)
        for edge in edges:
            if edge[0] < len(vertices_3d) and edge[1] < len(vertices_3d):
                curve = cmds.curve(p=[vertices_3d[edge[0]], vertices_3d[edge[1]]], degree=1)
                cmds.parent(curve, tesseract_group)
                tesseract_curves.append(curve)
                # Apply random colors if enabled
                if random_colors:
                    cmds.setAttr(curve + ".overrideEnabled", 1)
                    cmds.setAttr(curve + ".overrideColor", random.randint(1, 31))
                # Set edge thickness
                cmds.setAttr(curve + ".lineWidth", edge_thickness)
                # Apply the shader to the curve
                cmds.sets(curve, edit=True, forceElement=shader_sg)

# Function to animate the tesseract
def animate_tesseract(speed, loop):
    global animation_running
    if animation_running:
        animation_running = False
        return
    animation_running = True
    angle = 0
    def update_animation():
        nonlocal angle
        if not animation_running:
            return
        angle += speed
        if angle > 360:
            angle = 0 if loop else 360
        update_tesseract(angle * (math.pi / 180), angle * (math.pi / 180), angle * (math.pi / 180), 0, 1, True, 2, 0.5, 0.1)
        cmds.refresh()
        if animation_running:
            cmds.scriptJob(runOnce=True, idleEvent=update_animation)
    update_animation()

# Function to export the animation
def export_animation(output_dir, frame_range):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for frame in range(frame_range[0], frame_range[1] + 1):
        cmds.currentTime(frame)
        cmds.refresh()
        cmds.playblast(frame=frame, format="image", filename=os.path.join(output_dir, "frame_"), compression="png", quality=100, width=1920, height=1080)

# Function to create the GUI
def create_gui():
    if cmds.window("TesseractGUI", exists=True):
        cmds.deleteUI("TesseractGUI")
    cmds.window("TesseractGUI", title="4D Tesseract Controls", width=400)
    cmds.columnLayout(adjustableColumn=True)

    # Sliders for 4D rotation angles
    cmds.text(label="4D Rotation Angles")
    angle_xw_slider = cmds.floatSliderGrp(label="XW Angle", minValue=0, maxValue=360, field=True, value=0)
    angle_yw_slider = cmds.floatSliderGrp(label="YW Angle", minValue=0, maxValue=360, field=True, value=0)
    angle_zw_slider = cmds.floatSliderGrp(label="ZW Angle", minValue=0, maxValue=360, field=True, value=0)

    # Slider for W slicing
    cmds.text(label="W Slice")
    w_slice_slider = cmds.floatSliderGrp(label="W Slice", minValue=-1, maxValue=1, field=True, value=0)

    # Slider for number of slices
    cmds.text(label="Number of Slices")
    num_slices_slider = cmds.intSliderGrp(label="Slices", minValue=1, maxValue=10, field=True, value=1)

    # Checkbox for random colors
    random_colors_checkbox = cmds.checkBoxGrp(label="Random Colors", value1=False)

    # Slider for edge thickness
    cmds.text(label="Edge Thickness")
    edge_thickness_slider = cmds.floatSliderGrp(label="Thickness", minValue=1, maxValue=5, field=True, value=2)

    # Slider for transparency
    cmds.text(label="Transparency")
    transparency_slider = cmds.floatSliderGrp(label="Transparency", minValue=0, maxValue=1, field=True, value=0.5)

    # Slider for glow intensity
    cmds.text(label="Glow Intensity")
    glow_intensity_slider = cmds.floatSliderGrp(label="Glow", minValue=0, maxValue=1, field=True, value=0.1)

    # Button to update the tesseract
    cmds.button(label="Update Tesseract", command=lambda _: update_tesseract(
        cmds.floatSliderGrp(angle_xw_slider, query=True, value=True) * (math.pi / 180),
        cmds.floatSliderGrp(angle_yw_slider, query=True, value=True) * (math.pi / 180),
        cmds.floatSliderGrp(angle_zw_slider, query=True, value=True) * (math.pi / 180),
        cmds.floatSliderGrp(w_slice_slider, query=True, value=True),
        cmds.intSliderGrp(num_slices_slider, query=True, value=True),
        cmds.checkBoxGrp(random_colors_checkbox, query=True, value1=True),
        cmds.floatSliderGrp(edge_thickness_slider, query=True, value=True),
        cmds.floatSliderGrp(transparency_slider, query=True, value=True),
        cmds.floatSliderGrp(glow_intensity_slider, query=True, value=True)
    ))

    # Button to animate the tesseract
    cmds.button(label="Animate Tesseract", command=lambda _: animate_tesseract(1, True))

    # Button to export animation
    cmds.button(label="Export Animation", command=lambda _: export_animation("C:/TesseractAnimation", (1, 100)))

    cmds.showWindow()

# Run the GUI
create_gui()
