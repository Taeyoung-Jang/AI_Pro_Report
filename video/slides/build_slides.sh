#!/usr/bin/env bash
# 본문(chapters/)에서 그림 1과 경계 그래프의 TikZ 코드를 추출해 슬라이드를 빌드하고, 쪽마다 1920x1080 PNG로 내보낸다.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build png
CH=../../chapters
# 그림 1: \definecolor{c1} 줄부터 첫 \end{tikzpicture}까지
awk '/\\definecolor\{c1\}/{f=1} f{print} f&&/\\end\{tikzpicture\}/{exit}' "$CH/02_system.tex" > build/fig_arch.tex
# 경계 그래프: 06장의 첫 tikzpicture
awk '/\\begin\{tikzpicture\}/{f=1} f{print} f&&/\\end\{tikzpicture\}/{exit}' "$CH/06_failure_cases.tex" > build/fig_boundary.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build slides.tex >/dev/null
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build slides.tex >/dev/null
rm -f png/slide-*.png
pdftoppm -png -scale-to-x 1920 -scale-to-y 1080 build/slides.pdf png/slide
ls png
