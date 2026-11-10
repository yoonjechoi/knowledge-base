## 하네스: 지식베이스 플러그인 (knowledge-base)

**목표:** 카파시 LLM Wiki 방식의 개인 지식베이스를 setup 한 번과 ingest · query · lint 세 동작으로 다룬다. ingest 의 노트 쓰기는 대화를 막지 않게 뒷단 에이전트가 한다.

**호출 조건:** 이 저장소는 플러그인 소스다. 지식베이스 일은 `knowledge-base:kb` 스킬(입구 · 오케스트레이터)로 하고, 노트 쓰기는 그 스킬이 `knowledge-base:ingester` 에이전트를 백그라운드로 부른다. 개발 · 시험은 `--plugin-dir plugins/knowledge-base` 로 한다.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-11-11 | 동작을 ingest · query · lint 셋 + setup 으로 줄임(init → setup, capture · split 은 ingest 안의 단계로) | skills/kb, scripts/setup.py | 윤제님 — 「더 간단히」, 카파시 LLM Wiki 와 같은 세 동작 |
| 2026-11-11 | ingest 를 1단계 raw 저장(대화 중, 수 초) + 2단계 노트 쓰기(뒷단 서브에이전트)로, 절차는 references/ingest.md 로 옮김 | skills/kb, agents/ingester(옛 tidier) | 윤제님 — 「대화가 중단되지 않게 background 에서」. 받은 자료 86개 중 77개가 10분 안에 정리됐고 새벽 예약은 한 번도 돌지 않음 |
| 2026-11-11 | 대화 결론도 raw 에 결론으로 저장하고 노트 쓰기가 synthesis/ 에 넣음(옛 「결론 넣기」 없앰) | skills/kb, rules.md, inbox.py --conclusion | 윤제님 — 결론도 raw 를 거쳐 한 길로 |
| 2026-11-11 | ingester 에이전트의 모델을 정하지 않음(쓰는 사람의 기본 설정 모델로 돎), 부를 때도 model 을 넘기지 않음 | agents/ingester, skills/kb | 윤제님 — 수강생은 sonnet 으로 써야 사용량이 덜 듦 |
