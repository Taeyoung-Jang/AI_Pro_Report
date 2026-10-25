"""실험 1 확장: LIBERO 과제 묶음 3개(Spatial·Object·Goal)의 실행 장면과 AFS/Random 실패 발견 수를 한 화면에 보여 준다.

열마다 공통 시작 장면의 실행 영상을 반복 재생하고, 아래에 방법당 FAIL 수를 막대로 표시한다.
수치는 각 실행의 receipt.json에서 다시 센다(유효 실행만, 제외된 실행은 분모에서 뺀다).
출력: out/arm_libero_suites.mp4
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import common as c

DUR = 18.0
VW, VH = 580, 324
X0, GAP, VY = 50, 45, 200

SUITES = [
    dict(key="spatial", name="LIBERO-Spatial (주 실험)", task="그릇을 집어 접시에 놓기",
         runs=os.path.join(c.ARM, "environment_comparison_v2/seed_*/{m}/attempt_*"),
         video=os.path.join(c.ARM, "environment_comparison_v2/seed_661/random/attempt_00001"),
         design="3세트 × 방법당 4회", note="AFS가 장애물로 이송 경로를 막는 실패를 찾음"),
    dict(key="object", name="LIBERO-Object", task="버터를 집어 바구니에 넣기",
         runs=os.path.join(c.ARM_OG, "object/set_*/seed_*/{m}/attempt_*"),
         video=os.path.join(c.ARM_OG, "object/set_1/seed_470290/random/attempt_00001"),
         design="3세트 × 방법당 4회 구성을 독립적으로 3번 반복", note="세 번 모두 AFS ≥ Random 테스트\n다만 AFS 제안 대부분이 범위 끝값 조합\n(버터 질량 최대, 장애물 최대 크기 등)"),
    dict(key="goal", name="LIBERO-Goal", task="가운데 서랍 열기",
         runs=os.path.join(c.ARM_OG, "goal/set_*/seed_*/{m}/attempt_*"),
         video=os.path.join(c.ARM_OG, "goal/set_1/seed_477723/random/attempt_00000"),
         design="3세트 × 방법당 4회 구성을 독립적으로 3번 반복", note="비교 불가: 정책이 기본 장면에서도\n거의 항상 실패 (Random 테스트 전부 FAIL)", na=True),
]


def count(pattern, method):
    fail = valid = 0
    for d in glob.glob(pattern.format(m=method)):
        rp = os.path.join(d, "receipt.json")
        if not os.path.exists(rp):  # 제외된 실행(응답 오류·초기 침투)은 receipt가 없다
            continue
        r = json.load(open(rp))
        if r.get("status") != "VALID":
            continue
        valid += 1
        fail += r["task_outcome"] == "FAIL"
    return fail, valid


def draw(suites, path):
    im = Image.new("RGB", (c.W, c.H), c.BG)
    d = ImageDraw.Draw(im)
    d.text((X0, 34), "실험 1 확장 · LIBERO 과제 묶음별 확인", font=c.font(46, True), fill=c.INK)
    d.text((c.W - X0, 50), "같은 Panda 로봇팔 + GR00T N1.7 (묶음별 공개 체크포인트)", font=c.font(26), fill=c.MUTED, anchor="ra")
    for i, s in enumerate(suites):
        x = X0 + i * (VW + GAP)
        d.text((x, 118), s["name"], font=c.font(34, True), fill=c.INK)
        d.text((x, 162), s["task"], font=c.font(26), fill=c.MUTED)
        d.rectangle([x - 3, VY - 3, x + VW + 2, VY + VH + 2], fill=(215, 215, 212))
        y = VY + VH + 30
        d.text((x, y), s["design"], font=c.font(24), fill=c.MUTED)
        y += 48
        for m, label, col in (("afs", "AFS", c.AFS_C), ("random", "Random 테스트", c.RAND_C)):
            fail, valid = s[m]
            frac = fail / valid
            d.text((x, y), label, font=c.font(26, True), fill=col)
            y += 36
            bx, bw = x, VW
            d.rectangle([bx, y, bx + bw, y + 40], fill=(232, 232, 228))
            fill = (190, 190, 186) if s.get("na") else col
            d.rectangle([bx, y, bx + int(bw * frac), y + 40], fill=fill)
            txt = f"FAIL {fail}/{valid} = {100 * frac:.1f}%"
            if frac >= 0.55:
                ink = c.INK if s.get("na") else (255, 255, 255)
                d.text((bx + 14, y + 20), txt, font=c.font(26, True), fill=ink, anchor="lm")
            else:
                d.text((bx + int(bw * frac) + 14, y + 20), txt, font=c.font(26, True), fill=c.INK, anchor="lm")
            y += 52
        y += 6
        d.multiline_text((x, y), s["note"], font=c.font(25), fill=c.FAIL_C if s.get("na") else c.INK, spacing=8)
    d.line([X0, c.H - 110, c.W - X0, c.H - 110], fill=(215, 215, 212), width=2)
    d.text((X0, c.H - 92), "LIBERO는 Spatial·Object·Goal·Long 등 과제 묶음으로 구성되고, 과제마다 장면 변수와 범위를 따로 정의해야 합니다.",
           font=c.font(26), fill=c.MUTED)
    d.text((X0, c.H - 54), "그래서 주 실험은 Spatial의 과제 하나로 하고, Object·Goal은 대표 과제 1개씩으로 같은 경향인지 확인했습니다.",
           font=c.font(26), fill=c.MUTED)
    im.save(path)


def main():
    for s in SUITES:
        s["afs"], s["random"] = count(s["runs"], "afs"), count(s["runs"], "random")
        print(s["key"], "afs", s["afs"], "random", s["random"])
    bg = os.path.join(c.ASSETS, "arm_libero_suites_bg.png")
    draw(SUITES, bg)
    args = ["-loop", "1", "-t", str(DUR), "-i", bg]
    for s in SUITES:
        args += ["-stream_loop", "-1", "-i", glob.glob(os.path.join(s["video"], "videos/*.mp4"))[0]]
    parts, last = [], "0:v"
    for i, s in enumerate(SUITES, start=1):
        parts.append(f"[{i}:v]scale={VW}:{VH},fps={c.FPS}[v{i}]")
        x = X0 + (i - 1) * (VW + GAP)
        parts.append(f"[{last}][v{i}]overlay={x}:{VY}:shortest=0[o{i}]")
        last = f"o{i}"
    out = os.path.join(c.OUT, "arm_libero_suites.mp4")
    c.run_ffmpeg(args + ["-filter_complex", ";".join(parts), "-map", f"[{last}]", "-t", str(DUR)] + c.encode_args(out))
    print(out)


if __name__ == "__main__":
    main()
