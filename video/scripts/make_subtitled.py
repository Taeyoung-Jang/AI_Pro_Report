"""narration.md 원고를 자막으로 만들어 가편집본에 입힌다.

- 원고의 각 구간(### m:ss–m:ss)에서 '>'로 시작하는 화면 지시는 빼고 본문만 쓴다.
- 문장 단위로 나누고, 긴 문장은 쉼표에서 더 나눈다. 구간 안에서 글자 수에 비례해 표시 시간을 나눈다.
- 기존 클립의 자막·진행 막대와 겹치지 않도록 본 화면을 줄여 위에 두고, 아래 띠에 자막을 넣는다.
출력: out/final_subtitled.mp4, out/narration.srt
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as c

BAND = 130          # 아래 자막 띠 높이(px)
MAX_CHARS = 40      # 자막 한 덩어리 최대 글자 수(한 줄)
GAP = 0.15          # 자막 사이 간격(초)


def parse(path):
    """[(시작초, 끝초, 본문)]"""
    out, cur, body = [], None, []
    pat = re.compile(r"^### (\d+):(\d+)–(\d+):(\d+)")
    for line in open(path, encoding="utf-8"):
        m = pat.match(line)
        if m or line.startswith("## "):
            if cur:
                out.append((*cur, " ".join(body)))
            cur, body = None, []
            if m:
                a, b, x, y = map(int, m.groups())
                cur = (a * 60 + b, x * 60 + y)
            continue
        s = line.strip()
        if cur and s and not s.startswith(">"):
            body.append(s.replace("`", ""))
    if cur:
        out.append((*cur, " ".join(body)))
    return out


def chunks(text):
    """문장 → 너무 길면 쉼표·공백에서 나눠 MAX_CHARS 이하 덩어리로."""
    sents = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if s.strip()]
    res = []
    for s in sents:
        res.extend(balanced(s))
    return res


def balanced(s):
    """긴 문장을 비슷한 길이의 덩어리로 나눈다. 목표 위치 근처의 쉼표를 먼저, 없으면 공백을 고른다."""
    n = -(-len(s) // MAX_CHARS)
    if n <= 1:
        return [s]
    pieces, rest = [], s
    for k in range(n - 1, 0, -1):
        target = len(rest) // (k + 1)
        spaces = [i for i, ch in enumerate(rest) if ch == " "]
        if not spaces:
            break
        commas = [i for i in spaces if i > 0 and rest[i - 1] == ","]
        pool = [i for i in commas if abs(i - target) <= MAX_CHARS // 4] or spaces
        cut = min(pool, key=lambda i: abs(i - target))
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    pieces.append(rest)
    return pieces


def timed(sections, voice=None):
    """voice가 있으면({구간 시작초: [음성 시작 지연, 음성 길이]}) 자막을 실제 음성 구간에 맞춘다."""
    events = []
    for a, b, text in sections:
        parts = chunks(text)
        if not parts:
            continue
        total = sum(len(p) for p in parts)
        t = a + 0.3
        span = (b - a) - 0.6
        if voice and str(a) in voice:
            lead, dur = voice[str(a)]
            t, span = a + lead, dur
        for p in parts:
            d = span * len(p) / total
            events.append((t, t + d - GAP, p))
            t += d
    return events


def srt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


def main():
    sections = parse(os.path.join(c.VIDEO, "narration.md"))
    vpath = os.path.join(c.ASSETS, "narration_voice.json")  # make_narrated.py가 만드는 음성 구간 정보
    voice = json.load(open(vpath)) if os.path.exists(vpath) else None
    events = timed(sections, voice)
    srt = os.path.join(c.OUT, "narration.srt")
    with open(srt, "w", encoding="utf-8") as f:
        for i, (a, b, t) in enumerate(events, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n")
    ass = os.path.join(c.ASSETS, "narration.ass")
    c.write_ass(ass, [(a, b, t) for a, b, t in events], size=44, margin_v=(BAND - 56) // 2)
    h = c.H - BAND
    w = int(c.W * h / c.H) // 2 * 2
    vf = (f"scale={w}:{h},pad={c.W}:{c.H}:{(c.W - w) // 2}:0:color=0x1e2024,"
          f"{c.subtitles_filter(ass)}")
    out = os.path.join(c.OUT, "final_subtitled.mp4")
    c.run_ffmpeg(["-i", os.path.join(c.OUT, "rough_cut.mp4"), "-vf", vf] + c.encode_args(out))
    print(out, f"자막 {len(events)}개, 구간 {len(sections)}개")


if __name__ == "__main__":
    main()
