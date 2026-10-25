"""회귀 재실행 결과 화면: 로봇 LLM을 GPT-6 Luna에서 Qwen3.8-27B로 바꿨을 때 저장 사례의 결과와 호출 수.

결과는 Qwen 비교 보고서(comparison_reports/*/summary.json)와 추가 1회(normal_429_followup_once_v1)에서 읽고,
호출 수는 각 실행의 decisions.jsonl에서 센다. Luna 기준선은 본 실험의 시작 장면 6회와 사전 점검 1회다.
출력: out/regression_qwen_card.mp4
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

QWEN = os.path.join(c.REPO, "experiment_results_qwen38/humanoid_qwen38_20261025_v1")
DUR = 12.0
CAP = 20  # 로봇 판단 상한


def calls(rollout):
    return sum('"call_started"' in ln for ln in open(os.path.join(rollout, "decisions.jsonl")))


def load():
    rep = sorted(glob.glob(os.path.join(QWEN, "comparison_reports/*/summary.json")))[-1]
    s = json.load(open(rep))
    follow = json.load(open(glob.glob(os.path.join(QWEN, "normal_429_followup_once_v1/reports/*/summary.json"))[0]))
    luna_calls = [calls(os.path.join(p, "rollout")) for p in
                  glob.glob(os.path.join(c.HUMANOID, "seed_*/seeds/*/*/attempts/attempt_00000"))]
    luna_calls.append(calls(os.path.join(c.HUMANOID, "control")))
    qwen_pass = []
    for suite in (os.path.join(QWEN, "qwen"), os.path.join(QWEN, "normal_429_followup_once_v1")):
        for a in sorted(glob.glob(os.path.join(suite, "attempts/attempt_*"))):
            r = json.load(open(os.path.join(a, "rollout/result.json")))
            if r.get("task_outcome") == "PASS":
                qwen_pass.append(calls(os.path.join(a, "rollout")))
    return s, follow, sorted(luna_calls), sorted(qwen_pass)


def outcome_text(case):
    p, f, x = case["pass"], case["fail"], case["excluded"]
    parts = [f"PASS {p}"] if p else []
    parts += [f"FAIL {f}"] if f else []
    parts += [f"제외 {x}"] if x else []
    return " · ".join(parts)


def main():
    s, follow, luna, qwen = load()
    cand = {c_["baseline_role"]: c_ for c_ in s["candidate_suite"]["cases"]}
    ref = {c_["baseline_role"]: c_ for c_ in s["reference_suite"]["cases"]}
    fol = follow["cases"][0]
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    d.text((60, 40), "회귀 재실행 결과 · 본 실험 저장 사례", font=c.font(30), fill=c.MUTED)
    d.text((60, 84), "로봇 LLM을 GPT-6 Luna → Qwen3.8-27B로 바꿔 다시 실행", font=c.font(48, True), fill=c.INK)

    # 왼쪽: 결과 표
    x0, y0 = 60, 200
    cols = [x0, x0 + 300, x0 + 560]
    for cx, h in zip(cols, ["원래 사례", "Qwen 재실행", "분류"]):
        d.text((cx, y0), h, font=c.font(28, True), fill=c.MUTED)
    rows = [
        ("시작 장면", "Luna 7/7 PASS", f"{outcome_text(cand['success_control'])}\n추가 1회 {outcome_text(fol)}",
         "유지(성공)", c.PASS_C),
        ("목표 점유", "원래 FAIL", f"{outcome_text(cand['observed_failure'])}\n(Luna 재실행 {outcome_text(ref['observed_failure'])})",
         "유지(실패)", c.INK),
    ]
    y = y0 + 60
    for name, orig, res, label, col in rows:
        d.line([x0, y - 14, x0 + 800, y - 14], fill=(215, 215, 212), width=2)
        d.text((cols[0], y), name, font=c.font(34, True), fill=c.INK)
        d.text((cols[0], y + 50), orig, font=c.font(26), fill=c.MUTED)
        d.multiline_text((cols[1], y), res, font=c.font(30), fill=c.INK, spacing=12)
        d.text((cols[2], y), label, font=c.font(34, True), fill=col)
        if name == "시작 장면":  # 계획한 3회는 제외 1회 때문에 판정 불가, 추가 1회가 유지(성공)
            d.text((cols[2], y + 50), "(계획 3회만으로는 판정 불가)", font=c.font(22), fill=c.MUTED)
        y += 170
    d.text((x0, y), "API 호출 한도 오류(429) 1회는 실패가 아닌 '판정 불가'로 분리", font=c.font(26), fill=c.MUTED)

    # 오른쪽: 시작 장면 성공 실행의 로봇 LLM 호출 수
    X, Y, W = 960, 200, 900
    d.text((X, Y), "시작 장면 성공까지 쓴 로봇 판단 횟수", font=c.font(30, True), fill=c.INK)
    ax_y = Y + 420
    left, right = X + 160, X + W - 40

    def px(v):
        return left + (right - left) * v / CAP

    for v in range(0, CAP + 1, 5):
        d.line([px(v), Y + 90, px(v), ax_y], fill=(225, 225, 222), width=2)
        d.text((px(v), ax_y + 12), str(v), font=c.font(24), fill=c.MUTED, anchor="ma")
    d.line([px(CAP), Y + 80, px(CAP), ax_y], fill=c.FAIL_C, width=4)
    d.text((px(CAP), Y + 70), "상한 20회", font=c.font(24, True), fill=c.FAIL_C, anchor="md")

    def median(xs):
        n = len(xs)
        return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2

    for k, (label, vals, col) in enumerate([("Luna", luna, c.RAND_C), ("Qwen", qwen, c.AFS_C)]):
        cy = Y + 170 + k * 150
        d.text((X, cy - 20), label, font=c.font(34, True), fill=col)
        d.text((X, cy + 22), f"{len(vals)}회", font=c.font(24), fill=c.MUTED)
        seen = {}
        for v in vals:
            off = seen.get(v, 0)
            seen[v] = off + 1
            r = 16
            yy = cy - off * 34
            d.ellipse([px(v) - r, yy - r, px(v) + r, yy + r], fill=col, outline=(255, 255, 255), width=3)
        m = median(vals)
        d.line([px(m), cy + 30, px(m), cy + 58], fill=c.INK, width=4)
        d.text((px(m) + 8, cy + 44), f"중앙값 {m:g}회", font=c.font(24, True), fill=c.INK, anchor="lm")

    # 아래: 교훈
    d.rectangle([60, 860, 1860, 990], fill=(234, 240, 250))
    d.text((90, 885), "결과는 그대로였지만 같은 장면을 끝내는 데 로봇 판단을 약 2배 사용 → 상한에 더 가까워짐",
           font=c.font(34, True), fill=c.AFS_C)
    d.text((90, 940), "회귀 테스트는 PASS/FAIL뿐 아니라 판단 횟수·소요 시간 같은 자원 사용량 변화도 함께 봐야 한다",
           font=c.font(28), fill=c.INK)
    png = os.path.join(c.ASSETS, "regression_qwen_card.png")
    im.save(png)
    out = os.path.join(c.OUT, "regression_qwen_card.mp4")
    c.run_ffmpeg(["-loop", "1", "-t", str(DUR), "-i", png, "-vf", f"fps={c.FPS}"] + c.encode_args(out))
    print(out, "Luna", luna, "Qwen", qwen)


if __name__ == "__main__":
    main()
