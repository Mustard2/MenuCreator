
import bpy
import mcdata

# Class to store collections for section informations
class MCCollectionItem(bpy.types.PropertyGroup):
    collection : bpy.props.PointerProperty(name="Collection",type=bpy.types.Collection)


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


# Class to store linked properties informations
class MCLinkedPropertyItem(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(name="Property Path")
    id : bpy.props.StringProperty(name="Property Identifier")

# Class to store properties informations
class MCPropertyItem(bpy.types.PropertyGroup):
    mc_id : bpy.props.IntProperty(name="Section ID")
    name : bpy.props.StringProperty(name="Property Name")
    path: bpy.props.StringProperty(name="Property Path")
    id : bpy.props.StringProperty(name="Property Identifier")
    icon : bpy.props.EnumProperty(name="Property Icon", default="NONE",items=mcdata.mc_icon_list)
    section : bpy.props.StringProperty(name="Section", default="Unsorted")
    hide : bpy.props.BoolProperty(name="Hide Property", default=False)
    linked_props: bpy.props.CollectionProperty(name="Linked properties", type=MCLinkedPropertyItem)


def register():
    bpy.utils.register_class(MCCollectionItem)
    bpy.utils.register_class(MCSectionItem)
    bpy.utils.register_class(MCLinkedPropertyItem)
    bpy.utils.register_class(MCPropertyItem)
    bpy.types.Object.mc_properties = bpy.props.CollectionProperty(type=MCPropertyItem)
    bpy.types.Object.mc_sections = bpy.props.CollectionProperty(type=MCSectionItem)

def unregister():
    del bpy.types.Object.mc_properties
    del bpy.types.Object.mc_sections
    bpy.utils.unregister_class(MCSectionItem)
    bpy.utils.unregister_class(MCLinkedPropertyItem)
    bpy.utils.unregister_class(MCPropertyItem)
    bpy.utils.unregister_class(MCCollectionItem)