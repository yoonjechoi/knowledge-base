"""knowledge-base 도우미 — 지식베이스 위치, setup 뼈대, 아직 ingest 하지 않은 원자료 찾기.

  python3 wiki.py where              # 지식베이스 위치와 schema(CLAUDE.md) 있는지
  python3 wiki.py setup [폴더]        # 뼈대를 만든다. 이미 있는 파일은 그대로. 폴더를 주면 설정도 그 폴더로
  python3 wiki.py pending            # raw/ 에 있는데 wiki/sources/ 의 어느 요약 페이지도 가리키지 않는 파일
  python3 wiki.py move-old           # 옛 구조(knowledge-base 0.x) 지식베이스를 옆의 <이름>-old-YYYYMMDD 로 옮긴다

위치는 플러그인 밖 ~/.config/knowledge-base/config.json 의 "kb" 한 줄이다(플러그인을 업데이트해도 안 지워진다). 그 파일의 다른 값은 읽지도 출력하지도 않고 그대로 둔다.
나머지 일(읽기 · 쓰기 · 링크 · 판단)은 LLM 이 한다. 이 프로그램은 매번 같아야 하는 일만 한다.
"""
import datetime, json, os, pathlib, shutil, subprocess, sys

for _o in (sys.stdout, sys.stderr):   # 윈도우에서도 한글이 안 깨지게
    try:
        _o.reconfigure(encoding="utf-8")
    except Exception:
        pass

CONF = pathlib.Path.home() / ".config" / "knowledge-base" / "config.json"
KEY = "kb"
DEFAULT = "~/knowledge-base"
TEMPLATES = pathlib.Path(__file__).resolve().parent.parent / "templates"
FOLDERS = ["raw", "raw/assets", "wiki", "wiki/sources", "wiki/entities", "wiki/concepts", "wiki/analyses"]
FILES = {"CLAUDE.md": "schema.md", "wiki/index.md": "index.md", "wiki/log.md": "log.md", "wiki/overview.md": "overview.md"}


def wiki_dir():
    cfg = json.loads(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}
    return pathlib.Path(cfg.get(KEY, DEFAULT)).expanduser()


def set_dir(p):
    cfg = json.loads(CONF.read_text(encoding="utf-8")) if CONF.exists() else {}
    cfg[KEY] = str(p)
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(CONF, 0o600)   # 다른 프로그램의 값(알림 토큰 등)이 같은 파일에 있을 수 있다
    except OSError:
        pass


def is_old(w):
    """knowledge-base 0.x 의 옛 구조 — rules.md 와 대기 목록이 있고 schema(CLAUDE.md)가 없다."""
    return (w / "rules.md").exists() and (w / "wiki" / "inbox.md").exists() and not (w / "CLAUDE.md").exists()


def where():
    w = wiki_dir()
    print("지식베이스:", w)
    if is_old(w):
        print("옛 구조(knowledge-base 0.x) — setup 에서 옮기고 새로 시작")
    else:
        print("있음" if (w / "wiki" / "index.md").exists() else "없음 — setup 부터")
    print("schema:", w / "CLAUDE.md", "(있음)" if (w / "CLAUDE.md").exists() else "(없음)")


def setup(arg):
    if arg:
        w = pathlib.Path(arg).expanduser().resolve()
        set_dir(w)
    else:
        w = wiki_dir()
    if is_old(w):
        sys.exit("옛 구조(knowledge-base 0.x) 지식베이스예요 — move-old 로 옮긴 뒤 다시: " + str(w))
    today = datetime.date.today().isoformat()
    made = []
    for d in FOLDERS:
        p = w / d
        if not p.exists():
            p.mkdir(parents=True)
            made.append(d + "/")
    for dest, tpl in FILES.items():
        p = w / dest
        if not p.exists():
            p.write_text((TEMPLATES / tpl).read_text(encoding="utf-8").replace("{{오늘}}", today), encoding="utf-8")
            made.append(dest)
    gi = w / ".gitignore"
    if not gi.exists():
        gi.write_text(".DS_Store\nThumbs.db\n.obsidian/workspace*\n.obsidian/cache\n", encoding="utf-8")
        made.append(".gitignore")
    git = shutil.which("git")
    if not git:
        msg = "git 이 없어 기록 저장소는 건너뜀(지식베이스는 그대로 쓸 수 있어요)"
    elif (w / ".git").exists():
        msg = "git 저장소가 이미 있음"
    else:
        run = lambda *a: subprocess.run([git, "-C", str(w), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
        run("init", "-q")
        run("add", "-A")
        r = run("-c", "user.name=kb", "-c", "user.email=kb@localhost", "commit", "-qm", "setup: 지식베이스 만듦")
        msg = "git 저장소로 시작하고 첫 기록을 남김" if r.returncode == 0 else "git 저장소는 만들었지만 첫 기록은 못 남김: " + r.stderr.strip()[:120]
    print("지식베이스:", w)
    print("새로 만든 것:", ", ".join(made) if made else "없음(이미 있었어요)")
    print(msg)


def move_old():
    w = wiki_dir()
    if not is_old(w):
        sys.exit("옛 구조가 아니에요 — 옮기지 않음: " + str(w))
    dest = w.with_name(w.name + "-old-" + datetime.date.today().strftime("%Y%m%d"))
    if dest.exists():
        sys.exit("이미 있어요 — 옮기지 않음: " + str(dest))
    w.rename(dest)
    print("옮김:", w, "→", dest)


def pending():
    w = wiki_dir()
    raw = w / "raw"
    if not raw.exists():
        sys.exit("raw/ 가 없어요 — setup 부터")
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in (w / "wiki" / "sources").glob("*.md"))
    left = [p.relative_to(w).as_posix() for p in sorted(raw.rglob("*"))
            if p.is_file() and "assets" not in p.relative_to(raw).parts and not p.name.startswith(".")]
    left = [r for r in left if r not in text]
    print("\n".join(left) if left else "모두 ingest 됨")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "where"
    if cmd == "where":
        where()
    elif cmd == "setup":
        setup(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "pending":
        pending()
    elif cmd == "move-old":
        move_old()
    else:
        sys.exit(__doc__)
