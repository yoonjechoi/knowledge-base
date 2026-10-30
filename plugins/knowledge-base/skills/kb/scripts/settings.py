"""내 설정 — 사람마다 다른 값은 플러그인 밖 ~/.config/knowledge-base/ 한 곳에만 둔다(플러그인을 업데이트해도 안 지워진다).

  ~/.config/knowledge-base/
  ├── config.json    {"kb": 지식베이스 폴더, "ntfy_topic": 휴대폰 알림 구독 이름, "ntfy_token": 선택, "exclude_extra": [일지에서 뺄 폴더]}
  ├── last-run.txt   마지막으로 업무 일지를 정리한 시각
  └── page-url.txt   내 일지 화면 주소

  python3 settings.py show     # 설정을 보여 준다(ntfy 값은 「있음/없음」만)
  python3 settings.py path     # 설정 폴더 위치

다른 스크립트는 importlib 로 이 파일을 불러 load() · state(이름) 를 쓴다. ntfy 값은 그 프로그램 안에서만 읽고 출력하지 않는다.
"""
import json, os, pathlib, sys

for _o in (sys.stdout, sys.stderr):   # 윈도우 터미널에서도 한글 · ☐ 가 안 깨지게
    try:
        _o.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIR = pathlib.Path.home() / ".config" / "knowledge-base"
CONFIG = DIR / "config.json"
DEFAULT = {"kb": "~/knowledge-base"}
SECRET = ("ntfy_topic", "ntfy_token")


def load():
    """설정을 읽는다. 없으면 기본값으로 만든다."""
    if not CONFIG.exists():
        DIR.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(DEFAULT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**DEFAULT, **json.loads(CONFIG.read_text(encoding="utf-8"))}


def save(cfg):
    DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(CONFIG, 0o600)   # 구독 이름이 들어 있으니 나만 읽게
    except OSError:
        pass


def kb_dir():
    return pathlib.Path(os.path.expanduser(load()["kb"]))


def state(name):
    """last-run.txt · page-url.txt 같은 상태 파일 경로."""
    DIR.mkdir(parents=True, exist_ok=True)
    return DIR / name


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "path":
        print(DIR)
    else:
        c = load()
        for k, v in c.items():
            print(f"{k}: {('있음' if v else '없음') if k in SECRET else v}")
        for k in SECRET:
            if k not in c:
                print(f"{k}: 없음")
        for n in ("last-run.txt", "page-url.txt"):
            p = DIR / n
            print(f"{n}: {p.read_text(encoding='utf-8').strip() if p.exists() else '없음'}")
