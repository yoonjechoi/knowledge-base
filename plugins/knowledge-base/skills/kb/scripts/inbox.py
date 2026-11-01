"""대기 목록 — 받았지만 아직 정리하지 않은 자료. 지식베이스의 wiki/inbox.md 하나에 한 줄씩 있고, 이 프로그램만 고친다.

  한 줄: - raw 경로 | 받은 날 | 출처 | 주제 | 핵심 사실 [| 보류: 이유]

받기 (수 초):
  python3 inbox.py add --file <파일> --topic 주제 --facts 핵심사실 [--title 제목] [--source 출처]
  python3 inbox.py add --stdin --title 제목 --topic 주제 --facts 핵심사실 [--source 출처]   # 글은 표준 입력으로
  python3 inbox.py add --raw raw/이미-있는-파일.md --topic 주제 --facts 핵심사실 [--source 출처]
보기:
  python3 inbox.py list
정리 (한 번에 한 실행만):
  python3 inbox.py begin                                    # 다른 정리가 돌면 종료 코드 3. 지난 보류를 풀어 다시 시도한다
  python3 inbox.py next                                     # 다음 항목 한 줄, 없으면 「대기 없음」
  python3 inbox.py done -m "ingest: 제목" <raw 경로> [파일들]  # 항목을 빼고 적은 파일과 함께 커밋
  python3 inbox.py hold <raw 경로> 이유                      # 이번에 못 하는 항목. 대기에 남고 다음 실행에 다시 시도
  python3 inbox.py end

done 전에 멈추면 항목이 대기에 남는다. 멈춘 정리의 표시는 30분 뒤 다음 begin 이 넘겨받는다.
"""
import argparse, datetime, importlib.util, os, pathlib, re, shutil, sys, time, unicodedata

_c = importlib.util.spec_from_file_location("kbcommit", pathlib.Path(__file__).resolve().parent / "commit.py")
C = importlib.util.module_from_spec(_c); _c.loader.exec_module(C)   # 커밋과 lock 은 commit.py 한 곳에
S = C.S

NAME = "wiki/inbox.md"
HEAD = ("# 대기 목록\n\n받았지만 아직 정리하지 않은 자료. kb 스킬의 inbox.py 만 고친다.\n"
        "한 줄 = `- raw 경로 | 받은 날 | 출처 | 주제 | 핵심 사실`\n\n")
TIDY_STALE = 1800      # 이보다 오래 소식이 없는 정리는 멈춘 것으로 본다
IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".svg"}


def field(s):
    return re.sub(r"\s+", " ", (s or "-").replace("|", "/")).strip() or "-"


def slug(s):
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"[\s/\\:*?\"<>|\[\]]+", "-", s).strip("-.") or "자료"


def parse(line):
    """대기 줄 → dict, 대기 줄이 아니면 None."""
    if not line.startswith("- raw/"):
        return None
    f = line[2:].split(" | ")
    if len(f) < 5:
        return None
    return {"raw": f[0], "date": f[1], "source": f[2], "topic": f[3], "facts": f[4], "hold": " | ".join(f[5:])}


def read(kb):
    p = kb / NAME
    return p.read_text(encoding="utf-8") if p.exists() else HEAD


def items(kb):
    return [x for x in map(parse, read(kb).splitlines()) if x]


