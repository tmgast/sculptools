bl_info = {
    "name": "Quick Retopology",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy

class QuickRetopo(bpy.types.Operator):
    """Auto retopologize"""            # Use this as a tooltip for menu items and buttons.
    bl_idname = "sculpt.quick_retop"   # Unique identifier for buttons and menu items to reference.
    bl_label = "Quick Retopologize"    # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.
    
    level: bpy.props.IntProperty(name="Level", default=1, min=1, max=10)
    base: bpy.props.FloatProperty(name="Base", default=0.250, min=0.100, max=0.500)

    def execute(self, context):        # execute() is called when running the operator.

        # The original script
        context.object.data.remesh_voxel_size = self.base / self.level
        bpy.ops.object.voxel_remesh()
        
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.


classes=[QuickRetopo]
addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Sculpt', space_type='EMPTY')
    kmi = km.keymap_items.new('sculpt.quick_retop', 'ONE', 'PRESS')
    kmi.properties.level = 1
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.quick_retop', 'TWO', 'PRESS')
    kmi.properties.level = 3
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.quick_retop', 'THREE', 'PRESS')
    kmi.properties.level = 5
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.quick_retop', 'FOUR', 'PRESS')
    kmi.properties.level = 8
    addon_keymaps.append((km, kmi))
        
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()