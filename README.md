# Physical AI 작업 수행 검증 및 회귀 테스트 자동화 보고서

초기 기획서와 프로젝트 구현·개발 실험 근거를 바탕으로 작성하는 한글 보고서입니다.

## 파일

- `init_report.md`: 초기 기획서. 원본을 보존합니다.
- `report.tex`: A4 10쪽 구성을 목표로 한 보고서 초안 v0.1.
- `additional_work.tex`: 제출 자료 보완, 회귀 검증, 정량 평가와 후속 구현의 우선순위·완료 기준.
- `Makefile`: XeLaTeX로 PDF를 두 번 빌드하여 전체 쪽 수 참조를 갱신합니다.

## PDF 만들기

XeLaTeX와 한글 지원 패키지 `kotex`가 있는 TeX 배포판이 필요합니다.
이 초안은 TikZ, geometry, booktabs, tabularx, enumitem, fancyhdr, lastpage,
hyperref, xurl, setspace 등 일반 LaTeX 패키지를 사용합니다.

```bash
make pdf
```

출력은 `build/report.pdf`입니다. 직접 빌드할 때도 XeLaTeX를 두 번 실행합니다.

추가 작업 계획서는 `make tasks`로 빌드하며, 출력은 `build/additional_work.pdf`입니다.

```bash
mkdir -p build
xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build report.tex
xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build report.tex
```

Overleaf에서는 `report.tex`를 주 문서로 지정하고 컴파일러를 **XeLaTeX**로 선택합니다.

## 초안의 범위와 검증 상태

- 경량 AI 예측과 RGB-D 처리 설명은 본문에서 제외했습니다.
- 실제 실행 관찰에 따른 12종 분류 확장을 주요 분석으로 다루고, 초기 6종 기준 결과를 병기합니다.
- 12종은 정의한 유형 수이며, 최신 기록에서 실제 확인한 것은 사후 분석 기준 5종입니다. 새 유형의 온라인 탐색 연결과 독립 검증은 남아 있습니다.
- 각 절 앞에 쪽 나눔을 두어 총 10쪽을 의도했지만, PDF 빌드 후 실제 쪽 수와 넘침을 확인해야 합니다.
- 작성 환경에서 LaTeX 엔진이 발견되지 않아 PDF 컴파일과 시각 검수는 아직 수행하지 못했습니다.
- 본문에 표시한 `제출 전 보완`은 실제 캡처, 조건표와 피드백 사례 등 추가 자료가 필요한 지점입니다.
- 실제 회귀 실행과 Random 비교 결과를 새로 생성하지 않았습니다. 구현과 실행 성과를 구분해 기술했습니다.
- 마지막 쪽의 원본 경로는 근거 추적용입니다. 보고서 저장소만으로 외부 archive가 복원되지는 않습니다.
