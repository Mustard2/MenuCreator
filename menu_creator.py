# Mustard Menu Creator addon
# https://github.com/Mustard2/MenuCreator

bl_info = {
    "name": "Menu Creator",
    "description": "Create a custom menu for each Object. To add properties or collections, just right click on the properties and hit Add property to the Menu",
    "author": "Mustard",
    "version": (0, 0, 3),
    "blender": (2, 91, 0),
    "warning": "",
    "wiki_url": "https://github.com/Mustard2/MenuCreator",
    "category": "User Interface",
}

import bpy
import addon_utils
import sys
import os
import re
import time
import math
from bpy.types import Header, Menu, Panel
from bpy.props import *
from bpy.app.handlers import persistent
from mathutils import Vector, Color
import webbrowser

# CLASSES

# Arrays for ENUM properties
# Array to store different section type
mc_section_type_list = [
                ("DEFAULT","Standard","A simple collection of properties that can be added right clicking on fields -> Add Property to the Menu"),
                ("COLLECTION","Collection List","Right clicking on them in the Outliner, you can add collections whose elements can be shown/hidden in the Menu. Only one collection will be shown at the same time.\nIdeal for: Outfit lists","OUTLINER_COLLECTION",1)
            ]
# Array to store possible icons to be used by properties and sections
mc_icon_list = [
                ("NONE","No Icon","No Icon"),
                ("USER", "Face", "Face","USER",1),
                ("HAIR", "Hair", "Hair","HAIR",2),
                ("MOD_CLOTH", "Cloth", "Cloth","MOD_CLOTH",3),
                ("MATERIAL", "Material", "Material","MATERIAL",4),
                ("ARMATURE_DATA", "Armature", "Armature","ARMATURE_DATA",5),
                ("MOD_ARMATURE", "Armature", "Armature","MOD_ARMATURE",6),
                ("EXPERIMENTAL", "Experimental", "Experimental","EXPERIMENTAL",7),
                ("WORLD", "World", "World","WORLD",8),
                ("PARTICLEMODE", "Comb", "Comb","PARTICLEMODE",9)
            ]

# Class with all the settings variables
class MC_Settings(bpy.types.PropertyGroup):
    
    # Update functions for settings
    # Function to avoid edit mode and fixed object while exiting edit mode
    def mc_ms_editmode_update(self, context):
    
        if not self.ms_editmode:
            for obj in bpy.data.objects:
                obj.mc_edit_enable = False
    
        return
    
    # Function to save the fixed object pointer to be used until the object is released
    def mc_em_fixobj_update(self, context):
    
        if self.em_fixobj:
            self.em_fixobj_pointer = context.active_object
    
        return
    
    # Main Settings definitions
    ms_editmode: bpy.props.BoolProperty(name="Enable Edit Mode Tools",
                                        description="Unlock tools to customize the menu.\nDisable when the Menu is complete",
                                        default=False,
                                        update = mc_ms_editmode_update)
    ms_advanced: bpy.props.BoolProperty(name="Advanced Options",
                                        description="Unlock advanced options",
                                        default=False)
    ms_debug: bpy.props.BoolProperty(name="Debug mode",
                                        description="Unlock debug mode.\nMore messaged will be generated in the console.\nEnable it only if you encounter problems, as it might degrade general Blender performance",
                                        default=False)
    
    # Menu Specific properties
    mss_name: bpy.props.StringProperty(name="Name",
                                        description="Name of the menu.\nChoose the name of the menu to be shown before the properties",
                                        default="Object: ")
    mss_obj_name: bpy.props.BoolProperty(name="Show the Object Name",
                                        description="Show the Object name after the Name.\nFor instance, if the Name is \"Object: \", the shown name will be \"Object: name_of_object\"",
                                        default=True)
    
    # Edit mode properties
    em_fixobj: bpy.props.BoolProperty(name="Pin Object",
                                        description="Pin the Object you are using to edit the menu.\nThe object you pin will be considered as the target of all properties addition, and only this Object menu will be shown",
                                        default=False,
                                        update = mc_em_fixobj_update)
    em_fixobj_pointer : bpy.props.PointerProperty(type=bpy.types.Object)

bpy.utils.register_class(MC_Settings)
bpy.types.Scene.mc_settings = bpy.props.PointerProperty(type=MC_Settings)

# Object specific properties
bpy.types.Object.mc_enable = bpy.props.BoolProperty(name="", default=False)
bpy.types.Object.mc_edit_enable = bpy.props.BoolProperty(name="Edit Mode", default=False, description="Enable edit mode in this menu.\nActivating this option you will have access to various tools to modify properties and sections")

# Class to store collections for section informations
class MCCollectionItem(bpy.types.PropertyGroup):
    collection : bpy.props.PointerProperty(name="Collection",type=bpy.types.Collection)

