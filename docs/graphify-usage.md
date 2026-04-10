# Graphify 사용 가이드

> 출처: https://github.com/safishamsi/graphify/blob/v3/README.ko-KR.md
> AI 코딩 어시스턴트용 Knowledge Graph 생성 도구

---

## 개요

Graphify는 코드베이스·문서·이미지를 **구조화된 지식 그래프**로 변환하는 스킬이다.
클래스/함수/임포트/호출 그래프 등 아키텍처 관계와 설계 의도를 시각화할 수 있다.

### 핵심 동작 방식 (2-Pass)

| Pass | 방식 | 대상 |
|------|------|------|
| 1st (deterministic) | AST 파싱 (tree-sitter) | 코드 구조 추출 — LLM 미사용 |
| 2nd (AI) | Claude 서브에이전트 병렬 처리 | 문서·논문·이미지 개념 및 관계 추출 |

---

## 설치

**요구사항:** Python 3.10+, 지원 AI 어시스턴트 중 하나 (Claude Code, Codex, OpenCode 등)

```bash
pip install graphifyy && graphify install
```

---

## 기본 사용법

```bash
/graphify .          # 현재 디렉토리 전체 분석
```

---

## 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--mode deep` | INFERRED 엣지 적극 추출 (관계 추론 강화) |
| `--update` | 기존 그래프에 변경사항 병합 |
| `--watch` | 파일 변경 시 자동 동기화 |
| `--wiki` | 브라우저로 열 수 있는 문서 생성 |
| `--neo4j-push` | Neo4j 데이터베이스 직접 연동 |

### 서브커맨드

```bash
graphify query   # 특정 서브그래프 검색
graphify path    # 두 개념 사이의 연결 경로 추적
```

---

## 출력 파일

| 파일 | 내용 |
|------|------|
| `GRAPH_REPORT.md` | 최고 연결도 노드(god node), 예상치 못한 연결, 추천 쿼리 요약 |
| `graph.json` | 영속적·쿼리 가능한 그래프 구조 (MCP 서버로 노출 가능) |
| `graph.html` | 인터랙티브 시각화 (노드 필터링, 커뮤니티 탐색) |

---

## 관계 태그

- `EXTRACTED` — AST에서 직접 추출된 명확한 관계
- `INFERRED` — 의미·문맥으로 추론된 관계 (신뢰도 점수 포함)
- `AMBIGUOUS` — 불확실한 관계

---

## 지원 언어 (20개)

Python, JavaScript, TypeScript, Go, Rust, Java, C++, C, C#, Ruby,
PHP, Swift, Kotlin, Scala, Shell, HTML, CSS, SQL, R, Lua

---

## 성능

- 쿼리당 토큰 사용량: 원본 파일 직접 읽기 대비 **71.5배 절감**
- 토폴로지 기반 클러스터링: Leiden 커뮤니티 탐지 알고리즘 사용

---

## 기술 스택

`NetworkX` + `Leiden (graspologic)` + `tree-sitter` + `vis.js`
로컬 실행 전용 — Neo4j, 서버, 클라우드 불필요

---

## 프라이버시

- **코드**: tree-sitter AST로 로컬 처리 (외부 전송 없음)
- **문서·논문·이미지**: 사용자 인증 자격증명으로 모델 API에 전송
- 텔레메트리 수집 없음
