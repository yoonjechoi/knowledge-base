"""업무 일지(지식베이스 journal/*.md) → 일지 화면 html 한 장.

  python3 render.py            # → ~/.cache/knowledge-base/journal.html 경로와 저장된 화면 주소를 출력

일지는 kb 스킬의 scripts/journal.py 가 꺼내 준다 — 지식베이스 위치와 일지 칸은 kb 만 안다.
morning-brief/scripts/brief.py 가 이 파일의 days() · URLFILE 을 같이 쓴다.
"""
import importlib.util, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent          # journal-page 스킬 폴더
_spec = importlib.util.spec_from_file_location("kbjournal", HERE.parent / "kb/scripts/journal.py")
J = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(J)   # 일지는 kb 가 꺼내 준다
days = J.days
_s = importlib.util.spec_from_file_location("kbsettings", HERE.parent / "kb/scripts/settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/
URLFILE = S.state("page-url.txt")
OUT = pathlib.Path.home() / ".cache/knowledge-base/journal.html"


def main():
    t = (HERE / "assets/template.html").read_text(encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(t.replace("/*DAYS*/[]", json.dumps(days(), ensure_ascii=False)), encoding="utf-8")
    print(OUT)
    print("url:", URLFILE.read_text(encoding="utf-8").strip() if URLFILE.exists() and URLFILE.read_text(encoding="utf-8").strip() else "(없음 — 처음 올리고 ~/.config/knowledge-base/page-url.txt 에 적기)")


if __name__ == "__main__":
    main()
