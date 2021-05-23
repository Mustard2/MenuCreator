import bpy

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

def register():
    bpy.utils.register_class(MC_Settings)
    bpy.types.Scene.mc_settings = bpy.props.PointerProperty(type=MC_Settings)

    # Object specific properties
    bpy.types.Object.mc_enable = bpy.props.BoolProperty(name="", default=False)
    bpy.types.Object.mc_edit_enable = bpy.props.BoolProperty(name="Edit Mode", default=False, description="Enable edit mode in this menu.\nActivating this option you will have access to various tools to modify properties and sections")

def unregister():
    del bpy.types.Object.mc_edit_enable
    del bpy.types.Object.mc_enable
    del bpy.types.Scene.mc_settings
    bpy.utils.unregister_class(MC_Settings)
