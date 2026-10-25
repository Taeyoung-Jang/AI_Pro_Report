"""영상 스크립트 공통 설정: ffmpeg 경로, 글꼴, 경로, 자막(ASS) 생성 도우미."""
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
REPO = os.path.dirname(VIDEO)
OUT = os.path.join(VIDEO, "out")
ASSETS = os.path.join(VIDEO, "assets")
EXP = os.path.join(REPO, "experiment_results/src/physical_ai_test_gen/scene2test")
ARM = os.path.join(EXP, "experiments/robot_arm_libero")
HUMANOID = os.path.join(EXP, "development/humanoid_reasoning_fallback3_20261024_v1")
# 추가 실험(2026-10-25 전달분): LIBERO Object·Goal 과제, 휴머노이드 3개 장소
EXP2 = os.path.join(REPO, "experiment_results_20261025")
ARM_OG = os.path.join(EXP2, "experiments/robot_arm_libero/object_goal_search_repetitions3_v1")
VENUES = os.path.join(EXP2, "development/humanoid_three_venues_20261024_v1")

FONT_DIR = "/usr/share/fonts/opentype/noto"
FONT_REG = os.path.join(FONT_DIR, "NotoSansCJK-Regular.ttc")
FONT_BOLD = os.path.join(FONT_DIR, "NotoSansCJK-Bold.ttc")
FONT_KR_INDEX = 1  # ttc 안의 Noto Sans CJK KR
ASS_FONT = "Noto Sans CJK KR"

W, H, FPS = 1920, 1080, 30
BG = (250, 250, 248)
INK = (30, 32, 36)
MUTED = (110, 114, 120)
PASS_C = (34, 139, 84)
FAIL_C = (200, 50, 45)
AFS_C = (40, 90, 170)
RAND_C = (120, 120, 120)


def ffmpeg_exe():
    """시스템 ffmpeg가 있으면 쓰고, 없으면 imageio-ffmpeg에 포함된 실행 파일을 쓴다."""
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(args):
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *args]
    subprocess.run(cmd, check=True)


def encode_args(out_path):
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-movflags", "+faststart", "-an", out_path]


def font(size, bold=False):
    from PIL import ImageFont
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size, index=FONT_KR_INDEX)


def ass_time(t):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(path, events, size=40, align=2, margin_v=40):
    """events: [(start_s, end_s, text)] 목록을 ASS 자막 파일로 쓴다. 기본 위치는 하단 중앙."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{ASS_FONT},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,0,0,0,0,100,100,0,0,3,10,0,{align},60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{txt}" for a, b, txt in events]
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")


def subtitles_filter(ass_path):
    esc = ass_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return f"subtitles='{esc}':fontsdir='{FONT_DIR}'"
