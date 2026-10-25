# Physical AI 작업 수행 검증 및 회귀 테스트 자동화 보고서

초기 기획서와 프로젝트 구현·개발 실험 근거를 바탕으로 작성하는 한글 보고서입니다.

## 파일

- `init_report.md`: 초기 기획서. 원본을 보존합니다.
- `report.tex`: 논문 형식 보고서의 메인 파일(프리앰블, 표지·초록). 실험 설정·시도별 결과 등 상세 자료도 본문에 포함하고, 부록은 용어 정리만 둡니다.
- `chapters/`: 본문 장별 파일(`01_introduction.tex`~`08_conclusion.tex`, `references.tex`)과 `appendix/A_glossary.tex`(부록 A 용어와 사용 도구). `report.tex`에서 `\input`으로 불러옵니다.
- `additional_work.tex`: 제출 자료 보완, 회귀 검증, 정량 평가와 후속 구현의 우선순위·완료 기준.
- `figures/`: 보고서 그림. 현재 본문은 `humanoid_scene.png`만 사용합니다(`arm_failure_frames.png`는 시연 영상과 겹쳐 본문에서 제외).
- `evidence/robot_arm_environment_20261023/`: 로봇팔 비교·통제 실험 분석 사본.
- `evidence/robot_arm_free_pair_20261024/`: 이전 두 상자 로봇팔 실험(16개 변수)의 분석 사본. 최종 보고서 결과에는 쓰지 않습니다.
- `evidence/humanoid_matched_local_20261023/`: 최종 비교 집계, 실행·제안 기록, 실패 분석과 해시 근거의 소형 사본. 영상·전체 trace는 원본 경로에 남습니다.
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

## 보고 범위

- 본문 8개 절 + 참고문헌 + 부록 A(용어 정리), 전체 10쪽(10쪽 제한 이내).
- 실험 1(주 결과): LIBERO Panda + GR00T N1.7 pick-and-place, `environment_comparison_v2`. AFS 7/12 FAIL(58.3%), Random 2/12(16.7%).
- 실험 2: G1 휴머노이드 동적 사람 횡단. 본 실험 `humanoid_reasoning_fallback3_20261024_v1`(시드 3개, GPT-6 Luna): 공통 기준 장면 제외 방법별 18회 기준 AFS 6/18(33.3%), Random 2/18(11.1%). 기준 장면 포함 21회 기준은 28.6%/9.5%. 예비 실험 `paired_crossing_matched_local_20261023_v1`(시드 74001): AFS 2/5(40%), Random 0/5.
- 실패 유형: 초기 6종 중 4종(충돌, 장애물 간섭, 목표 위치 점유, 작업자 안전 위험) + 도달 불가 후보.
- 그림은 `figures/`, 결과 사본은 `evidence/`에 있습니다.
- `additional_work.tex`는 10월 20일 당시 계획 문서이며 최신 상태는 `report.tex` 기준입니다.
