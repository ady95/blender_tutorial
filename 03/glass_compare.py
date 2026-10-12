# 유리 재질 렌더링 비교: EEVEE 기본 / EEVEE 레이트레이싱 / Cycles (Blender 5.2, 책 03-2)
# 사용: blender -b --factory-startup --python 03/glass_compare.py
# 결과: 현재 폴더의 render/03/glass_*.png
import os
import time

import bpy

OUT = os.path.join(os.getcwd(), "render", "03")
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


def make_material(name, color, metallic=0.0, roughness=0.5, transmission=0.0, ior=1.5):
    mat = bpy.data.materials.new(name)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = ior
    return mat


# 바닥: 체커 무늬
bpy.ops.mesh.primitive_plane_add(size=12)
floor_mat = make_material("Floor", (1, 1, 1, 1))
floor_bsdf = next(n for n in floor_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
checker = floor_mat.node_tree.nodes.new('ShaderNodeTexChecker')
checker.inputs['Scale'].default_value = 12
checker.inputs['Color1'].default_value = (0.9, 0.9, 0.9, 1)
checker.inputs['Color2'].default_value = (0.05, 0.05, 0.05, 1)
floor_mat.node_tree.links.new(checker.outputs['Color'], floor_bsdf.inputs['Base Color'])
bpy.context.active_object.data.materials.append(floor_mat)

# 뒤쪽 색 기둥 3개
for i, color in enumerate([(0.8, 0.1, 0.1, 1), (0.1, 0.6, 0.1, 1), (0.1, 0.2, 0.8, 1)]):
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(-0.9 + i * 0.9, 1.6, 0.6))
    pillar = bpy.context.active_object
    pillar.scale.z = 2
    pillar.data.materials.append(make_material(f"Pillar{i}", color))

# 유리 구
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(0, 0, 0.8), segments=64, ring_count=32)
bpy.ops.object.shade_smooth()
glass = make_material("Glass", (1, 1, 1, 1), roughness=0.0, transmission=1.0, ior=1.45)
bpy.context.active_object.data.materials.append(glass)

# 조명·카메라·배경
bpy.ops.object.light_add(type='AREA', location=(2.5, -2.5, 4), rotation=(0.6, 0.4, 0.8))
bpy.context.active_object.data.energy = 600
bpy.context.active_object.data.size = 3
bpy.ops.object.camera_add(location=(0, -5.2, 1.8), rotation=(1.35, 0, 0))
scene.camera = bpy.context.active_object
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs['Color'].default_value = (0.25, 0.27, 0.3, 1)

scene.render.resolution_x, scene.render.resolution_y = 640, 400
scene.render.image_settings.file_format = 'PNG'


def render(tag):
    """첫 렌더는 셰이더 준비 시간이 섞이므로 두 번 렌더링해 두 번째 시간을 출력합니다."""
    scene.render.filepath = os.path.join(OUT, f"glass_{tag}.png")
    for _ in range(2):
        start = time.perf_counter()
        bpy.ops.render.render(write_still=True)
    print(f"{tag}: {time.perf_counter() - start:.2f}초")


# 1) EEVEE 기본값: 유리가 뒤의 물체를 굴절시키지 못함
scene.render.engine = 'BLENDER_EEVEE'
render("eevee_default")

# 2) EEVEE: 장면 Raytracing + 재질 Raytraced Transmission (둘 다 필요)
scene.eevee.use_raytracing = True
glass.use_raytrace_refraction = True
render("eevee_raytrace")

# 3) Cycles GPU (OptiX가 없으면 CUDA, GPU가 없으면 CPU)
prefs = bpy.context.preferences.addons['cycles'].preferences
for device_type in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
    try:
        prefs.compute_device_type = device_type
    except TypeError:
        continue
    prefs.get_devices()
    if any(d.type == device_type for d in prefs.devices):
        break
for d in prefs.devices:
    d.use = d.type == prefs.compute_device_type
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU' if any(d.use for d in prefs.devices) else 'CPU'
scene.cycles.samples = 128
render("cycles")
