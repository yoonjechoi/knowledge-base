"""업무 일지 꺼내기 — 지식베이스 wiki/journal/*.md 를 날짜별 데이터로 내준다.
일지가 어디에 어떤 칸으로 있는지는 kb 만 안다(규칙 파일 「journal 칸」). 다른 스킬(journal-page · morning-brief · daily-journal)은 이걸 불러 쓴다.

  python3 journal.py days            # 모든 날, 새 날 먼저 (JSON)
  python3 journal.py day 2026-10-30  # 그날 하나 (JSON, 없으면 null)
  python3 journal.py text 2026-10-30 # 그날 일지 원문 그대로 (이어 쓸 때)
  python3 journal.py path            # 지식베이스 · journal 폴더 위치

파이썬에서: importlib 로 이 파일을 불러 days() · day(날짜) 를 쓴다.
"""
import datetime, importlib.util, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent.parent       # kb 스킬 폴더
_s = importlib.util.spec_from_file_location("kbsettings", HERE / "scripts/settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/
KB = S.kb_dir()
JDIR = KB / "wiki/journal"
DOW = "월화수목금토일"
LOG_KEYS = ["한 일", "정한 것", "만든 것", "내일 이어서"]
TOP = ("오늘 할 일", "해 두면 좋은 일", "이번 주에 마칠 것")


def clean(s):
    s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = re.split(r"\s+(?:—|→)\s+", s)[0]
    return s.replace("**", "").replace("`", "").strip()


def parse(path):
    secs, cur = {}, None
    body = path.read_text(encoding="utf-8").split("\n---", 2)[-1]
    for line in body.splitlines():
        m = re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            name = m.group(2).strip()
            if m.group(1) == "##" and name not in LOG_KEYS and name not in TOP:
                cur = None  # 일 갈래 머리 — 아래 ### 칸으로
                continue
            cur = name
            secs.setdefault(cur, [])
            continue
        m = re.match(r"^\s*-\s+(.*)", line)
        if m and cur:
            secs[cur].append(m.group(1))
    return secs


def _day(path, prev):
    d = datetime.date.fromisoformat(path.stem)
    s = parse(path)
    todo = []
    for x in s.get("오늘 할 일", []):
        done = x[:3] in ("[x]", "[X]")
        x = re.sub(r"^\[[ xX]\]\s*", "", x)
        if clean(x).startswith("AI가 먼저 정했어요"):
            continue
        t, _, p = x.rpartition(" · ") if " · " in x else (x, "", "")   # 「· 무슨 일」을 먼저 떼고 다듬는다
        if len(clean(p)) > 12:                                          # 뒤가 길면 무슨 일이 아니라 제목의 일부
            t, p = x, ""
        todo.append([clean(t) or clean(x), clean(p), 1 if done else 0])
    sug = [list(clean(x).partition(" | ")[::2]) for x in s.get("해 두면 좋은 일", [])
           if not clean(x).startswith("AI가 먼저 정했어요")]
    week = []
    for x in s.get("이번 주에 마칠 것", []):
        if x[:3] in ("[x]", "[X]"):
            continue
        a, _, due = re.sub(r"^\[[ xX]\]\s*", "", x).partition(" | ")
        try:
            n = (datetime.date.fromisoformat(due.strip()[:10]) - d).days
            dd = "D-day" if n == 0 else (f"D-{n}" if n > 0 else f"D+{-n}")
        except ValueError:
            dd = due.strip()
        week.append([clean(a), dd])
    yest = [clean(x) for x in prev.get("한 일", [])] if prev else []
    log = {k: [clean(re.sub(r"^\[[ xX]\]\s*", "", x)) for x in s[k]
               if not (k == "내일 이어서" and x[:3] in ("[x]", "[X]"))]   # 끝난 내일 이어서는 안 보인다
           for k in LOG_KEYS if s.get(k)}
    log = {k: v for k, v in log.items() if v}
    return dict(id="d-" + path.stem, date=f"{d.month}.{d.day}", dow=DOW[d.weekday()],
                todo=todo, suggest=sug, yesterday=yest, week=week, log=log or None), s


def days():
    out, prev = [], None
    for f in sorted(JDIR.glob("????-??-??.md")):
        dct, prev = _day(f, prev)
        out.append(dct)
    return out[::-1]


def day(date):
    return next((x for x in days() if x["id"] == "d-" + date), None)


if __name__ == "__main__":
    a = sys.argv[1:] or ["days"]
    if a[0] == "path":
        print(json.dumps({"kb": str(KB), "journal": str(JDIR)}, ensure_ascii=False))
    elif a[0] == "text":
        f = JDIR / f"{a[1] if len(a) > 1 else datetime.date.today().isoformat()}.md"
        print(f.read_text(encoding="utf-8") if f.exists() else "")
    elif a[0] == "day":
        print(json.dumps(day(a[1] if len(a) > 1 else datetime.date.today().isoformat()), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(days(), ensure_ascii=False, indent=1))
