import bpy
from . import mcdata
from .mcutils import *
from .mccolutils import *

# Operator to add the right click button on properties
class MC_AddProperty(bpy.types.Operator):
    """Add the property to the menu"""
    bl_idname = "mc.add_property"
    bl_label = "Add property to Menu"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        #if hasattr(context, 'button_pointer'):
        #    btn = context.button_pointer 
        #    dump(btn, 'button_pointer')

        if hasattr(context, 'button_prop'):
            prop = context.button_prop
            #dump(prop, 'button_prop')
            
            try:
                bpy.ops.ui.copy_data_path_button(full_path=True)
            except:
                self.report({'WARNING'}, 'Menu Creator - Invalid selection.')
                return {'FINISHED'}
            
            rna, path = split_path(context.window_manager.clipboard)
            
            if obj.mc_enable:
            
                if mc_add_property_item(obj.mc_properties, [prop.name,rna,path]):
                    self.report({'INFO'}, 'Menu Creator - Property added to the \'' + obj.name + '\' menu.')
                else:
                    self.report({'WARNING'}, 'Menu Creator - Property of \'' + obj.name + '\' was already added.')
            
            else:
                self.report({'ERROR'}, 'Menu Creator - Can not add property \'' + obj.name + '\'. No menu has been initialized.')

        #if hasattr(context, 'button_operator'):
        #    op = context.button_operator
        #    dump(op, 'button_operator')     

        return {'FINISHED'}

# Operator to link a property to another one
class MC_LinkProperty(bpy.types.Operator):
    """Link the selected property to this one"""
    bl_idname = "mc.link_property"
    bl_label = "Link Property"
    
    prop_id: bpy.props.StringProperty()
    prop_path: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object

        if hasattr(context, 'button_prop'):
            prop = context.button_prop
            #dump(prop, 'button_prop')
            
            try:
                bpy.ops.ui.copy_data_path_button(full_path=True)
            except:
                self.report({'WARNING'}, 'Menu Creator - Invalid selection.')
                return {'FINISHED'}
            
            rna, path = split_path(context.window_manager.clipboard)
            
            if obj.mc_enable:
        
                i = mc_find_index(obj.mc_properties, ['',self.prop_path,self.prop_id])
                
                prop_type = type(eval(obj.mc_properties[i].path + '.' + obj.mc_properties[i].id))
                if '].[' in rna + '.' + path:
                    link_type = type(eval(rna + path))
                else:
                    link_type = type(eval(rna + '.' + path))
                
                if prop_type == link_type:
                
                    already_added = False
                    for el in obj.mc_properties[i].linked_props:
                        if el.path == rna and el.id == path:
                            already_added = True
                            break    
                    if not already_added:    
                        add_item = obj.mc_properties[i].linked_props.add()
                        add_item.id = path
                        add_item.path = rna
                
                        self.report({'INFO'}, 'Menu Creator - Property \'' + path + '\' linked to \'' + obj.mc_properties[i].name + '\'')
                    else:
                        self.report({'WARNING'}, 'Menu Creator - Property \'' + path + '\' already linked to \'' + obj.mc_properties[i].name + '\'')
                    
                else:
                    self.report({'ERROR'}, 'Menu Creator - Property \'' + path + '\' can not be linked to \'' + obj.mc_properties[i].name + '\'')
                    if settings.ms_debug:
                        print('MenuCreator - Property \'' + path + '\' can not be linked to \'' + obj.mc_properties[i].name + '\'')
                        print('              Data types are ' + str(link_type) + ' and ' + str(prop_type) + '.')
            
            else:
                self.report({'ERROR'}, 'Menu Creator - Can not link property in \'' + obj.name + '\'. No menu has been initialized.') 

        return {'FINISHED'}

# Operator to add the collection to the selected section
class MC_AddCollection(bpy.types.Operator):
    """Add the collection to the selected section"""
    bl_idname = "mc.add_collection"
    bl_label = "Add collection to Menu"
    
    section: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        add_coll = bpy.context.collection
        
        sec_index = mc_find_index_section(obj.mc_sections, self.section)

        i=True
        for el in obj.mc_sections[sec_index].collections:
            if el.collection == add_coll:
                i=False
                break
        if i:
            add_item = obj.mc_sections[sec_index].collections.add()
            add_item.collection = add_coll
            self.report({'INFO'}, 'Menu Creator - Collection has been added to section \''+self.section+'\'.')
        else:
            self.report({'WARNING'}, 'Menu Creator - Collection was already added to section \''+self.section+'\'.')

        return {'FINISHED'}

