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
from bpy.app.handlers import persistent
from .mcdata import *
from . import mcitems
from . import mcops
from . import mcpanels
from . import mcsettings
from . import mcmenu

# USER INTERFACE

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

modules = (
    mcsettings,
    mcitems,
    mcops,
    mcpanels,
    mcmenu
)

def register():

    for mod in modules:
        mod.register()
    
    # Handlers
    bpy.app.handlers.depsgraph_update_post.append(mc_scene_modification_handler)
    bpy.app.handlers.redo_post.append(mc_scene_modification_handler)
    bpy.app.handlers.undo_post.append(mc_scene_modification_handler)

def unregister():
    # Handlers
    bpy.app.handlers.undo_post.remove(mc_scene_modification_handler)
    bpy.app.handlers.redo_post.remove(mc_scene_modification_handler)
    bpy.app.handlers.depsgraph_update_post.remove(mc_scene_modification_handler)
    
    for mod in reversed(modules):
        mod.unregister()

if __name__ == "__main__":
    register()
    