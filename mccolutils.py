import bpy

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
