LATEX ?= xelatex
REPORT ?= report
BUILD := build

.PHONY: all pdf tasks
all: pdf

tasks:
	$(MAKE) pdf REPORT=additional_work

pdf:
	@command -v "$(LATEX)" >/dev/null 2>&1 || { echo "XeLaTeX가 필요합니다. README.md의 빌드 안내를 확인하세요."; exit 1; }
	mkdir -p $(BUILD)
	$(LATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=$(BUILD) $(REPORT).tex
	$(LATEX) -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=$(BUILD) $(REPORT).tex
