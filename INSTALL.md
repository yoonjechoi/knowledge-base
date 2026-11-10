> 이 문서는 AI 에이전트용입니다. 위에서 아래로 그대로 실행하세요. 사람은 README.md 를 보면 됩니다.

# knowledge-base 설치 · 업데이트

Claude Code 플러그인 `knowledge-base` 를 설치하고 지식베이스를 만든다. 카파시 LLM Wiki gist 그대로의 구조다 — `raw/`(원자료) · `wiki/`(LLM 이 쓰는 페이지) · `CLAUDE.md`(schema).

순서는 1번부터 5번까지다. 사용자가 업데이트만 원하면 1번, 2번, 6번만 한다. 2번이 이미 설치됐는지 가려 준다.

## 지킬 것

- 사용자 승인 없이 저장소를 만들거나 공개하지 않는다. 푸시도 승인받은 백업에서만 한다.
- 토큰 · 비밀번호를 화면에 출력하지 않는다. 설정 파일 `~/.config/knowledge-base/config.json` 을 통째로 출력하지 않는다(다른 프로그램의 값이 있을 수 있다). 위치는 `wiki.py where` 로만 본다.
- 기존 폴더 · 파일을 덮어쓰거나 지우지 않는다.
- 로그인, 앱 화면 작업, 프로그램 설치 승인은 사람이 한다. 대신 하려고 하지 말고 「사람이 해야 하는 일」을 알려 주고 기다린다.
- 사람에게는 「위키」라고 하지 않고 「지식베이스」라고 한다.
- 단계마다 결과를 한 줄로 알린다. 실패하면 「실패했을 때」를 따르고, 거기 없는 실패면 멈추고 그대로 알린다.

## 지원 운영체제

| 운영체제 | 상태 |
|---|---|
| 맥 | **실제로 시험함** — 단위 시험, 임시 폴더에서 setup · ingest(함께 · 일괄) · query · lint 를 `claude -p` 로 실행 |
| 리눅스 | 코드만 읽음(파이썬 표준 라이브러리 · git 만 쓴다) |
| 윈도우 | **1.0 은 코드만 읽음.** 0.3 판은 윈도우 11 에서 실제로 시험했다. 사용자가 윈도우면 이 점을 먼저 알리고, 문제가 나면 그대로 보고한다 |

- 윈도우: 파이썬 명령은 `python` 또는 `py -3`. 설정은 `C:\Users\내이름\.config\knowledge-base\config.json`, 기본 위치는 `C:\Users\내이름\knowledge-base`. 스킬의 셸 명령(`grep`, `ls`)은 Git Bash 가 있어야 그대로 돈다.
- 모든 운영체제 공통: 지식베이스를 iCloud, Dropbox, OneDrive 같은 동기화 폴더나 네트워크 드라이브에 두지 않는다. `.git` 이 동기화되면 커밋이 깨질 수 있다.

## 1. 환경 점검

맥 · 리눅스는 셸, 윈도우는 PowerShell 에서 친다.

```
claude --version
claude auth status
python3 --version
git --version
```

- `claude`: 없으면 「사람이 해야 하는 일」의 Claude Code 설치를 안내하고 멈춘다.
- `claude auth status`: `loggedIn` 만 본다. `false` 면 설치는 계속하되, 로그인해야 쓸 수 있다고 끝날 때 알린다.
- 파이썬: 3.9 이상이어야 한다. `python3` 이 없으면 `python --version`, 그것도 없으면 `py -3 --version` 을 본다. 되는 명령을 아래 `<PY>` 자리에 쓴다.
- `git`: 없어도 된다. 없으면 바뀐 기록이 안 남고 백업을 못 한다고 알리고 계속한다.

## 2. 플러그인 설치

먼저 설치돼 있는지 본다.

```
claude plugin list --json
```

