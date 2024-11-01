import maya.cmds as cmds
import json
import os

class EnhancedMeshReductionUI:
    def __init__(self):
        self.window_name = "EnhancedMeshReductionWindow"
        self.presets_file = os.path.join(cmds.internalVar(userAppDir=True), "enhanced_mesh_reduction_presets.json")
        self.presets = self.load_presets()
        self.create_ui()

    def load_presets(self):
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                cmds.warning(f"Failed to load presets. Using default presets.\nError: {e}")
        return {
            "High Quality": {"percentage": 25},
            "Medium Quality": {"percentage": 50},
            "Low Quality": {"percentage": 75}
        }

    def save_presets(self):
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(self.presets, f, indent=4)
        except Exception as e:
            cmds.warning(f"Failed to save presets: {e}")

    def create_ui(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        window = cmds.window(self.window_name, title="Enhanced Mesh Reduction Tool", widthHeight=(450, 650))
        main_layout = cmds.scrollLayout(horizontalScrollBarThickness=0, verticalScrollBarThickness=16)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAlign="center")

        cmds.text(label="Enhanced Mesh Reduction Tool", font="boldLabelFont", height=30)
        cmds.separator(height=10, style='none')

        cmds.text(label="Select one or more mesh objects to reduce.", align="center")

        cmds.frameLayout(label="Reduction Settings", collapsable=True, collapse=False, width=420)
        cmds.columnLayout(adjustableColumn=True, columnAlign="left", rowSpacing=10)

        cmds.text(label="Reduction Percentage (%):", align="left")
        self.percentage_field = cmds.floatField(value=50.0, minValue=1.0, maxValue=99.0)

        cmds.text(label="Reduction Quality:", align="left")
        self.quality_menu = cmds.optionMenu()
        for preset in ["High Quality", "Medium Quality", "Low Quality"]:
            cmds.menuItem(label=preset)

        cmds.setParent('..')
        cmds.setParent('..')

        cmds.frameLayout(label="Presets Management", collapsable=True, collapse=False, width=420)
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 140), (2, 140), (3, 140)], columnSpacing=[(1, 10), (2,10), (3,10)])

        self.preset_menu = cmds.optionMenu(label="Load Preset", changeCommand=self.apply_selected_preset)
        for preset_name in self.presets:
            cmds.menuItem(label=preset_name)

        cmds.button(label="Save Current Settings", command=self.save_current_preset)
        cmds.button(label="Delete Selected Preset", command=self.delete_selected_preset)

        cmds.setParent('..')
        cmds.setParent('..')

        self.progress_bar = cmds.progressBar(maxValue=100, width=400, visible=False)

        cmds.button(label="Reduce Selected Mesh(es)", command=self.reduce_mesh, height=50, width=400, bgc=[0.2, 0.6, 0.2])
        cmds.separator(height=10, style='none')

        cmds.showWindow(window)

    def is_valid_mesh(self, obj):
        shapes = cmds.listRelatives(obj, shapes=True, type='mesh')
        return shapes is not None and len(shapes) > 0

    def adaptive_reduction_percentage(self, initial_vertices):
        """
        Simple adaptive calculation for reduction percentage.
        Based on mesh vertex count, provides a higher reduction percentage for more complex meshes.
        """
        # Define a basic linear scale for adaptive percentage calculation
        if initial_vertices < 5000:
            return 25.0  # Low reduction for simple meshes
        elif initial_vertices < 20000:
            return 50.0  # Medium reduction for moderately complex meshes
        else:
            return 75.0  # High reduction for complex meshes

    def reduce_mesh(self, *args):
        selected = cmds.ls(selection=True, transforms=True)
        if not selected:
            cmds.warning("Please select at least one mesh to reduce.")
            return

        meshes = []
        for obj in selected:
            if not self.is_valid_mesh(obj):
                cmds.warning(f"'{obj}' is not a valid mesh or does not contain a mesh shape. Skipping.")
                continue
            if obj.endswith("_reduced"):
                cmds.warning(f"'{obj}' has already been reduced. Skipping to prevent recursive reductions.")
                continue
            meshes.append(obj)

        if not meshes:
            cmds.warning("No valid mesh objects selected for reduction.")
            return

        for mesh in meshes:
            initial_vertex_count = cmds.polyEvaluate(mesh, vertex=True)
            target_percentage = self.adaptive_reduction_percentage(initial_vertex_count)

            try:
                cmds.polyReduce(mesh, percentage=target_percentage)
                print(f"Reduced '{mesh}' to {target_percentage}% of its original size.")
            except RuntimeError as e:
                cmds.warning(f"Failed to reduce mesh '{mesh}': {e}")

    def apply_selected_preset(self, preset_name):
        preset = self.presets.get(preset_name, {})
        if preset:
            cmds.floatField(self.percentage_field, edit=True, value=preset.get("percentage", 50.0))

    def save_current_preset(self, *args):
        preset_name = cmds.promptDialog(
            title="Save Preset",
            message="Enter preset name:",
            button=["Save", "Cancel"],
            defaultButton="Save",
            cancelButton="Cancel",
            dismissString="Cancel")

        if preset_name == "Save":
            name = cmds.promptDialog(query=True, text=True)
            if name:
                target_percentage = cmds.floatField(self.percentage_field, query=True, value=True)

                self.presets[name] = {
                    "percentage": target_percentage
                }

                cmds.menuItem(label=name, parent=self.preset_menu)
                self.save_presets()
                cmds.confirmDialog(title="Preset Saved", message=f"Preset '{name}' saved successfully.", button=["OK"])

    def delete_selected_preset(self, *args):
        selected_preset = cmds.optionMenu(self.preset_menu, query=True, value=True)
        if selected_preset in self.presets:
            confirm = cmds.confirmDialog(
                title="Delete Preset",
                message=f"Are you sure you want to delete preset '{selected_preset}'?",
                button=["Yes", "No"],
                defaultButton="No",
                cancelButton="No",
                dismissString="No")
            if confirm == "Yes":
                self.presets.pop(selected_preset)
                menu_items = cmds.optionMenu(self.preset_menu, query=True, itemListLong=True)
                if menu_items:
                    for item in menu_items:
                        if cmds.menuItem(item, query=True, label=True) == selected_preset:
                            cmds.deleteUI(item)
                            break
                self.save_presets()
                cmds.confirmDialog(title="Preset Deleted", message=f"Preset '{selected_preset}' deleted.", button=["OK"])

# Initialize and open the UI
if __name__ == "__main__":
    tool = EnhancedMeshReductionUI()
