# GPU 렌더링 점검 스크립트 (Blender 5.2)
# 사용: blender -b --factory-startup --python gpu_check.py
import time

import bpy

scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
prefs = bpy.context.preferences.addons["cycles"].preferences


def render_twice():
    """첫 렌더는 준비 시간이 섞이므로 두 번째 렌더 시간을 잽니다."""
    times = []
    for _ in range(2):
        start = time.perf_counter()
        bpy.ops.render.render()
        times.append(time.perf_counter() - start)
    return times


results = []

scene.render.engine = 'BLENDER_EEVEE'
results.append(("EEVEE", render_twice()))

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.device = 'CPU'
results.append(("Cycles CPU", render_twice()))

for backend in ('CUDA', 'OPTIX', 'HIP', 'ONEAPI'):
    try:
        prefs.compute_device_type = backend
    except TypeError:
        continue  # 이 운영체제에서 지원하지 않는 방식
    prefs.refresh_devices()
    gpus = [d for d in prefs.devices if d.type == backend]
    if not gpus:
        continue
    for d in prefs.devices:
        d.use = d.type == backend
    scene.cycles.device = 'GPU'
    results.append((f"Cycles {backend} ({gpus[0].name})", render_twice()))

print("\n=== GPU 렌더링 점검 결과 (1280x720, Cycles 64샘플) ===")
for name, (first, second) in results:
    print(f"{name:45s} 첫 렌더 {first:6.2f}초 / 두 번째 {second:6.2f}초")
