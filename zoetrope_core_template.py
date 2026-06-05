"""
This is an example of what your core script should look like before you upload it to GitHub.
It must have a register() and unregister() function at the bottom.

If you are using collision_detector.py, you can just upload it as-is, as it already has register() and unregister().
"""

import bpy

class ZOETROPE_OT_example_operator(bpy.types.Operator):
    bl_idname = "zoetrope.example_operator"
    bl_label = "Example Zoetrope Action"
    
    def execute(self, context):
        self.report({'INFO'}, "Core script executed!")
        return {'FINISHED'}

classes = (
    ZOETROPE_OT_example_operator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
