"""로봇팔 통제 실험의 PASS/FAIL 경계를 나란히 재생하는 클립을 만든다.

- 장애물 높이 12 cm(PASS) vs 14 cm(FAIL)
- 접시 이동 37.5 %(PASS) vs 50 %(FAIL)
측정값은 evidence/robot_arm_environment_20261023/capability_review.json에서 읽는다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

REVIEW = os.path.join(c.REPO, "evidence/robot_arm_environment_20261023/capability_review.json")
SRC = os.path.join(c.ARM, "capability_followup_v2")
PAIRS = [
    ("arm_height_12v14cm.mp4", "장애물 높이: 2 cm 차이로 결과가 바뀐다",
     [("box_12cm", "장애물 12 cm"), ("box_14cm", "장애물 14 cm")]),
    ("arm_plate_shift_375v50.mp4", "접시 위치: 이동 비율 37.5 % → 50 %",
     [("target_t0_375", "접시 이동 37.5 %"), ("target_t0_5", "접시 이동 50 %")]),
]
VW, VH = 900, 496
X0 = [40, c.W - 40 - VW]
Y0 = 250
HOLD_S = 3.5


def rows():
    out = {}
    for r in json.load(open(REVIEW))["rows"]:
        rel = r["video"].split("capability_followup_v2/")[1]
        r["local_video"] = os.path.join(SRC, rel)
        out[r["case"]] = r
    return out


def describe(r):
    m = r["measurement"]
    contact = m["contact_duration_s"]["robot_obstacle"]
    lines = [f"그릇–접시 최종 거리 {100 * r['final_bowl_plate_center_xy_gap_m']:.1f} cm"]
    if contact > 0:
        lines.append(f"로봇–장애물 접촉 {contact:.1f}초, 최대 접촉력 {m['peak_obstacle_force_n']:.0f} N")
    else:
        lines.append("장애물 접촉 없음")
    lines.append(f"실행 시간 {m['duration_s']:.1f}초 ({r['steps']} 제어 단계)")
    return lines


def layers(title, cases, data, bg_path, fg_path):
    bg = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(bg)
    d.text((40, 40), "로봇팔 통제 실험 · PASS/FAIL 경계", font=c.font(30), fill=c.MUTED)
    d.text((40, 82), title, font=c.font(48, True), fill=c.INK)
    d.text((c.W - 40, 52), "영상 2배속 · 나머지 조건은 동일", font=c.font(26), fill=c.MUTED, anchor="ra")
    for x, (case, label) in zip(X0, cases):
        d.text((x, Y0 - 16), label, font=c.font(36, True), fill=c.INK, anchor="ld")
    bg.save(bg_path)

    fg = Image.new("RGBA", (c.W, c.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    for x, (case, label) in zip(X0, cases):
        r = data[case]
        col = (c.FAIL_C if r["outcome"] == "FAIL" else c.PASS_C) + (255,)
        d.rectangle([x - 6, Y0 - 6, x + VW + 5, Y0 + VH + 5], outline=col, width=8)
        d.rectangle([x, Y0, x + 150, Y0 + 56], fill=col)
        d.text((x + 75, Y0 + 28), r["outcome"], font=c.font(34, True), fill=(255, 255, 255, 255), anchor="mm")
        for i, line in enumerate(describe(r)):
            d.text((x, Y0 + VH + 36 + i * 50), line, font=c.font(32, i == 0), fill=c.INK + (255,))
    fg.save(fg_path)


def main():
    data = rows()
    for name, title, cases in PAIRS:
        stem = os.path.splitext(name)[0]
        bg_path = os.path.join(c.ASSETS, stem + "_bg.png")
        fg_path = os.path.join(c.ASSETS, stem + "_fg.png")
        layers(title, cases, data, bg_path, fg_path)
        play = max(data[k]["measurement"]["duration_s"] for k, _ in cases) / 2
        total = play + HOLD_S
        args = ["-loop", "1", "-t", str(total), "-i", bg_path]
        for k, _ in cases:
            args += ["-i", data[k]["local_video"]]
        args += ["-loop", "1", "-t", str(total), "-i", fg_path]
        f = [f"[{i}:v]scale={VW}:{VH},fps={c.FPS},tpad=stop_mode=clone:stop_duration={total}[v{i}]" for i in (1, 2)]
        f.append(f"[0:v][v1]overlay={X0[0]}:{Y0}:eof_action=repeat[a]")
        f.append(f"[a][v2]overlay={X0[1]}:{Y0}:eof_action=repeat[b]")
        f.append(f"[b][3:v]overlay=0:0:enable='gte(t,{play:.2f})'[out]")
        out = os.path.join(c.OUT, name)
        c.run_ffmpeg(args + ["-filter_complex", ";".join(f), "-map", "[out]", "-t", f"{total:.2f}"] + c.encode_args(out))
        print(out, [(k, data[k]["outcome"]) for k, _ in cases])


if __name__ == "__main__":
    main()
