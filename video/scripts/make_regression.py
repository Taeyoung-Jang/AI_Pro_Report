"""발견한 FAIL 환경을 다시 실행해 같은 결과가 나오는지 보여 주는 회귀(재현성) 클립을 만든다.

원본 실행과 재실행 2회를 나란히 재생하고, 각 실행의 판정·접촉 시간·물리 기록 해시를 표시한다.
대상은 로봇팔 개발 단계 재현성 점검(23개 환경 × 3회)의 한 사례다.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

CASE = "seed_733/afs/attempt_00000"
RUNS = [
    ("원본 실행", os.path.join(c.ARM, "free_pair_continuation_v5", CASE)),
    ("재실행 1", os.path.join(c.ARM, "free_pair_reproducibility_3x_v1/round_2", CASE)),
    ("재실행 2", os.path.join(c.ARM, "free_pair_reproducibility_3x_v1/round_3", CASE)),
]
ANALYSIS = os.path.join(c.EXP, "development/robot_arm_repeat_analysis_20261024/analysis.json")
VW, VH, GAP = 600, 330, 30
Y0 = 260
HOLD_S = 4.0


def main():
    analysis = json.load(open(ANALYSIS))
    obs = next(r for r in analysis["records"] if r["case"] == CASE)["observations"]
    runs = []
    for (label, d), o in zip(RUNS, obs):
        m = json.load(open(os.path.join(d, "measurement.json")))
        runs.append(dict(label=label, video=glob.glob(os.path.join(d, "videos/*.mp4"))[0],
                         outcome=json.load(open(os.path.join(d, "receipt.json")))["task_outcome"],
                         contact=m["contact_duration_s"]["robot_obstacle"], physics=o["physics_sha"]))
    x0 = (c.W - 3 * VW - 2 * GAP) // 2
    xs = [x0 + i * (VW + GAP) for i in range(3)]

    bg = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(bg)
    d.text((x0, 40), "회귀 테스트 · 발견한 실패를 다시 실행", font=c.font(30), fill=c.MUTED)
    d.text((x0, 82), "같은 환경, 같은 난수 시드 → 같은 실패", font=c.font(48, True), fill=c.INK)
    d.text((c.W - x0, 52), "영상 2배속", font=c.font(26), fill=c.MUTED, anchor="ra")
    for x, r in zip(xs, runs):
        d.text((x, Y0 - 16), r["label"], font=c.font(34, True), fill=c.INK, anchor="ld")
    bg_path = os.path.join(c.ASSETS, "regression_bg.png")
    bg.save(bg_path)

    fg = Image.new("RGBA", (c.W, c.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    for x, r in zip(xs, runs):
        col = (c.FAIL_C if r["outcome"] == "FAIL" else c.PASS_C) + (255,)
        d.rectangle([x - 5, Y0 - 5, x + VW + 4, Y0 + VH + 4], outline=col, width=7)
        d.rectangle([x, Y0, x + 120, Y0 + 46], fill=col)
        d.text((x + 60, Y0 + 23), r["outcome"], font=c.font(28, True), fill=(255, 255, 255, 255), anchor="mm")
        d.text((x, Y0 + VH + 30), f"로봇–장애물 접촉 {r['contact']:.2f}초", font=c.font(28), fill=c.INK + (255,))
        d.text((x, Y0 + VH + 74), f"물리 기록 해시 {r['physics'][:12]}…", font=c.font(26), fill=c.MUTED + (255,))
    s = analysis["summary"]["totals"]
    n_env = analysis["environment_count"]
    orig_fail = s["afs"]["original_fail"] + s["random"]["original_fail"]
    repro = s["afs"]["original_fail_three_fail"] + s["random"]["original_fail_three_fail"]
    mixed = s["afs"]["mixed"] + s["random"]["mixed"]
    summary = [
        f"개발 단계 재현성 점검: {n_env}개 환경 × 3회 실행",
        f"원래 FAIL {orig_fail}건 중 {repro}건이 3회 모두 FAIL · 결과가 엇갈린 환경 {mixed}개",
        f"초기 상태 일치 {analysis['same_initial_state_count']}/{n_env} · "
        f"물리 기록 완전 일치 {analysis['same_physics_bytes_count']}/{n_env} · "
        f"동작 양상 일치 {analysis['same_motion_pattern_count']}/{n_env}",
    ]
    for i, line in enumerate(summary):
        d.text((x0, Y0 + VH + 160 + i * 52), line, font=c.font(32, i == 0), fill=c.INK + (255,))
    fg_path = os.path.join(c.ASSETS, "regression_fg.png")
    fg.save(fg_path)

    play = 7.5
    total = play + HOLD_S
    args = ["-loop", "1", "-t", str(total), "-i", bg_path]
    for r in runs:
        args += ["-i", r["video"]]
    args += ["-loop", "1", "-t", str(total), "-i", fg_path]
    f = [f"[{i}:v]scale={VW}:{VH},fps={c.FPS},tpad=stop_mode=clone:stop_duration={total}[v{i}]" for i in (1, 2, 3)]
    f.append(f"[0:v][v1]overlay={xs[0]}:{Y0}:eof_action=repeat[a]")
    f.append(f"[a][v2]overlay={xs[1]}:{Y0}:eof_action=repeat[b]")
    f.append(f"[b][v3]overlay={xs[2]}:{Y0}:eof_action=repeat[e]")
    f.append(f"[e][4:v]overlay=0:0:enable='gte(t,{play})'[out]")
    out = os.path.join(c.OUT, "regression_rerun_3x.mp4")
    c.run_ffmpeg(args + ["-filter_complex", ";".join(f), "-map", "[out]", "-t", str(total)] + c.encode_args(out))
    print(out, [(r["label"], r["outcome"], round(r["contact"], 2), r["physics"][:12]) for r in runs])


if __name__ == "__main__":
    main()
