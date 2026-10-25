"""입력 화면: 휴머노이드 시드 253785482 탐색의 실제 입력값(작업 목표·실행 조건·장면 변수와 범위·시도 횟수)을 보여 준다.

값은 afs/protocol.json(시드·시도 횟수·AFS 요청 상한)과 첫 제안의 context.json(task_contract, scene_domain.axes)에서 읽는다.
세 묶음을 차례로 나타나게 한다.
출력: out/input_settings.mp4
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

SEED = 253785482
AFS = os.path.join(c.HUMANOID, f"seed_{SEED}/seeds/{SEED}/afs")
DUR = 21.0
REVEAL = [0.0, 5.0, 10.0]  # 세 묶음이 나타나는 시각

# 장면 변수 이름 → (묶음, 한글 이름, 단위)
GROUPS = [
    ("상자", [("box_mass_kg", "질량", "kg"), ("box_friction", "마찰계수", ""),
             ("box_lateral_fraction", "가로 위치", ""), ("box_goal_x_m", "진행 방향 위치", "m")]),
    ("바닥·통로", [("floor_friction", "바닥 마찰계수", ""), ("corridor_width_m", "통로 폭", "m")]),
    ("사람", [("human_x_m", "횡단 위치", "m"), ("human_speed_mps", "속도", "m/s"),
             ("human_trigger_distance_m", "출발 거리", "m")]),
    ("장애물 2개", [("obstacle_{i}_x_m", "위치", "m"), ("obstacle_{i}_lateral_fraction", "가로 위치", ""),
                 ("obstacle_{i}_size_x_m", "가로 크기", "m"), ("obstacle_{i}_size_y_m", "세로 크기", "m"),
                 ("obstacle_{i}_height_m", "높이", "m"), ("obstacle_{i}_yaw_deg", "회전", "°")]),
]


def fmt(v):
    return f"{v:g}"


def load():
    plan = json.load(open(os.path.join(AFS, "protocol.json")))["lock"]["plan"]
    ctx = json.load(open(os.path.join(AFS, "proposals/proposal_00000/context.json")))
    return plan, ctx


def draw(plan, ctx, upto, path):
    axes = ctx["scene_domain"]["axes"]
    task = ctx["task_contract"]
    goal = task["goal"]
    budget = plan["budget"]
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    d.text((60, 40), "입력 · 탐색 1회분 설정 (실제 설정 파일의 값)", font=c.font(30), fill=c.MUTED)
    d.text((60, 84), "무엇을 시험하고, 무엇을 바꿀 수 있고, 몇 번 시도하나", font=c.font(48, True), fill=c.INK)

    def box(x, y, w, h, title):
        d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=(215, 215, 212), width=2)
        d.text((x + 28, y + 22), title, font=c.font(32, True), fill=c.AFS_C)

    # ① 작업 목표
    x, y, w = 60, 190, 720
    box(x, y, w, 300, "① 작업 목표")
    gx, gy = goal["target_xy_m"]
    lines = [f"목표 ({fmt(gx)}, {fmt(gy)}) m 반경 {fmt(goal['radius_m'])} m 안에",
             f"{fmt(goal['dwell_s'])}초 이상 머무르기",
             f"로봇 판단 {task['episode_budget']['max_robot_policy_calls']}회 이내"]
    for i, ln in enumerate(lines):
        d.text((x + 28, y + 90 + i * 56), ln, font=c.font(32), fill=c.INK)
    if upto >= 1:
        # ② 시도 횟수
        y2 = 520
        box(x, y2, w, 480, "② 실험 세트와 시도 횟수")
        rows = [("세트 (시드)", str(plan["seed"])), ("방법", plan["method"].upper()),
                ("실행 시도", f"{budget['max_attempts']}회 (첫 1회는 공통 시작 장면)"),
                ("AFS 제안 요청", f"최대 {budget['max_afs_requests']}회"),
                ("AFS의 LLM", "GPT-6 Luna" if budget["afs_model"].endswith("gpt-6-luna") else budget["afs_model"])]
        for i, (k, v) in enumerate(rows):
            d.text((x + 28, y2 + 90 + i * 70), k, font=c.font(28), fill=c.MUTED)
            d.text((x + 260, y2 + 86 + i * 70), v, font=c.font(32, True), fill=c.INK)
    if upto >= 2:
        # ③ 환경 변경 축
        X, Y, W = 830, 190, 1030
        box(X, Y, W, 810, f"③ 바꿀 수 있는 장면 변수 {len(axes)}개와 범위")
        # 왼쪽 열: 상자·바닥·사람, 오른쪽 열: 장애물
        for col, groups in ((0, GROUPS[:3]), (1, GROUPS[3:])):
            cx = X + 28 + col * 520
            yy = Y + 92
            for gname, items in groups:
                d.text((cx, yy), gname, font=c.font(28, True), fill=c.INK)
                yy += 46
                for key, name, unit in items:
                    lo, hi = axes[key.format(i=1)]
                    d.text((cx + 20, yy), name, font=c.font(26), fill=c.MUTED)
                    d.text((cx + 230, yy), f"{fmt(lo)} ~ {fmt(hi)} {unit}".strip(), font=c.font(26), fill=c.INK)
                    yy += 40
                yy += 18
            if col == 1:
                d.text((cx, yy), "(장애물 1·2 각각 6개 변수)", font=c.font(24), fill=c.MUTED)
    im.save(path)


def main():
    plan, ctx = load()
    tmp = os.path.join(c.ASSETS, "input_card")
    os.makedirs(tmp, exist_ok=True)
    segs = []
    for i, t0 in enumerate(REVEAL):
        png = os.path.join(tmp, f"card_{i}.png")
        draw(plan, ctx, i, png)
        t1 = REVEAL[i + 1] if i + 1 < len(REVEAL) else DUR
        mp4 = os.path.join(tmp, f"card_{i}.mp4")
        c.run_ffmpeg(["-loop", "1", "-t", str(t1 - t0), "-i", png, "-vf", f"fps={c.FPS}"] + c.encode_args(mp4))
        segs.append(mp4)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in segs)
    out = os.path.join(c.OUT, "input_settings.mp4")
    c.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    print(out, len(ctx["scene_domain"]["axes"]), "축")


if __name__ == "__main__":
    main()
