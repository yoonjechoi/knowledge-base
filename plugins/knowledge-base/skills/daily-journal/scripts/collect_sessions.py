"""마지막 정리 이후의 모든 클로드 · 코덱스 세션을 모아 업무일(새벽 1시 경계)별로 보여 준다.

  python3 collect_sessions.py collect [--since ISO] [--until ISO]   # 기본: since = ~/.config/knowledge-base/last-run.txt, until = 지금
  python3 collect_sessions.py commit --until ISO                    # 일지 · 화면을 다 저장한 뒤에만

시각은 이 컴퓨터의 시간대 기준. 세션 파일 시각(UTC)은 바꿔서 쓴다.
출력: 업무일마다 세션별 사람 말(전부) + AI 의 긴 답(시각순 전부, 앞부분만 — 마지막 것은 길게). 사람 말이 없는 세션은 뺀다.
"""
import argparse, datetime, importlib.util, json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((HERE / "config.json").read_text())   # 모두에게 같은 값(하루 경계 · 세션 폴더 · 뺄 폴더)
_s = importlib.util.spec_from_file_location("kbsettings", HERE.parent / "kb/scripts/settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/
CUR = S.state("last-run.txt")
TZ = datetime.datetime.now().astimezone().tzinfo
B = CFG.get("day_boundary_hour", 1)


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(TZ)
    except ValueError:
        return None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for c in content:
            if isinstance(c, dict) and c.get("type") in ("text", "input_text", "output_text"):
                out.append(c.get("text", ""))
        return "\n".join(out)
    return ""


def messages(path):
    """(시각, 누가, 글) — 클로드 jsonl · 코덱스 jsonl 둘 다."""
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        ts = parse_ts(o.get("timestamp"))
        msg = o.get("message") if isinstance(o.get("message"), dict) else None
        if msg is None and isinstance(o.get("payload"), dict):   # 코덱스
            p = o["payload"]
            if p.get("type") == "message":
                msg = {"role": p.get("role"), "content": p.get("content")}
        if not msg or not ts:
            continue
        role = msg.get("role") or o.get("type")
        t = text_of(msg.get("content")).strip()
        if not t:
            continue
        if role == "user" and (t.startswith("<") or "tool_result" in t[:40]):
            continue
        yield ts, role, t


def workday(ts):
    return (ts - datetime.timedelta(hours=B)).date()


def collect(since, until):
    roots = [pathlib.Path(os.path.expanduser(r)) for r in CFG["session_roots"]]
    ex = CFG.get("exclude_path_parts", []) + S.load().get("exclude_extra", [])   # 내 것만 뺄 폴더는 내 설정에
    days = {}
    for root in roots:
        if not root.exists():
            continue
        for f in root.rglob("*.jsonl"):
            sp = str(f)
            if any(x in sp for x in ex):
                continue
            if datetime.datetime.fromtimestamp(f.stat().st_mtime, TZ) < since:
                continue
            per = {}
            for ts, role, t in messages(f):
                if since <= ts < until:
                    per.setdefault(workday(ts), []).append((ts, role, t))
            for d, ms in per.items():
                if any(r == "user" for _, r, _ in ms):
                    days.setdefault(d, []).append((f, ms))
    print(f"정리 범위: {since.isoformat(timespec='minutes')} ~ {until.isoformat(timespec='minutes')} (새벽 {B}시 경계)")
    print(f"끝 시각: {until.isoformat(timespec='seconds')}")
    if not days:
        print("대화 0줄 — 일지에 넣을 것이 없어요"); return
    for d in sorted(days):
        print(f"\n=== 업무일 {d} ({len(days[d])}개 세션)")
        for f, ms in sorted(days[d], key=lambda x: x[1][0][0]):
            where = f.parent.name if "projects" in str(f) else "codex"
            print(f"\n--- {where} · {ms[0][0]:%H:%M}~{ms[-1][0]:%H:%M} · {f.stem[:8]}")
            for ts, role, t in ms:
                if role == "user":
                    print(f"[{ts:%H:%M} 사람] {t[:600]}")
            longs = [(ts, t) for ts, r, t in ms if r == "assistant" and len(t) > 300]
            for i, (ts, t) in enumerate(longs):   # 긴 세션은 중간 결과도 — 마지막 것만 길게
                cut = 1200 if i == len(longs) - 1 else 350
                print(f"[{ts:%H:%M} AI 정리] {t[:cut]}")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["collect", "commit"])
    a.add_argument("--since"); a.add_argument("--until")
    o = a.parse_args()
    now = datetime.datetime.now(TZ)
    until = parse_ts(o.until) if o.until else now
    if o.cmd == "commit":
        if not o.until:
            sys.exit("--until(collect 가 찍은 끝 시각)을 꼭 줘요")
        CUR.write_text(until.isoformat(timespec="seconds"))
        print("마지막 정리 시각:", CUR.read_text()); sys.exit()
    if o.since:
        since = parse_ts(o.since)
    elif CUR.exists() and CUR.read_text().strip():
        since = parse_ts(CUR.read_text().strip())
    else:
        y = (now - datetime.timedelta(days=1)).date()
        since = datetime.datetime(y.year, y.month, y.day, tzinfo=TZ)
    collect(since, until)
