# Physical AI 작업 수행 검증 및 회귀 테스트 자동화 보고서

초기 기획서와 프로젝트 구현·개발 실험 근거를 바탕으로 작성하는 한글 보고서입니다.

## 파일

- `init_report.md`: 초기 기획서. 원본을 보존합니다.
- `report.tex`: 보고서 v0.3. 기존 10개 절에 로봇팔 완료 실험·추가 분석 2개 절을 추가(2026년 10월 24일).
- `additional_work.tex`: 제출 자료 보완, 회귀 검증, 정량 평가와 후속 구현의 우선순위·완료 기준.
- `evidence/humanoid_matched_local_20261023/`: 최종 비교 집계, 실행·제안 기록, 실패 분석과 해시 근거의 소형 사본. 영상·전체 trace는 원본 경로에 남습니다.
- `evidence/robot_arm_free_pair_20261024/`: 로봇팔 전체 시도 기준 집계, 24슬롯 검증 분석, 실행별 CSV와 목표 근처 실패 영상 모음 사본. 원본 결과는 수정하지 않았습니다.
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

## 보고 범위와 검증 상태

- 주 정량 결과는 `paired_crossing_matched_local_20261023_v1`의 최종 완료 스냅샷입니다. 이후 준비된 별도 10회 평가는 포함하지 않습니다.
- AFS는 유효 5회 중 3 PASS·2 FAIL(40%), Random은 유효 5회 중 5 PASS·0 FAIL(0%)이며 Random 1회가 별도 제외됐습니다.
- 차이는 40퍼센트포인트입니다. Random FDR이 0이므로 상대 향상률은 정의되지 않습니다.
- 검증된 주 실패 유형은 목표 위치 점유 1종이며 다른 FAIL 1건은 미분류입니다. 이전 사후 분석의 5종은 별도 실험으로 표시했습니다.
- 사람 안전 이벤트는 AFS 4/5, Random 5/5이며 목표 PASS/FAIL 및 기존 유형 수와 분리합니다.
- 최종 보고서 스냅샷 11개 산출물과 11개 실행의 result/protocol/decisions 해시가 검증된 근거를 보존했습니다. 소형 사본의 해시는 evidence 아래 manifest.json에 있습니다.
- 기존 10개 절 뒤에 로봇팔 실험·분석 제11–12절을 추가했습니다. PDF의 실제 쪽 수와 넘침은 빌드 후 검수가 필요합니다.
- `제출 전 보완`은 장면 캡처와 영상 타임코드 등 아직 필요한 자료입니다. 실제 회귀 재실행 및 독립 seed 성능 평가는 새로 수행하지 않았습니다.
- `additional_work.tex`는 10월 20일 당시 계획을 보존한 문서이며, 최신 완료 비교 상태는 `report.tex`와 위 근거 사본을 기준으로 합니다.

## 로봇팔 추가 결과 (2026-10-24)

취소 포함 전체 시도당 AFS 7/12=58.33%, Random 3/12=25.00%입니다. 차이 33.33퍼센트포인트, 2.33배, 상대 증가 133.33%이며 결과 확인 후 추가한 보고 지표입니다. 취소는 INCONCLUSIVE를 유지하고 분모에만 포함했습니다. 유효 실행 기준 기존 FDR과 null Gain은 변경하지 않았습니다. AFS 고유 실패 설정 7개 중 6개는 물체 정체, 1개는 목표 근처 미완료이며 원인 7종의 증명이 아닙니다. AFS 선택 단계 6/6 FAIL 대 Random 2/6 FAIL이나 큰 장애물 선택 편향과 3개 탐색 seed의 한계가 있습니다. 새 API·로봇 실행 없이 저장 증거를 분석했습니다. G1 결과와 합산하지 않습니다.

빌드 확인: 2026-10-24 `make pdf`는 XeLaTeX 미설치로 중단됐습니다. PDF 생성과 페이지 넘침의 시각 검수는 미완료입니다. 문서 diff 공백 검사, 12개 절 구조 및 근거 사본 해시는 확인했습니다.
