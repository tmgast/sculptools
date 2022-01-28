bl_info = {
    "name": "Touch Viewport",
    "blender": (2, 80, 0),
    "category": "View 3D",
}

import bpy
import mathutils

class TouchInput(bpy.types.Operator):
    bl_idname = "view3d.touch_view"
    bl_label = "Touch View"
    
    mode: bpy.props.EnumProperty(
        name="Mode", 
        description="Sets the viewport control type",
        items={
            ('ORBIT','rotate','Rotate the viewport'),
            ('PAN','pan','Move the viewport'),
            ('DOLLY','zoom','Zoom in/out the viewport')
        },
        default="ORBIT")

    def execute(self, context):
        if self.mode == "ORBIT":
            bpy.ops.view3d.view_orbit(angle=self.delta.x/180, type="ORBITRIGHT")
            bpy.ops.view3d.view_orbit(angle=self.delta.y/180, type="ORBITUP")
        elif self.mode == "PAN":
            if self.delta.y > 0:
                bpy.ops.view3d.view_pan("INVOKE_REGION_WIN",type="PANUP")
            if self.delta.y < 0:
                bpy.ops.view3d.view_pan("INVOKE_REGION_WIN",type="PANDOWN")
            if self.delta.x > 0:
                bpy.ops.view3d.view_pan("INVOKE_REGION_WIN",type="PANRIGHT")
            if self.delta.x < 0:
                bpy.ops.view3d.view_pan("INVOKE_REGION_WIN",type="PANLEFT")
        elif self.mode == "DOLLY":
            bpy.ops.view3d.dolly()
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':  # Apply
            #print(event.id_data)
            self.delta.x = (event.mouse_prev_x - event.mouse_x)
            self.delta.y = (event.mouse_prev_y - event.mouse_y)
            self.execute(context)
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':  # Confirm
            return {'FINISHED'}
        elif event.type == 'ESC':  # Cancel\
            return {'CANCELLED'}
        elif event.type not in {'INBETWEEN_MOUSEMOVE', 'TIMER_REPORT'}:
            print(event.type, event.value)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.delta = mathutils.Vector((0.0,0.0))
        self.mode = "PAN"
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'

addon_keymaps = []

def register():
    bpy.utils.register_class(TouchInput)
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='', space_type='EMPTY')
    kmi = km.keymap_items.new('view3d.touch_view', 'LEFTMOUSE', 'PRESS')
    addon_keymaps.append((km, kmi))
    
    km = wm.keyconfigs.addon.keymaps.new(name='Sculpt', space_type='EMPTY')
    kmi = km.keymap_items.new('view3d.touch_view', 'LEFTMOUSE', 'PRESS')
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'PEN', 'PRESS')
    kmi.properties.mode = "NORMAL"
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'ERASER', 'PRESS')
    kmi.properties.mode = "INVERT"
    addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(TouchInput)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    

if __name__ == "__main__":
    register()