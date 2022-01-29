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
from gpu_extras.presets import draw_circle_2d
from bpy.app.handlers import persistent

class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ViewOps"
    
class PanelOne(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_view_ops"
    bl_label = "Viewport Settings"

    def draw(self, context):
        self.layout.label(text="Control Zones")
        row = self.layout.row()
        self.layout.prop(context.window_manager, "dolly_wid")
        self.layout.prop(context.window_manager, "pan_rad")
        row = self.layout.row()
        self.layout.prop(context.window_manager, "con_overlay")
    

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
        
        dolly_wid = mid_point.x * dolly_scale
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
def update_overlay(self, context):
    if self == "NONE": self = overlay_manager
    if context.area == None: context = bpy.context
    clear_overlays(self, context)
    wm = context.window_manager
    if wm.con_overlay:
        dolly_scale = wm.dolly_wid
        view_width = context.area.width
        view_half_wd = view_width/2
        view_half_ht = context.area.height/2
        pan_diameter = math.dist((0,0), (view_half_wd, view_half_ht)) * (wm.pan_rad*0.4)
        
        left_rail = (
            Vector((0.0,0.0)), 
            Vector((view_width/2*dolly_scale, context.area.height))
        )
        right_rail = (
            Vector((view_width,0.0)), 
            Vector((view_width - view_width/2*dolly_scale, context.area.height))
        )
        mid_ring = (
            Vector((view_half_wd, view_half_ht)),
            pan_diameter
        )
        overlay_manager.renderShape(
            "left_rail",
            "RECT",
            left_rail,
            (0,0.5,0.5,0.10)
        )
        overlay_manager.renderShape(
            "right_rail",
            "RECT",
            right_rail,
            (0,0.5,0.5,0.10)
        )
        overlay_manager.renderShape(
            "mid_ring",
            "CIRC",
            mid_ring,
            (00.5,0.2,0.2,0.10)
        )
            
def clear_overlays(self, context):
    overlays = ["left_rail","right_rail","mid_ring"]
    for ov in overlays:
        overlay_manager.clearOverlay(ov)

class OverlayAgent:
    def __init__(self):
        self.objects = []
        bpy.app.timers.register(self.run_10_times)

    def run_10_times(self):
        counter=0
        if counter == 10:
            return None
        
        update_overlay(self, bpy.context)
        return 0.1

    def drawVectorBox(self, a, b, color):
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
    
    def drawVectorCircle(self, mid, rad, color):
        segments = 100
        vertices = [Vector(mid)]
        indices = []
        for p in range(segments):
            if p > 0:
                point = Vector((
                    mid.x + rad * math.cos(math.radians(360/segments)*p),
                    mid.y + rad * math.sin(math.radians(360/segments)*p)
                ))
                vertices.append(point)
                indices.append((0,p-1, p))
        indices.append((0,1, p))
        
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        glEnable(GL_BLEND)
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
        glDisable(GL_BLEND)


    def renderShape(self, name, shape, args, color):
        # create draw call
        if shape == "RECT":
            _handle = bpy.types.SpaceView3D.draw_handler_add(
                self.drawVectorBox, 
                (args[0],args[1], color), 
                'WINDOW', 
                'POST_PIXEL'
            )
        elif shape == "CIRC":
            _handle = bpy.types.SpaceView3D.draw_handler_add(
                self.drawVectorCircle, 
                (args[0],args[1], color), 
                'WINDOW', 
                'POST_PIXEL'
            )
            
        bpy.context.area.tag_redraw()
        self.objects.append((name, _handle))
        
        # remove draw call and clear objects
    def clearOverlay(self, name):
        # search for overlay
        _handlers = [item for item in self.objects if item[0] == name]

        #remove if found
        for element in _handlers:
            bpy.types.SpaceView3D.draw_handler_remove(element[1], 'WINDOW')
            self.objects.remove(element)
            
        viewports = []
        for area in bpy.context.window.screen.areas:
            if area.type == "VIEW_3D":
                viewports.append(area)
    
    def clearAll(self):
        for element in self.objects:
            bpy.types.SpaceView3D.draw_handler_remove(element[1], 'WINDOW')
            bpy.context.area.tag_redraw()
            self.objects.remove(element)
            
@persistent
def handle_vp_change(self, context, *args):
    print(args[0])
    


    ## NEED TO TEST
#@persistent
#def load_handler(dummy):
#    print("Load Handler:", bpy.data.filepath)

    ## need to add functionality to track draw handlers 
    ##    and monitor sources for change to invoke tag_redraw()
 
#########################################
### END DRAW SCRIPT
#########################################

overlay_manager = OverlayAgent()
addon_keymaps = []

def register():
    wm = bpy.context.window_manager    
    bpy.utils.register_class(TouchInput)
    bpy.types.WindowManager.dolly_wid = bpy.props.FloatProperty(
        name="Rail Width", 
        default=0.4, 
        min=0.1, 
        max=1,
        update=update_overlay
    )
    bpy.types.WindowManager.pan_rad = bpy.props.FloatProperty(
        name="Center Radius", 
        default=0.35, 
        min=0.1, 
        max=1.0,
        update=update_overlay
    )
    bpy.types.WindowManager.con_overlay = bpy.props.BoolProperty(
        name="Show Overlay", 
        default=False,
        update=update_overlay
    )

#    bpy.app.handlers.load_post.append(load_handler)
    bpy.utils.register_class(PanelOne)
    
    #view_center_pick
    #view_center_cursor
    #view_center_lock
    #view_lock_to_active
    #view_lock_clear
    
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
    overlay_manager.clearAll()
    bpy.utils.unregister_class(TouchInput)
    bpy.utils.unregister_class(PanelOne)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    

if __name__ == "__main__":
    register()