bpy.utils.register_class(MCCollectionItem)

# Class to store section informations
class MCSectionItem(bpy.types.PropertyGroup):
    
    # Properties and update functions
    # Function to update the collapsed status if the collapsed section property is changed
    def mc_sections_collapsed_update(self, context):
    
        if not self.collapsable:
            self.collapsed = False
        
        return
    
    # Function to create an array of tuples for enum collections
    def mc_collections_list(self, context):
        
        items = []
        
        for el in self.collections:
            if hasattr(el.collection, 'name'):
                items.append( (el.collection.name,el.collection.name,el.collection.name) )
            
        return sorted(items)

    # Function to update global collection properties
    def mc_collections_list_update(self, context):
        
        for collection in self.collections:
            if collection.collection.name == self.collections_list:
                collection.collection.hide_viewport = False
                collection.collection.hide_render = False
            else:
                collection.collection.hide_viewport = True
                collection.collection.hide_render = True

    def mc_collections_global_options_update(self, context):
        
        items = []
        
        i = 0
        for el in self.collections:
            for obj in el.collection.objects:
                
                if obj.type == "MESH":
                    obj.data.use_auto_smooth = self.collections_global_normalautosmooth
                
                for modifier in obj.modifiers:
                    if modifier.type == "CORRECTIVE_SMOOTH":
                        modifier.show_viewport = self.collections_global_smoothcorrection
                        modifier.show_render = self.collections_global_smoothcorrection
                    elif modifier.type == "MASK":
                        modifier.show_viewport = self.collections_global_mask
                        modifier.show_render = self.collections_global_mask
                    elif modifier.type == "SHRINKWRAP":
                        modifier.show_viewport = self.collections_global_shrinkwrap
                        modifier.show_render = self.collections_global_shrinkwrap
        
        if self.outfit_enable:
            for modifier in self.outfit_body.modifiers:
                if modifier.type == "MASK":
                    if not self.collections_global_mask:
                        modifier.show_viewport = False
                        modifier.show_render = False
                    else:
                        for el in self.collections:
                            for obj in el.collection.objects:
                                if obj.name in modifier.name and not obj.hide_viewport:
                                    modifier.show_viewport = True
                                    modifier.show_render = True
            
        return
    
    # Poll function for the selection of mesh only in pointer properties
    def mc_poll_mesh(self, object):
        return object.type == 'MESH'
    
    
    # Global section options
    id : bpy.props.IntProperty(name="Section ID")
    name : bpy.props.StringProperty(name="Section Name")
    icon : bpy.props.StringProperty(name="Section Icon", default="")
    type : bpy.props.StringProperty(name="Section Type", default="DEFAULT")
    collapsable : bpy.props.BoolProperty(name="Section Collapsable", default=False, update=mc_sections_collapsed_update)
    
    # Global section option enforcer
    collapsed : bpy.props.BoolProperty(name="", default = False, description="")
    
    # COLLECTION type options
    collections_enable_global_smoothcorrection: bpy.props.BoolProperty(default=False)
    collections_enable_global_shrinkwrap: bpy.props.BoolProperty(default=False)
    collections_enable_global_mask: bpy.props.BoolProperty(default=False)
    collections_enable_global_normalautosmooth: bpy.props.BoolProperty(default=False)
    # COLLECTION type data
    collections: bpy.props.CollectionProperty(name="Section Collection List", type=MCCollectionItem)
    collections_list: bpy.props.EnumProperty(name="Section Collection List", items = mc_collections_list, update=mc_collections_list_update)
    collections_global_smoothcorrection: bpy.props.BoolProperty(name="Smooth Correction", default=True, update=mc_collections_global_options_update)
    collections_global_shrinkwrap: bpy.props.BoolProperty(name="Shrinkwrap", default=True, update=mc_collections_global_options_update)
    collections_global_mask: bpy.props.BoolProperty(name="Mask", default=True, update=mc_collections_global_options_update)
    collections_global_normalautosmooth: bpy.props.BoolProperty(name="Normals Auto Smooth", default=True, update=mc_collections_global_options_update)
    # Outfit variant
    outfit_enable : bpy.props.BoolProperty(name="Outfit", default=False)
    outfit_body : bpy.props.PointerProperty(name="Outfit Body", description = "The masks of this object will be switched on/off depending on which elements of the collections visibility", type=bpy.types.Object, poll=mc_poll_mesh)

bpy.utils.register_class(MCSectionItem)
bpy.types.Object.mc_sections = bpy.props.CollectionProperty(type=MCSectionItem)

