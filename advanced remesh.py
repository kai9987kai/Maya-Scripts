import maya.cmds as cmds
import json
import os
import numpy as np

class HeuristicMeshReduction:
    def __init__(self, mesh_name, target_face_count):
        """
        Heuristic-based adaptive mesh reduction to mimic ML-based prediction.
        
        Parameters:
            mesh_name (str): Name of the mesh to reduce.
            target_face_count (int): Desired face count after reduction.
        """
        self.mesh_name = mesh_name
        self.target_face_count = target_face_count

    def extract_mesh_features(self):
        """
        Extracts basic mesh features used to determine reduction parameters.
        """
        face_count = cmds.polyEvaluate(self.mesh_name, face=True)
        edge_count = cmds.polyEvaluate(self.mesh_name, edge=True)
        uv_count = len(cmds.polyListComponentConversion(self.mesh_name, tuv=True))
        
        # Normalize features (simple scaling for example purposes)
        features = np.array([face_count, edge_count, uv_count])
        features = features / (np.max(features) + 1e-5)  # Prevent division by zero
        return features

    def predict_parameters(self):
        """
        Heuristic-based prediction of reduction parameters.
        """
        face_count, edge_count, uv_count = self.extract_mesh_features()

        # Heuristic-based reduction based on complexity of mesh features
        reduction_percent = max(5, min(90, 70 * (1 - face_count)))
        feature_angle = 10 + 25 * (1 - edge_count)
        smoothing_strength = 0.05 * (1 - uv_count)

        return reduction_percent, feature_angle, smoothing_strength

    def reduce_mesh(self):
        """
        Perform mesh reduction using heuristically predicted parameters.
        """
        if not cmds.objExists(self.mesh_name):
            raise ValueError(f"Mesh {self.mesh_name} does not exist")

        initial_face_count = cmds.polyEvaluate(self.mesh_name, face=True)
        if self.target_face_count >= initial_face_count:
            print("Target face count exceeds current - no reduction needed")
            return self.mesh_name

        reduction_percent, feature_angle, smoothing_strength = self.predict_parameters()

        reduced_mesh = cmds.duplicate(self.mesh_name, name=f"{self.mesh_name}_reduced")[0]
        
        try:
            cmds.polyReduce(reduced_mesh, percentage=reduction_percent,
                            keepQuadsWeight=1.0, keepBorder=True,
                            keepHardEdge=True, triangulate=False,
                            replaceOriginal=True)
            
            cmds.polyAverageNormal(reduced_mesh, postSmoothing=smoothing_strength)
            
            final_face_count = cmds.polyEvaluate(reduced_mesh, face=True)
            print(f"Reduction complete: {initial_face_count} → {final_face_count} faces")
            return reduced_mesh
            
        except Exception as e:
            print(f"Error during reduction: {str(e)}")
            if cmds.objExists(reduced_mesh):
                cmds.delete(reduced_mesh)
            return None

