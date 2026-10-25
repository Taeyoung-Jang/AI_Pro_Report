"""회귀 실행기 실제 동작 화면(demo_recording_20261025_v2/demo.mp4)을 회귀 구간 길이에 맞게 편집한다.

녹화는 저장된 시작 장면(시드 253785482, 원래 PASS)을 회귀 실행기로 재실행하는 모습이다(시연 전용, 평가 미포함).
timeline.json의 시각을 기준으로 준비 구간은 빠르게, LLM 응답과 로봇 이동은 느리게 재생하고 자막을 붙인다.
시연을 위해 LLM 응답 2회 뒤 녹화를 멈췄으므로, 그 실행은 '판정 불가(외부 중단)'로 기록되었다.
출력: out/demo_regression_run.mp4
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c

DEMO = os.path.join(c.REPO, "demo_recording_20261025_v2")
HOLD = 2.3
MOV = "화면 기록 2026-10-25 오후 3.18.50.mov"
MOV_CROP = (2400, 300, 640, 800)  # 4096x2304 녹화에서 터미널 줄 부분 (w, h, x, y)
MOV_RANGE = (12.0, 20.0)  # "Recording screen" 줄이 나타나는 구간
PREFIX_OUT = 4.0


def main():
    ev = {}
    for e in json.load(open(os.path.join(DEMO, "timeline.json")))["events"]:
        ev.setdefault(e["event"], []).append(e["offset_s"])
    start = ev["execution_started"][0]
    c1, r1 = ev["llm_call_started"][0], ev["llm_response_received"][0]
    c2, r2 = ev["llm_call_started"][1], ev["llm_response_received"][1]
    motion = ev["robot_motion_detected"][0]
    end = ev["recording_stopped"][0]
    # (구간 시작, 끝, 배속)
    segs = [(0.0, start, 4.0), (start, c1, 9.0), (c1, r1, 3.0), (r1, c2, 2.0), (c2, r2, 3.0),
            (r2, motion, 1.0), (motion, end, 1.5)]

    def to_out(t):
        out = 0.0
        for a, b, sp in segs:
            if t <= b:
                return out + (max(t, a) - a) / sp
            out += (b - a) / sp
        return out

    total = to_out(end)
    events = [
        (0, total + HOLD, "{\\an7\\fs30\\b1\\pos(850,56)}회귀 실행기 실제 동작 · 저장된 시작 장면(원래 PASS) 재실행"),
        (0, to_out(start), "명령 실행: 저장된 사례를 불러와 같은 조건으로 장면 구성"),
        (to_out(start), to_out(c1), "시뮬레이션 시작 (화면 오른쪽: 로봇 상태를 그대로 보여 주는 뷰어)"),
        (to_out(c1), to_out(r1), "로봇 판단 1/20 → LLM 응답"),
        (to_out(r1), to_out(r2), "로봇 판단 2/20 → LLM 응답"),
        (to_out(r2), total, "로봇이 판단대로 이동 시작"),
        (total, total + HOLD, "{\\fs40\\b1}시연을 위해 도중에 중단 → '판정 불가'로 기록, 평가에서 제외"),
    ]
    for a, b, sp in segs:
        if b - a > 0.05:
            events.append((to_out(a), to_out(b), "{\\an9\\fs28\\pos(1880,100)}" + f"{sp:g}배속"))
    ass = os.path.join(c.ASSETS, "demo_regression_run.ass")
    c.write_ass(ass, events, size=36)
    parts = [f"[0:v]split={len(segs)}" + "".join(f"[s{i}]" for i in range(len(segs)))]
    for i, (a, b, sp) in enumerate(segs):
        parts.append(f"[s{i}]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{sp}[t{i}]")
    parts.append("".join(f"[t{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[cat]")
    parts.append(f"[cat]scale={c.W}:{c.H},fps={c.FPS},tpad=stop_mode=clone:stop_duration={HOLD},"
                 f"{c.subtitles_filter(ass)}[out]")
    body = os.path.join(c.ASSETS, "demo_regression_body.mp4")
    c.run_ffmpeg(["-i", os.path.join(DEMO, "demo.mp4"), "-filter_complex", ";".join(parts), "-map", "[out]"]
                 + c.encode_args(body))
    head = terminal_prefix()
    lst = os.path.join(c.ASSETS, "demo_regression_list.txt")
    with open(lst, "w") as f:
        f.write(f"file '{head}'\nfile '{body}'\n")
    out = os.path.join(c.OUT, "demo_regression_run.mp4")
    c.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    print(out, f"{PREFIX_OUT + total + HOLD:.1f}초")


def terminal_prefix():
    """화면 녹화(.mov)에서 터미널 부분만 잘라 명령 실행 장면을 만든다.
    아래쪽 상태 표시줄(서버 IP 표시)과 파일 탐색기는 잘라 내 보이지 않게 한다."""
    src = os.path.join(DEMO, MOV)
    w = c.W - 80
    h = int(MOV_CROP[1] * w / MOV_CROP[0])
    ass = os.path.join(c.ASSETS, "demo_terminal_prefix.ass")
    c.write_ass(ass, [(0, PREFIX_OUT, "{\\an8\\fs40\\b1\\pos(960,250)}실제 서버 터미널에서 명령으로 실행"),
                      (0, PREFIX_OUT, "명령 실행 → 화면 녹화 시작 → 회귀 실행기가 저장된 사례를 재실행")], size=36)
    cw, ch, cx, cy = MOV_CROP
    vf = (f"[0:v]trim=start={MOV_RANGE[0]}:end={MOV_RANGE[1]},setpts=(PTS-STARTPTS)*{PREFIX_OUT / (MOV_RANGE[1] - MOV_RANGE[0]):.4f},"
          f"crop={cw}:{ch}:{cx}:{cy},scale={w}:{h},pad={c.W}:{c.H}:40:{(c.H - h) // 2}:color=0x161616,fps={c.FPS},"
          f"{c.subtitles_filter(ass)}[out]")
    out = os.path.join(c.ASSETS, "demo_terminal_prefix.mp4")
    c.run_ffmpeg(["-i", src, "-filter_complex", vf, "-map", "[out]", "-t", str(PREFIX_OUT)] + c.encode_args(out))
    return out


if __name__ == "__main__":
    main()
