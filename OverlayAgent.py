import bpy
from mathutils import Vector
import gpu
from bgl import *
from gpu_extras.batch import batch_for_shader

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
    
renderShape("RECT", (Vector((500,0)), Vector((800,300))), 0)