# Class to store linked properties informations
class MCLinkedPropertyItem(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(name="Property Path")
    id : bpy.props.StringProperty(name="Property Identifier")

bpy.utils.register_class(MCLinkedPropertyItem)

# Class to store properties informations
class MCPropertyItem(bpy.types.PropertyGroup):
    mc_id : bpy.props.IntProperty(name="Section ID")
    name : bpy.props.StringProperty(name="Property Name")
    path: bpy.props.StringProperty(name="Property Path")
    id : bpy.props.StringProperty(name="Property Identifier")
    icon : bpy.props.EnumProperty(name="Property Icon", default="NONE",items=mc_icon_list)
    section : bpy.props.StringProperty(name="Section", default="Unsorted")
    hide : bpy.props.BoolProperty(name="Hide Property", default=False)
    
    linked_props: bpy.props.CollectionProperty(name="Linked properties", type=MCLinkedPropertyItem)

bpy.utils.register_class(MCPropertyItem)
bpy.types.Object.mc_properties = bpy.props.CollectionProperty(type=MCPropertyItem)



# COLLECTION MANAGEMENT FUNCTIONS

# ---- Properties only functions

# Function to remove a specific property from the collection
# Return 1 if the property was found and deleted
def mc_remove_property_item(collection, item):
    i=-1
    for el in collection:
        i=i+1
        if el.path == item[1] and el.id == item[2]:
            break
    if i>=0:
        collection.remove(i)
    
    return i>=0

# Function to add a specific property to the collection, if not already there
# Return 0 if the property has not been added because already in the properties list
def mc_add_property_item(collection, item):
    i=True
    for el in collection:
        if el.path == item[1] and el.id == item[2]:
            i=False
            break
    if i:
        add_item = collection.add()
        add_item.name = item[0]
        add_item.path = item[1]
        add_item.id = item[2]
        add_item.mc_id = mc_len_collection(collection)
    
    return i

# Function to find the index of a property
def mc_find_index(collection, item):
    i=-1
    for el in collection:
        i=i+1
        if el.path == item[1] and el.id == item[2]:
            break
    return i

# Function to clean properties of a single object
def mc_clean_single_properties(obj):
    obj.mc_properties.clear()

# Function to clean all the properties of every object
def mc_clean_properties():
    for obj in bpy.data.objects:
        obj.mc_properties.clear()

# Function to print the properties
def mc_print_properties():
    for obj in bpy.data.objects:
        for el in obj.mc_properties:
            print(el.id + " : property" + el.name + " with path "+el.path)

# Function to iutput the ID of the element
def mc_prop_ID(elem):
    return elem.mc_id

# ---- Sections only functions

# Function to create an array of tuples for enum properties
def mc_section_list(scene, context):
    
    settings = bpy.context.scene.mc_settings
    if settings.em_fixobj:
        obj = settings.em_fixobj_pointer
    else:
        obj = context.active_object
    
    items = []
    
    i = 0
    for el in obj.mc_sections:
        if el.type == "DEFAULT":
            items.append( (el.name,el.name,el.name,el.icon,i) )
            i = i + 1
        
    return items

# Function to clean sections of a single object
def mc_clean_single_sections(obj):
    obj.mc_sections.clear()
    
# Function to clean the sections of every object
def mc_clean_sections():
    for obj in bpy.data.objects:
        obj.mc_sections.clear()

# Function to find the index of a section from the name
def mc_find_index_section(collection, item):
    i=-1
    for el in collection:
        i=i+1
        if el.name == item:
            break
    return i

# Function to find the index of a section from the ID
def mc_find_index_section_fromID(collection, item):
    i=-1
    for el in collection:
        i=i+1
        if el.id == item:
            break
    return i

# Function to iutput the ID of the element
def mc_sec_ID(elem):
    return elem.id

# ---- Sections and properties functions

# Function to find the length of a collection
def mc_len_collection(collection):
    i=0
    for el in collection:
        i=i+1
    return i




# OPERATORS

# Right click functions and operators
def dump(obj, text):
    print('-'*40, text, '-'*40)
    for attr in dir(obj):
        if hasattr( obj, attr ):
            print( "obj.%s = %s" % (attr, getattr(obj, attr)))

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
            
            rna, path = context.window_manager.clipboard.rsplit('.', 1)
            if '][' in path:
                path, rem = path.rsplit('[', 1)
                rna = rna + '.' + path
                path = '[' + rem
            elif '[' in path:
                path, rem = path.rsplit('[', 1)
            
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
            
            rna, path = context.window_manager.clipboard.rsplit('.', 1)
            if '][' in path:
                path, rem = path.rsplit('[', 1)
                rna = rna + '.' + path
                path = '[' + rem
            elif '[' in path:
                path, rem = path.rsplit('[', 1)
            
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

class WM_MT_button_context(Menu):
    bl_label = "Custom Action"

    def draw(self, context):
        pass

def menu_func(self, context):
    
    if hasattr(context, 'button_prop'):
        layout = self.layout
        layout.separator()
        layout.operator(MC_AddProperty.bl_idname)
        
def menu_func_link(self, context):
    
    if hasattr(context, 'button_prop'):
        layout = self.layout
        #layout.label(text="Try")
        self.layout.menu(OUTLINER_MT_link_mcmenu.bl_idname)

class OUTLINER_MT_collection(Menu):
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
            op = layout.operator(MC_LinkProperty.bl_idname, text=prop.name, icon=prop.icon)
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
                layout.operator(MC_AddCollection.bl_idname, text=sec.name, icon=sec.icon).section = sec.name
                no_col_sec = False
        
        if no_col_sec:
            layout.label(text="No Collection List sections found")

def mc_collection_menu(self, context):
    self.layout.separator()
    self.layout.menu(OUTLINER_MT_collection_mcmenu.bl_idname)

# Operator to clean all properties and sections from all objects
class MC_CleanAll(bpy.types.Operator):
    """Clean all the menus.\nIf you choose reset, it will also delete all Menu options from all objects"""
    bl_idname = "mc.cleanprop"
    bl_label = "Clean all the properties"
    
    reset : BoolProperty(default=False)
    
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
    
    reset : BoolProperty(default=False)
    
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
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon.",items=mc_icon_list)
    section : bpy.props.EnumProperty(name='Section',
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon.",items=mc_section_list)

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
    
    mod : BoolProperty(default=False) # False = down, True = Up
    
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
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon",items=mc_icon_list)
    collapsable : bpy.props.BoolProperty(name="Collapsable",
        description="Add a collapse button near the name of the section")
    type : bpy.props.EnumProperty(name='Type',
        description="Choose the section type",items=mc_section_type_list)

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
        description="Choose the icon.\nNote that the icon name MUST respect Blender convention. All the icons can be found in the Icon Viewer default Blender addon.",items=mc_icon_list)
    collapsable : bpy.props.BoolProperty(name="Collapsable",
        description="Add a collapse button near the name of the section")
    type : bpy.props.EnumProperty(name='Type',
        description="The Section type can not be changed after creation",items=mc_section_type_list)
    
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
    
    mod : BoolProperty(default=False) # False = down, True = Up
    
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



# USER INTERFACE

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

# Handlers

@persistent
def mc_scene_modification_handler(scene):
    """Called at every modification done to the scene."""
    
    for obj in bpy.data.objects:
        
        # Handler for linked custom properties
        for prop in obj.mc_properties:
            for link_prop in prop.linked_props:
                if '].[' in link_prop.path + '.' + link_prop.id:
                    exec(link_prop.path + link_prop.id + '=' + prop.path + '.' + prop.id)
                else:
                    exec(link_prop.path + '.' + link_prop.id + '=' + prop.path + '.' + prop.id)
        
        # Part checking for changes in the list collection
        # This is needed to ensure a clean list against deletion of collections from the outliner
        for sec in obj.mc_sections:
            i = 0
            for el in sec.collections:
                if not hasattr(el.collection, 'name'):
                    sec.collections.remove(i)
                i = i + 1


# Register

classes = (
    MC_AddProperty,
    MC_LinkProperty,
    WM_MT_button_context,
    MC_RemoveProperty,
    MC_CleanAll,
    MC_CleanObject,
    MC_RemoveLinkedProperty,
    MC_PropertySettings,
    MC_SwapProperty,
    MC_AddSection,
    MC_AddCollection,
    MC_RemoveCollection,
    MC_SectionSettings,
    MC_SwapSection,
    MC_DeleteSection,
    MC_CollectionObjectVisibility,
    MC_InitialConfiguration,
    OUTLINER_MT_link_mcmenu,
    OUTLINER_MT_collection_mcmenu,
    PT_MenuCreator_InitialConfiguration_Panel,
    PT_MenuCreator_Panel,
    PT_MenuCreator_Settings_Panel
)

def register():
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    bpy.types.WM_MT_button_context.append(menu_func)
    bpy.types.WM_MT_button_context.append(menu_func_link)
    bpy.types.OUTLINER_MT_collection.append(mc_collection_menu)
    
    # Handlers
    bpy.app.handlers.depsgraph_update_post.append(mc_scene_modification_handler)
    bpy.app.handlers.redo_post.append(mc_scene_modification_handler)
    bpy.app.handlers.undo_post.append(mc_scene_modification_handler)

def unregister():
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    bpy.types.WM_MT_button_context.remove(menu_func)
    bpy.types.WM_MT_button_context.remove(menu_func_link)
    bpy.types.OUTLINER_MT_collection.remove(mc_collection_menu)
    
    # Handlers
    bpy.app.handlers.depsgraph_update_post.remove(mc_scene_modification_handler)
    bpy.app.handlers.redo_post.remove(mc_scene_modification_handler)
    bpy.app.handlers.undo_post.remove(mc_scene_modification_handler)

if __name__ == "__main__":
    register()
    