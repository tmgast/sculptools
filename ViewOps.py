bl_info = {
    "name": "Touch Viewport",
    "blender": (2, 80, 0),
    "category": "View 3D",
}

import bpy
import math
from mathutils import Vector
import gpu
import bgl
from gpu_extras.batch import batch_for_shader    

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
        dolly_scale = context.area.ov.dolly_wid
        pan_scale = context.area.ov.pan_rad
        
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

###
### NEED REWRITE TO USE TIMER AND UPDATE SCREEN AREAS
###    ONLY IF SHOW OVERLAY IS ON
###
class Overlay:
    def __init__(self, area):
        self.area = area
        self.pointer = str(area.as_pointer())
        overlays = []
    
        wm = bpy.types.WindowManager.viewops_conf
        wm[self.pointer+"dolly_wid"]: bpy.props.FloatProperty(
            name="Rail Width", 
            default=0.4, 
            min=0.1, 
            max=1
        )
        wm[self.pointer+"pan_rad"]: bpy.props.FloatProperty(
            name="Center Radius", 
            default=0.35, 
            min=0.1, 
            max=1.0
        )
        wm[self.pointer+"isVisible"]: bpy.props.BoolProperty(
            name="Show Overlay", 
            default=False
        )
        
    def get(self, attr):
        wm = bpy.types.WindowManager.viewops_conf
        return wm[self.pointer+attr]

    def add_overlay(self, overlay):
        self.overlays.append(overlay)

    def clear_overlays(self):
        for ol in self.overlays:
            bpy.types.SpaceView3D.draw_handler_remove(ol, 'WINDOW')
        self.overlays = []

class OverlayAgent:
    def __init__(self):
        bpy.app.timers.register(self.refresh_overlays)
        self.views = []
        
    def indexView(self, area):
        ao = (area, Overlay(area))
        self.views.append(ao)
        return ao
    
    def findView(self, view):
        for area, overlay in self.views:
            if area == view: return (area, overlay)
        return False

    def refresh_overlays(self):
        self.update_overlay()
        return None

    def init_viewport(self, view):
        ao = self.findView(view)
        if ao == False: return self.indexView(view)
        return ao

    def update_overlay(self):
        self.clearAll()

        # find/register all viewports
        for area in bpy.context.window.screen.areas.values():
            if area.type != "VIEW_3D": continue
            a, ov = self.init_viewport(area)

            if ov.get("isVisible"):
                wd = area.width
                ht = area.height
                print(ov.get("pan_rad"))
                pan_diameter = math.dist((0,0), (wd/2, ht/2)) * (ov.get("pan_rad") * 0.4)
                
                left_rail = (
                    Vector((0.0,0.0)), 
                    Vector((wd/2*ov.get("dolly_wid"), ht))
                )
                right_rail = (
                    Vector((wd,0.0)), 
                    Vector((wd - wd/2*ov.get("dolly_wid"), ht))
                )
                mid_ring = (
                    Vector((wd/2, ht/2)),
                    pan_diameter
                )
                area.ov.add_overlay(
                    overlay_manager.renderShape(
                        "left_rail", "RECT", left_rail, (0,0.5,0.5,0.10)
                ))
                area.ov.add_overlay(
                    overlay_manager.renderShape(
                        "right_rail",
                        "RECT",
                        right_rail,
                        (0,0.5,0.5,0.10)
                ))
                area.ov.add_overlay(
                    overlay_manager.renderShape(
                        "mid_ring",
                        "CIRC",
                        mid_ring,
                        (00.5,0.2,0.2,0.10)
                ))

    def clearAll(self):
        for area in bpy.context.window.screen.areas.values():
            if area.type != "VIEW_3D": continue
            if not hasattr(area.spaces.data, "ov"): continue
            area.spaces.data.ov.clear_overlays()
            area.tag_redraw()

    def renderShape(self, name, shape, args, color):
        # create draw call
        if shape == "CIRC":
            _handle = bpy.types.SpaceView3D.draw_handler_add(
                self.drawVectorCircle, 
                (args[0],args[1], color), 
                'WINDOW', 
                'POST_PIXEL'
            )
        elif shape == "RECT":
            _handle = bpy.types.SpaceView3D.draw_handler_add(
                self.drawVectorBox, 
                (args[0],args[1], color), 
                'WINDOW', 
                'POST_PIXEL'
            )
        else:
            return {"INVALID_SHAPE"}
            
        bpy.context.area.tag_redraw()
        return _handle

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
        p = 0
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

overlay_manager = OverlayAgent()

    ## NEED TO TEST
#@persistent
#def load_handler(dummy):
#    print("Load Handler:", bpy.data.filepath)

    ## need to add functionality to track draw handlers 
    ##    and monitor sources for change to invoke tag_redraw()
 
#########################################
### END DRAW SCRIPT
#########################################

class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ViewOps"
    
class PanelOne(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_view_ops"
    bl_label = "Viewport Settings"

    def draw(self, context):
        overlay_manager.update_overlay()
        a, ov = overlay_manager.findView(context.area)
        self.layout.label(text="Control Zones")
        row = self.layout.row()
        self.layout.prop(a.spaces.data, "dolly_wid")
        row = self.layout.row()
        self.layout.prop(a.spaces.data, "pan_rad")
        row = self.layout.row()
        self.layout.prop(a.spaces.data, "isVisible", text="Show Overlay")

addon_keymaps = []

def register():
    wm = bpy.context.window_manager   
    bpy.types.WindowManager.viewops_conf = {}
    bpy.utils.register_class(TouchInput)

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
