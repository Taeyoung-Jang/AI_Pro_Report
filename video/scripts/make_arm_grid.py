"""실험 1 로봇팔 AFS 12회 vs Random 12회를 한 화면에 동시 재생하는 클립을 만든다.

열 = 세트(시드 661·673·677), 행 = 시도 순서. 재생이 끝나면 PASS/FAIL 테두리와 합계를 보여 준다.
원본 영상은 15초 실행을 2배속(7.5초)으로 기록한 것이다.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

SRC = os.path.join(c.ARM, "environment_comparison_v2")
SEEDS = [661, 673, 677]
METHODS = [("afs", "AFS (능동 실패 탐색)", c.AFS_C), ("random", "Random 테스트 (무작위 선택)", c.RAND_C)]
TW, TH, GAP = 290, 160, 12
TOP, HEAD = 112, 96
PANEL_W = 3 * TW + 2 * GAP
PLAY_S, HOLD_S = 7.5, 4.0


def tiles():
    out = []
    for mi, (m, _, _) in enumerate(METHODS):
        x0 = 36 + mi * (PANEL_W + 60)
        for si, seed in enumerate(SEEDS):
            for a in range(4):
                d = os.path.join(SRC, f"seed_{seed}/{m}/attempt_{a:05d}")
                outcome = json.load(open(os.path.join(d, "receipt.json")))["task_outcome"]
                video = glob.glob(os.path.join(d, "videos/*.mp4"))[0]
                x = x0 + si * (TW + GAP)
                y = TOP + HEAD + a * (TH + GAP)
                out.append(dict(method=m, seed=seed, attempt=a, outcome=outcome, video=video, x=x, y=y))
    return out


def draw_layers(ts, bg_path, fg_path):
    bg = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(bg)
    d.text((36, 30), "실험 1 · Panda 로봇팔 + GR00T N1.7: 같은 시도 횟수 12회씩", font=c.font(44, True), fill=c.INK)
    d.text((c.W - 36, 44), "영상 2배속 · 행=시도 순서, 열=세트", font=c.font(26), fill=c.MUTED, anchor="ra")
    for mi, (m, label, col) in enumerate(METHODS):
        x0 = 36 + mi * (PANEL_W + 60)
        d.text((x0, TOP), label, font=c.font(34, True), fill=col)
        for si, seed in enumerate(SEEDS):
            d.text((x0 + si * (TW + GAP) + TW // 2, TOP + HEAD - 14), f"세트 {si + 1} (시드 {seed})",
                   font=c.font(22), fill=c.MUTED, anchor="md")
    for t in ts:
        d.rectangle([t["x"] - 4, t["y"] - 4, t["x"] + TW + 3, t["y"] + TH + 3], fill=(215, 215, 212))
    d.text((36, c.H - 46), "각 세트의 처음 2회(시도 0·1)는 두 방법이 같은 장면을 쓰는 공통 시작 장면입니다.",
           font=c.font(24), fill=c.MUTED)
    bg.save(bg_path)

    fg = Image.new("RGBA", (c.W, c.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    for mi, (m, label, col) in enumerate(METHODS):
        x0 = 36 + mi * (PANEL_W + 60)
        n_fail = sum(t["outcome"] == "FAIL" for t in ts if t["method"] == m)
        d.text((x0 + PANEL_W, TOP + 2), f"FAIL {n_fail}/12 = {100 * n_fail / 12:.1f}%",
               font=c.font(34, True), fill=c.FAIL_C, anchor="ra")
    for t in ts:
        col = c.FAIL_C if t["outcome"] == "FAIL" else c.PASS_C
        x, y = t["x"], t["y"]
        d.rectangle([x - 5, y - 5, x + TW + 4, y + TH + 4], outline=col + (255,), width=6)
        if t["outcome"] == "PASS":
            d.rectangle([x, y, x + TW, y + TH], fill=(255, 255, 255, 110))
        bw = 92
        d.rectangle([x, y, x + bw, y + 36], fill=col + (235,))
        d.text((x + bw // 2, y + 18), t["outcome"], font=c.font(24, True), fill=(255, 255, 255, 255), anchor="mm")
    fg.save(fg_path)


def main():
    os.makedirs(c.OUT, exist_ok=True)
    ts = tiles()
    bg_path = os.path.join(c.ASSETS, "arm_grid_bg.png")
    fg_path = os.path.join(c.ASSETS, "arm_grid_fg.png")
    draw_layers(ts, bg_path, fg_path)
    total = PLAY_S + HOLD_S
    args = ["-loop", "1", "-t", str(total), "-i", bg_path]
    for t in ts:
        args += ["-i", t["video"]]
    args += ["-loop", "1", "-t", str(total), "-i", fg_path]
    parts, last = [], "0:v"
    for i, t in enumerate(ts, start=1):
        parts.append(f"[{i}:v]scale={TW}:{TH},fps={c.FPS},tpad=stop_mode=clone:stop_duration={total}[v{i}]")
    for i, t in enumerate(ts, start=1):
        parts.append(f"[{last}][v{i}]overlay={t['x']}:{t['y']}:shortest=0:eof_action=repeat[o{i}]")
        last = f"o{i}"
    fg_idx = len(ts) + 1
    parts.append(f"[{last}][{fg_idx}:v]overlay=0:0:enable='gte(t,{PLAY_S})'[out]")
    out = os.path.join(c.OUT, "arm_grid_12v12.mp4")
    c.run_ffmpeg(args + ["-filter_complex", ";".join(parts), "-map", "[out]", "-t", str(total)] + c.encode_args(out))
    print(out, {m: sum(t["outcome"] == "FAIL" for t in ts if t["method"] == m) for m, _, _ in METHODS})


if __name__ == "__main__":
    main()
