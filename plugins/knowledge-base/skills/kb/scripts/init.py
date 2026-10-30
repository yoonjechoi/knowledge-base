"""지식베이스 처음 만들기 — 빈 폴더에 raw · wiki 두 층과 wiki 칸 여덟, 길잡이 두 파일(index · log)을 만든다. 이미 있는 파일은 건드리지 않는다.

  python3 init.py              # 내 설정의 kb 위치(기본 ~/knowledge-base)에
  python3 init.py <폴더>       # 다른 곳에 — 내 설정의 kb 도 그 폴더로 바꾼다

git 이 있으면 저장소로 시작하고 첫 커밋을 한다. 없으면 건너뛴다(기록은 log.md 에 남는다).
"""
import datetime, importlib.util, pathlib, shutil, subprocess, sys

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parent / "settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/

CELLS = [("me", "나"), ("business", "비즈니스"), ("brands", "브랜드"), ("customers", "고객"),
         ("projects", "프로젝트"), ("topics", "그 밖의 주제"), ("synthesis", "대화에서 얻은 결론"), ("journal", "날짜별 업무 일지")]


def write_new(p, text):
    if p.exists():
        return False
    p.write_text(text, encoding="utf-8")
    return True


def main():
    if len(sys.argv) > 1:
        kb = pathlib.Path(sys.argv[1]).expanduser().resolve()
        c = S.load(); c["kb"] = str(kb); S.save(c)
    else:
        kb = S.kb_dir()
    today = datetime.date.today().isoformat()
    made = []
    for d in ["raw", "raw/assets", "wiki"] + [f"wiki/{n}" for n, _ in CELLS]:
        p = kb / d
        if not p.exists():
            p.mkdir(parents=True); made.append(d + "/")
    index = "# 지식베이스 목록\n\n노트 이름을 글자로만 적는다(링크 없이). 칸마다 한 줄 = 노트 이름 — 한 줄 요약.\n\n" + \
        "\n".join(f"## {n} ({ko})\n(아직 없음)\n" for n, ko in CELLS if n != "journal") + \
        "\n## journal (날짜별 업무 일지)\n날짜 파일 이름으로 찾는다 — 날마다 적지 않는다.\n"
    if write_new(kb / "wiki/index.md", index):
        made.append("wiki/index.md")
    log = "# 지식베이스 기록\n\n한 줄 머리: `## [YYYY-MM-DD] ingest|query|save|lint | 내용` — 맨 아래에 덧붙이기만 한다.\n\n" + \
        f"## [{today}] init | 지식베이스 만듦 (카파시 LLM Wiki 방식, raw · wiki 두 층 + kb 스킬 규칙)\n"
    if write_new(kb / "wiki/log.md", log):
        made.append("wiki/log.md")
    if write_new(kb / ".gitignore", ".DS_Store\nThumbs.db\n.obsidian/workspace*\n.obsidian/cache\n"):
        made.append(".gitignore")

    git = shutil.which("git")
    if not git:
        gitmsg = "git 이 없어 기록 저장소는 건너뜀(지식베이스는 그대로 쓸 수 있어요)"
    elif (kb / ".git").exists():
        gitmsg = "git 저장소가 이미 있음"
    else:
        run = lambda *a: subprocess.run([git, "-C", str(kb), *a], capture_output=True, text=True)
        run("init", "-q")
        run("add", "--", "wiki/index.md", "wiki/log.md", ".gitignore")
        r = run("-c", "user.name=kb", "-c", "user.email=kb@localhost", "commit", "-qm", "init: 지식베이스 만듦")
        gitmsg = "git 저장소로 시작하고 첫 기록을 남김" if r.returncode == 0 else "git 저장소는 만들었지만 첫 기록은 못 남김: " + r.stderr.strip()[:120]

    print("지식베이스:", kb)
    print("새로 만든 것:", ", ".join(made) if made else "없음(이미 있었어요)")
    print(gitmsg)


if __name__ == "__main__":
    main()
