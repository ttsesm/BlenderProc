# This file can be used to execute the pipeline from the blender scripting UI
import os
import bpy
import sys

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
        
        
#        rooms = [o for o in bpy.data.objects
#            if 'Room' in o.name]
            
        rooms = [o for o in bpy.data.objects
            if "type" in o and o["type"] == 'Room']
            
        print("Room objects: {}".format(rooms))
        
#        for i, room in enumerate(rooms):
#            rooms2hide = rooms[:i]+rooms[i+1:]
            
#            toggle_hide(room.children, False)
#            room.hide_set(False)
##            toggle_hide(room, False)
#            
#            for room2hide in rooms2hide:
#                toggle_hide(room2hide.children)
#                room2hide.hide_set(True)
##                toggle_hide(room2hide)
            
        
    finally:
        # Revert back to previous view
        bpy.ops.screen.back_to_previous()