def write(kb, text):
    p = kb / NAME
    tmp = p.with_name(f"inbox.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def unique(path):
    """같은 이름이 있으면 -2 · -3. lock 안에서만 부른다."""
    if not path.exists():
        return path
    n = 2
    while True:
        c = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not c.exists():
            return c
        n += 1


def add(kb, a):
    today = datetime.date.today().isoformat()
    body = sys.stdin.read() if a.stdin else None
    src = pathlib.Path(a.file).expanduser() if a.file else None
    if src and not src.is_file():
        C.fail(f"파일이 없음: {a.file}", 2)
    with C.Lock(kb):
        if a.raw:
            rel = C.relative(kb, a.raw)
            if not rel.startswith("raw/") or "|" in rel or not (kb / rel).is_file():
                C.fail(f"raw 안의 파일이 아님: {a.raw}", 2)
            if any(x["raw"] == rel for x in items(kb)):
                C.fail(f"이미 대기 중: {rel}", 2)
            new = []
        else:
            ext = src.suffix.lower() if src else ".md"
            stem = f"{today}-{slug(a.title)}" if a.title else slug(src.stem)
            folder = kb / ("raw/assets" if ext in IMAGES else "raw")
            folder.mkdir(parents=True, exist_ok=True)
            dest = unique(folder / (stem + ext))
            if src:
                shutil.copy2(src, dest)
            else:
                dest.write_text(f"> 출처: {field(a.source)} · {today}\n\n{body}", encoding="utf-8")
            rel = dest.relative_to(kb).as_posix()
            new = [rel]
        text = read(kb)
        line = f"- {rel} | {today} | {field(a.source)} | {field(a.topic)} | {field(a.facts)}\n"
        write(kb, (text if text.endswith("\n") else text + "\n") + line)
        done = C.save(kb, f"inbox: {field(a.title or a.topic)}", new + [NAME])
        print(f"받음 {rel} · 대기 {len(items(kb))}개 · {done}")


def begin(kb):
    path = C.lock_dir(kb) / "kb-tidy.lock"
    for _ in range(50):
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except (FileExistsError, PermissionError):     # 윈도우는 지워지는 중인 파일에 PermissionError 를 낸다
            try:
                if time.time() - os.path.getmtime(path) <= TIDY_STALE:
                    print("다른 정리가 도는 중")
                    sys.exit(3)
                os.unlink(path)
            except OSError:
                time.sleep(0.1)
    else:
        C.fail("정리 표시를 못 만듦")
    with C.Lock(kb):
        lines = read(kb).splitlines(keepends=True)
        out = []
        for ln in lines:
            x = parse(ln.rstrip("\n"))
            out.append(f"- {x['raw']} | {x['date']} | {x['source']} | {x['topic']} | {x['facts']}\n" if x and x["hold"] else ln)
        if out != lines:
            write(kb, "".join(out))
            C.save(kb, "inbox: 보류 풀기", [NAME])
    print(f"정리 시작 · 대기 {len(items(kb))}개")


def touch(kb):
    try:
        os.utime(C.lock_dir(kb) / "kb-tidy.lock")
    except OSError:
        pass


def show(x):
    return " | ".join([x["raw"], x["date"], x["source"], x["topic"], x["facts"]] + ([x["hold"]] if x["hold"] else []))


def next_item(kb):
    touch(kb)
    rest = [x for x in items(kb) if not x["hold"]]
    print(show(rest[0]) if rest else "대기 없음")


def take(kb, raw, change):
    """raw 항목의 줄을 change(줄) 로 바꾼다. None 이면 뺀다. 없으면 멈춘다."""
    lines = read(kb).splitlines(keepends=True)
    hit = [i for i, ln in enumerate(lines) if (parse(ln.rstrip("\n")) or {}).get("raw") == raw]
    if not hit:
        C.fail(f"대기에 없음: {raw}", 2)
    for i in reversed(hit):
        v = change(lines[i])
        lines[i:i + 1] = [v] if v else []
    write(kb, "".join(lines))


def done(kb, a):
    touch(kb)
    with C.Lock(kb):
        take(kb, a.raw, lambda _: None)
        print(f"{C.save(kb, a.msg, list(a.files) + [NAME])} · 대기 {len(items(kb))}개")


def hold(kb, a):
    touch(kb)
    why = field(a.why)
    with C.Lock(kb):
        take(kb, a.raw, lambda ln: ln.split(" | 보류: ")[0].rstrip("\n") + f" | 보류: {why}\n")
        print(C.save(kb, f"inbox: 보류 {a.raw}", [NAME]))


def end(kb):
    try:
        os.unlink(C.lock_dir(kb) / "kb-tidy.lock")
    except OSError:
        pass
    its = items(kb)
    print(f"정리 끝 · 남은 대기 {len(its)}개 · 보류 {sum(1 for x in its if x['hold'])}개")


def main():
    ap = argparse.ArgumentParser(description="대기 목록")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--file"); g.add_argument("--stdin", action="store_true"); g.add_argument("--raw")
    p.add_argument("--title"); p.add_argument("--source")
    p.add_argument("--topic", required=True); p.add_argument("--facts", required=True)
    sub.add_parser("list"); sub.add_parser("begin"); sub.add_parser("next"); sub.add_parser("end")
    p = sub.add_parser("done"); p.add_argument("-m", required=True, dest="msg"); p.add_argument("raw"); p.add_argument("files", nargs="*")
    p = sub.add_parser("hold"); p.add_argument("raw"); p.add_argument("why")
    a = ap.parse_args()
    if a.cmd == "add" and a.stdin and not a.title:
        ap.error("--stdin 에는 --title 이 필요하다")

    kb = S.kb_dir()
    if a.cmd == "add":
        add(kb, a)
    elif a.cmd == "list":
        its = items(kb)
        for x in its:
            print(show(x))
        print(f"대기 {len(its)}개")
    elif a.cmd == "begin":
        begin(kb)
    elif a.cmd == "next":
        next_item(kb)
    elif a.cmd == "done":
        done(kb, a)
    elif a.cmd == "hold":
        hold(kb, a)
    else:
        end(kb)


if __name__ == "__main__":
    main()
