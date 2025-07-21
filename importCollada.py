import bpy
import os
import sys
import math # Import the math module for radians

# Get arguments passed to the script after '--'
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

# Check if at least the input DAE path is provided
if len(argv) < 1:
    print("Error: No input DAE file path provided.")
    print("Usage: blender -b -P script.py -- input.dae [output.blend] [render.png]")
    sys.exit(1)

input_dae_path = argv[0]
output_blend_path = argv[1] if len(argv) > 1 else None # Optional output .blend
output_image_path = argv[2] if len(argv) > 2 else None # Optional output render image

# Ensure output directories exist if paths are provided
if output_blend_path:
    os.makedirs(os.path.dirname(output_blend_path), exist_ok=True)
if output_image_path:
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

print(f"Attempting to import DAE: {input_dae_path}")

# --- Clear default scene (optional, but good practice for clean imports) ---
# This ensures you don't have the default cube, camera, and light.
# If you used `--factory-startup` when launching Blender, this might be redundant,
# but it's safe to include.
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- Import the DAE file ---
try:
    # The 'collada_import' operator can have various options.
    # Common ones are:
    # auto_connect=True: Connect loose parts.
    # find_chains=True: Detect bone chains.
    # fix_orientation=True: Fix common orientation issues.
    # You might need to experiment with these based on your DAE files.
    bpy.ops.wm.collada_import(filepath=input_dae_path,
                               auto_connect=True,
                               find_chains=False,
                               fix_orientation=True)
    print(f"Successfully imported DAE: {input_dae_path}")

except RuntimeError as e:
    print(f"Error importing DAE file: {e}")
    sys.exit(1)

# --- Remove Armatures (Optional) ---
bpy.ops.object.select_all(action='DESELECT') # Deselect everything first

armature_objects_to_delete = []

for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        armature_objects_to_delete.append(obj)
        # If this armature is a parent of any mesh, clear the parent first
        for child_obj in obj.children:
            if child_obj.type == 'MESH':
                # Clear parent and keep the mesh's current transformation
                bpy.context.view_layer.objects.active = child_obj
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                print(f"Cleared parent of mesh '{child_obj.name}' from armature '{obj.name}'.")

# Now, delete the armature objects
if armature_objects_to_delete:
    # Select the armatures
    bpy.ops.object.select_all(action='DESELECT')
    for arm_obj in armature_objects_to_delete:
        arm_obj.select_set(True)

    # Set one of them as active to ensure bpy.ops.object.delete works
    if armature_objects_to_delete:
        bpy.context.view_layer.objects.active = armature_objects_to_delete[0]

    # Delete the selected armature objects
    bpy.ops.object.delete(use_global=True, confirm=False) # use_global=True ensures it's removed from all scenes
    print(f"Deleted {len(armature_objects_to_delete)} armature objects.")
else:
    print("No armatures found to delete.")

# Re-select meshes for centering (if applicable)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

# --- Optional: Post-import processing ---
# (e.g., center imported object, add lighting, adjust camera)
# Select all newly imported objects (usually the last ones added to the scene)
bpy.ops.object.select_all(action='DESELECT') # Deselect everything first
# Select all objects that are not cameras or lights (assuming your DAE contains mesh data)
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

# If any objects were selected
if any(obj.select_get() for obj in bpy.context.selected_objects):
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0] # Set active for origin op
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS') # Set origin to geometry center
    bpy.ops.object.location_clear() # Move to global origin (0,0,0)
    print("Imported objects centered to origin.")
else:
    print("No mesh objects found after DAE import to center.")

# Add a camera if one doesn't exist
if not bpy.context.scene.camera:
    bpy.ops.object.camera_add(location=(7.0, -7.0, 5.0))
    bpy.context.object.rotation_euler = (1.1, 0, 0.8) # Example rotation
    bpy.context.scene.camera = bpy.context.object # Set as active camera
    print("Added a default camera.")

# Add a light if one doesn't exist
# Check if any light object exists, not just a specific type
existing_light = next((obj for obj in bpy.data.objects if obj.type == 'LIGHT'), None)

