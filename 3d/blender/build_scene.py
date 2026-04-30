"""
Blender script for A.F.O conceptual scene generation.
Usage (inside Blender):
  blender --background --python 3d/blender/build_scene.py
"""

import bpy


# Clean scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def add_cube(name, loc, scale, color):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    mat = bpy.data.materials.new(name + "_mat")
    mat.diffuse_color = (*color, 1.0)
    obj.data.materials.append(mat)
    return obj


add_cube("substrate", (0, 0, 0), (10, 7, 0.4), (0.6, 0.6, 0.6))
add_cube("compute_die", (0, 0, 1.0), (7, 4.5, 0.35), (0.25, 0.45, 0.8))
add_cube("bridge", (0, 0, 1.5), (7, 4.5, 0.08), (0.55, 0.4, 0.2))

hbm_positions = [
    (-8.5, -4.5, 2.2), (-8.5, -1.5, 2.2), (-8.5, 1.5, 2.2), (-8.5, 4.5, 2.2),
    (8.5, -4.5, 2.2), (8.5, -1.5, 2.2), (8.5, 1.5, 2.2), (8.5, 4.5, 2.2),
]
for i, p in enumerate(hbm_positions):
    add_cube(f"hbm_{i}", p, (0.7, 0.7, 1.0), (0.15, 0.62, 0.35))

add_cube("hbf_0", (-2.2, -6.2, 2.3), (1.1, 0.7, 1.1), (0.95, 0.45, 0.1))
add_cube("hbf_1", (2.2, -6.2, 2.3), (1.1, 0.7, 1.1), (0.95, 0.45, 0.1))

# Camera and light
bpy.ops.object.camera_add(location=(18, -16, 12), rotation=(1.0, 0, 0.85))
cam = bpy.context.active_object
bpy.context.scene.camera = cam

bpy.ops.object.light_add(type="SUN", location=(8, -8, 15))
light = bpy.context.active_object
light.data.energy = 3.0

# Output path
bpy.context.scene.render.filepath = "results/visualization/afo_blender_render.png"
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

bpy.ops.render.render(write_still=True)
print("Rendered results/visualization/afo_blender_render.png")
