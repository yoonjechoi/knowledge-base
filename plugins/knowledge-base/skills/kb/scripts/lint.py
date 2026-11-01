"""지식베이스 기계 점검 — 판단이 필요 없는 것만. 판단(어긋남 · 낡은 주장 · 빠진 개념)은 AI가 한다.
칸 목록을 따로 갖지 않는다. wiki/ 안의 폴더가 곧 칸이고, 칸 이름은 index.md 의 `## 폴더이름` 머리와 맞으면 된다.

  python3 lint.py [지식베이스 폴더] [--fix]     # 기본 = 내 설정의 kb (~/.config/knowledge-base/config.json)

--fix: 링크를 `[[파일-이름|보일 이름]]` 모양으로 맞추고 고친 파일을 「고침: 경로」로 출력한다. 표기만 다른 끊긴 링크는 실제 쪽 이름으로 고치고 쓰던 말을 보일 이름으로 남기며, 보일 이름 없이 하이픈이 보이는 링크에는 보일 이름을 더한다. 머리말 · 코드 · log · 날짜 이름은 건드리지 않고, 그 밖에는 아무것도 바꾸지 않는다.
"""
import argparse, importlib.util, pathlib, re, unicodedata

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parent / "settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/
_i = importlib.util.spec_from_file_location("kbinbox", pathlib.Path(__file__).resolve().parent / "inbox.py")
I = importlib.util.module_from_spec(_i); _i.loader.exec_module(I)   # 대기 목록의 모양은 inbox.py 만 안다

ap = argparse.ArgumentParser(description="기계 점검")
ap.add_argument("kb", nargs="?")
ap.add_argument("--fix", action="store_true")
args = ap.parse_args()
KB = pathlib.Path(args.kb).expanduser() if args.kb else S.kb_dir()
W = KB / "wiki"
SPECIAL = {"index", "log", "inbox"}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")     # 날짜 이름 쪽은 날짜로 찾으니 링크 · index 를 보지 않는다


def visible(p, top=W):
    return not any(x.startswith(".") for x in p.relative_to(top).parts)


def nfc(s):
    return unicodedata.normalize("NFC", s)


def key(s):
    return re.sub(r"[\s-]+", "", nfc(s).lower())


def find_links(text):
    return {m.split("|")[0].split("#")[0].strip() for m in re.findall(r"\[\[([^\]]+)\]\]", text)}


notes = {p.stem: p for p in W.rglob("*.md") if visible(p)}
same = {}
for n in notes:
    same.setdefault(key(n), []).append(n)

def split_body(text):
    """머리말을 떼고, 코드(`…` · ```…```)는 건드리지 않게 나눈다. 홀수 번째 조각이 코드다."""
    head = ""
    if text.startswith("---\n") and "\n---" in text[4:]:
        end = text.index("\n---", 4) + 4
        head, text = text[:end], text[end:]
    return head, re.split(r"(```.*?```|`[^`\n]*`)", text, flags=re.S)


def bare(name):
    """하이픈이 화면에 그대로 보이게 될 쪽 이름인가 — 날짜 이름은 하이픈이 맞다."""
    return "-" in name and not DATE.fullmatch(name)


def relink(m):
    target, _, shown = m.group(1).partition("|")
    base, sharp, part = target.strip().partition("#")
    real = base
    if base and base not in notes and not (KB / base).exists() and len(same.get(key(base), [])) == 1:
        real = same[key(base)][0]
    if real not in notes:
        return m.group(0)
    if not shown and bare(real):
        shown = base if "-" not in base else real.replace("-", " ")
    return "[[" + real + sharp + part + ("|" + shown if shown else "") + "]]"


if args.fix:
    for name, p in notes.items():
        if name in SPECIAL:      # log 는 덧붙이기만 한다
            continue
        old = p.read_text(encoding="utf-8", errors="ignore")
        head, parts = split_body(old)
        text = head + "".join(x if i % 2 else re.sub(r"\[\[([^\]]+)\]\]", relink, x) for i, x in enumerate(parts))
        if text != old:
            p.write_text(text, encoding="utf-8")
            print("고침:", p.relative_to(KB).as_posix())

links = {name: find_links(p.read_text(encoding="utf-8", errors="ignore")) for name, p in notes.items()}
index = (W / "index.md").read_text(encoding="utf-8") if (W / "index.md").exists() else ""
found = []

for name, ts in links.items():
    for t in ts:
        if t and t not in notes and not (KB / t).exists():
            found.append(("끊긴 링크", f"{notes[name].relative_to(KB)} → [[{t}]]"))
for name, p in notes.items():
    if name in SPECIAL:
        continue
    _, parts = split_body(p.read_text(encoding="utf-8", errors="ignore"))
    for m in re.findall(r"\[\[([^\]|]+)\]\]", "".join(parts[::2])):
        if m.split("#")[0].strip() in notes and bare(m.split("#")[0].strip()):
            found.append(("보일 이름 없는 링크", f"{p.relative_to(KB)} → [[{m}]]"))
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

# 대기 목록과 raw 맞추기
waiting = {nfc(x["raw"]) for x in I.items(KB)}
seen = set()
for x in I.items(KB):
    r = nfc(x["raw"])
    if r in seen:
        found.append(("대기에 두 번", x["raw"]))
    seen.add(r)
    if not (KB / x["raw"]).is_file():
        found.append(("대기에 있는데 raw 없음", x["raw"]))
    if x["hold"]:
        found.append(("대기 보류", f"{x['raw']} — {x['hold']}"))
for ln in I.read(KB).splitlines():
    if ln.startswith("- ") and not I.parse(ln):
        found.append(("대기 줄 모양이 틀림", ln[:60]))
wiki_text = nfc("\n".join(p.read_text(encoding="utf-8", errors="ignore") for s, p in notes.items() if s != "inbox"))
if (KB / "raw").is_dir():
    for p in sorted((KB / "raw").rglob("*")):
        if not p.is_file() or not visible(p, KB):
            continue
        rel = nfc(p.relative_to(KB).as_posix())
        if rel not in waiting and nfc(p.name) not in wiki_text and nfc(p.stem) not in wiki_text:
            found.append(("대기에도 노트에도 없는 raw", rel))

print(f"쪽 {len(notes) - len(SPECIAL & set(notes))}개 · 대기 {len(waiting)}개 · 찾은 것 {len(found)}개 · 규칙 {'내 rules.md' if S.rules_path(KB) != S.DEFAULT_RULES else '기본'}")
for k, v in found:
    print(f"- {k}: {v}")
