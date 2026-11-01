"""지식베이스 기계 점검 — 판단이 필요 없는 것만. 판단(어긋남 · 낡은 주장 · 빠진 개념)은 AI가 한다.
칸 목록을 따로 갖지 않는다. wiki/ 안의 폴더가 곧 칸이고, 칸 이름은 index.md 의 `## 폴더이름` 머리와 맞으면 된다.

  python3 lint.py [지식베이스 폴더]     # 기본 = 내 설정의 kb (~/.config/knowledge-base/config.json)
"""
import importlib.util, pathlib, re, sys

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parent / "settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/
KB = pathlib.Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else S.kb_dir()
W = KB / "wiki"
SPECIAL = {"index", "log"}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")     # 날짜 이름 쪽은 날짜로 찾으니 링크 · index 를 보지 않는다


def visible(p):
    return not any(x.startswith(".") for x in p.relative_to(W).parts)


notes = {p.stem: p for p in W.rglob("*.md") if visible(p)}
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
    if c == 0 and n not in SPECIAL and not DATE.fullmatch(n):
        found.append(("아무도 안 가리킴", str(notes[n].relative_to(KB))))
for n, p in notes.items():
    if n in SPECIAL or DATE.fullmatch(n):
        continue
    if n not in index and n.replace("-", " ") not in index:
        found.append(("index 에 없음", str(p.relative_to(KB))))
for p in W.rglob("*"):
    if " " in p.name and visible(p):
        found.append(("이름에 띄어쓰기", str(p.relative_to(KB))))
for p in W.glob("*.md"):
    if p.stem not in SPECIAL:
        found.append(("칸 밖에 있음", str(p.relative_to(KB))))
heads = set(re.findall(r"^##\s+(\S+)", index, re.M))
for cell in (p for p in W.iterdir() if p.is_dir() and visible(p)):
    if cell.name not in heads:
        found.append(("index 에 칸 머리 없음", str(cell.relative_to(KB))))
    for sub in cell.iterdir():
        if sub.is_dir() and visible(sub) and not list(sub.rglob("*.md")):
            found.append(("노트 없는 폴더", str(sub.relative_to(KB))))

print(f"쪽 {len(notes) - len(SPECIAL & set(notes))}개 · 찾은 것 {len(found)}개 · 규칙 {'내 rules.md' if S.rules_path(KB) != S.DEFAULT_RULES else '기본'}")
for k, v in found:
    print(f"- {k}: {v}")
