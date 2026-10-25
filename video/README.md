# 시연 영상 자료

10분 시연 영상(개요 → 구현 시연 → 기술·성과)용 클립, 그림, 슬라이드, 내레이션 원고입니다.
원본 데이터는 `../experiment_results/`를 읽기만 하고, 결과는 `out/`과 `assets/`에 씁니다.

## 준비

ffmpeg가 시스템에 없으면 `imageio-ffmpeg`에 포함된 실행 파일을 씁니다(`FFMPEG` 환경 변수로 지정 가능).

```bash
python3 -m venv .venv && .venv/bin/pip install imageio-ffmpeg numpy pillow matplotlib
```

## 만들기

```bash
PY=.venv/bin/python
$PY -I scripts/make_arm_grid.py          # out/arm_grid_12v12.mp4        로봇팔 AFS 12회 vs Random 12회
$PY -I scripts/make_boundary_pairs.py    # out/arm_height_12v14cm.mp4    장애물 12 vs 14 cm
                                         # out/arm_plate_shift_375v50.mp4 접시 이동 37.5 vs 50 %
$PY -I scripts/make_regression.py        # out/regression_rerun_3x.mp4   같은 FAIL 3회 재현
$PY -I scripts/make_humanoid_case.py     # out/humanoid_baseline_vs_box_shift.mp4 기준 PASS → 상자 이동 FAIL (가변 배속·자막)
$PY -I scripts/make_libero_suites.py    # out/arm_libero_suites.mp4      LIBERO Spatial·Object·Goal 묶음별 AFS/Random (experiment_results_20261025)
$PY -I scripts/make_venues.py           # out/humanoid_venues.mp4        창고·사무실·교차로 배치와 결과
$PY -I scripts/make_fall_case.py        # out/humanoid_warehouse_fall.mp4 창고: 사람 접촉 후 넘어짐
$PY -I scripts/make_input_card.py       # out/input_settings.mp4        입력: 작업 목표·환경 변경 축 21개·시도 횟수 (실제 설정값)
$PY -I scripts/make_afs_loop.py         # out/afs_loop_box_shift.mp4    AFS 한 바퀴: 관측 → 요청·응답 → 규칙 검증 → 결과
$PY -I scripts/make_demo_run.py         # out/demo_regression_run.mp4   회귀 실행기 실제 동작 (demo_recording_20261025_v2, 시연 전용)
$PY -I scripts/make_qwen_card.py        # out/regression_qwen_card.mp4  회귀 재실행 결과: 로봇 LLM Qwen 교체 (experiment_results_qwen38)
$PY -I scripts/render_env_generation.py  # assets/env_generation.png     MJCF·이동 지도·장면 그래프 비교
slides/build_slides.sh                   # slides/png/slide-01~13.png   개요·성과 슬라이드(본문 그림 재사용)
$PY -I scripts/assemble_rough_cut.py     # out/rough_cut.mp4            무음 가편집본 10:00
$PY -I scripts/make_subtitled.py        # out/final_subtitled.mp4 (+ out/narration.srt)  narration.md 원고를 아래 자막 띠에 입힌 완성본
$PY -I scripts/make_narrated.py         # out/final_narrated.mp4  원고를 edge-tts(ko-KR-InJoonNeural, 원고가 Microsoft 음성 서비스로 전송됨)로 읽어 음성을 입힌 완성본
$PY -I scripts/index_humanoid.py <휴머노이드 결과 디렉터리> assets/humanoid_index.json  # 42개 실행 목록
```

## 파일

- `narration.md`: 구간별 내레이션 원고와 화면 지시. 시간표는 `scripts/assemble_rough_cut.py`의 `TIMELINE`과 같습니다.
- `out/rough_cut.mp4`: 실시간 화면 3곳(입력 설정, AFS 한 바퀴, 회귀 실행기)은 안내 카드로 자리만 잡혀 있습니다. 녹화본을 `out/`에 두고 `TIMELINE`의 해당 항목을 `clip`으로 바꾸면 됩니다.
- 영상 배속: 로봇팔 원본 영상은 15초 실행을 2배속으로 기록한 것입니다. 휴머노이드 클립은 로봇 동작 구간 4배속, LLM 응답 대기 구간 30배속이며 화면에 표시됩니다. 원본 상단의 시뮬레이션 시각(t=)은 그대로 보입니다.
- 회귀 클립의 사례(`free_pair_continuation_v5` seed 733)는 개발 단계 재현성 점검 자료입니다. 보고서 주 실험(`environment_comparison_v2`)의 재실행이 아님을 화면에 "개발 단계 재현성 점검"으로 표시했습니다.
