import maya.cmds as cmds
import random

def random_animation_generator(object_name, frames=100):
    """
    Generates a random animation for the specified object in Maya.
    
    Parameters:
    object_name (str): The name of the object to animate.
    frames (int): The number of frames for the animation timeline.
    """
    # Set the timeline range
    cmds.playbackOptions(min=1, max=frames)
    
    # Ensure the object exists, create it if not
    if not cmds.objExists(object_name):
        print(f"Object '{object_name}' does not exist. Creating a new object.")
        object_name = cmds.polySphere(name=object_name)[0]  # This ensures we only get the object's name

    # Keyframe every 10 frames with random transformations
    for frame in range(1, frames + 1, 10):
        # Random translation values
        tx = random.uniform(-10, 10)
        ty = random.uniform(0, 10)
        tz = random.uniform(-10, 10)
        
        # Random rotation values
        rx = random.uniform(0, 360)
        ry = random.uniform(0, 360)
        rz = random.uniform(0, 360)
        
        # Random scale values
        sx = random.uniform(0.5, 2.0)
        sy = random.uniform(0.5, 2.0)
        sz = random.uniform(0.5, 2.0)
        
        # Set keyframes for translation, rotation, and scale
        cmds.setKeyframe(object_name, time=frame, attribute="translateX", value=tx)
        cmds.setKeyframe(object_name, time=frame, attribute="translateY", value=ty)
        cmds.setKeyframe(object_name, time=frame, attribute="translateZ", value=tz)
        
        cmds.setKeyframe(object_name, time=frame, attribute="rotateX", value=rx)
        cmds.setKeyframe(object_name, time=frame, attribute="rotateY", value=ry)
        cmds.setKeyframe(object_name, time=frame, attribute="rotateZ", value=rz)
        
        cmds.setKeyframe(object_name, time=frame, attribute="scaleX", value=sx)
        cmds.setKeyframe(object_name, time=frame, attribute="scaleY", value=sy)
        cmds.setKeyframe(object_name, time=frame, attribute="scaleZ", value=sz)
    
    print(f"Random animation generated for '{object_name}' over {frames} frames.")

# Usage example
random_animation_generator("myRandomObject", frames=120)
