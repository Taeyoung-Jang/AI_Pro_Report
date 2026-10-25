"""휴머노이드 본 실험의 시작 장면(PASS)과 상자 위치 변수 1개 변경(FAIL)을 이어 붙인 클립을 만든다.

실행 영상은 대부분 로봇 LLM의 응답을 기다리는 시간이므로, 로봇이 움직이는 구간은 느리게(SLOW배),
응답 대기 구간은 빠르게(FAST배) 재생하고 화면 오른쪽 위에 현재 배속을 표시한다.
하단 자막은 decisions.jsonl의 LLM 판단과 도구 결과를 요약한 것이다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c

SEED = 253785482
ATT = os.path.join(c.HUMANOID, f"seed_{SEED}/seeds/{SEED}/afs/attempts")
SLOW, FAST = 4, 30

# (판단 번호 범위, 자막). 번호는 decisions.jsonl의 observation_version이다.
CASES = [
    dict(name="humanoid_baseline_pass", rollout=os.path.join(ATT, "attempt_00000/rollout"),
         title="시작 장면 · 상자는 통로 가장자리 (가로 위치 1.0)",
         captions=[((0, 3), "로봇 판단 {n}: 목표 (7.0, 0.0)로 이동 → 중앙 통로로 진행")],
         ending="PASS · 목표 도달 (로봇 판단 4회)"),
    dict(name="humanoid_goal_occupied_fail", rollout=os.path.join(ATT, "attempt_00001/rollout"),
         title="AFS 제안 · 상자를 통로 가장자리 → 중앙으로 (가로 위치 1.0 → 0.0, 하나만 변경)",
         captions=[
             ((0, 0), "로봇 판단 {n}: 상자를 밀기 위해 남쪽으로 이동 → 경로 없음"),
             ((1, 1), "로봇 판단 {n}: 목표까지 경로 질의 → 목표 지점이 상자에 막힘"),
             ((2, 6), "로봇 판단 {n}: 상자 북쪽으로 우회해 접근"),
             ((7, 9), "로봇 판단 {n}: 남쪽을 향해 회전하고 상자 북쪽에 정렬"),
             ((10, 14), "로봇 판단 {n}: 밀기 위한 미세 정렬"),
             ((15, 15), "로봇 판단 {n}: 남쪽으로 밀기 요청 → 거부 (밀 수 없는 상자 면)"),
             ((16, 19), "로봇 판단 {n}: 상자 서쪽으로 돌아가려 함 → 목표 지점 막힘 반복"),
         ],
         ending="FAIL · 로봇 판단 20회 소진, 목표 0.85 m 앞 · 검출 유형: 목표 위치 점유"),
]


def load_actions(rollout):
    """판단별 (번호, 동작 시작, 동작 종료) 시뮬레이션 시각."""
    acts = []
    for line in open(os.path.join(rollout, "decisions.jsonl")):
        d = json.loads(line)
        if d.get("event") != "tool_result":
            continue
        r = d["result"]
        m = r.get("motion") or {}
        t0 = m.get("start_simulation_s", r.get("simulation_time_s"))
        t1 = m.get("end_simulation_s", t0)
        acts.append((d["observation_version"], t0, t1))
    return acts


def duration(rollout):
    states = os.path.join(rollout, "states.jsonl")
    with open(states, "rb") as f:
        f.seek(-4096, os.SEEK_END)
        last = f.read().splitlines()[-1]
    return json.loads(last)["time_s"]


def segments(acts, end):
    """동작 구간은 SLOW, 나머지(LLM 대기)는 FAST 배속으로 나눈다."""
    segs, t = [], 0.0
    for _, a0, a1 in acts:
        if a0 > t + 0.05:
            segs.append((t, a0, FAST))
        if a1 > a0 + 0.05:
            segs.append((max(a0, t), a1, SLOW))
        t = max(t, a1)
    if end > t + 0.05:
        segs.append((t, end, FAST))
    return segs


def to_out(segs, ts):
    out = 0.0
    for a, b, sp in segs:
        if ts <= b:
            return out + (max(ts, a) - a) / sp
        out += (b - a) / sp
    return out


def build(case):
    rollout = case["rollout"]
    acts = load_actions(rollout)
    end = duration(rollout)
    segs = segments(acts, end)
    total = to_out(segs, end)
    hold = 3.0
    starts = {}
    prev_end = 0.0
    for n, a0, a1 in acts:
        starts[n] = prev_end
        prev_end = a1
    events = [(0, total + hold, "{\\an7\\fs40\\b1\\pos(40,140)}" + case["title"])]
    for (lo, hi), text in case["captions"]:
        for n in range(lo, hi + 1):
            if n not in starts:
                continue
            t0 = to_out(segs, starts[n])
            nxt = starts.get(n + 1, end)
            events.append((t0, to_out(segs, nxt), text.format(n=n + 1)))
    for a, b, sp in segs:
        label = f"로봇 동작 · {sp}배속" if sp == SLOW else f"LLM 응답 대기 · {sp}배속"
        events.append((to_out(segs, a), to_out(segs, b), "{\\an9\\fs32\\pos(1880,140)}" + label))
    events.append((total, total + hold, "{\\fs48\\b1}" + case["ending"]))
    ass = os.path.join(c.ASSETS, case["name"] + ".ass")
    c.write_ass(ass, events, size=38)

    src = os.path.join(rollout, "rollout.mp4")
    parts = [f"[0:v]split={len(segs)}" + "".join(f"[s{i}]" for i in range(len(segs)))]
    for i, (a, b, sp) in enumerate(segs):
        parts.append(f"[s{i}]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{sp}[t{i}]")
    parts.append("".join(f"[t{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[cat]")
    parts.append(f"[cat]scale={c.W}:{c.H}:flags=lanczos,fps={c.FPS},"
                 f"tpad=stop_mode=clone:stop_duration={hold},{c.subtitles_filter(ass)}[out]")
    out = os.path.join(c.OUT, case["name"] + ".mp4")
    c.run_ffmpeg(["-i", src, "-filter_complex", ";".join(parts), "-map", "[out]"] + c.encode_args(out))
    print(out, f"원본 {end:.0f}초 → {total + hold:.1f}초, 구간 {len(segs)}개")
    return out


def main():
    outs = [build(case) for case in CASES]
    lst = os.path.join(c.ASSETS, "humanoid_concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in outs)
    out = os.path.join(c.OUT, "humanoid_baseline_vs_box_shift.mp4")
    c.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    print(out)


if __name__ == "__main__":
    main()
