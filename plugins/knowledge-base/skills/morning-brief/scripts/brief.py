"""오늘 업무 일지 → 아침 브리핑 글, --send 면 ntfy 로 휴대폰에.

  python3 brief.py [YYYY-MM-DD] [--send]

모양(바꾸려면 여기만):
  10.29 목 · 오늘 할 일 3개        ← 알림 제목
  오늘 할 일 / ☐ 할 일 · 무슨 일 (8개까지, 넘으면 「외 n개 — 일지에서」)
  해 두면 좋은 일 / ＋ 무엇 — 왜
  이번 주에 마칠 것 / ☐ 할 일  D-3
  어제 한 일 / ☑ … (6개까지, 넘으면 「외 n개 — 일지에서」)
  빈 칸은 통째로 뺀다.
구독 이름 · 토큰은 내 설정(~/.config/knowledge-base/config.json 의 ntfy_topic · ntfy_token)에서 이 프로그램만 읽고, 어디에도 출력하지 않는다.
구독 이름이 없으면 보내기만 건너뛴다 — 설정은 ntfy-setup 스킬.
"""
import datetime, importlib.util, pathlib, sys, urllib.request

PAGE = pathlib.Path(__file__).resolve().parents[2] / "journal-page/scripts/render.py"
spec = importlib.util.spec_from_file_location("render", PAGE)
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)


def cut(s, n=40):
    return s if len(s) <= n else s[:n - 1] + "…"


def build(date):
    d = next((x for x in R.days() if x["id"] == "d-" + date), None)
    if not d:
        return None, None
    left = [t for t in d["todo"] if not t[2]]
    L = []
    if left:
        L += ["오늘 할 일"] + [f"☐ {cut(t[0])}" + (f" · {t[1]}" if t[1] else "") for t in left[:8]]
        L += ([f"외 {len(left) - 8}개 — 일지에서"] if len(left) > 8 else []) + [""]
    if d["suggest"]:
        L += ["해 두면 좋은 일"] + [f"＋ {a}" + (f" — {b}" if b else "") for a, b in d["suggest"]] + [""]
    if d["week"]:
        L += ["이번 주에 마칠 것"] + [f"☐ {a}  {b}" for a, b in d["week"]] + [""]
    y = d["yesterday"]
    if y:
        L += ["어제 한 일"] + [f"☑ {cut(x)}" for x in y[:6]] + ([f"외 {len(y) - 6}개 — 일지에서"] if len(y) > 6 else [])
    return f"{d['date']} {d['dow']} · 오늘 할 일 {len(left)}개", "\n".join(L).strip(), d["id"]


def send(title, body, did):
    c = R.S.load()
    topic = (c.get("ntfy_topic") or "").strip()
    if not topic:
        return "휴대폰 알림은 건너뜀 — 아직 구독 이름이 없어요(ntfy-setup 스킬로 설정)"
    url = R.URLFILE.read_text(encoding="utf-8").strip() if R.URLFILE.exists() else ""
    hdr = {"Title": title.encode("utf-8").decode("latin-1"), "Priority": "high", "Tags": "sunrise"}
    if url:
        hdr["Click"] = f"{url}#{did}"
        hdr["Actions"] = f"view, 일지 열기, {url}#{did}".encode("utf-8").decode("latin-1")
    tok = (c.get("ntfy_token") or "").strip()
    if tok:
        hdr["Authorization"] = "Bearer " + tok
    req = urllib.request.Request("https://ntfy.sh/" + topic, data=body.encode("utf-8"), headers=hdr, method="POST")
    why = ""
    for _ in range(2):   # 실패하면 한 번 다시
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return "휴대폰으로 보냈어요"
                why = f"HTTP {r.status}"
        except Exception as e:
            why = str(e).replace(topic, "***").replace(tok or "\0", "***")
    return "알림 실패: " + why


if __name__ == "__main__":
    a = sys.argv[1:]
    rest = [x for x in a if x != "--send"]
    date = rest[0] if rest else datetime.date.today().isoformat()
    out = build(date)
    if out[0] is None:
        print(f"{date} 일지가 없어요"); sys.exit(1)
    title, body, did = out
    print(title); print(); print(body)
    if "--send" in a:
        print(); print(send(title, body, did))
