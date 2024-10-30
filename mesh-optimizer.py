import maya.cmds as cmds
import maya.api.OpenMaya as om

def topology_optimizer_ui():
    """
    Creates a UI for the Topology Optimizer tool with sliders for reduction percentage and edge threshold.
    """
    if cmds.window("topologyOptimizerWin", exists=True):
        cmds.deleteUI("topologyOptimizerWin")
    
    window = cmds.window("topologyOptimizerWin", title="Topology Optimizer", widthHeight=(300, 200))
    cmds.columnLayout(adjustableColumn=True)
    cmds.text(label="Topology Optimizer for Low-Poly Modeling", align="center", height=30)
    
    cmds.separator(height=10)
    cmds.text(label="Reduction Settings", align="left")
    
    # Reduction Percentage Slider
    cmds.floatSliderGrp("reductionPercent", label="Reduction %", field=True, minValue=0, maxValue=100, value=50)
    
    # Edge Threshold Slider
    cmds.floatSliderGrp("edgeThreshold", label="Edge Threshold", field=True, minValue=0, maxValue=1, value=0.5)
    
    # Buttons
    cmds.separator(height=20)
    cmds.button(label="Apply Optimization", command=optimize_topology)
    cmds.button(label="Close", command=lambda x: cmds.deleteUI("topologyOptimizerWin"))
    
    cmds.showWindow(window)

def optimize_topology(*args):
    """
    Applies topology optimization based on user-specified settings.
    """
    # Get selected objects
    selected = cmds.ls(selection=True)
    if not selected:
        cmds.warning("Please select a mesh object to optimize.")
        return

    # Get reduction percentage and edge threshold from UI
    reduction_percent = cmds.floatSliderGrp("reductionPercent", query=True, value=True)
    edge_threshold = cmds.floatSliderGrp("edgeThreshold", query=True, value=True)
    
    for obj in selected:
        if not cmds.nodeType(obj) == "transform":
            continue

        shape_node = cmds.listRelatives(obj, shapes=True)[0]
        if not cmds.nodeType(shape_node) == "mesh":
            continue
        
        # Apply polyReduce with custom settings
        try:
            # Lock any transforms to prevent unintentional scale/rotate changes
            cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True)

            # Use polyReduce with specified reduction and threshold settings
            cmds.polyReduce(
                shape_node,
                version=1,
                percentage=reduction_percent,
                keepQuadsWeight=edge_threshold,
                useVirtualSymmetry=True,
                symmetryTolerance=0.001,
                keepBorder=True,
                keepHardEdge=True,
                keepCreaseEdge=True,
                keepMapBorder=True,
                keepFaceGroupBorder=True,
                cachingReduce=True,
                preserveTopology=True,
                termination=0
            )
            cmds.polySoftEdge(shape_node, angle=180, constructionHistory=False)
            cmds.select(obj)
            om.MGlobal.displayInfo(f"Topology optimization applied to {obj} with {reduction_percent}% reduction.")
        
        except Exception as e:
            cmds.warning(f"Failed to apply topology optimization on {obj}. Error: {e}")

if __name__ == "__main__":
    topology_optimizer_ui()
