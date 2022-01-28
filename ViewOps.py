bl_info = {
    "name": "Touch Viewport",
    "blender": (2, 80, 0),
    "category": "View 3D",
}

import bpy
import math
from mathutils import Vector
import gpu
from bgl import *
from gpu_extras.batch import batch_for_shader

class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ViewOps"
    
class PanelOne(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_test_1"
    bl_label = "Viewport Settings"

    def draw(self, context):
        self.layout.label(text="Control Zones")
        row = self.layout.row()
        
        self.layout.prop(context.window_manager, "dolly_wid")
        self.layout.prop(context.window_manager, "pan_rad")
    

class TouchInput(bpy.types.Operator):
    bl_idname = "view3d.view_ops"
    bl_label = "Viewport Control Regions"
    
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
            bpy.ops.view3d.rotate('INVOKE_DEFAULT')
        elif self.mode == "PAN":
            bpy.ops.view3d.move('INVOKE_DEFAULT')
        elif self.mode == "DOLLY":
            bpy.ops.view3d.dolly('INVOKE_DEFAULT')
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.delta = Vector((event.mouse_region_x, event.mouse_region_y))
        mid_point = self.getMidPoint(context.area)
        dolly_scale = context.window_manager.dolly_wid
        pan_scale = context.window_manager.pan_rad
        
        dolly_wid = mid_point.y * dolly_scale
        pan_diameter = math.dist((0,0), mid_point) * (pan_scale*0.4)
        
        if dolly_wid > self.delta.x or self.delta.x > context.area.width-dolly_wid:
            self.mode = "DOLLY"
        elif math.dist(self.delta, mid_point) < pan_diameter:
            self.mode = "PAN"
        else:
            self.mode = "ORBIT"
        
        self.execute(context)
        return {'FINISHED'}
        
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'
    
    def getArea(self, area):
        return Vector(( area.width, area.height))
    
    def getMidPoint(self, area):
        return self.getArea(area)/2

    
#########################################
### BEGIN DRAW SCRIPT
#########################################    
# import bpy
# from mathutils import Vector
# import gpu
# from bgl import *
# from gpu_extras.batch import batch_for_shader

class OverlayAgent:
    objects = []

    def drawVectorBox(a, b, color):
        vertices = (
            (a.x,a.y),(b.x,a.y),
            (a.x,b.y),(b.x,b.y)
        )
        indices = ((0, 1, 2), (2, 3, 1))
        
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        glEnable(GL_BLEND)
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
        glDisable(GL_BLEND)

    def renderShape(shape, coords, color):
        # create draw call
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            drawVectorBox, 
            (coords[0],coords[1], (0, 0.5, 0.5, 0.10)), 
            'WINDOW', 
            'POST_PIXEL'
        )
        bpy.context.area.tag_redraw()
        
        # remove draw call and clear objects
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        
    ## need to add functionality to track draw handlers 
    ##    and monitor sources for change to invoke tag_redraw()
 
#########################################
### END DRAW SCRIPT
#########################################

addon_keymaps = []

def register():
    bpy.utils.register_class(TouchInput)
    bpy.types.WindowManager.dolly_wid = bpy.props.FloatProperty(
        name="Rail Width", 
        default=0.4, 
        min=0.1, 
        max=1
    )
    bpy.types.WindowManager.pan_rad = bpy.props.FloatProperty(
        name="Center Radius", 
        default=0.35, 
        min=0.1, 
        max=1.0
    )
    bpy.utils.register_class(PanelOne)
    
    #view_center_pick
    #view_center_cursor
    #view_center_lock
    #view_lock_to_active
    #view_lock_clear
    
    wm = bpy.context.window_manager    
    km = wm.keyconfigs.addon.keymaps.new(name='', space_type='EMPTY')
    kmi = km.keymap_items.new('view3d.view_ops', 'MIDDLEMOUSE', 'PRESS')
    addon_keymaps.append((km, kmi)) 
    km = wm.keyconfigs.addon.keymaps.new(name='Sculpt', space_type='EMPTY')
    kmi = km.keymap_items.new('view3d.view_ops', 'LEFTMOUSE', 'PRESS')
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'PEN', 'PRESS')
    kmi.properties.mode = "NORMAL"
    addon_keymaps.append((km, kmi))
    
    kmi = km.keymap_items.new('sculpt.brush_stroke', 'ERASER', 'PRESS')
    kmi.properties.mode = "INVERT"
    addon_keymaps.append((km, kmi))

def unregister():
    bpy.utils.unregister_class(TouchInput)
    bpy.utils.unregister_class(PanelOne)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    

if __name__ == "__main__":
    register()