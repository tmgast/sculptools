bl_info = {
    "name":"TouchView",
    "author":"Terri Gast",
    "version":(1,0),
    "blender":(2,80,0),
    "location":"view3d > Tool",
    "warning":"",
    "wiki_url":"",
    "category":"View 3D"
}

import bpy

class TouchView(bpy.types.Panel):
    bl_label = "Test Panel"
    bl_idname = "PT_TouchView"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Touch View"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text= "Sample Text", icon= "CUBE")
        
        
def register():
    bpy.utils.register_class(TouchView)
    
    
def unregister():
    bpy.utils.unregister_class(TouchView)
    

if __name__ == "__main__":
    register()