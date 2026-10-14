# 제품 촬영용 가상 스튜디오 템플릿 (Blender 5.2, 책 05-5)
# 05-5 실습에서 AI 에이전트가 Blender MCP로 장면을 만든 뒤 정리해 준 스크립트입니다.
# (책 기준에 맞춰 import 위치와 use_nodes 줄만 정리)
#  - Studio 컬렉션: 곡면 배경, 받침대, 3점 Area 조명, 카메라, Product_Target
#  - Product 컬렉션: Product_Placeholder (제품 모델로 바꿔 넣을 자리 표시 물체)
#  - bpy.ops를 쓰지 않으므로 명령줄 백그라운드 실행에서도 동작합니다
# 사용 1: Blender Scripting 작업 공간에서 실행
# 사용 2: blender -b --factory-startup --python 05/build_studio.py -- studio_template.blend
import math
import os
import sys

import bmesh
import bpy

scene = bpy.context.scene


# ---------- 도우미 함수 ----------
def get_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    return col


def clear_collection(col):
    for ob in list(col.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def make_material(name, color, roughness, specular=0.5):
    """같은 이름의 재질이 있으면 다시 씁니다(03-4)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = specular
    mat.diffuse_color = (*color, 1.0)   # Solid 모드 표시 색도 맞춤(03-2)
    return mat


def mesh_object(name, bm, col, mat):
    old = bpy.data.meshes.get(name)
    if old is not None and old.users == 0:
        bpy.data.meshes.remove(old)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def track_to(ob, target):
    con = ob.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return con


# ---------- Blender 기본 장면의 Cube·Light·Camera 정리 (사람이 검증하며 추가한 부분) ----------
default = bpy.data.collections.get("Collection")
if default is not None:
    for name in ("Cube", "Light", "Camera"):
        ob = default.objects.get(name)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    if not default.all_objects:            # 비어 있으면 기본 컬렉션도 지움
        bpy.data.collections.remove(default)

# ---------- 컬렉션 ----------
studio = get_collection("Studio")
product = get_collection("Product")
clear_collection(studio)
clear_collection(product)

# ---------- 재질 ----------
mat_bg = make_material("MAT_Backdrop", (0.62, 0.62, 0.62), 0.85, 0.2)          # 밝은 회색, 무광
mat_ped = make_material("MAT_Pedestal_White", (0.85, 0.85, 0.85), 0.45, 0.5)   # 흰색
mat_ph = make_material("MAT_Placeholder_Grey", (0.35, 0.35, 0.35), 0.5, 0.5)   # 회색

# ---------- 배경: 바닥과 벽이 곡면으로 이어진 무한 배경 ----------
WIDTH = 6.0          # X 방향 폭
FLOOR_FRONT = -3.0   # 바닥 앞쪽 끝(Y)
CURVE_START = 1.0    # 곡면 시작 위치(Y)
RADIUS = 1.0         # 바닥-벽 곡률 반경
WALL_TOP = 4.0       # 벽 높이(Z)
CURVE_SEG = 24

profile = []  # 옆에서 본 단면 (y, z)
for i in range(9):                                   # 바닥
    profile.append((FLOOR_FRONT + (CURVE_START - FLOOR_FRONT) * i / 8, 0.0))
for i in range(1, CURVE_SEG + 1):                    # 곡면(1/4 원)
    a = (math.pi / 2) * i / CURVE_SEG
    profile.append((CURVE_START + RADIUS * math.sin(a), RADIUS - RADIUS * math.cos(a)))
for i in range(1, 7):                                # 벽
    profile.append((CURVE_START + RADIUS, RADIUS + (WALL_TOP - RADIUS) * i / 6))

bm = bmesh.new()
xs = [-WIDTH / 2 + WIDTH * i / 12 for i in range(13)]
grid = [[bm.verts.new((x, y, z)) for (y, z) in profile] for x in xs]
for i in range(len(xs) - 1):
    for j in range(len(profile) - 1):
        f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        f.smooth = True
bm.normal_update()
mesh_object("Studio_Backdrop", bm, studio, mat_bg)

# ---------- 받침대: 지름 60cm, 높이 40cm ----------
PED_R, PED_H = 0.30, 0.40
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=64,
                      radius1=PED_R, radius2=PED_R, depth=PED_H)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, PED_H / 2))   # 원점이 바닥면에 오게
for f in bm.faces:
    f.smooth = abs(f.normal.z) < 0.5   # 옆면만 부드럽게
mesh_object("Studio_Pedestal", bm, studio, mat_ped)

# ---------- 제품 자리 표시: 20cm 정육면체 ----------
CUBE = 0.20
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=CUBE)
placeholder = mesh_object("Product_Placeholder", bm, product, mat_ph)
placeholder.location = (0, 0, PED_H + CUBE / 2)      # 밑면 = 받침대 윗면

# ---------- 조준점: 받침대 윗면 중심에서 10cm 위 ----------
target = bpy.data.objects.new("Product_Target", None)
target.empty_display_type = "PLAIN_AXES"
target.empty_display_size = 0.1
target.location = (0, 0, PED_H + 0.10)
studio.objects.link(target)


# ---------- 3점 Area 조명 ----------
def area_light(name, loc, power, size):
    old = bpy.data.lights.get(name)
    if old is not None and old.users == 0:
        bpy.data.lights.remove(old)
    ld = bpy.data.lights.new(name, type="AREA")
    ld.energy = power
    ld.shape = "SQUARE"
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    studio.objects.link(ob)
    track_to(ob, target)
    return ob


area_light("Light_Key", (-1.6, -1.6, 1.6), 60, 1.0)    # 왼쪽 앞
area_light("Light_Fill", (1.8, -0.9, 1.0), 20, 1.2)    # 오른쪽, 약하게
area_light("Light_Rim", (0.0, 1.2, 1.9), 30, 0.8)      # 뒤쪽 위

# ---------- 카메라: 85mm ----------
old = bpy.data.cameras.get("Studio_Camera")
if old is not None and old.users == 0:
    bpy.data.cameras.remove(old)
cd = bpy.data.cameras.new("Studio_Camera")
cd.lens = 85
cd.sensor_width = 36
cd.clip_end = 100
cam = bpy.data.objects.new("Studio_Camera", cd)
cam.location = (0, -3.1, 0.95)
studio.objects.link(cam)
track_to(cam, target)
scene.camera = cam

# ---------- World: Blender에 들어 있는 studio.exr을 약하게 ----------
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
env = nt.nodes.new("ShaderNodeTexEnvironment")
hdri_path = os.path.join(bpy.utils.system_resource("DATAFILES", path="studiolights"),
                         "world", "studio.exr")
env.image = bpy.data.images.load(hdri_path, check_existing=True)
bg.inputs["Strength"].default_value = 0.1
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
out.location, bg.location, env.location = (300, 0), (100, 0), (-200, 0)

# ---------- 렌더 설정 ----------
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.eevee.use_raytracing = True

print("Studio template ready:", [o.name for o in studio.objects], [o.name for o in product.objects])

# 명령줄에서 '-- 파일이름.blend'를 주면 그 이름으로 저장합니다
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if args:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args[0]))
