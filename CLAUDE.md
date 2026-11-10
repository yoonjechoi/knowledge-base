## 하네스: 지식베이스 플러그인 (knowledge-base)

**목표:** 카파시 LLM Wiki gist 그대로의 개인 지식베이스 — raw · wiki · schema(지식베이스 폴더의 CLAUDE.md) 세 층, setup 한 번과 ingest · query · lint.

**호출 조건:** 이 저장소는 플러그인 소스다. 지식베이스 일은 `knowledge-base:setup` · `ingest` · `query` · `lint` 스킬로 하고, 일괄 넣기는 ingest 가 `knowledge-base:batch-ingester` 를 백그라운드로 부른다. `knowledge-base:kb` 는 다른 플러그인 · 예약용 옛 입구로 넷 중 하나로 넘긴다. 개발 · 시험은 `--plugin-dir plugins/knowledge-base` 로 한다. 설계를 바꿀 때는 gist(https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)와 견준다.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-11-11 | 동작을 ingest · query · lint 셋 + setup 으로 줄임(init → setup, capture · split 은 ingest 안의 단계로) | skills/kb, scripts/setup.py | 저장소 주인 요청 — 「더 간단히」, 카파시 LLM Wiki 와 같은 세 동작 |
| 2026-11-11 | ingest 를 1단계 raw 저장(대화 중, 수 초) + 2단계 노트 쓰기(뒷단 서브에이전트)로, 절차는 references/ingest.md 로 옮김 | skills/kb, agents/ingester(옛 tidier) | 저장소 주인 요청 — 「대화가 중단되지 않게 background 에서」. 받은 자료 86개 중 77개가 10분 안에 정리됐고 새벽 예약은 한 번도 돌지 않음 |
| 2026-11-11 | 대화 결론도 raw 에 결론으로 저장하고 노트 쓰기가 synthesis/ 에 넣음(옛 「결론 넣기」 없앰) | skills/kb, rules.md, inbox.py --conclusion | 저장소 주인 요청 — 결론도 raw 를 거쳐 한 길로 |
| 2026-11-11 | ingester 에이전트의 모델을 정하지 않음(쓰는 사람의 기본 설정 모델로 돎), 부를 때도 model 을 넘기지 않음 | agents/ingester, skills/kb | 저장소 주인 요청 — 수강생은 sonnet 으로 써야 사용량이 덜 듦 |
| 2026-11-11 | 1.0.0 — llm-wiki-plugin 내용으로 통째로 바꿈(스킬 setup · ingest · query · lint, 에이전트 batch-ingester, 도우미 wiki.py). 옛 kb 는 얇은 입구로, 옛 구조 지식베이스는 move-old 로 옆에 보관 | 전체 | 저장소 주인 요청 — gist 그대로, 이름만 knowledge-base |
| 2026-11-11 | 1.0.1 — query 가 「결론을 받아 저장만」 요청이면 찾기를 건너뛰고 analyses 에 바로 저장 | skills/query | 다른 플러그인이 kb 대신 query 로 결론을 저장하게 바뀜 |
| 2026-11-11 | 파일 이름에 윈도우 금지 문자(\ / : * ? " < > \|)를 쓰지 않는 규칙을 schema 틀 · ingest · query 에 | templates/schema.md, skills/ingest, skills/query | 윈도우에서 제목에 : ? 가 든 원자료 파일이 안 만들어질 수 있음(코드 읽기로 찾음) |