# Operator to clean all properties and sections from all objects
class MC_CleanAll(bpy.types.Operator):
    """Clean all the menus.\nIf you choose reset, it will also delete all Menu options from all objects"""
    bl_idname = "mc.cleanprop"
    bl_label = "Clean all the properties"
    
    reset : bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        
        mc_clean_properties()
        mc_clean_sections()
        
        if self.reset:
            for obj in bpy.data.objects:
                obj.mc_enable = False
        
        self.report({'INFO'}, 'Menu Creator - All the objects has been reset.')
        
        return {'FINISHED'}

# Operator to clean all properties and sections from an objects. If reset is on, it will also disable the menu for that object
class MC_CleanObject(bpy.types.Operator):
    """Clean all the object properties.\nIf you choose reset, it will also delete all Menu options from the object"""
    bl_idname = "mc.cleanpropobj"
    bl_label = "Clean the object"
    
    reset : bpy.props.BoolProperty(default=False)
    
    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        mc_clean_single_properties(obj)
        mc_clean_single_sections(obj)
        if self.reset:
            obj.mc_enable = False
        
        self.report({'INFO'}, 'Menu Creator - \'' + obj.name + '\' menu has been reset.')
        
        return {'FINISHED'}

# Operator to remove a linked property (button in UI)
class MC_RemoveLinkedProperty(bpy.types.Operator):
    """Remove the linked property"""
    bl_idname = "mc.removelinkedproperty"
    bl_label = ""
    
    prop_index : bpy.props.IntProperty()
    link_path : bpy.props.StringProperty()
    link_id : bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        props = obj.mc_properties
        
        i=-1
        for el in obj.mc_properties[self.prop_index].linked_props:
            i=i+1
            if el.path == self.link_path and el.id == self.link_id:
                break
        if i>=0:
            obj.mc_properties[self.prop_index].linked_props.remove(i)

        return {'FINISHED'}

