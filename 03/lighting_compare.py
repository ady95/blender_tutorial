# 조명 방식과 초점 거리 비교 렌더링 (Blender 5.2, 책 03-3)
# 사용: blender -b --factory-startup --python 03/lighting_compare.py
# 결과: 현재 폴더의 render/03/light_*.png, lens_*.png
import os

import bpy

OUT = os.path.join(os.getcwd(), "render", "03")
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
# Blender에 들어 있는 CC0 HDRI (설치 폴더 기준이라 Windows·Linux 모두 동작)
HDRI = os.path.join(os.path.dirname(bpy.app.binary_path),
                    "5.2", "datafiles", "studiolights", "world", "studio.exr")

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 640, 400
scene.render.image_settings.file_format = 'PNG'


def make_material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def build_scene():
    """금속 원숭이 머리, 어두운 바닥, 원숭이를 바라보는 카메라를 만듭니다."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 1))
    monkey = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    monkey.modifiers.new("Subdivision", 'SUBSURF').levels = 2
    monkey.data.materials.append(make_material("Silver", (0.9, 0.9, 0.9, 1), 1.0, 0.2))
    bpy.ops.mesh.primitive_plane_add(size=30)
    bpy.context.active_object.data.materials.append(make_material("Floor", (0.05, 0.05, 0.06, 1), 0.0, 0.6))
    bpy.ops.object.camera_add(location=(0, -5, 1.6))
    camera = bpy.context.active_object
    camera.constraints.new('TRACK_TO').target = monkey
    scene.camera = camera
    return monkey, camera


def set_world(hdri=None):
    tree = scene.world.node_tree
    background = next(n for n in tree.nodes if n.type == 'BACKGROUND')
    for node in [n for n in tree.nodes if n.type == 'TEX_ENVIRONMENT']:
        tree.nodes.remove(node)
    background.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1)
    if hdri:
        env = tree.nodes.new('ShaderNodeTexEnvironment')
        env.image = bpy.data.images.load(hdri, check_existing=True)
        tree.links.new(env.outputs['Color'], background.inputs['Color'])


def add_light(kind, location, energy, size=None, target=None):
    bpy.ops.object.light_add(type=kind, location=location)
    light = bpy.context.active_object
    light.data.energy = energy          # 코드로 추가한 조명의 기본 세기는 10 W라 꼭 지정합니다
    if size is not None:
        light.data.size = size
    if target is not None:
        light.constraints.new('TRACK_TO').target = target
    return light


def three_point(target):
    add_light('AREA', (-3, -3, 3.5), 500, size=2, target=target)     # 키: 왼쪽 앞 위
    add_light('AREA', (3.5, -2.5, 1.8), 150, size=3, target=target)  # 필: 오른쪽, 약하게
    add_light('AREA', (0.5, 3.5, 3), 600, size=1.5, target=target)   # 림: 뒤쪽 위


def render(name):
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)


# 조명 비교 1: Point 조명 1개 (기본 장면의 Light와 같은 위치·세기)
build_scene()
set_world()
add_light('POINT', (4.08, 1.01, 5.9), 1000)
render("light_A_point")

# 조명 비교 2: 3점 조명
monkey, camera = build_scene()
set_world()
three_point(monkey)
render("light_B_three_point")

# 조명 비교 3: HDRI만 (조명 객체 없음)
build_scene()
set_world(HDRI)
render("light_C_hdri")

# 초점 거리 비교: 원숭이가 비슷한 크기로 보이도록 거리를 초점 거리에 비례시킴
monkey, camera = build_scene()
set_world()
three_point(monkey)
for i, color in enumerate([(0.8, 0.1, 0.1, 1), (0.1, 0.6, 0.1, 1), (0.1, 0.2, 0.8, 1)]):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.5 + i * 2.5, 6, 1))
    bpy.context.active_object.scale.z = 2
    bpy.context.active_object.data.materials.append(make_material(f"Pillar{i}", color))
for lens in (24, 50, 85):
    distance = 5.0 * lens / 50
    camera.data.lens = lens
    camera.location = (0, -distance, 1.0 + 0.12 * distance)
    render(f"lens_{lens}mm")
    print(f"{lens}mm: 카메라 거리 {distance:.1f} m")