- `id` 가 `knowledge-base@knowledge-base` 인 항목이 있으면 이미 설치된 것이다. 「6. 업데이트」로 간다.
- 없으면 설치한다. `SSH clone failed, retrying with HTTPS` 가 나와도 공개 저장소라 이어서 성공한다.

  ```
  claude plugin marketplace add yoonjechoi/knowledge-base
  claude plugin install knowledge-base@knowledge-base
  ```

그다음 `claude plugin list --json` 을 다시 쳐서 그 항목의 `installPath` 를 아래 `<PLUGIN>` 자리에 쓴다. 명령에서는 `<PLUGIN>` · `<KB>` · `<폴더>` 를 큰따옴표로 감싼다.

## 3. setup — 지식베이스 만들기

```
<PY> "<PLUGIN>/scripts/wiki.py" where
```

첫 줄이 지식베이스 위치다. 사용자에게 묻는다: 「지식베이스를 ○○ 에 만들까요? 다른 곳을 원하면 말해 주세요.」 둘째 줄을 보고 고른다.

| `where` 둘째 줄 | 할 일 |
|---|---|
| 없음 — setup 부터 | 아래 명령으로 만든다 |
| 있음 | 이미 지식베이스다. 새로 만들지 말고 그대로 쓴다고 알린다 |
| 옛 구조(knowledge-base 0.x) | 「6. 업데이트」의 「0.x 에서 1.0 으로」를 따른다 |

```
<PY> "<PLUGIN>/scripts/wiki.py" setup              # 기본 위치
<PY> "<PLUGIN>/scripts/wiki.py" setup "<폴더>"     # 다른 위치. 설정도 그 폴더로 바뀐다
```

이미 있는 파일은 건드리지 않는다. 무엇을 쌓을지 정해 schema(`<KB>/CLAUDE.md`)를 쓰는 대화는 설치가 끝난 뒤 새 세션에서 「지식베이스 설정해 줘」로 한다(setup 스킬).

## 4. 설치 확인

```
claude plugin list --json
<PY> "<PLUGIN>/scripts/wiki.py" where
<PY> "<PLUGIN>/scripts/wiki.py" pending
```

- 플러그인의 `enabled` 가 `true`, `where` 가 「있음」, `pending` 이 「모두 ingest 됨」이면 된다.
- 지금 세션에는 스킬이 아직 없다. 사용자에게 알린다: 「새 세션을 열거나 이 세션에서 `/reload-plugins` 를 치면 『지식베이스 설정해 줘』로 시작할 수 있어요.」

## 5. 선택 항목

항목마다 사용자에게 물어서 원할 때만 한다.

### 옵시디언으로 보기

사람이 한다. 안내: 「obsidian.md 에서 옵시디언을 설치하고, 『폴더를 보관함으로 열기』로 지식베이스 폴더를 고르세요. 그래프 보기로 무엇이 이어졌는지 볼 수 있어요. 웹 글은 Obsidian Web Clipper 로 `raw/` 에 바로 넣을 수 있어요.」

### 비공개 저장소 백업

git 과 GitHub CLI(`gh`)가 있어야 한다. `<KB>` 는 지식베이스 폴더, `<PY>` · `<PLUGIN>` 은 위와 같다.

1. `gh auth status` 로 로그인을 확인한다. `gh` 가 없거나 로그인이 안 돼 있으면 「사람이 해야 하는 일」을 안내하고 기다린다.
2. git 이름 · 이메일이 없으면 첫 커밋 작성자가 `kb <kb@localhost>` 로 올라간다고 알린다. 저장소 이름을 묻는다(권장: `knowledge-base-data`). **「비공개 저장소 ○○ 를 만들고 지식베이스 전체를 올릴까요?」라고 묻고 승인받는다.**
3. `gh repo view <이름>` 이 저장소를 찾으면 멈추고 알린다. 있는 저장소에 올리지 않는다.
4. 올리기 전에 기록 전체를 점검한다. 파일 이름만 나오고 값은 나오지 않는다. 맥 · 리눅스 · 윈도우의 Git Bash 에서 친다.

   ```
   git -C "<KB>" grep -lE 'sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|xox[baprs]-|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|BEGIN [A-Z ]*PRIVATE KEY|[0-9]{6}-[1-4][0-9]{6}|[0-9]{4}[- ][0-9]{4}[- ][0-9]{4}[- ][0-9]{4}' $(git -C "<KB>" rev-list --all)
   ```

   걸리면 **올리지 말고** 파일 이름만 사용자에게 알리고 멈춘다. 이 점검은 글자 패턴만 본다. PDF · 사진 안은 못 본다고 함께 알린다.