# Single Property settings
class MC_PropertySettings(bpy.types.Operator):
    """Modify some of the property settings"""
    bl_idname = "mc.propsettings"
    bl_label = "Property settings"
    bl_icon = "PREFERENCES"
    bl_options = {'UNDO'}
    
    name : bpy.props.StringProperty(name='Name',
        description="Choose the name of the property")
    path : bpy.props.StringProperty()
    id : bpy.props.StringProperty()
    icon : bpy.props.EnumProperty(name='Icon',
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon.",items=mcdata.mc_icon_list)
    section : bpy.props.EnumProperty(name='Section',
        description="Choose the section of the property",items=mc_section_list)

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        i = mc_find_index(obj.mc_properties,[self.name,self.path,self.id])
        
        if i>=0:
            obj.mc_properties[i].name = self.name
            obj.mc_properties[i].icon = self.icon
            obj.mc_properties[i].section = self.section
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        
        settings = bpy.context.scene.mc_settings
                
        if settings.ms_debug:
            return context.window_manager.invoke_props_dialog(self, width=650)
        else:
            return context.window_manager.invoke_props_dialog(self, width=550)
            
    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        i = mc_find_index(obj.mc_properties,[self.name,self.path,self.id])
        
        layout = self.layout
        
        layout.prop(self, "name")
        layout.prop(self, "icon")
        layout.prop(self, "section")
        
        layout.separator()
        layout.label(text="Property info", icon="INFO")
        box = layout.box()
        box.label(text="Identifier: "+self.id)
        
        if settings.ms_debug:
            layout.label(text="Full path", icon="RNA")
            box = layout.box()
            box.label(text=self.path+'.'+self.id)
        
        if len(obj.mc_properties[i].linked_props)>0:
            layout.separator()
            layout.label(text="Linked Properties", icon="LINKED")
            box = layout.box()
            for prop in obj.mc_properties[i].linked_props:
                row = box.row()
                row.label(text=prop.path + '.' + prop.id, icon="DOT")
                link_del_op = row.operator(MC_RemoveLinkedProperty.bl_idname, icon="X")
                link_del_op.prop_index = i
                link_del_op.link_id = prop.id
                link_del_op.link_path = prop.path
                

# Swap Properties Operator
class MC_SwapProperty(bpy.types.Operator):
    """Change the position of the property"""
    bl_idname = "mc.swapprops"
    bl_label = "Change the property position"
    
    mod : bpy.props.BoolProperty(default=False) # False = down, True = Up
    
    name : bpy.props.StringProperty()
    path : bpy.props.StringProperty()
    id : bpy.props.StringProperty()
    
    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        col =  sorted(obj.mc_properties, key = mc_prop_ID)
        col_len = mc_len_collection(col)
        
        i = mc_find_index(col,[self.name,self.path,self.id])
    
        if i>=0:
            if self.mod:
                
                j=i
                while j>0:
                    j = j - 1
                    if col[j].section==col[i].section:
                        break
                if j>-1:
                    
                    col[i].mc_id = j
                    col[j].mc_id = i
        
            else:
                
                j=i
                while j<col_len-1:
                    j=j+1
                    if col[j].section==col[i].section:
                        break
                if j<col_len:
                    
                    col[i].mc_id = j
                    col[j].mc_id = i
        
        return {'FINISHED'}

# Operator to remove a property (button in UI)
class MC_RemoveProperty(bpy.types.Operator):
    """Remove the property from the current menu"""
    bl_idname = "mc.removeproperty"
    bl_label = "Remove the property"
    
    path : bpy.props.StringProperty()
    id : bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        props = obj.mc_properties
        
        mc_remove_property_item(obj.mc_properties,['',self.path,self.id])

        return {'FINISHED'}

# Operator to add a new section
class MC_AddSection(bpy.types.Operator):
    """Add a new section to the section list."""
    bl_idname = "mc.addsection"
    bl_label = "Add section"
    bl_icon = "PREFERENCES"
    bl_options = {'UNDO'}
    
    name : bpy.props.StringProperty(name='Name',
        description="Choose the name of the section", default = "Section")
    icon : bpy.props.EnumProperty(name='Icon',
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon",items=mcdata.mc_icon_list)
    collapsable : bpy.props.BoolProperty(name="Collapsable",
        description="Add a collapse button near the name of the section")
    type : bpy.props.EnumProperty(name='Type',
        description="Choose the section type",items=mcdata.mc_section_type_list)

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        sec_obj = obj.mc_sections
        sec_len = mc_len_collection(sec_obj)
        
        if self.name!="":
           
            i=True
            j=-1
            for el in sec_obj:
                j=j+1
                if el.name == self.name:
                    i=False
                    break
            if i:
                add_item = sec_obj.add()
                add_item.name = self.name
                add_item.type = self.type
                add_item.icon = self.icon
                add_item.collapsable = self.collapsable
                add_item.id = sec_len
            
                self.report({'INFO'}, 'Menu Creator - Section \'' + self.name +'\' created.')
            else:
                self.report({'WARNING'}, 'Menu Creator - Cannot create sections with same name.')
        
        else:
            self.report({'ERROR'}, 'Menu Creator - Cannot create sections with this name.')
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        
        settings = bpy.context.scene.mc_settings
                
        if settings.ms_debug:
            return context.window_manager.invoke_props_dialog(self, width=550)
        else:
            return context.window_manager.invoke_props_dialog(self)
            
    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        
        layout = self.layout
        
        scale = 3.0
        
        row=layout.row()
        row.label(text="Name:")
        row.scale_x=scale
        row.prop(self, "name", text="")
        
        row=layout.row()
        row.label(text="Icon:")
        row.scale_x=scale
        row.prop(self, "icon", text="")
        
        row=layout.row()
        row.label(text="")
        row.scale_x=scale
        row.prop(self, "collapsable")
        
        layout.separator()
        
        row=layout.row()
        row.label(text="Type:")
        row.scale_x=scale
        row.prop(self, "type", text="")

# Section Property settings
class MC_SectionSettings(bpy.types.Operator):
    """Modify the section settings."""
    bl_idname = "mc.sectionsettings"
    bl_label = "Section settings"
    bl_icon = "PREFERENCES"
    bl_options = {'UNDO'}
    
    name : bpy.props.StringProperty(name='Name',
        description="Choose the name of the section")
    icon : bpy.props.EnumProperty(name='Icon',
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon.",items=mcdata.mc_icon_list)
    collapsable : bpy.props.BoolProperty(name="Collapsable",
        description="Add a collapse button near the name of the section")
    type : bpy.props.EnumProperty(name='Type',
        description="The Section type can not be changed after creation",items=mcdata.mc_section_type_list)
    
    # COLLECTION type settings
    collections_enable_global_smoothcorrection : bpy.props.BoolProperty(name="Enable Global Smooth Correction")
    collections_enable_global_shrinkwrap : bpy.props.BoolProperty(name="Enable Global Shrinkwrap")
    collections_enable_global_mask : bpy.props.BoolProperty(name="Enable Global Mask")
    collections_enable_global_normalautosmooth : bpy.props.BoolProperty(name="Enable Global Normal Auto Smooth")
    # Outfit variant
    outfit_enable : bpy.props.BoolProperty(name="Outfit", description="With this option a Body entry will be added to the Section. This Body's masks will be enabled when elements of the collections are shown, and viceversa, if the masks are called the same name as the element of the collection")
            
    name_edit : bpy.props.StringProperty(name='Name',
        description="Choose the name of the section")
    ID : bpy.props.IntProperty()

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        prop_obj = obj.mc_properties
        sec_obj = obj.mc_sections
        
        
        i = mc_find_index_section(sec_obj,self.name)
        
        if i>=0:
            
            for el in prop_obj:
                if el.section == self.name:
                    el.section = self.name_edit
           
            sec_obj[i].name = self.name_edit
            sec_obj[i].icon = self.icon
            sec_obj[i].collapsable = self.collapsable
            sec_obj[i].collections_enable_global_smoothcorrection = self.collections_enable_global_smoothcorrection
            sec_obj[i].collections_enable_global_shrinkwrap = self.collections_enable_global_shrinkwrap
            sec_obj[i].collections_enable_global_mask = self.collections_enable_global_mask
            sec_obj[i].collections_enable_global_normalautosmooth = self.collections_enable_global_normalautosmooth
            sec_obj[i].outfit_enable = self.outfit_enable
            if obj.type == "MESH":
                sec_obj[i].outfit_body = obj
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        
        settings = bpy.context.scene.mc_settings
        
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        sec_obj = obj.mc_sections
        
        self.name_edit = self.name
        self.ID = mc_find_index_section(sec_obj,self.name)
        self.collapsable = sec_obj[self.ID].collapsable
        self.collections_enable_global_smoothcorrection = sec_obj[self.ID].collections_enable_global_smoothcorrection
        self.collections_enable_global_shrinkwrap = sec_obj[self.ID].collections_enable_global_shrinkwrap
        self.collections_enable_global_mask = sec_obj[self.ID].collections_enable_global_mask
        self.collections_enable_global_normalautosmooth = sec_obj[self.ID].collections_enable_global_normalautosmooth
        self.outfit_enable = sec_obj[self.ID].outfit_enable
        
        return context.window_manager.invoke_props_dialog(self)
            
    def draw(self, context):
        
        settings = bpy.context.scene.mc_settings
        
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        sec_obj = obj.mc_sections
        
        scale = 3.0
        
        layout = self.layout
        
        row=layout.row()
        row.label(text="Name:")
        row.scale_x=scale
        row.prop(self, "name_edit", text="")
        
        row=layout.row()
        row.label(text="Icon:")
        row.scale_x=scale
        row.prop(self, "icon", text="")
        
        row=layout.row()
        row.label(text="")
        row.scale_x=scale
        row.prop(self, "collapsable")
        
        layout.separator()
        col = layout.column()
        col.enabled = False
        col.prop(self, "type")
        if self.type == "COLLECTION":
            layout.separator()
            row = layout.row()
            row.label(text="")
            row.scale_x = 3
            row.prop(self,"collections_enable_global_smoothcorrection")
            row = layout.row()
            row.label(text="")
            row.scale_x = 3
            row.prop(self,"collections_enable_global_shrinkwrap")
            row = layout.row()
            row.label(text="")
            row.scale_x = 3
            row.prop(self,"collections_enable_global_mask")
            row = layout.row()
            row.label(text="")
            row.scale_x = 3
            row.prop(self,"collections_enable_global_normalautosmooth")
            layout.separator()
            row = layout.row()
            row.label(text="")
            row.scale_x = 3
            row.prop(self,"outfit_enable")

# Operator to change Section position
class MC_SwapSection(bpy.types.Operator):
    """Change the position of the section"""
    bl_idname = "mc.swapsections"
    bl_label = "Change the section position"
    
    mod : bpy.props.BoolProperty(default=False) # False = down, True = Up
    
    name : bpy.props.StringProperty()
    icon : bpy.props.StringProperty()
    
    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        col = obj.mc_sections
        col_len = mc_len_collection(col)
        
        sec_index = mc_find_index_section(col,self.name)
        i = col[sec_index].id
            
        if self.mod and i > 1:
            j = mc_find_index_section_fromID(col, i-1)
            col[sec_index].id = i-1
            col[j].id = i
        elif not self.mod and i < col_len-1:
            j = mc_find_index_section_fromID(col, i+1)
            col[sec_index].id = i+1
            col[j].id = i
        
        return {'FINISHED'}

# Delete Section
class MC_DeleteSection(bpy.types.Operator):
    """Delete Section"""
    bl_idname = "mc.deletesection"
    bl_label = "Section settings"
    bl_options = {'UNDO'}
    
    name : bpy.props.StringProperty(name='Name',
        description="Choose the name of the section")

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        sec_obj = obj.mc_sections
        
        i=-1
        for el in sec_obj:
            i=i+1
            if el.name == self.name:
                break
        
        if i>=0:
            
            j = sec_obj[i].id
            
            for k in range(j+1,len(sec_obj)):
                sec_obj[mc_find_index_section_fromID(sec_obj, k)].id = k-1
            
            sec_obj.remove(i)
        
        self.report({'INFO'}, 'Menu Creator - Section \'' + self.name +'\' deleted.')
        
        return {'FINISHED'}

# Operator to shiwtch visibility of an object
class MC_CollectionObjectVisibility(bpy.types.Operator):
    """Chenge the visibility of the selected object"""
    bl_idname = "mc.colobjvisibility"
    bl_label = "Hide/Unhide Object visibility"
    bl_options = {'UNDO'}
    
    obj : bpy.props.StringProperty()
    sec : bpy.props.StringProperty()

    def execute(self, context):
        
        bpy.data.objects[self.obj].hide_viewport = not bpy.data.objects[self.obj].hide_viewport
        bpy.data.objects[self.obj].hide_render = not bpy.data.objects[self.obj].hide_render
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            body_obj = settings.em_fixobj_pointer
        else:
            body_obj = context.active_object
        sec_obj = body_obj.mc_sections
        i = mc_find_index_section(sec_obj,self.sec)
        
        if sec_obj[i].outfit_enable:
            if sec_obj[i].outfit_body:
                for modifier in sec_obj[i].outfit_body.modifiers:
                    if modifier.type == "MASK" and self.obj in modifier.name and sec_obj[i].collections_global_mask:
                        modifier.show_viewport = not bpy.data.objects[self.obj].hide_viewport
                        modifier.show_render = not bpy.data.objects[self.obj].hide_viewport
            else:
                self.report({'WARNING'}, 'Menu Creator - Outfit Body has not been specified.')
        
        return {'FINISHED'}

# Operator to delete a collection
class MC_RemoveCollection(bpy.types.Operator):
    """Remove the selected collection from the Menu.\nThe collection will NOT be deleted"""
    bl_idname = "mc.deletecollection"
    bl_label = "Remove the selected collection from the menu"
    bl_options = {'UNDO'}
    
    col : bpy.props.StringProperty()
    sec : bpy.props.StringProperty()

    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        sec_obj = obj.mc_sections
        
        sec_index = mc_find_index_section(sec_obj,self.sec)
        
        i = 0
        for el in sec_obj[sec_index].collections:
            if el.collection.name == self.col:
                sec_obj[sec_index].collections.remove(i)
                break
            i = i + 1
        
        self.report({'INFO'}, 'Menu Creator - Collection removed from the Menu.')
        
        return {'FINISHED'}

# Initial Configuration Operator
class MC_InitialConfiguration(bpy.types.Operator):
    """Clean all the object properties"""
    bl_idname = "mc.initialconfig"
    bl_label = "Clean all the properties"
    
    def execute(self, context):
        
        settings = bpy.context.scene.mc_settings
        if settings.em_fixobj:
            obj = settings.em_fixobj_pointer
        else:
            obj = context.active_object
        
        mc_clean_single_sections(obj)
        mc_clean_single_properties(obj)
        
        add_item = obj.mc_sections.add()
        add_item.id = 0
        add_item.name = "Unsorted"
        add_item.icon = "LIBRARY_DATA_BROKEN"
        
        obj.mc_enable = True
        
        self.report({'INFO'}, 'Menu Creator - Menu for \''+obj.name+'\' successfully created.')
        
        return {'FINISHED'}

classes = (
    MC_AddProperty,
    MC_LinkProperty,
    MC_AddCollection,
    MC_CleanAll,
    MC_CleanObject,
    MC_RemoveLinkedProperty,
    MC_PropertySettings,
    MC_SwapProperty,
    MC_RemoveProperty,
    MC_AddSection,
    MC_SectionSettings,
    MC_SwapSection,
    MC_DeleteSection,
    MC_CollectionObjectVisibility,
    MC_RemoveCollection,
    MC_InitialConfiguration
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)