if not existing_light:
    print("No light found, adding a default Sun light.")
    bpy.ops.object.light_add(type='SUN', location=(0,0,0)) # Location doesn't matter for Sun
    sun_light_object = bpy.context.object # Get reference to the newly created light object
    
    # --- Adjust Sun Light Properties ---

    # Adjust energy (brightness)
    sun_data = sun_light_object.data # Get the light data block (bpy.types.SunLight)
    sun_data.energy = 3.0 # Increase brightness, e.g., from default 1.0 to 3.0
    sun_data.diffuse_factor = 1.0 # How much it contributes to diffuse (default 1.0)
    sun_data.specular_factor = 1.0 # How much it contributes to specular (default 1.0)
    sun_data.angle = math.radians(5.0) # Soften shadows by increasing the angle (in degrees)

    # Adjust Sun Light Rotation (Direction)
    # Euler angles are X, Y, Z rotations in radians.
    # X-axis rotation (pitch): Controls elevation (how high the sun is)
    # Y-axis rotation (roll): Rarely used for sun unless you want a weird tilt
    # Z-axis rotation (yaw): Controls direction around the object (e.g., from front, side, back)

    # Example 1: Sun from top-front-right (common, good for general lighting)
    # Rotates 45 degrees up from the horizon (X-axis) and 45 degrees around the Z-axis.
    #sun_light_object.rotation_euler[0] = math.radians(-45) # Rotate around X (pitch)
    #sun_light_object.rotation_euler[2] = math.radians(45)  # Rotate around Z (yaw)

    # Example 2: More from the side (comment out Example 1 to use this)
    # sun_light_object.rotation_euler[0] = math.radians(-30) # Higher elevation
    # sun_light_object.rotation_euler[2] = math.radians(90)  # Directly from the right

    # Example 3: Directly from the front (comment out Example 1 and 2)
    sun_light_object.rotation_euler[0] = math.radians(-60) # High elevation
    sun_light_object.rotation_euler[2] = math.radians(0)   # Directly front

    print(f"Sun light energy set to {sun_data.energy} and rotated.")
else:
    print("Existing light found, not adding a new one.")



# --- Optional: Save the .blend file ---
if output_blend_path:
    bpy.ops.wm.save_mainfile(filepath=output_blend_path)
    print(f"Saved .blend file to: {output_blend_path}")

# --- Optional: Render the scene ---
# --- Cycles Engine and World Background Setup ---
if output_image_path: # Only apply these settings if we're actually rendering
    scene = bpy.context.scene

    # Set the render engine to Cycles
    scene.render.engine = 'CYCLES'
    print("Render engine set to Cycles.")

    # Optional: Configure Cycles samples for quality/speed
    # You might want to adjust these based on your needs
    # For a quick preview:
    # scene.cycles.samples = 128
    # For higher quality:
    # scene.cycles.samples = 256 # Or higher

    # Get the world background
    world = scene.world
    if world is None:
        # Create a new world if one doesn't exist (unlikely in default setup)
        world = bpy.data.worlds.new("NewWorld")
        scene.world = world

    # Ensure the world uses nodes for custom background
    world.use_nodes = True
    print("World nodes enabled.")

    # Get the node tree for the world
    node_tree = world.node_tree
    nodes = node_tree.nodes

    # Clear existing nodes to start fresh for the background setup
    # Keep only the output node
    for node in nodes:
        if node.type != 'OUTPUT_WORLD':
            nodes.remove(node)

    # Add a Background node
    background_node = nodes.new(type='ShaderNodeBackground')
    background_node.location = (-300, 0) # Position for better readability

    # Set the color to white
    background_node.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1.0) # RGBA for white
    print("Background color set to white.")

    # Set the strength
    background_node.inputs['Strength'].default_value = 5.0
    print(f"Background strength set to {background_node.inputs['Strength'].default_value}.")

    # Connect the Background node to the World Output node
    output_node = next(node for node in nodes if node.type == 'OUTPUT_WORLD')
    node_tree.links.new(background_node.outputs['Background'], output_node.inputs['Surface'])
    print("Background node connected to World Output.")

    # --- Rest of your existing rendering setup ---
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = output_image_path
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = True # Set to False for solid background (not transparent)

    print("Starting render...")
    bpy.ops.render.render(write_still=True)
    print(f"Render saved to: {output_image_path}")
# --- Quit Blender ---
bpy.ops.wm.quit_blender()
