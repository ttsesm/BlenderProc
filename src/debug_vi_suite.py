# This file can be used to execute the pipeline from the blender scripting UI
import os
import bpy
import sys

from src.utility.Utility import Utility
from src.utility.LabelIdMapping import LabelIdMapping
import src.utility.BlenderUtility


def toggle_hide (lst, mode=True):

    children_list = []    
#    if obj.children:
#        children_list.append(obj.children)
#        
#        obj.hide_set(mode)
#    else:

#    print("List: {}".format(list(lst)))
#    print("List: {}".format(lst))
    
    for obj in lst:
        if obj.children:
#            print (obj.children)
            children_list.append(obj.children)

        obj.hide_set(mode)  # hide the child
#        obj.hide_viewport = False  # use this if you want to show the child
#    print (">>children_list: " + str(children_list))
    if children_list:
        for child in children_list:
#            print ("going deeper")
            toggle_hide (child)
            
def material_mapping(obj, type):
    for m in obj.material_slots:
        print("Material name: {}".format(m.name))

        obj.active_material = m.material
        o = obj.active_material
        o.vi_params.mattype = '1' # set material to be a light sensor so that we calculate radiance on their vertices/faces

        if o.use_nodes == True:
            
            # TODO: this might need some better arrangement
            if type == 'window' and o.node_tree.nodes["Principled BSDF"].inputs['Alpha'].default_value < 1:
                o.vi_params.radmatmenu = '1' # set the "VI-Suite Material --> LiVi Radiance type"
            elif type == 'lamp' and "emission" in o.name.lower():
                o.vi_params.radmatmenu = '5' # set the "VI-Suite Material --> LiVi Radiance type"
                o.vi_params.radcolmenu = '0' # set the "VI-Suite Material --> Colour type"
                o.vi_params.radct = 4700 # set the "VI-Suite Material --> Temperature"
                o.vi_params.radintensity = 75.0 # set the "VI-Suite Material --> Intensity"
            # This is redundant, but adding it for a completion aspect
            elif type == 'ceiling' and "emission" in o.name.lower():
                o.vi_params.radmatmenu = '5' # set the "VI-Suite Material --> LiVi Radiance type"
                o.vi_params.radcolmenu = '0' # set the "VI-Suite Material --> Colour type"
                o.vi_params.radct = 4700 # set the "VI-Suite Material --> Temperature"
                o.vi_params.radintensity = 75.0 # set the "VI-Suite Material --> Intensity"
            else:
                o.vi_params.radmatmenu = '0' # set the "VI-Suite Material --> LiVi Radiance type"
            
            if o.node_tree.nodes["Principled BSDF"].inputs["Base Color"].links:
                o.vi_params.radtex = True
#                # Get the linked textured image
#                link = o.node_tree.nodes["Principled BSDF"].inputs["Base Color"].links[0]
#                link_node = link.from_node
#                print( link_node.image.name )
                o.vi_params.radcolour = o.node_tree.nodes["Principled BSDF"].inputs["Subsurface Color"].default_value[0:3]
            else:                                    
                o.vi_params.radcolour = o.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[0:3] # set the "VI-Suite Material --> Material Reflectance"
                
            o.vi_params.radrough = o.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value # set the "VI-Suite Material --> Roughness"
            o.vi_params.radspec = o.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value  # set the "VI-Suite Material --> Specularity"
        else:
            o.vi_params.radrough = o.roughness
            o.vi_params.radspec = o.specular_intensity
            o.vi_params.radcolour = o.diffuse_color # set the "VI-Suite Material --> Material Reflectance"
            

if __name__ == "__main__":
    # Make sure the current script directory is in PATH, so we can load other python modules
    working_dir = os.path.dirname(bpy.context.space_data.text.filepath) + "/../"
    
#    print("Working dir: {}".format(working_dir))

    if not working_dir in sys.path:
        sys.path.append(working_dir)

    # Add path to custom packages inside the blender main directory
    # TODO: fix this for some reason is not working, thus I have to hard set the packages path
    if sys.platform == "linux" or sys.platform == "linux2":
        packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "custom-python-packages"))
    elif sys.platform == "darwin":
        packages_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "Resources", "custom-python-packages"))
    else:
        raise Exception("This system is not supported yet: {}".format(sys.platform))
#    print("Packages path: {}".format(packages_path))
#    packages_path = "/home/theodore/Development/BlenderProc/blender/blender-2.83.6-linux64/custom-python-packages/"
    sys.path.append(packages_path)

    # Delete all loaded models inside src/, as they are cached inside blender
    for module in list(sys.modules.keys()):
        if module.startswith("src"):
            del sys.modules[module]

    from src.main.Pipeline import Pipeline

    config_path = "examples/suncg_with_vi_suite/config.yaml"

    # Focus the 3D View, this is necessary to make undo work (otherwise undo will focus on the scripting area)
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        for area in screen.areas:
            if area.type == 'VIEW_3D':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.screen.screen_full_area(override)
                break

    try:
        # In this debug case the rendering is avoided, everything is executed except the final render step
        # For the RgbRenderer the undo is avoided to have a direct way of rendering in debug
        pipeline = Pipeline(config_path, [], working_dir, avoid_rendering=True)
        pipeline.run()
        
        # create an object label id mapper
        LabelIdMapping.assign_mapping(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
        
#        # find rooms by name
#        rooms = [o for o in bpy.data.objects
#            if 'Room' in o.name]
            
        # find rooms by type    
        rooms = [o for o in bpy.data.objects
            if "type" in o and o["type"] == 'Room']
            
#        print("Room objects: {}".format(rooms))
        
        if rooms:
            for i, room in enumerate(rooms):
                # find non active rooms
                rooms2hide = rooms[:i]+rooms[i+1:]

                # unhide room to be processed
                room.hide_children = False
    #            toggle_hide(room.children, False)
    #            room.hide_set(False)
                
                for room2hide in rooms2hide:
                    room2hide.hide_children = True
    #                toggle_hide(room2hide.children)
    #                room2hide.hide_set(True)
                
                # map materials from wavefront prototype to radiance 
                for obj in room.children:
                    material_mapping(obj, LabelIdMapping.id_label_map[obj["category_id"]])
            
            
        
    finally:
        # Revert back to previous view
        bpy.ops.screen.back_to_previous()

# how to access object by name
# bpy.data.objects["Room#0_0"].hide_children()
# bpy.context.scene.objects["Room#0_0"].hide_children = True
# bpy.data.objects["Room#0_0"].hide_children = True