5. 옵시디언 설정을 기록에서 뺀다. `<KB>/.gitignore` 에 `.obsidian/` 줄이 없으면 더하고 커밋한다.

   ```
   git -C "<KB>" add .gitignore
   git -C "<KB>" commit -m "lint: 옵시디언 설정을 기록에서 뺌"
   ```

6. 비공개로 만들고 **비공개인지 확인한다.** `PRIVATE` 가 아니면 멈추고 알린다.

   ```
   gh repo create <이름> --private
   gh repo view <이름> --json visibility -q .visibility
   gh auth setup-git
   ```

7. 올린다.

   ```
   git -C "<KB>" remote add origin "$(gh repo view <이름> --json url -q .url)"
   git -C "<KB>" push -u origin HEAD
   ```

8. 사용자에게 자동 백업을 원하는지 묻는다. 원하면 커밋할 때마다 뒤에서 조용히 push 하는 훅을 넣는다. 이 컴퓨터에만 적용되고, push 가 실패해도 커밋을 막지 않으며 실패는 `.git/kb-push.log` 에 남는다. 아래 두 파일을 `<KB>/.git/hooks/` 에 그대로 만들고, 맥 · 리눅스에서는 `chmod +x` 한다.

   `post-commit`:

   ```sh
   #!/bin/sh
   # 지식베이스 자동 백업 — 커밋 뒤 뒤에서 조용히 push 한다. 실패해도 커밋을 막지 않는다. 기록: .git/kb-push.log
   dir=$(cd "$(dirname "$0")" && pwd)
   nohup /bin/sh "$dir/kb-push.sh" >/dev/null 2>&1 </dev/null &
   exit 0
   ```

   `kb-push.sh`:

   ```sh
   #!/bin/sh
   # 한 번에 하나만 push 한다. 도는 중에 새 커밋이 오면 want 표시를 보고 이어서 한 번 더 민다.
   unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_PREFIX GIT_LITERAL_PATHSPECS GIT_EDITOR
   PATH=/opt/homebrew/bin:/usr/local/bin:$PATH
   export PATH GIT_TERMINAL_PROMPT=0
   hooks=$(cd "$(dirname "$0")" && pwd)
   gitdir=$(dirname "$hooks")
   lock=$gitdir/kb-push.lock
   want=$gitdir/kb-push.want
   log=$gitdir/kb-push.log

   note() {
       printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$log"
       tail -n 200 "$log" > "$log.tmp" 2>/dev/null && mv "$log.tmp" "$log"
   }

   : > "$want"
   while [ -e "$want" ]; do
       if ! mkdir "$lock" 2>/dev/null; then
           [ -n "$(find "$lock" -maxdepth 0 -mmin +10 2>/dev/null)" ] || exit 0   # 도는 프로그램이 want 를 본다
           rmdir "$lock" 2>/dev/null
           continue
       fi
       while [ -e "$want" ]; do
           rm -f "$want"
           out=$(git --git-dir="$gitdir" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=60 push -q origin HEAD 2>&1) || note "push 실패: $(printf '%s' "$out" | tail -n 3 | tr '\n' ' ')"
       done
       rmdir "$lock"
   done
   ```

9. 확인한다. `git -C "<KB>" status -sb` 가 `origin` 과 같으면 끝이다. 자동 백업을 넣었으면 다음 커밋 뒤 `git -C "<KB>" ls-remote origin HEAD` 가 지역 커밋과 같은지 본다.

