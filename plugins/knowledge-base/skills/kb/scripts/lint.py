"""지식베이스 기계 점검 — 판단이 필요 없는 것만. 판단(어긋남 · 낡은 주장 · 빠진 개념)은 AI가 한다.

  python3 lint.py [지식베이스 폴더]     # 기본 = 내 설정의 kb (~/.config/knowledge-base/config.json)
"""
import importlib.util, pathlib, re, sys

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parent / "settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/
KB = pathlib.Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else S.kb_dir()
W = KB / "wiki"
CELLS = ["me", "business", "brands", "customers", "projects", "topics", "synthesis", "journal"]
SPECIAL = {"index", "log"}

notes = {p.stem: p for p in W.rglob("*.md")}
links = {}   # 쪽 → 가리키는 이름들
for name, p in notes.items():
    t = p.read_text(encoding="utf-8", errors="ignore")
    links[name] = {m.split("|")[0].split("#")[0].strip() for m in re.findall(r"\[\[([^\]]+)\]\]", t)}

index = (W / "index.md").read_text(encoding="utf-8") if (W / "index.md").exists() else ""
found = []

for name, ts in links.items():
    for t in ts:
        if t and t not in notes and not (KB / t).exists():
            found.append(("끊긴 링크", f"{notes[name].relative_to(KB)} → [[{t}]]"))
incoming = {n: 0 for n in notes}
for ts in links.values():
    for t in ts:
        if t in incoming:
            incoming[t] += 1
for n, c in incoming.items():
    p = notes[n]
    if c == 0 and n not in SPECIAL and p.parent.name != "journal":
        found.append(("아무도 안 가리킴", str(p.relative_to(KB))))
for n, p in notes.items():
    if n in SPECIAL or p.parent.name == "journal":
        continue
    label = n
    if label not in index and label.replace("-", " ") not in index:
        found.append(("index 에 없음", str(p.relative_to(KB))))
for p in W.rglob("*"):
    if " " in p.name:
        found.append(("이름에 띄어쓰기", str(p.relative_to(KB))))
for p in W.glob("*.md"):
    if p.stem not in SPECIAL:
        found.append(("칸 밖에 있음", str(p.relative_to(KB))))
for p in W.iterdir():
    if p.is_dir() and p.name not in CELLS and not p.name.startswith("."):
        found.append(("규칙에 없는 칸", str(p.relative_to(KB))))
for p in (W / "journal").glob("*.md") if (W / "journal").exists() else []:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem):
        found.append(("journal 이름이 날짜가 아님", str(p.relative_to(KB))))
for p in (W / "brands").glob("*/") if (W / "brands").exists() else []:
    if not list(p.glob("*.md")):
        found.append(("브랜드 노트 없음", str(p.relative_to(KB))))

print(f"쪽 {len(notes) - len(SPECIAL & set(notes))}개 · 찾은 것 {len(found)}개")
for k, v in found:
    print(f"- {k}: {v}")