class MeshReductionUI:
    def __init__(self):
        self.window_name = "MeshReductionUIWindow"
        self.presets_file = os.path.join(cmds.internalVar(userAppDir=True), "mesh_reduction_presets.json")
        self.presets = self.load_presets()
        self.percentage_supported = self.check_polyReduce_percentage_flag()
        self.create_ui()

    def check_polyReduce_percentage_flag(self):
        temp_mesh = cmds.polyCube(name="temp_poly_reduce_test")[0]
        percentage_supported = False
        try:
            cmds.polyReduce(temp_mesh, percentage=50.0, q=True)
            percentage_supported = True
        except RuntimeError:
            print("Debug: 'percentage' flag is NOT supported.")
        
        cmds.delete(temp_mesh)
        return percentage_supported

    def create_ui(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        window = cmds.window(self.window_name, title="Mesh Reduction Tool", widthHeight=(400, 600))
        main_layout = cmds.scrollLayout(horizontalScrollBarThickness=0, verticalScrollBarThickness=16)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAlign="center")
        
        cmds.text(label="Mesh Reduction Tool", font="boldLabelFont", height=30)
        cmds.separator(height=10, style='none')
        cmds.text(label="Select one or more mesh objects to reduce.", align="center")

        cmds.frameLayout(label="Reduction Mode", collapsable=True, collapse=False, width=380)
        cmds.columnLayout(adjustableColumn=True, columnAlign="left", rowSpacing=10)
        self.reduction_mode_menu = cmds.optionMenu(label="Reduction Mode", changeCommand=self.update_reduction_mode)
        cmds.menuItem(label="Manual")
        cmds.menuItem(label="Adaptive (Heuristic-based)")
        cmds.setParent('..')
        cmds.setParent('..')

        cmds.frameLayout(label="Reduction Settings", collapsable=True, collapse=False, width=380)
        cmds.columnLayout(adjustableColumn=True, columnAlign="left", rowSpacing=10)
        self.percentage_field = cmds.floatField(value=50.0, minValue=1.0, maxValue=100.0)
        cmds.setParent('..')
        cmds.setParent('..')

        cmds.frameLayout(label="Presets", collapsable=True, collapse=False, width=380)
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 150), (3, 120)], columnSpacing=[(1, 5), (2,5), (3,5)])
        self.preset_menu = cmds.optionMenu(label="Load Preset", changeCommand=self.apply_selected_preset)
        for preset_name in self.presets:
            cmds.menuItem(label=preset_name)
        cmds.button(label="Save Preset", command=self.save_current_preset)
        cmds.button(label="Delete Preset", command=self.delete_selected_preset)
        cmds.setParent('..')
        cmds.setParent('..')

        self.progress_bar = cmds.progressBar(maxValue=100, width=350, visible=False)
        cmds.button(label="Reduce Selected Mesh(es)", command=self.reduce_mesh, height=50, width=350)
        cmds.separator(height=10, style='none')
        cmds.showWindow(window)

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

    def save_current_preset(self, *args):
        preset_name = cmds.promptDialog(title="Save Preset", message="Enter preset name:", button=["Save", "Cancel"],
                                        defaultButton="Save", cancelButton="Cancel", dismissString="Cancel")
        if preset_name == "Save":
            name = cmds.promptDialog(query=True, text=True)
            if name:
                target_percentage = cmds.floatField(self.percentage_field, query=True, value=True)
                self.presets[name] = {"percentage": target_percentage}
                cmds.menuItem(label=name, parent=self.preset_menu)
                self.save_presets()
                cmds.confirmDialog(title="Preset Saved", message=f"Preset '{name}' saved successfully.", button=["OK"])

    def delete_selected_preset(self, *args):
        selected_preset = cmds.optionMenu(self.preset_menu, query=True, value=True)
        if selected_preset in self.presets:
            confirm = cmds.confirmDialog(title="Delete Preset", message=f"Are you sure you want to delete preset '{selected_preset}'?",
                                         button=["Yes", "No"], defaultButton="No", cancelButton="No", dismissString="No")
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

    def apply_selected_preset(self, preset_name):
        preset = self.presets.get(preset_name, {})
        if preset:
            cmds.floatField(self.percentage_field, edit=True, value=preset.get("percentage", 50.0))

    def update_reduction_mode(self, mode):
        cmds.floatField(self.percentage_field, edit=True, enable=(mode == "Manual"))

    def reduce_mesh(self, *args):
        selected = cmds.ls(selection=True, transforms=True)
        if not selected:
            cmds.warning("Please select at least one mesh to reduce.")
            return

        mode = cmds.optionMenu(self.reduction_mode_menu, query=True, value=True)
        if mode == "Manual":
            self.perform_manual_reduction(selected)
        elif mode == "Adaptive (Heuristic-based)":
            self.perform_heuristic_reduction(selected)

    def perform_manual_reduction(self, selected):
        reduction_percent = cmds.floatField(self.percentage_field, query=True, value=True)
        cmds.progressBar(self.progress_bar, edit=True, beginProgress=True, maxValue=len(selected), visible=True)

        for mesh in selected:
            try:
                base_name = mesh if not mesh.endswith("_reduced") else mesh[:-8]
                reduced_mesh = cmds.duplicate(mesh, name=f"{base_name}_reduced")[0]
                cmds.polyReduce(reduced_mesh, percentage=reduction_percent, keepBorder=True, keepHardEdge=True)
            except Exception as e:
                cmds.warning(f"Error reducing '{mesh}': {e}")
            finally:
                cmds.progressBar(self.progress_bar, edit=True, step=1)

        cmds.progressBar(self.progress_bar, edit=True, endProgress=True, visible=False)
        cmds.confirmDialog(title="Reduction Complete", message="Manual reduction is complete.", button=["OK"])

    def perform_heuristic_reduction(self, selected):
        target_face_count = 1000

        cmds.progressBar(self.progress_bar, edit=True, beginProgress=True, maxValue=len(selected), visible=True)
        for mesh in selected:
            try:
                reducer = HeuristicMeshReduction(mesh_name=mesh, target_face_count=target_face_count)
                reducer.reduce_mesh()
            except Exception as e:
                cmds.warning(f"Error during heuristic reduction for '{mesh}': {e}")
            finally:
                cmds.progressBar(self.progress_bar, edit=True, step=1)

        cmds.progressBar(self.progress_bar, edit=True, endProgress=True, visible=False)
        cmds.confirmDialog(title="Reduction Complete", message="Heuristic reduction is complete.", button=["OK"])

# Initialize and show the UI
if __name__ == "__main__":
    MeshReductionUI()
