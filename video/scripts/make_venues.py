"""실험 2 확장: 창고·사무실·교차로 배치의 이동 지도, 시작 장면 실행 영상, AFS/Random 테스트 결과를 한 화면에 보여 준다.

이동 지도는 각 장소 시작 장면의 navigation_map.json(점유 격자와 초기 경로)과 scene_graph.json에서 그린다.
시작 장면 영상은 장소마다 길이가 달라 DUR초에 맞춰 빠르게 재생한다.
결과는 suite_summary.json에서 읽는다.
출력: out/humanoid_venues.mp4
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Rectangle
from PIL import Image, ImageDraw

import common as c

DUR = 14.0
VW, VH = 580, 326
MAP_H = 305
X0, GAP = 50, 45
MAP_Y, VID_Y = 200, 530

VENUES = [("warehouse", "창고", "양옆 선반 4개"),
          ("office", "사무실", "칸막이 문·책상·의자"),
          ("junction", "교차로", "엇갈린 모퉁이 벽 2개")]
LABEL_KO = {"shelf": "선반", "desk": "책상", "chair": "의자", "door_partition": "칸막이",
            "blind_corner": "모퉁이 벽", "exit_corner": "모퉁이 벽"}

font_manager.fontManager.addfont(c.FONT_REG)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=c.FONT_REG).get_name()


def label_of(oid):
    for k, v in LABEL_KO.items():
        if oid.startswith(k):
            return v
    return None


def render_map(venue, path):
    rollout = os.path.join(c.VENUES, venue, "control/rollout")
    nav = json.load(open(os.path.join(rollout, "navigation_map.json")))
    graph = json.load(open(os.path.join(rollout, "scene_graph.json")))
    res, (ox, oy), grid = nav["resolution_m"], nav["origin_xy_m"], nav["blocked"]
    rows, cols = len(grid), len(grid[0])
    fig = plt.figure(figsize=(VW / 100, MAP_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(grid, origin="lower", cmap=matplotlib.colors.ListedColormap(["#ffffff", "#aab0b8"]),
              extent=(ox, ox + cols * res, oy, oy + rows * res), interpolation="nearest")
    if nav["path_xy_m"]:
        xs, ys = zip(*nav["path_xy_m"])
        ax.plot(xs, ys, color="#228b54", lw=2.5, ls="--")
    objs = {o["id"]: o["position"][:2] for o in graph["objects"]}
    ax.add_patch(Circle(objs["robot_goal"], 0.22, fc="#2a6fdb", ec="white", lw=1.5, zorder=4))
    bx, by = nav["box_xy_m"]
    ax.add_patch(Rectangle((bx - 0.4, by - 0.55), 0.8, 1.1, fc="#e8870e", ec="white", lw=1.5, zorder=4))
    hx, hy = objs["human_proxy_1"]
    ax.add_patch(Circle((hx, hy), 0.22, fc="#1aa59a", ec="white", lw=1.5, zorder=4))
    ax.annotate("", xy=(hx, hy - 1.0), xytext=(hx, hy - 0.3),
                arrowprops=dict(arrowstyle="->", color="#1aa59a", lw=2), zorder=4)
    ax.plot([1.0], [0.0], "o", color="#1e2024", ms=8, zorder=5)
    seen = set()
    for oid, (x, y) in objs.items():
        name = label_of(oid)
        if name and (name, round(y)) not in seen:
            seen.add((name, round(y)))
            ax.text(x, y, name, ha="center", va="center", fontsize=12, color="#1e2024", zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.75, boxstyle="round,pad=0.15"))
    ax.set_xlim(ox, ox + cols * res)
    ax.set_ylim(oy, oy + rows * res)
    ax.axis("off")
    fig.savefig(path)
    plt.close(fig)


def result_lines(summary, venue):
    v = next(x for x in summary["venues"] if x["venue"] == venue)
    if not v["complete"]:
        return [("시작 장면부터 FAIL (로봇 판단 20회 소진)", c.FAIL_C), ("→ 비교 실행을 진행하지 않음", c.MUTED)]
    res = {}
    for m in ("afs", "random"):  # 첫 실행(공통 시작 장면)을 뺀 평가 실행만 센다
        outs = [json.load(open(p))["task_outcome"] for p in sorted(glob.glob(os.path.join(
            c.VENUES, venue, f"campaign/seeds/*/{m}/attempts/attempt_*/rollout/result.json")))][1:]
        res[m] = (outs.count("FAIL"), len(outs))
    (af, an), (rf, rn) = res["afs"], res["random"]
    return [(f"AFS  FAIL {af}/{an}", c.AFS_C), (f"Random 테스트  FAIL {rf}/{rn}", c.RAND_C)]


def main():
    summary = json.load(open(os.path.join(c.VENUES, "suite_summary.json")))
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    d.text((X0, 34), "실험 2 확장 · 다른 배치에서도 실행", font=c.font(46, True), fill=c.INK)
    d.text((c.W - X0, 50), "같은 G1 휴머노이드 + LLM Agent · 장소마다 공통 시작 장면 + 방법당 2회", font=c.font(26), fill=c.MUTED, anchor="ra")
    for i, (venue, name, desc) in enumerate(VENUES):
        x = X0 + i * (VW + GAP)
        d.text((x, 118), name, font=c.font(36, True), fill=c.INK)
        d.text((x + d.textlength(name, font=c.font(36, True)) + 20, 132), desc, font=c.font(24), fill=c.MUTED)
        mp = os.path.join(c.ASSETS, f"venue_map_{venue}.png")
        render_map(venue, mp)
        im.paste(Image.open(mp).convert("RGB"), (x, MAP_Y))
        d.rectangle([x - 2, MAP_Y - 2, x + VW + 1, MAP_Y + MAP_H + 1], outline=(215, 215, 212), width=2)
        d.rectangle([x - 3, VID_Y - 3, x + VW + 2, VID_Y + VH + 2], fill=(215, 215, 212))
        y = VID_Y + VH + 22
        for text, col in result_lines(summary, venue):
            d.text((x, y), text, font=c.font(30, True), fill=col)
            y += 44
    legend = "지도: ● 출발  파랑 목표  주황 상자  청록 사람(화살표 방향으로 횡단)  점선 초기 경로"
    d.text((X0, c.H - 46), legend + "   ·   아래 영상은 시작 장면, 빠르게 재생", font=c.font(24), fill=c.MUTED)
    bg = os.path.join(c.ASSETS, "humanoid_venues_bg.png")
    im.save(bg)

    args = ["-loop", "1", "-t", str(DUR), "-i", bg]
    for venue, _, _ in VENUES:
        args += ["-i", os.path.join(c.VENUES, venue, "control/rollout/rollout.mp4")]
    parts, last = [], "0:v"
    for i, (venue, _, _) in enumerate(VENUES, start=1):
        src = os.path.join(c.VENUES, venue, "control/rollout/rollout.mp4")
        sp = c_duration(src) / (DUR - 1.0)
        parts.append(f"[{i}:v]setpts=PTS/{sp:.3f},scale={VW}:{VH},fps={c.FPS},"
                     f"tpad=stop_mode=clone:stop_duration={DUR}[v{i}]")
        x = X0 + (i - 1) * (VW + GAP)
        parts.append(f"[{last}][v{i}]overlay={x}:{VID_Y}:shortest=0:eof_action=repeat[o{i}]")
        last = f"o{i}"
    out = os.path.join(c.OUT, "humanoid_venues.mp4")
    c.run_ffmpeg(args + ["-filter_complex", ";".join(parts), "-map", f"[{last}]", "-t", str(DUR)] + c.encode_args(out))
    print(out)


def c_duration(path):
    import subprocess
    probe = c.ffmpeg_exe().replace("ffmpeg", "ffprobe")
    r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


if __name__ == "__main__":
    main()
