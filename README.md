# knowledge-base

내 지식베이스와 그 위에서 도는 AI 비서를 Claude Code 플러그인 하나로 묶었어요.

| 스킬 | 하는 일 |
|---|---|
| `kb` | 지식베이스 넣기 · 찾기 · 결론 저장 · 점검 (카파시 LLM Wiki 방식 — `raw/` 원자료 · `wiki/` 정리 노트) |
| `daily-journal` | 이 컴퓨터의 클로드 · 코덱스 대화를 읽어 업무 일지를 쓰고 지식베이스에 넣기 |
| `journal-page` | 업무 일지를 휴대폰에서 보는 화면 한 장으로 올리기 |
| `morning-brief` | 아침 브리핑(오늘 할 일 · 해 두면 좋은 일 · 이번 주 · 어제 한 일)을 휴대폰 알림으로 |
| `ntfy-setup` | 휴대폰 알림(ntfy) 설정 — 앱 깔기 · 구독 이름 · 시험 알림 |
| `ai-secretary` | 위 셋을 한 번에 · 다시 · 부분만 돌리기 |

## 설치

Claude Code 에서:

```
/plugin marketplace add yoonjechoi/knowledge-base
/plugin install knowledge-base@knowledge-base
```

## 처음 한 번

1. 「지식베이스에 넣어 줘」처럼 kb 를 한 번 부르면 내 설정 `~/.config/knowledge-base/config.json` 이 생겨요. 지식베이스 폴더는 기본 `~/knowledge-base` 예요. 다른 곳에 두려면 그 파일의 `kb` 한 줄만 고쳐요.
2. 휴대폰으로 브리핑을 받으려면 「휴대폰 알림 설정해 줘」라고 하세요.
3. 클로드 데스크톱 앱 「예약」에 두 개를 만들어요. 폴더 = 지식베이스 폴더, 권한 무시, 이 컴퓨터에서만.
   - 업무 일지 새벽 정리: `/knowledge-base:daily-journal` 매일 01:00
   - 아침 브리핑 알림: `/knowledge-base:morning-brief` 매일 07:00

## 내 값은 플러그인 밖에

사람마다 다른 값은 `~/.config/knowledge-base/` 한 곳에만 둬요. 플러그인을 업데이트해도 지워지지 않아요.

```
~/.config/knowledge-base/
├── config.json    kb(지식베이스 폴더) · ntfy_topic · ntfy_token(선택) · exclude_extra(일지에서 뺄 폴더)
├── last-run.txt   마지막으로 업무 일지를 정리한 시각
└── page-url.txt   내 일지 화면 주소
```

`ntfy_topic` 은 비밀번호처럼 다뤄요. 아는 사람은 누구나 내 휴대폰에 알림을 보낼 수 있어요.

## 필요한 것

- Claude Code (예약 작업은 클로드 데스크톱 앱)
- python3
- git (지식베이스 기록용)
