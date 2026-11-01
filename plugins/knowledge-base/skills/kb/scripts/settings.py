"""내 설정 — 지식베이스 위치는 플러그인 밖 ~/.config/knowledge-base/config.json 의 `kb` 한 줄이 정한다(플러그인을 업데이트해도 안 지워진다).

  python3 settings.py show     # 지식베이스 위치와 지금 쓰는 규칙
  python3 settings.py path     # 설정 폴더 위치
  python3 settings.py rules    # 지금 쓰는 규칙 파일 경로 (지식베이스의 rules.md, 없으면 기본 규칙)

다른 스크립트는 importlib 로 이 파일을 불러 kb_dir() · rules_path() 를 쓴다.
설정 파일에 다른 프로그램의 값이 있어도 kb 만 읽고, 나머지는 출력하지 않고 그대로 둔다.
"""
import json, os, pathlib, sys

for _o in (sys.stdout, sys.stderr):   # 윈도우 터미널에서도 한글이 안 깨지게
    try:
        _o.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIR = pathlib.Path.home() / ".config" / "knowledge-base"
CONFIG = DIR / "config.json"
DEFAULT = {"kb": "~/knowledge-base"}
DEFAULT_RULES = pathlib.Path(__file__).resolve().parent.parent / "references" / "rules.md"


def load():
    """설정을 읽는다. 없으면 기본값으로 만든다."""
    if not CONFIG.exists():
        save(DEFAULT)
    return {**DEFAULT, **json.loads(CONFIG.read_text(encoding="utf-8"))}


def save(cfg):
    DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(CONFIG, 0o600)
    except OSError:
        pass


def kb_dir():
    return pathlib.Path(os.path.expanduser(load()["kb"]))


def rules_path(kb=None):
    """규칙 파일 — 지식베이스 안의 rules.md 가 있으면 그것만, 없으면 기본 규칙."""
    mine = pathlib.Path(kb or kb_dir()) / "rules.md"
    return mine if mine.is_file() else DEFAULT_RULES


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "path":
        print(DIR)
    elif cmd == "rules":
        print(rules_path())
    else:
        print("kb:", kb_dir())
        print("rules:", rules_path())
