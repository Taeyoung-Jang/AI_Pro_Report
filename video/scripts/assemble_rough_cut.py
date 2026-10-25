"""narration.md의 타임라인대로 슬라이드·클립을 이어 붙인 무음 가편집본(10분)을 만든다.

- 슬라이드·그림은 구간 길이만큼 정지 화면으로 보여 준다.
- 클립이 구간보다 짧으면 마지막 프레임을 유지하고, 길면 구간 길이에서 자른다.
- 실시간 화면(직접 녹화할 부분)은 안내 카드로 자리만 잡아 둔다. 녹화본이 생기면
  LIVE 항목의 경로를 그 파일로 바꾸면 된다.
출력: out/rough_cut.mp4, out/rough_cut_timeline.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

SLIDE = os.path.join(c.VIDEO, "slides/png/slide-{:02d}.png")
STEPS = ["입력", "AFS 탐색", "규칙 검증", "환경 생성", "실행", "판정·저장", "회귀"]
BAR_H = 60

# (시작 초, 구간 길이 초, 종류, 대상, 메모[, 진행 단계]). 종류: slide | image | clip | live
# 진행 단계가 있으면 화면 아래에 전체 흐름 표시 막대를 붙이고 해당 단계를 강조한다.
TIMELINE = [
    (0, 17, 'slide', 1, '오프닝'),
    (17, 35, 'slide', 2, '배경과 문제'),
    (52, 17, 'slide', 3, '평가 지표'),
    (69, 27, 'slide', 4, '시스템 구성'),
    (96, 21, 'clip', 'input_settings.mp4', '입력: 작업 목표·환경 변경 축·시도 횟수', ['입력']),
    (117, 24, 'slide', 6, 'AFS 입력과 출력', ['AFS 탐색']),
    (141, 50, 'clip', 'afs_loop_box_shift.mp4', 'AFS 한 바퀴: 관측 → 제안 → 검증 → 결과 (휴머노이드 상자 이동)', ['AFS 탐색', '규칙 검증']),
    (191, 35, 'image', 'env_generation.png', '환경 생성: MJCF·이동 지도·장면 그래프', ['환경 생성']),
    (226, 46, 'clip', 'humanoid_baseline_vs_box_shift.mp4', '휴머노이드: 기준 PASS → 상자 이동 FAIL', ['실행', '판정·저장']),
    (272, 18, 'clip', 'regression_rerun_3x.mp4', '회귀: 같은 실패 3회 재현', ['회귀']),
    (290, 26, 'clip', 'demo_regression_run.mp4', '회귀 실행기 실제 동작 (시연 전용 실행)', ['회귀']),
    (316, 15, 'clip', 'regression_qwen_card.mp4', '회귀 재실행 결과: 로봇 LLM Qwen 교체', ['회귀']),
    (331, 16, 'slide', 5, '주요 적용 기술'),
    (347, 23, 'slide', 7, '두 종류의 테스트 대상'),
    (370, 19, 'clip', 'arm_grid_12v12.mp4', '로봇팔 12 vs 12'),
    (389, 31, 'slide', 8, '결과 FDR'),
    (420, 25, 'clip', 'arm_libero_suites.mp4', 'LIBERO 과제 묶음별 확인'),
    (445, 18, 'clip', 'humanoid_venues.mp4', '휴머노이드 다른 배치: 창고·사무실·교차로'),
    (463, 18, 'clip', 'humanoid_warehouse_fall.mp4', '창고: 사람 접촉 후 넘어짐'),
    (481, 20, 'slide', 9, '가설 적중'),
    (501, 14, 'clip', 'arm_height_12v14cm.mp4', '높이 경계'),
    (515, 13, 'clip', 'arm_plate_shift_375v50.mp4', '접시 경계'),
    (528, 17, 'slide', 10, '경계 그래프'),
    (545, 19, 'slide', 11, '실패 유형'),
    (564, 16, 'slide', 12, '목표 달성'),
    (580, 20, 'slide', 13, '마무리'),
]


def live_card(text, path):
    im = Image.new("RGB", (c.W, c.H), (36, 40, 48))
    d = ImageDraw.Draw(im)
    d.text((c.W // 2, c.H // 2 - 60), "실시간 화면 (직접 녹화)", font=c.font(40), fill=(170, 176, 186), anchor="mm")
    d.text((c.W // 2, c.H // 2 + 20), text, font=c.font(48, True), fill=(255, 255, 255), anchor="mm")
    im.save(path)


def step_bar(active, path):
    """전체 흐름 7단계를 한 줄로 그리고 active 단계를 강조한 막대 이미지."""
    im = Image.new("RGB", (c.W, BAR_H), (36, 40, 48))
    d = ImageDraw.Draw(im)
    f = c.font(26, True)
    n = len(STEPS)
    cell = c.W / n
    for k, name in enumerate(STEPS):
        x0 = int(k * cell)
        on = name in active
        if on:
            d.rectangle([x0 + 4, 6, int((k + 1) * cell) - 4, BAR_H - 6], fill=c.AFS_C)
        d.text((x0 + cell / 2, BAR_H / 2), name, font=f, fill=(255, 255, 255) if on else (140, 146, 156), anchor="mm")
        if k < n - 1:
            d.text((int((k + 1) * cell), BAR_H / 2), "›", font=f, fill=(110, 116, 126), anchor="mm")
    im.save(path)


def fit_vf(steps):
    """화면 맞춤 필터. 진행 단계가 있으면 본 화면을 줄여 위에 두고 아래에 막대 자리를 남긴다."""
    h = c.H - BAR_H if steps else c.H
    return (f"scale={c.W}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={c.W}:{c.H}:(ow-iw)/2:{'0' if steps else '(oh-ih)/2'}:color=white")


def with_bar(i, steps, vf_in, inputs, out, dur):
    """inputs의 첫 입력에 vf_in을 적용하고, 진행 단계가 있으면 막대를 아래에 겹친다."""
    if not steps:
        c.run_ffmpeg(inputs + ["-vf", vf_in, "-t", str(dur)] + c.encode_args(out))
        return
    bar = os.path.join(c.ASSETS, f"stepbar_{i:02d}.png")
    step_bar(steps, bar)
    fc = f"[0:v]{vf_in}[m];[m][1:v]overlay=0:{c.H - BAR_H}[out]"
    c.run_ffmpeg(inputs + ["-loop", "1", "-t", str(dur), "-i", bar, "-filter_complex", fc, "-map", "[out]",
                           "-t", str(dur)] + c.encode_args(out))


def segment(i, item, out):
    start, dur, kind, target, note = item[:5]
    steps = item[5] if len(item) > 5 else None
    if kind == "clip":
        src = os.path.join(c.OUT, target)
        vf = f"{fit_vf(steps)},fps={c.FPS},tpad=stop_mode=clone:stop_duration={dur}"
        with_bar(i, steps, vf, ["-i", src], out, dur)
        return
    if kind == "slide":
        img = SLIDE.format(target)
    elif kind == "image":
        img = os.path.join(c.ASSETS, target)
    else:
        img = os.path.join(c.ASSETS, f"live_{i:02d}.png")
        live_card(target, img)
    with_bar(i, steps, f"{fit_vf(steps)},fps={c.FPS}", ["-loop", "1", "-t", str(dur), "-i", img], out, dur)


def main():
    seg_dir = os.path.join(c.OUT, "segments")
    os.makedirs(seg_dir, exist_ok=True)
    t = 0
    paths, lines = [], []
    for i, item in enumerate(TIMELINE):
        start, dur, kind, target, note = item[:5]
        assert start == t, f"{i}번 구간 시작 {start} != 누적 {t}"
        t += dur
        p = os.path.join(seg_dir, f"{i:02d}.mp4")
        segment(i, item, p)
        paths.append(p)
        lines.append(f"{start // 60}:{start % 60:02d}–{t // 60}:{t % 60:02d}  {kind:5s}  {target}  ({note})")
    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in paths)
    out = os.path.join(c.OUT, "rough_cut.mp4")
    c.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    with open(os.path.join(c.OUT, "rough_cut_timeline.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(out, f"총 {t // 60}분 {t % 60}초")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
