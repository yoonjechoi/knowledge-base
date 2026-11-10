# knowledge-base

카파시의 [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 그대로 만든 개인 지식베이스 플러그인이에요(Claude Code).

자료를 넣을 때마다 AI가 읽고 요약하고, 관련 페이지를 고치고 서로 이어서 지식베이스가 점점 쌓여요. 질문할 때마다 처음부터 찾는 대신, 이미 정리된 페이지에서 답해요.

## 세 층

```
~/knowledge-base/
├── CLAUDE.md   schema — 구조 · 약속 · 내 방식. 쓰면서 AI와 함께 고쳐요
├── raw/        원자료. AI는 읽기만 해요
└── wiki/       AI가 쓰는 페이지
    ├── index.md · log.md · overview.md
    └── sources/ · entities/ · concepts/ · analyses/
```

## 동작

| 동작 | 이렇게 말해요 |
|---|---|
| setup (처음 한 번) | 「지식베이스 설정해 줘」 — 무엇을 쌓을지 이야기하고 schema 를 같이 써요 |
| ingest | 「이거 지식베이스에 넣어 줘」 — 핵심을 같이 이야기하고 넣어요. 「밀린 자료 다 넣어 줘」는 뒤에서 알아서 |
| query | 「지식베이스에서 찾아 줘」 — 근거를 붙여 답하고, 좋은 답은 새 페이지로 남겨요 |
| lint | 「지식베이스 점검해 줘」 — 어긋남 · 낡은 주장 · 외톨이 페이지 · 빠진 링크 · 채울 빈 곳 |

## 설치

Claude Code 에 이 문장을 붙여 넣으세요. 업데이트도 같은 문장에서 「설치」를 「업데이트」로 바꾸면 돼요.

```
https://raw.githubusercontent.com/yoonjechoi/knowledge-base/main/INSTALL.md 를 읽고 그대로 설치해 줘
```

설치가 끝나면 새 세션에서 「지식베이스 설정해 줘」 — 무엇을 쌓을지 이야기하고 schema 를 같이 써요. 옵시디언으로 지식베이스 폴더를 열면 그래프로 무엇이 이어졌는지 볼 수 있어요.

## 0.x 에서 왔다면

1.0 부터 카파시 gist 그대로의 구조예요. 옛 지식베이스는 지우지 않고 옆 폴더(`knowledge-base-old-날짜`)로 옮겨 두고 새로 시작해요. 다른 플러그인이 부르던 `/knowledge-base:kb …` 는 그대로 돌아요.
