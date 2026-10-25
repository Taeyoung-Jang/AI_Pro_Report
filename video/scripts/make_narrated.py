"""narration.md 원고를 TTS(Microsoft Edge 온라인 음성, edge-tts)로 읽어 자막 완성본에 음성을 입힌다.

- 구간마다 음성을 만들고, 구간보다 길면 말 빠르기를 MAX_TEMPO까지 올린다. 그래도 넘치면 경고하고 구간 끝에서 자른다.
- 영문 약어 일부는 음성용 원고에서만 한글 발음으로 바꾼다(화면 자막은 그대로).
- 음성 구간 정보를 assets/narration_voice.json에 남기고, 자막을 그 구간에 맞춰 다시 만든 뒤 음성을 합친다.
- 원고 글은 Microsoft 음성 서비스로 전송된다.
출력: out/final_narrated.mp4, out/narration_voice.m4a
"""
import asyncio
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edge_tts

import common as c
from make_subtitled import parse

VOICE = "ko-KR-InJoonNeural"
LEAD = 0.3        # 구간 시작 후 말을 시작하는 시각(초)
TAIL = 0.3        # 구간 끝 전에 남길 여유(초)
MAX_TEMPO = 1.15  # 이보다 빠르게는 재생하지 않는다
SR = 24000

# 음성용 발음 (화면 자막에는 적용하지 않는다)
SAY = [("GR00T", "그루트"), ("MuJoCo", "무조코"), ("Random 테스트", "랜덤 테스트"), ("Qwen", "큐웬"),
       ("LIBERO", "리베로"), ("Unitree", "유니트리"), ("Franka", "프랑카"), ("G1", "지원"),
       ("Luna", "루나"), ("Sol", "솔"), ("AFS", "에이에프에스"), ("VLA", "브이엘에이"), ("LLM", "엘엘엠"),
       ("Physical AI", "피지컬 에이아이"), ("Object", "오브젝트"), ("Goal", "골"), ("Spatial", "스페이셜"),
       ("PASS", "패스"), ("FAIL", "페일"), ("API", "에이피아이"), ("GPT-6", "지피티 식스")]


def say(text):
    for a, b in SAY:
        text = text.replace(a, b)
    return text


def probe(path):
    probe_exe = c.ffmpeg_exe().replace("ffmpeg", "ffprobe")
    r = subprocess.run([probe_exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout)


async def synth(text, path):
    await edge_tts.Communicate(text, VOICE).save(path)


def main():
    sections = parse(os.path.join(c.VIDEO, "narration.md"))
    tmp = os.path.join(c.ASSETS, "tts")
    os.makedirs(tmp, exist_ok=True)
    voice, parts, warn = {}, [], []
    for i, (a, b, text) in enumerate(sections):
        raw = os.path.join(tmp, f"{i:02d}.mp3")
        txt = raw[:-4] + ".txt"  # 같은 글이면 다시 요청하지 않는다
        if not (os.path.exists(raw) and os.path.exists(txt) and open(txt, encoding="utf-8").read() == say(text)):
            asyncio.run(synth(say(text), raw))
            with open(txt, "w", encoding="utf-8") as f:
                f.write(say(text))
        dur = probe(raw)
        room = (b - a) - LEAD - TAIL
        tempo = min(MAX_TEMPO, max(1.0, dur / room))
        spoken = dur / tempo
        if spoken > room:
            warn.append(f"{a // 60}:{a % 60:02d} 구간: 음성 {dur:.1f}초, 최대 배속 후 {spoken:.1f}초 > 여유 {room:.1f}초")
        seg = os.path.join(tmp, f"{i:02d}.wav")
        # mp3의 시작 시각 오프셋을 없애고(asetpts), 출력 길이를 구간 길이로 고정한다(-t)
        af = f"atempo={tempo:.4f},aresample={SR},asetpts=N/SR/TB,adelay={int(LEAD * 1000)}:all=1,apad"
        c.run_ffmpeg(["-i", raw, "-af", af, "-ac", "1", "-ar", str(SR), "-t", str(b - a), seg])
        voice[str(a)] = [LEAD, min(spoken, room)]
        parts.append(seg)
        print(f"{a // 60}:{a % 60:02d}  음성 {dur:5.1f}초 → {spoken:5.1f}초 (배속 {tempo:.2f}, 구간 {b - a}초)")
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    track = os.path.join(c.OUT, "narration_voice.m4a")
    c.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", lst, "-c:a", "aac", "-b:a", "128k", track])
    with open(os.path.join(c.ASSETS, "narration_voice.json"), "w") as f:
        json.dump(voice, f)
    # 자막을 실제 음성 구간에 맞춰 다시 만든다
    subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(__file__), "make_subtitled.py")], check=True)
    out = os.path.join(c.OUT, "final_narrated.mp4")
    c.run_ffmpeg(["-i", os.path.join(c.OUT, "final_subtitled.mp4"), "-i", track, "-map", "0:v", "-map", "1:a",
                  "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out])
    print(out)
    for w in warn:
        print("경고:", w)


if __name__ == "__main__":
    main()
