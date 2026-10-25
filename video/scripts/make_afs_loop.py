"""AFS 한 바퀴: 휴머노이드 본 실험 한 세트(시드 253785482)의 시작 장면(PASS) → AFS 요청·응답 → 규칙 검증 → 실행(FAIL).

환경 생성 그림·휴머노이드 클립과 같은 사례다. 가설·반증 조건·변경값·검증 항목은
reports/*/253785482_afs_proposals.json의 첫 제안에서 읽고, 결과는 attempt_00001의 result.json에서 읽는다.
화면 4장(관측·제안·검증·결과)을 이어 붙이며, 관측과 결과 장에는 실행 영상을 넣는다.
출력: out/afs_loop_box_shift.mp4
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

SEED = 253785482
ROOT = os.path.join(c.HUMANOID, f"seed_{SEED}")
ATT = os.path.join(ROOT, f"seeds/{SEED}/afs/attempts")
# (장 이름, 길이 초)
CARDS = [("observe", 12.0), ("propose", 23.0), ("validate", 9.0), ("result", 6.0)]  # 내레이션 문장 시각에 맞춘 길이
VW, VH, VX, VY = 1100, 619, 760, 250

FAMILY_KO = {"goal_occupied": "목표 위치 점유", "obstacle_interference": "장애물 간섭",
             "locomotion_stall": "이동 정체", "collision": "충돌"}
# 영어 원문 옆에 보여 줄 한글 요약 (원문은 proposals.json의 evidence 필드)
KO = {
    "hypothesis": "상자를 목표 위치 한가운데로 옮기면 상자가 목표 영역을 덮는다. 시작 장면 실행에서는 상자가 목표에서 떨어져 있어 "
                  "써 본 적 없는 행동이 필요해지므로, 관측된 성공 패턴이 깨질 수 있다.",
    "failure_prediction": "상자가 목표 위에 남아 실행이 완료되지 못하고 정체할 수 있다.",
    "alternative": "로봇이 상자를 밀어내거나 다른 방법으로 목표에 도달할 수도 있다.",
    "falsification": "PASS가 나오면 이 장면이 목표 완료를 막지 못한다는 뜻이다.",
}


def load():
    rep = glob.glob(os.path.join(ROOT, "reports/*/"))[0]
    prop = json.load(open(glob.glob(os.path.join(rep, f"{SEED}_afs_proposals.json"))[0]))[0]
    base = json.load(open(os.path.join(ATT, "attempt_00000/rollout/result.json")))
    fail = json.load(open(os.path.join(ATT, "attempt_00001/rollout/result.json")))
    calls = {}
    for a in ("attempt_00000", "attempt_00001"):
        calls[a] = sum('"call_started"' in ln for ln in open(os.path.join(ATT, a, "rollout/decisions.jsonl")))
    return prop, base, fail, calls


def header(d, step, title):
    d.text((60, 40), f"AFS 한 바퀴 · {step}", font=c.font(30), fill=c.MUTED)
    d.text((60, 84), title, font=c.font(48, True), fill=c.INK)


def wrap(d, text, font, width):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=font) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    return lines


def block(d, x, y, label, text, width, col=c.INK, size=30):
    d.text((x, y), label, font=c.font(24, True), fill=c.MUTED)
    y += 38
    f = c.font(size)
    for ln in wrap(d, text, f, width):
        d.text((x, y), ln, font=f, fill=col)
        y += int(size * 1.45)
    return y + 18


def card_observe(base, calls, path):
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    header(d, "① 이전 실행 관측", "시작 장면: 상자는 통로 가장자리 (가로 위치 1.0)")
    y = 260
    for k, v, col in [("결과", base["task_outcome"], c.PASS_C), ("로봇 판단", f"{calls['attempt_00000']}회", c.INK),
                      ("상자", "움직이지 않음", c.INK), ("밀기 요청", "없음", c.INK)]:
        d.text((60, y), k, font=c.font(28), fill=c.MUTED)
        d.text((330, y - 4), v, font=c.font(36, True), fill=col)
        y += 70
    y += 20
    d.multiline_text((60, y), "AFS는 영상이 아니라\n이 행동 기록을 텍스트로 읽는다", font=c.font(28), fill=c.MUTED, spacing=10)
    d.rectangle([VX - 3, VY - 3, VX + VW + 2, VY + VH + 2], fill=(215, 215, 212))
    im.save(path)


def card_propose(prop, path):
    ev = prop["candidate"]["evidence"]
    ba = prop["candidate"]["branch_audit"]
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    header(d, "② AFS 요청 → 응답", f"AFS의 LLM (GPT-6 Luna) · 응답 {prop['wall_s']:.0f}초")
    axis = ba["changed_axis"]
    d.rectangle([60, 190, 1860, 280], fill=(234, 240, 250))
    d.text((90, 214), f"제안: 상자를 통로 가장자리 → 중앙으로  (가로 위치 {ba['before'][axis]} → {ba['after'][axis]}, 변수 하나만 변경)",
           font=c.font(38, True), fill=c.AFS_C)
    y = 310
    y = block(d, 60, y, "가설", KO["hypothesis"], 1080)
    y = block(d, 60, y, "예상 실패", KO["failure_prediction"], 1080, c.FAIL_C)
    y = block(d, 60, y, "다른 설명", KO["alternative"], 1080)
    block(d, 60, y, "반증 조건", KO["falsification"], 1080)
    # 오른쪽: 원문 일부
    d.rectangle([1200, 310, 1860, 1010], fill=(36, 40, 48))
    d.text((1225, 330), "response (원문)", font=c.font(22), fill=(160, 166, 176))
    yy = 375
    mono = c.font(21)
    for key in ("hypothesis", "failure_prediction", "alternative", "falsification"):
        d.text((1225, yy), f'"{key}":', font=mono, fill=(130, 190, 255))
        yy += 30
        for ln in wrap(d, ev[key], mono, 600)[:4]:
            d.text((1245, yy), ln, font=mono, fill=(230, 232, 236))
            yy += 28
        yy += 14
    d.text((60, 1030), f"노린 실패 유형: {FAMILY_KO.get(ev['target_family'], ev['target_family'])}  ·  근거 실행: 시작 장면 ({ba['anchor_outcome']})",
           font=c.font(24), fill=c.MUTED)
    im.save(path)


def card_validate(prop, path):
    cand = prop["candidate"]
    ba = cand["branch_audit"]
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    header(d, "③ 규칙 기반 검증", "LLM 제안은 검사를 통과해야만 실행된다")
    checks = [
        ("근거로 든 실행이 실제로 있다", f"시작 장면 기록 ({ba['anchor_outcome']})", ba["anchor_case_id"] is not None),
        ("바꾼 장면 변수의 수", f"{len(cand['changed_axes'])}개: 상자 가로 위치", len(cand["changed_axes"]) <= 2),
        ("나머지 값이 그대로다", "바꾼 변수 외 장면 값 일치 확인", ba["unchanged_parameters_verified"]),
        ("최소 변경량 (변수 범위의 10%)", f"범위 대비 {100 * cand['exploration']['normalized_changes'][ba['changed_axis']]:.0f}% 변경",
         cand["exploration"]["normalized_changes"][ba["changed_axis"]] >= 0.1),
        ("로봇·정책·작업·판단 상한", "변경 없음 (고정)", True),
    ]
    y = 250
    for name, detail, ok in checks:
        col = c.PASS_C if ok else c.FAIL_C
        d.ellipse([60, y + 4, 104, y + 48], fill=col)
        d.text((82, y + 26), "✓" if ok else "✗", font=c.font(30, True), fill=(255, 255, 255), anchor="mm")
        d.text((140, y), name, font=c.font(36, True), fill=c.INK)
        d.text((140, y + 52), detail, font=c.font(28), fill=c.MUTED)
        y += 130
    d.rectangle([60, y + 10, 760, y + 90], fill=c.PASS_C)
    d.text((410, y + 50), "통과 → 환경 생성·실행", font=c.font(36, True), fill=(255, 255, 255), anchor="mm")
    im.save(path)


def card_result(fail, calls, path):
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    header(d, "④ 실행 결과", "상자를 통로 중앙으로 옮긴 장면 (가로 위치 0.0)")
    dist = fail.get("goal_progress", {}).get("distance_m")
    y = 260
    rows = [("결과", fail["task_outcome"], c.FAIL_C), ("검출 유형", "목표 위치 점유", c.FAIL_C),
            ("로봇 판단", f"{calls['attempt_00001']}회 모두 사용", c.INK)]
    if dist is not None:
        rows.append(("목표까지", f"{dist:.2f} m 남음", c.INK))
    for k, v, col in rows:
        d.text((60, y), k, font=c.font(28), fill=c.MUTED)
        d.text((300, y - 4), v, font=c.font(36, True), fill=col)
        y += 70
    d.rectangle([60, y + 30, 700, y + 110], fill=c.AFS_C)
    d.text((380, y + 70), "예상한 실패와 일치", font=c.font(36, True), fill=(255, 255, 255), anchor="mm")
    d.rectangle([VX - 3, VY - 3, VX + VW + 2, VY + VH + 2], fill=(215, 215, 212))
    im.save(path)


def segment(card_png, dur, out, video=None, speed=1.0, start=0.0):
    if video is None:
        c.run_ffmpeg(["-loop", "1", "-t", str(dur), "-i", card_png, "-vf", f"fps={c.FPS}", "-t", str(dur)] + c.encode_args(out))
        return
    fc = (f"[1:v]trim=start={start},setpts=(PTS-STARTPTS)/{speed},scale={VW}:{VH},fps={c.FPS},"
          f"tpad=stop_mode=clone:stop_duration={dur}[v];[0:v][v]overlay={VX}:{VY}:shortest=0[out]")
    c.run_ffmpeg(["-loop", "1", "-t", str(dur), "-i", card_png, "-i", video, "-filter_complex", fc,
                  "-map", "[out]", "-t", str(dur)] + c.encode_args(out))


def video_len(path):
    import subprocess
    probe = c.ffmpeg_exe().replace("ffmpeg", "ffprobe")
    r = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


def main():
    prop, base, fail, calls = load()
    tmp = os.path.join(c.ASSETS, "afs_loop")
    os.makedirs(tmp, exist_ok=True)
    paths = {k: os.path.join(tmp, f"{k}.png") for k, _ in CARDS}
    card_observe(base, calls, paths["observe"])
    card_propose(prop, paths["propose"])
    card_validate(prop, paths["validate"])
    card_result(fail, calls, paths["result"])
    v_base = os.path.join(ATT, "attempt_00000/rollout/rollout.mp4")
    v_fail = os.path.join(ATT, "attempt_00001/rollout/rollout.mp4")
    segs = []
    for k, dur in CARDS:
        out = os.path.join(tmp, f"{k}.mp4")
        if k == "observe":
            segment(paths[k], dur, out, v_base, speed=video_len(v_base) / (dur - 1))
        elif k == "result":
            ln = video_len(v_fail)
            segment(paths[k], dur, out, v_fail, speed=12.0, start=max(0.0, ln - 12.0 * (dur - 2)))
        else:
            segment(paths[k], dur, out)
        segs.append(out)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in segs)
    out = os.path.join(c.OUT, "afs_loop_box_shift.mp4")
    c.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    print(out, sum(d for _, d in CARDS), "초")


if __name__ == "__main__":
    main()