## 6. 업데이트

```
claude plugin marketplace update knowledge-base
claude plugin update knowledge-base@knowledge-base
```

- 떠 있는 세션은 옛 판을 계속 쓴다. 새 세션을 열거나 `/reload-plugins` 를 치면 새 판이 적용된다고 알린다.
- 지식베이스의 schema(`CLAUDE.md`)는 바뀌지 않는다. 사용자가 원하면 `<PLUGIN>/templates/schema.md` 와의 차이를 보여 주고 고른 내용만 넣는다.

### 0.x 에서 1.0 으로

1.0 은 구조가 다르다(카파시 LLM Wiki gist 그대로). `wiki.py where` 가 「옛 구조」라고 하면 사용자에게 알리고 묻는다: 「옛 지식베이스를 `<폴더>-old-오늘날짜` 로 옮겨 두고 같은 자리에 새로 시작할까요? 옛 자료는 그대로 남고, 필요하면 나중에 그 원자료를 새 지식베이스에 넣을 수 있어요.」

- 예면: `<PY> "<PLUGIN>/scripts/wiki.py" move-old` → `<PY> "<PLUGIN>/scripts/wiki.py" setup`.
- 옛 지식베이스에 비공개 백업이 있었으면 그 저장소는 옛 폴더를 따라간다. 새 지식베이스 백업은 5번의 백업을 새 저장소 이름으로 다시 한다.
- 예약 · 다른 플러그인이 쓰던 `/knowledge-base:kb …` 는 1.0 에서도 돈다(새 동작으로 넘겨준다).

## 실패했을 때

| 증상 | 대응 |
|---|---|
| `claude` 명령을 찾을 수 없음 | Claude Code 설치를 안내하고 멈춘다 |
| 마켓플레이스 추가가 네트워크 · 인증 오류로 끝남 | 인터넷 연결을 확인하고 한 번 다시 친다. 또 실패하면 오류 그대로 알린다 |
| `claude auth status` 가 로그인 안 됨 | 설치는 끝내고 「사람이 해야 하는 일」의 로그인을 안내한다 |
| `claude plugin list --json` 에 플러그인이 없음 | 2번을 다시 친다. 그래도 없으면 오류 그대로 알린다 |
| `enabled` 가 `false` | `claude plugin enable knowledge-base@knowledge-base` |
| 파이썬이 없거나 3.9 미만 | 파이썬 설치를 안내하고 멈춘다 |
| 윈도우에서 `python3` 이 스토어를 열거나 아무것도 안 나옴 | `python` 또는 `py -3` 으로 바꾼다 |
| `wiki.py setup` 이 「옛 구조」로 멈춤 | 6번의 「0.x 에서 1.0 으로」 |
| `wiki.py setup` 이 권한 오류 | 쓸 수 있는 다른 폴더를 사용자에게 묻는다 |
| `git push` 인증 실패 | `gh auth status` 와 `gh auth setup-git` 을 확인한다. 토큰을 명령에 적지 않는다 |

## 사람이 해야 하는 일

- **Claude Code 설치와 로그인:** https://claude.com/claude-code
- **파이썬 3.9 이상 설치:** https://www.python.org/downloads/ (맥은 `xcode-select --install` 로도 된다)
- **git 설치:** https://git-scm.com/downloads
- **GitHub CLI 설치와 로그인:** https://cli.github.com 설치 뒤 `gh auth login`. Claude Code 입력창에서 `! gh auth login` 으로 칠 수 있다.
- **옵시디언 설치와 보관함 열기**
- **프로그램 설치 · 저장소 생성 승인**

## 끝낼 때 보고

사용자에게 알린다: 플러그인 판, 지식베이스 위치, 로그인 상태, 한 선택 항목, 남은 「사람이 해야 하는 일」, 다음에 할 말 「지식베이스 설정해 줘」(무엇을 쌓을지 정하기) → 「이거 지식베이스에 넣어 줘」.
