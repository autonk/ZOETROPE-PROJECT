import bpy
import sys
import os

def main():
    argv = sys.argv
    if "--" not in argv:
        print("PROGRESS: 0/1 Error: No arguments passed to script")
        sys.exit(1)
    argv = argv[argv.index("--") + 1:]

    outdir = argv[0] if len(argv) > 0 else ""
    if not outdir or not os.path.exists(outdir):
        print(f"PROGRESS: 0/1 Error: Invalid output directory {outdir}")
        sys.exit(1)

    # Find the target animation collection
    # If the user has a zoetrope mapping active, use that. Otherwise use "Animation" collection.
    target_anim_col = None
    target_zoetrope = None
    
    if hasattr(bpy.context.scene, 'zoetrope_mappings'):
        mappings = bpy.context.scene.zoetrope_mappings
        if mappings and len(mappings) > 0:
            for mapping in mappings:
                if mapping.anim_collection:
                    target_anim_col = mapping.anim_collection
                    target_zoetrope = mapping.target_zoetrope
                    break

    if not target_anim_col:
        target_anim_col = bpy.data.collections.get("Animation")

    if not target_anim_col:
        print("PROGRESS: 0/1 Error: Could not find 'Animation' collection or any zoetrope mappings.")
        sys.exit(1)

    # Get meshes to export
    meshes = [obj for obj in target_anim_col.all_objects if obj.type == 'MESH']
    if not meshes:
        print(f"PROGRESS: 0/1 Error: No meshes found in {target_anim_col.name}")
        sys.exit(1)

    max_frame = 0
    for obj in target_anim_col.all_objects:
        if obj.animation_data and obj.animation_data.action:
            max_frame = max(max_frame, int(obj.animation_data.action.frame_range[1]))

    if max_frame == 0:
        max_frame = 24 # Fallback

    # If mapped to a zoetrope, match the frame count of the zoetrope empties
    if target_zoetrope:
        empties_count = sum(1 for obj in target_zoetrope.all_objects if obj.name.startswith("Frame_") and obj.type == 'EMPTY')
        if empties_count > 0:
            max_frame = empties_count

    print(f"Total Frames to Export: {max_frame}")

    depsgraph = bpy.context.evaluated_depsgraph_get()

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    for i in range(max_frame):
        print(f"PROGRESS: {i}/{max_frame} Evaluating Frame {i+1}...")
        
        bpy.context.scene.frame_set(i + 1)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        temp_objects = []
        for m in meshes:
            eval_m = m.evaluated_get(depsgraph)
            new_mesh = bpy.data.meshes.new_from_object(eval_m, preserve_all_data_layers=True, depsgraph=depsgraph)
            new_obj = bpy.data.objects.new(f"Temp_Export_{m.name}", new_mesh)
            
            # Apply the object-level transform of the original mesh at this frame
            new_obj.matrix_world = m.matrix_world.copy()
            
            # Ensure materials are linked (some exporters need this to write MTL files correctly, though vertex colors may not need it)
            for mat in m.data.materials:
                if mat.name not in new_mesh.materials:
                    new_mesh.materials.append(mat)
            
            bpy.context.scene.collection.objects.link(new_obj)
            temp_objects.append(new_obj)
            
        bpy.ops.object.select_all(action='DESELECT')
        for temp_obj in temp_objects:
            temp_obj.select_set(True)
            
        bpy.context.view_layer.objects.active = temp_objects[0]
        
        out_path = os.path.join(outdir, f"frame_{i+1:03d}.obj")
        
        try:
            # Modern C++ exporter in Blender 3.2+ (supports vertex colors)
            bpy.ops.wm.obj_export(filepath=out_path, export_selected_objects=True, export_vertex_colors=True)
        except AttributeError:
            # Fallback to old python exporter
            try:
                bpy.ops.export_scene.obj(filepath=out_path, use_selection=True)
            except Exception as e:
                print(f"Export Error: {e}")
                
        # Cleanup memory for this frame
        bpy.ops.object.delete()
        for temp_obj in temp_objects:
            if temp_obj.data:
                bpy.data.meshes.remove(temp_obj.data, do_unlink=True)

    print(f"PROGRESS: {max_frame}/{max_frame} Finished!")

if __name__ == "__main__":
    main()
