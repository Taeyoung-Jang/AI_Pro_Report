"""창고 배치 AFS 3번째 실행: LLM 응답을 기다리며 멈춘 로봇이 횡단하는 사람과 접촉한 뒤 넘어지는 장면.

접촉 전후(PLAY_A~PLAY_B초)는 실제 속도로, 넘어진 뒤 실행 종료까지는 빠르게 재생한다.
시각은 events.jsonl(contact_start, fall_start)과 decisions.jsonl에서 확인한 값이다.
출력: out/humanoid_warehouse_fall.mp4
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c

ROLLOUT = os.path.join(c.VENUES, "warehouse/campaign/seeds/2104076294/afs/attempts/attempt_00002/rollout")
PLAY_A, PLAY_B = 34.0, 43.5
FAST_OUT = 3.0  # 넘어진 뒤 남은 구간을 이 길이(초)로 압축
HOLD = 3.0


def first_event(kind, world=None):
    for line in open(os.path.join(ROLLOUT, "events.jsonl")):
        d = json.loads(line)
        if d.get("event") == kind and (world is None or d.get("world_geom_name") == world):
            return d["time_s"]
    raise ValueError(kind)


def main():
    contact = first_event("contact_start", "human_proxy_1")
    fall = first_event("fall_start")
    end = json.load(open(os.path.join(ROLLOUT, "terminal_state.json")))["time_s"]
    fast = (end - PLAY_B) / FAST_OUT
    real = PLAY_B - PLAY_A
    total = real + FAST_OUT + HOLD

    def t(sim):
        return sim - PLAY_A

    title = "{\\an7\\fs40\\b1\\pos(40,140)}창고 배치 · AFS 제안: 바닥 마찰 0.8→1.15, 장애물 2 위치 0→0.45"
    note = "{\\an7\\fs28\\pos(40,196)}AFS 예상: 이동 정체  ·  청록 기둥 = 사람 모형 (정해진 경로로 움직이며 로봇을 피하지 않음)"
    events = [
        (0, total, title),
        (0, total, note),
        (0, real, "{\\an9\\fs32\\pos(1880,140)}실제 속도"),
        (real, real + FAST_OUT, f"{{\\an9\\fs32\\pos(1880,140)}}{fast:.0f}배속"),
        (0, t(37.7), "로봇이 장애물을 돌아 목표로 이동"),
        (t(37.7), t(40.09), "사람이 통로를 가로질러 걷기 시작"),
        (t(40.09), t(contact), "이동이 막혀 정지 → 다음 로봇 판단(LLM 응답)을 기다리는 중 (23.5초)"),
        (t(contact), t(fall), f"{contact:.1f}초: 응답을 기다리던 로봇에 사람이 접촉"),
        (t(fall), real, f"{fall:.1f}초: 넘어짐"),
        (real, real + FAST_OUT, "이후 로봇 판단 16회: 일어서기 요청(지원 안 됨), 기어가기 시도"),
        (real + FAST_OUT, total, "{\\fs48\\b1}FAIL · 넘어짐 (예상한 이동 정체와 다른 유형) · 로봇 판단 20회 소진"),
    ]
    ass = os.path.join(c.ASSETS, "humanoid_warehouse_fall.ass")
    c.write_ass(ass, events, size=38)
    src = os.path.join(ROLLOUT, "rollout.mp4")
    fc = (f"[0:v]split=2[a][b];"
          f"[a]trim=start={PLAY_A}:end={PLAY_B},setpts=PTS-STARTPTS[ra];"
          f"[b]trim=start={PLAY_B}:end={end},setpts=(PTS-STARTPTS)/{fast:.3f}[rb];"
          f"[ra][rb]concat=n=2:v=1:a=0[cat];"
          f"[cat]scale={c.W}:{c.H}:flags=lanczos,fps={c.FPS},tpad=stop_mode=clone:stop_duration={HOLD},"
          f"{c.subtitles_filter(ass)}[out]")
    out = os.path.join(c.OUT, "humanoid_warehouse_fall.mp4")
    c.run_ffmpeg(["-i", src, "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.2f}"] + c.encode_args(out))
    print(out, f"접촉 {contact:.2f}s, 넘어짐 {fall:.2f}s, 길이 {total:.1f}s")


if __name__ == "__main__":
    main()
