# 첫 번째 AI 3D 영상: 회전하는 금속 원숭이 머리 (Blender 5.2)
# 실행 전 blend 파일을 먼저 저장해 두세요. 출력 경로(//render)가 blend 파일 위치 기준입니다.
import math

import bpy
from mathutils import Vector

scene = bpy.context.scene

# 1. 기존 객체를 모두 지웁니다.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


def make_material(name, color, metallic=0.0, roughness=0.5):
    """Principled BSDF 재질을 만듭니다. 노드는 이름이 아니라 타입으로 찾습니다."""
    mat = bpy.data.materials.new(name)
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def look_at(obj, target=(0, 0, 0)):
    """객체가 target 지점을 바라보도록 회전시킵니다."""
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


# 2. 원숭이 머리(Suzanne)를 만들고 부드럽게 다듬습니다.
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0))
monkey = bpy.context.object
bpy.ops.object.shade_smooth()
monkey.modifiers.new("Subdivision", 'SUBSURF').levels = 2
monkey.data.materials.append(
    make_material("Silver Metal", (0.65, 0.68, 0.72, 1.0), metallic=1.0, roughness=0.2))

# 3. 어두운 바닥을 깝니다.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -1.15))
bpy.context.object.data.materials.append(
    make_material("Dark Floor", (0.055, 0.055, 0.065, 1.0), roughness=0.75))

# 4. 배경(World)을 거의 검게 만듭니다.
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs['Color'].default_value = (0.003, 0.003, 0.006, 1.0)
background.inputs['Strength'].default_value = 0.2


# 5. 푸른색·보라색 Area 조명을 비춥니다.
def add_area_light(name, location, color, energy, size):
    light = bpy.data.lights.new(name, type='AREA')
    light.color, light.energy, light.shape, light.size = color, energy, 'DISK', size
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj)


add_area_light("Blue Key", (-4, -4, 3.5), (0.12, 0.32, 1.0), 900, 4.0)
add_area_light("Purple Rim", (4, 2, 3.5), (0.55, 0.12, 1.0), 1100, 3.0)

# 6. 카메라를 정면에서 약간 위에 둡니다.
camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
scene.collection.objects.link(camera)
camera.location = (0, -8, 2.2)
look_at(camera)
scene.camera = camera

# 7. 10초(240프레임) 동안 Z축으로 한 바퀴 돕니다.
scene.frame_start, scene.frame_end = 1, 240
scene.render.fps = 24
monkey.rotation_euler.z = 0
monkey.keyframe_insert("rotation_euler", index=2, frame=1)
monkey.rotation_euler.z = math.tau  # 360도
monkey.keyframe_insert("rotation_euler", index=2, frame=240)

# Blender 5부터 F-Curve는 레이어 > 스트립 > 채널백 안에 있습니다.
action = monkey.animation_data.action
for layer in action.layers:
    for strip in layer.strips:
        for channelbag in strip.channelbags:
            for fcurve in channelbag.fcurves:
                for key in fcurve.keyframe_points:
                    key.interpolation = 'LINEAR'  # 일정한 속도

# 8. 렌더링 설정: EEVEE, 1920x1080, MP4(H.264)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.media_type = 'VIDEO'  # Blender 5: 영상 출력 전 필수
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.filepath = "//render/first_animation"

scene.frame_set(1)
print("장면 준비 완료: Render > Render Animation으로 렌더링하세요.")
