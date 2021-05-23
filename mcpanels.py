import bpy
from mccolutils import *
from mcutils import *

# Poll functions

@classmethod
def mc_panel_poll(cls, context):
    
    settings = bpy.context.scene.mc_settings
    if settings.em_fixobj:
        obj = settings.em_fixobj_pointer
    else:
        obj = context.active_object
    
    return obj.mc_enable

# User Interface Panels

class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Menu"

class PT_MenuCreator_InitialConfiguration_Panel(MainPanel, bpy.types.Panel):
    bl_idname = "PT_MenuCreator_InitialConfiguration_Panel"
    bl_label = "Initial Configuration"
    
    @classmethod
    def poll(cls, context):
    
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        if obj is not None:
            return not obj.mc_enable
        else:
            return False
    
    def draw(self, context):
        
        layout = self.layout
        
        layout.label(text="Menu Configuration")
        
        layout.operator('mc.initialconfig', text="Create Menu")

class PT_MenuCreator_Panel(MainPanel, bpy.types.Panel):
    bl_idname = "PT_MenuCreator_Panel"
    bl_label = "Menu"
    
    @classmethod
    def poll(cls, context):
    
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
    
        if obj is not None:
            return obj.mc_enable
        else:
            return False

    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        mc_col = obj.mc_properties
        mcs_col = obj.mc_sections
        mc_col_len = mc_len_collection(mc_col)
        mcs_col_len = mc_len_collection(mcs_col)
        
        layout = self.layout
        
        row = layout.row(align=False)
        menu_name = settings.mss_name;
        if settings.mss_obj_name:
            menu_name = menu_name+obj.name
        row.label(text=menu_name)
        
        if settings.ms_editmode:
            row.prop(obj, "mc_edit_enable", text="",icon="MODIFIER")
            row.operator("mc.addsection",text="",icon="ADD")
            if settings.em_fixobj:
                row.prop(settings,"em_fixobj",icon="PINNED", text="")
            else:
                row.prop(settings,"em_fixobj",icon="UNPINNED", text= "")
        else:
            if settings.em_fixobj:
                row.prop(settings,"em_fixobj",icon="PINNED", text="")
            else:
                row.prop(settings,"em_fixobj",icon="UNPINNED", text= "")
        
        if mcs_col_len>1:
            
            for sec in sorted(mcs_col, key = mc_sec_ID):
                
                if sec.type == "DEFAULT":
                
                    sec_empty = True
                    sec_hidden = True
                    for el in mc_col:
                        if el.section == sec.name:
                            sec_empty = False
                            if not el.hide:
                                sec_hidden = False
                    
                    if (sec_empty and sec.name == "Unsorted") or (not obj.mc_edit_enable and not sec_empty and sec_hidden):
                        continue
                    else:
                        row = layout.row(align=False)
                        if sec.collapsable:
                            row.prop(sec, "collapsed", icon="TRIA_DOWN" if not sec.collapsed else "TRIA_RIGHT", icon_only=True, emboss=False)
                        if sec.icon == "NONE":
                            row.label(text=sec.name)
                        else:
                            row.label(text=sec.name,icon=sec.icon)
                        
                        if obj.mc_edit_enable:
                            
                            if sec.name != "Unsorted":
                                ssett_button = row.operator("mc.sectionsettings", icon="PREFERENCES", text="")
                                ssett_button.name = sec.name
                                ssett_button.icon = sec.icon
                                ssett_button.type = sec.type
                            
                                row2 = row.row(align=True)
                                sup_button = row2.operator("mc.swapsections", icon="TRIA_UP", text="")
                                sup_button.mod = True
                                sup_button.name = sec.name
                                sup_button.icon = sec.icon
                                sdown_button = row2.operator("mc.swapsections", icon="TRIA_DOWN", text="")
                                sdown_button.mod = False
                                sdown_button.name = sec.name
                                sdown_button.icon = sec.icon
                        
                        if not sec.collapsed:
                            box = layout.box()
                            if sec_empty and sec.name != "Unsorted":
                                row = box.row(align=False)
                                row.label(text="Section Empty", icon="ERROR")
                                row.operator("mc.deletesection",text="",icon="X").name = sec.name
                    
                    if not sec.collapsed:
                        
                        for el in sorted(mc_col, key = mc_prop_ID):
                            
                            if el.section == sec.name:
                            
                                el_index = mc_find_index(mc_col,[el.name,el.path,el.id])
                                
                                if obj.mc_edit_enable:
                                    
                                    row = box.row(align=False)
                                    if el.icon !="NONE":
                                        row.label(text=el.name,icon=el.icon)
                                    else:
                                        row.label(text=el.name)
                                    
                                    sett_button = row.operator("mc.propsettings", icon="PREFERENCES", text="")
                                    sett_button.name = el.name
                                    sett_button.path = el.path
                                    sett_button.id = el.id
                                    sett_button.icon = el.icon
                                    sett_button.section = el.section
                                    
                                    row2 = row.row(align=True)
                                    up_button = row2.operator("mc.swapprops", icon="TRIA_UP", text="")
                                    up_button.mod = True
                                    up_button.name = el.name
                                    up_button.path = el.path
                                    up_button.id = el.id
                                    down_button = row2.operator("mc.swapprops", icon="TRIA_DOWN", text="")
                                    down_button.mod = False
                                    down_button.name = el.name
                                    down_button.path = el.path
                                    down_button.id = el.id
                                    
                                    if el.hide:
                                        row.prop(el, "hide", text="", icon = "HIDE_ON")
                                    else:
                                        row.prop(el, "hide", text="", icon = "HIDE_OFF")
                                    
                                    del_button = row.operator("mc.removeproperty", icon="X", text="")
                                    del_button.path = el.path
                                    del_button.id = el.id
                                else:
                                    
                                    if not el.hide:
                                        row = box.row(align=False)
                                        if el.icon !="NONE":
                                            row.label(text=el.name,icon=el.icon)
                                        else:
                                            row.label(text=el.name)
                                    
                                        row.scale_x=1.0
                                        row.prop(eval(el.path), el.id, text="")
                    
                elif sec.type == "COLLECTION":
                    
                    sec_empty = True
                    for el in sec.collections:
                        sec_empty = False
                        break
                    
                    row = layout.row(align=False)
                    if sec.collapsable:
                        row.prop(sec, "collapsed", icon="TRIA_DOWN" if not sec.collapsed else "TRIA_RIGHT", icon_only=True, emboss=False)
                    if sec.icon == "NONE":
                        row.label(text=sec.name)
                    else:
                        row.label(text=sec.name,icon=sec.icon)
                        
                    if obj.mc_edit_enable:
                        
                        ssett_button = row.operator("mc.sectionsettings", icon="PREFERENCES", text="")
                        ssett_button.name = sec.name
                        ssett_button.icon = sec.icon
                        ssett_button.type = sec.type
                        
                        row2 = row.row(align=True)
                        sup_button = row2.operator("mc.swapsections", icon="TRIA_UP", text="")
                        sup_button.mod = True
                        sup_button.name = sec.name
                        sup_button.icon = sec.icon
                        sdown_button = row2.operator("mc.swapsections", icon="TRIA_DOWN", text="")
                        sdown_button.mod = False
                        sdown_button.name = sec.name
                        sdown_button.icon = sec.icon
                        
                        row.operator("mc.deletesection",text="",icon="X").name = sec.name
                        
                        if not sec.collapsed and len(sec.collections)>0:
                            box = layout.box()
                            if sec.outfit_enable:
                                box.prop(sec,"outfit_body", text="Body", icon="OUTLINER_OB_MESH")
                            
                            if len(sec.collections)>0:
                                box.label(text="Collection List", icon="OUTLINER_COLLECTION")
                                box = box.box()
                                for collection in sec.collections:
                                    row = box.row()
                                    row.label(text=collection.collection.name)
                                    del_col = row.operator("mc.deletecollection",text="",icon="X")
                                    del_col.sec = sec.name
                                    del_col.col = collection.collection.name
                                    
                    else:
                        if not sec.collapsed:
                            box = layout.box()
                            if sec_empty:
                                row = box.row(align=False)
                                row.label(text="No Collection Assigned", icon="ERROR")
                                row.operator("mc.deletesection",text="",icon="X").name = sec.name
                            
                            if len(sec.collections)>0:
                                box.prop(sec,"collections_list", text="")
                                box2 = box.box()
                                if len(bpy.data.collections[sec.collections_list].objects)>0:
                                    for obj2 in bpy.data.collections[sec.collections_list].objects:
                                        row = box2.row()
                                        if obj2.hide_viewport:
                                            vop=row.operator("mc.colobjvisibility",text=obj2.name, icon='OUTLINER_OB_'+obj2.type)
                                            vop.obj = obj2.name
                                            vop.sec = sec.name
                                        else:
                                            vop = row.operator("mc.colobjvisibility",text=obj2.name, icon='OUTLINER_OB_'+obj2.type, depress = True)
                                            vop.obj = obj2.name
                                            vop.sec = sec.name
                                else:
                                    box2.label(text="This Collection seems empty", icon="ERROR")
                                
                                if sec.collections_enable_global_smoothcorrection or sec.collections_enable_global_shrinkwrap or sec.collections_enable_global_mask or sec.collections_enable_global_normalautosmooth:
                                    box.label(text= "Global Properties", icon="MODIFIER")
                                    box2 = box.box()
                                    if sec.collections_enable_global_smoothcorrection:
                                        box2.prop(sec,"collections_global_smoothcorrection")
                                    if sec.collections_enable_global_shrinkwrap:
                                        box2.prop(sec,"collections_global_shrinkwrap")
                                    if sec.collections_enable_global_mask:
                                        box2.prop(sec,"collections_global_mask")
                                    if sec.collections_enable_global_normalautosmooth:
                                        box2.prop(sec,"collections_global_normalautosmooth")
                                                
        else:
            box = layout.box()
            box.label(text="No section added.",icon="ERROR")
                

class PT_MenuCreator_Settings_Panel(MainPanel, bpy.types.Panel):
    bl_idname = "PT_MenuCreator_Settings_Panel"
    bl_label = "Settings"
    
    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        
        layout = self.layout
        
        # Main Settings
        layout.label(text="Main Settings",icon="SETTINGS")
        box = layout.box()
        
        box.prop(settings,"ms_editmode")
        box.prop(settings,"ms_debug")
        box.prop(settings,"ms_advanced")
        
        # Menu specific settings
        layout.label(text="Menu Settings",icon="SETTINGS")
        box = layout.box()
        
        box.prop(settings,"mss_name")
        box.prop(settings,"mss_obj_name")
        
        layout.label(text="Reset functions",icon="SETTINGS")
        box = layout.box()
        
        box.operator('mc.cleanpropobj', text="Reset Object", icon="ERROR").reset = True
        box.operator('mc.cleanprop', text="Reset All Objects", icon="ERROR").reset = True

classes = (
    PT_MenuCreator_InitialConfiguration_Panel,
    PT_MenuCreator_Panel,
    PT_MenuCreator_Settings_Panel
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)