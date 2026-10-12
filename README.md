# 블렌더 AI 자동화 따라하기 — 예제 코드

위키독스 책 「블렌더 AI 자동화 따라하기 (AI 에이전트와 오픈소스로 시작하는 3D 영상 제작 자동화)」의 예제 코드 저장소입니다.

- 책: [https://wikidocs.net/book/21559](https://wikidocs.net/book/21559)
- 기준 버전: **Blender 5.2.2 LTS**
- 실측 환경: Windows 11 / GTX 1080 8GB(01·02장), RTX 3090 24GB(03장~) — 렌더링 시간은 GPU에 따라 다릅니다

## 폴더 구성

폴더 이름은 책의 장 번호와 같습니다.

| 폴더 | 파일 | 내용 | 책 페이지 |
|---|---|---|---|
| `01/` | `gpu_check.py` | EEVEE·Cycles CPU/GPU 렌더링 속도 점검 | 01-3 |
| `02/` | `first_animation.py` | 회전하는 금속 원숭이 머리 10초 영상 장면 생성 | 02-3 |
| `02/prompts/` | `1_create_scene.txt` | AI에게 코드를 요청한 프롬프트 | 02-1 |
| | `2_revise_metal_dolly.txt` | 1차 수정 요청 (금속 반사, 카메라 돌리 인) | 02-4 |
| | `3_restore_mood.txt` | 2차 수정 요청 (어두운 분위기 복원) | 02-4 |
| `03/` | `glass_compare.py` | 유리 재질 렌더링 비교 (EEVEE 기본·레이트레이싱·Cycles) | 03-2 |
| | `lighting_compare.py` | 조명 방식(Point·3점 조명·HDRI)과 초점 거리(24·50·85mm) 비교 | 03-3 |

## 실행 방법

### 명령줄에서 실행 (01/gpu_check.py, 03/*.py)

저장소 폴더에서 실행합니다.

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup --python 01/gpu_check.py
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup --python 03/glass_compare.py
```

03장 스크립트의 결과 이미지는 `render/03/` 폴더에 저장됩니다.

### Blender 안에서 실행 (02/first_animation.py)

1. Blender에서 **File → Save As**로 blend 파일을 먼저 저장합니다 (출력 경로 `//render`가 blend 파일 위치 기준).
2. **Scripting** 작업 공간 → Text Editor → **Open**으로 스크립트를 열거나 붙여 넣습니다.
3. `Alt+P`(Run Script)로 실행한 뒤 **Render → Render Animation**(`Ctrl+F12`)으로 렌더링합니다.

결과 영상은 `render/first_animation0001-0240.mp4`로 저장됩니다.

## 주의

- 예제는 Blender 5.2 기준입니다. Blender 4.x 이하에서는 API 차이로 동작하지 않을 수 있습니다 (책 02-2 참고).
- 한국어 UI에서는 **Edit → Preferences → Interface → Translation**의 New Data 번역을 끄는 것을 권장합니다 (책 01-4 참고).

## 라이선스

[MIT License](LICENSE)
