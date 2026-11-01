# knowledge-base

내 지식베이스를 Claude Code 플러그인으로 다뤄요. 카파시 LLM Wiki 방식이에요 — `raw/` 원자료를 AI가 `wiki/` 정리 노트로 쌓아 갑니다.

스킬은 `kb` 하나예요.

| 작업 | 이렇게 말해요 |
|---|---|
| 처음 만들기 | 「지식베이스 만들어 줘」 |
| 넣기 | 「지식베이스에 넣어 줘」 · 「이 결론 저장해 줘」 |
| 찾기 | 「지식베이스에서 찾아 줘」 · 「예전에 이거 어떻게 했지」 |
| 점검 | 「지식베이스 점검해」 |

- 결론 저장은 넣기 안에 있어요. 바깥에서 온 자료는 `raw/` 로, 대화나 기존 노트에서 나온 결론은 `wiki/synthesis/` 로 들어가요.

## 설치

Claude Code 에서:

```
/plugin marketplace add yoonjechoi/knowledge-base
/plugin install knowledge-base@knowledge-base
```

그다음 「지식베이스 만들어 줘」라고 하면 기본 `~/knowledge-base`(윈도우 `C:\Users\내이름\knowledge-base`)에 폴더가 생겨요. 다른 곳에 두려면 「○○ 폴더에 지식베이스 만들어 줘」.

## 내 지식베이스에 있는 것

```
~/knowledge-base/
├── rules.md    규칙 — 내 맘대로 고쳐요. 플러그인을 업데이트해도 안 바뀌어요
├── raw/        원자료 — AI가 읽기만 해요
└── wiki/       정리 노트 — AI가 써요
    ├── index.md · log.md
    └── me · business · brands · customers · projects · topics · synthesis …
```

- **규칙:** 지식베이스의 `rules.md` 가 있으면 그것만 쓰고, 없으면 플러그인의 기본 규칙을 써요. 내 `rules.md` 를 쓰면 기본 규칙이 나중에 좋아져도 자동으로 따라오지 않아요.
- **칸:** `wiki/` 안의 폴더가 곧 칸이에요. 새로운 용도가 생기면 맞는 폴더를 만들고 `index.md` 에 머리 한 줄을 더해요. 플러그인을 고칠 일이 없어요.
- **위치:** `~/.config/knowledge-base/config.json` 의 `kb` 한 줄이에요.

## 다른 플러그인에서 쓰기

지식베이스를 쓰는 플러그인은 `knowledge-base:kb` 스킬만 불러요. 호출 방법은 [kb 스킬의 「다른 플러그인에서 부를 때」](plugins/knowledge-base/skills/kb/SKILL.md)에 있어요.

- 지식베이스 폴더 · 설정 · kb 스크립트를 직접 쓰지 않아요. 위치는 kb 만 알아요.
- 쪽 틀은 부르는 플러그인이 갖고 있다가 넘겨요.
- 의존은 한 방향이에요. `plugin.json` 에 `dependencies` 로 knowledge-base 를 적어요. 마켓플레이스가 다르면 자기 `marketplace.json` 의 `allowCrossMarketplaceDependenciesOn` 도 필요해요.

## 필요한 것

- Claude Code
- 파이썬 3.9 이상 (윈도우는 `python` 또는 `py` 로 불러도 돼요)
- git — 있으면 지식베이스 바뀐 기록이 남아요. 없어도 쓸 수 있어요

## 시험

```
python3 -m unittest discover -s tests
```
