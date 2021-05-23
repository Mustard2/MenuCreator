import bpy
import mcops

class WM_MT_button_context(bpy.types.Menu):
    bl_label = "Custom Action"

    def draw(self, context):
        pass

def menu_func(self, context):
    
    if hasattr(context, 'button_prop'):
        layout = self.layout
        layout.separator()
        layout.operator(mcops.MC_AddProperty.bl_idname)
        
def menu_func_link(self, context):
    
    if hasattr(context, 'button_prop'):
        layout = self.layout
        #layout.label(text="Try")
        self.layout.menu(OUTLINER_MT_link_mcmenu.bl_idname)

class OUTLINER_MT_collection(bpy.types.Menu):
    bl_label = "Custom Action Collection"

    def draw(self, context):
        pass

# Operator to create the list of sections when right clicking on the property -> Link to property
class OUTLINER_MT_link_mcmenu(bpy.types.Menu):
    bl_idname = 'mc.menu_link'
    bl_label = 'Link to Property'

    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        layout = self.layout
        
        no_prop = True
        for prop in obj.mc_properties:
            op = layout.operator(mcops.MC_LinkProperty.bl_idname, text=prop.name, icon=prop.icon)
            op.prop_id = prop.id
            op.prop_path = prop.path
            no_prop = False
        
        if no_prop:
            layout.label(text="No properties found")

# Operator to create the list of sections when right clicking on the collection -> Add collection to Section
class OUTLINER_MT_collection_mcmenu(bpy.types.Menu):
    bl_idname = 'mc.menu_collection'
    bl_label = 'Add Collection to Section'

    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        layout = self.layout
        
        no_col_sec = True
        for sec in obj.mc_sections:
            if sec.type == "COLLECTION":
                layout.operator(mcops.MC_AddCollection.bl_idname, text=sec.name, icon=sec.icon).section = sec.name
                no_col_sec = False
        
        if no_col_sec:
            layout.label(text="No Collection List sections found")

def mc_collection_menu(self, context):
    self.layout.separator()
    self.layout.menu(OUTLINER_MT_collection_mcmenu.bl_idname)

classes = (
    WM_MT_button_context,
    OUTLINER_MT_link_mcmenu,
    OUTLINER_MT_collection_mcmenu
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WM_MT_button_context.append(menu_func)
    bpy.types.WM_MT_button_context.append(menu_func_link)
    bpy.types.OUTLINER_MT_collection.append(mc_collection_menu)

def unregister():
    bpy.types.WM_MT_button_context.remove(menu_func)
    bpy.types.WM_MT_button_context.remove(menu_func_link)
    bpy.types.OUTLINER_MT_collection.remove(mc_collection_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
