# Physical AI 작업 수행 검증 및 회귀 테스트 자동화 보고서

초기 기획서와 프로젝트 구현·개발 실험 근거를 바탕으로 작성하는 한글 보고서입니다.

## 파일

- `init_report.md`: 초기 기획서. 원본을 보존합니다.
- `report.tex`: 논문 형식 보고서. 본문 10쪽 이내, 실험 설정 등 상세 자료는 부록.
- `additional_work.tex`: 제출 자료 보완, 회귀 검증, 정량 평가와 후속 구현의 우선순위·완료 기준.
- `figures/`: 보고서 그림(휴머노이드 장면, 로봇팔 실패 프레임).
- `evidence/robot_arm_environment_20261023/`: 로봇팔 비교·통제 실험 분석 사본.
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

- 본문 9개 절(약 8쪽, 10쪽 제한 이내) + 참고문헌 + 부록 A–E.
- 실험 1(주 결과): LIBERO Panda + GR00T N1.7 pick-and-place, `environment_comparison_v2`. AFS 7/12 FAIL(58.3%), Random 2/12(16.7%).
- 실험 2: G1 휴머노이드 동적 사람 횡단, `paired_crossing_matched_local_20261023_v1`. AFS 2/5(40%), Random 0/5.
- 실패 유형: 초기 6종 중 4종(충돌, 장애물 간섭, 목표 위치 점유, 작업자 안전 위험) + 도달 불가 후보.
- 그림은 `figures/`, 결과 사본은 `evidence/`에 있습니다.
- `additional_work.tex`는 10월 20일 당시 계획 문서이며 최신 상태는 `report.tex` 기준입니다.
