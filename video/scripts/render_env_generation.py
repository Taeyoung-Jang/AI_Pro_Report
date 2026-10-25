"""환경 생성기의 세 산출물(MJCF, 이동 지도, 장면 그래프)을 시작 장면과 변경 장면으로 비교하는 그림을 만든다.

AFS가 상자 가로 위치를 1.0에서 0.0으로 바꾼 휴머노이드 사례를 사용한다.
출력: assets/env_generation.png (1920x1080), assets/env_map_<이름>.png
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

import common as c

SEED = 253785482
ATT = os.path.join(c.HUMANOID, f"seed_{SEED}/seeds/{SEED}/afs/attempts")
SCENES = [("시작 장면 (상자: 가장자리)", os.path.join(ATT, "attempt_00000/rollout")),
          ("AFS 변경 (상자: 중앙)", os.path.join(ATT, "attempt_00001/rollout"))]
RELATION_KO = {"CLEAR": "비어 있음", "FULLY_COVERED": "완전 점유", "PARTIALLY_COVERED": "일부 점유"}

font_manager.fontManager.addfont(c.FONT_REG)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=c.FONT_REG).get_name()
INK, MUTED = "#1e2024", "#6e7278"
BOX, GOAL, OBST, HUMAN, PATH = "#e8870e", "#2a6fdb", "#7a4fa0", "#1aa59a", "#228b54"


def hexc(rgb):
    return "#%02x%02x%02x" % rgb


def load(rollout):
    nav = json.load(open(os.path.join(rollout, "navigation_map.json")))
    graph = json.load(open(os.path.join(rollout, "scene_graph.json")))
    xml = open(os.path.join(rollout, "scene.xml")).read()
    m = re.search(r'<body name="clear_box" pos="([^"]+)">', xml)
    return nav, graph, m.group(0)


def draw_mjcf(ax, body_line, changed):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0, 0.95, "물리 시뮬레이션 모델 (MJCF)", fontsize=17, color=INK, weight="bold", va="top")
    ax.add_patch(FancyBboxPatch((0, 0.12), 1, 0.66, boxstyle="round,pad=0.01", fc="#f1f2f4", ec="#d5d7db"))
    pos = re.search(r'pos="([^"]+)"', body_line).group(1)
    lines = ['<body name="clear_box"', f'      pos="{pos}">', '  <geom type="box"', '    size=".4 .55 .35"',
             '    mass="2.0" .../>', "</body>"]
    for i, ln in enumerate(lines):
        hl = changed and i == 1
        ax.text(0.04, 0.70 - i * 0.095, ln, family="monospace", fontsize=14,
                color=hexc(c.FAIL_C) if hl else INK, weight="bold" if hl else "normal", va="top")


def draw_map(ax, nav, graph):
    res = nav["resolution_m"]
    ox, oy = nav["origin_xy_m"]
    grid = nav["blocked"]
    rows, cols = len(grid), len(grid[0])
    ax.imshow(grid, origin="lower", cmap=matplotlib.colors.ListedColormap(["#ffffff", "#9aa0a8"]),
              extent=(ox, ox + cols * res, oy, oy + rows * res), interpolation="nearest")
    goal = next(o for o in graph["objects"] if o["id"] == "robot_goal")["position"]
    ax.add_patch(Circle(goal[:2], 0.25, fc=GOAL, ec="white", lw=1.5, alpha=0.9, zorder=4))
    bx, by = nav["box_xy_m"]
    ax.add_patch(Rectangle((bx - 0.4, by - 0.55), 0.8, 1.1, fc="none", ec=BOX, lw=2.5, zorder=5))
    if nav["path_xy_m"]:
        xs, ys = zip(*nav["path_xy_m"])
        ax.plot(xs, ys, color=PATH, lw=3, zorder=6)
        label, col = "경로 있음", PATH
    else:
        label, col = "목표까지 경로 없음", hexc(c.FAIL_C)
    ax.text(0.02, 0.03, label, transform=ax.transAxes, fontsize=15, color="white", weight="bold",
            bbox=dict(fc=col, ec="none", boxstyle="round,pad=0.3"))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"이동 지도 (점유 격자 {cols}×{rows}, {res * 100:.0f} cm)", fontsize=17, color=INK,
                 weight="bold", loc="left")
    ax.set_aspect("equal")


def draw_graph(ax, graph):
    ax.set_xlim(-0.3, 8.3)
    ax.set_ylim(-2.4, 2.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("3D 장면 그래프 (객체와 관계)", fontsize=17, color=INK, weight="bold", loc="left")
    nodes = {}
    style = {"obstacle_1": (OBST, "장애물 1"), "obstacle_2": (OBST, "장애물 2"), "human_proxy_1": (HUMAN, "사람"),
             "clear_box": (BOX, "상자"), "robot_goal": (GOAL, "목표")}
    for o in graph["objects"]:
        if o["id"] in style:
            nodes[o["id"]] = o["position"][:2]
    for oid, (x, y) in nodes.items():
        col, name = style[oid]
        if oid == "clear_box":
            ax.add_patch(Rectangle((x - 0.4, y - 0.55), 0.8, 1.1, fc=col, ec="white", lw=2, zorder=3))
            ax.text(x - 0.55, y, name, ha="right", va="center", fontsize=13, color=INK, zorder=5)
        elif oid == "robot_goal":
            ax.add_patch(Circle((x, y), 0.25, fc=col, ec="white", lw=2.5, zorder=4))
            ax.text(x + 0.45, y, name, ha="left", va="center", fontsize=13, color=INK, zorder=5)
        else:
            ax.add_patch(Circle((x, y), 0.32, fc=col, ec="white", lw=2, zorder=3))
            ax.text(x, y - 0.62, name, ha="center", va="center", fontsize=13, color=INK, zorder=4)
    rel = graph["meta"]["initial_goal_relation"]
    (bx, by), (gx, gy) = nodes["clear_box"], nodes["robot_goal"]
    covered = rel["relation"] != "CLEAR"
    col = hexc(c.FAIL_C) if covered else PATH
    if abs(by - gy) > 0.05:
        ax.plot([bx, gx], [by, gy], color=col, lw=2.5, ls="--", zorder=2)
    ax.text(4.0, -2.15, f"상자–목표: {RELATION_KO.get(rel['relation'], rel['relation'])} "
            f"(거리 {rel['goal_to_box_distance_m']:.2f} m)", ha="center", fontsize=15, color="white",
            weight="bold", bbox=dict(fc=col, ec="none", boxstyle="round,pad=0.35"))
    ax.plot([0, 8, 8, 0, 0], [-1.8, -1.8, 1.8, 1.8, -1.8], color="#d5d7db", lw=1, zorder=1)


def main():
    data = [load(r) for _, r in SCENES]
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=hexc(c.BG))
    fig.text(0.025, 0.95, "환경 생성기: 하나의 장면 파라미터 → 세 가지 산출물", fontsize=30, weight="bold", color=INK)
    fig.text(0.025, 0.905, "값 하나(상자 가로 위치)만 바꿔도 세 산출물이 함께, 서로 일치하게 바뀝니다.",
             fontsize=18, color=MUTED)
    gs = fig.add_gridspec(2, 3, left=0.025, right=0.985, top=0.82, bottom=0.04, hspace=0.32, wspace=0.08,
                          width_ratios=[0.8, 1.3, 1.3])
    for row, ((title, _), (nav, graph, body)) in enumerate(zip(SCENES, data)):
        ax0 = fig.add_subplot(gs[row, 0])
        draw_mjcf(ax0, body, changed=row == 1)
        fig.text(0.025, 0.845 - row * 0.43, title, fontsize=21, weight="bold",
                 color=hexc(c.FAIL_C) if row else INK)
        draw_map(fig.add_subplot(gs[row, 1]), nav, graph)
        draw_graph(fig.add_subplot(gs[row, 2]), graph)
    out = os.path.join(c.ASSETS, "env_generation.png")
    fig.savefig(out, facecolor=fig.get_facecolor())
    print(out)


if __name__ == "__main__":
    main()
