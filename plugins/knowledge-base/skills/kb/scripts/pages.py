"""꺼내기 — 칸 하나의 노트를 원문 그대로 JSON 으로 내준다. 내용을 해석하지 않는다(모양을 아는 쪽이 해석한다).

  python3 pages.py <칸>                # 표준 출력으로
  python3 pages.py <칸> --out <파일>   # 파일로 (지식베이스 밖만)

내용: [{"name": 파일 이름, "path": "wiki/칸/파일.md", "text": 원문}, …] — 경로는 지식베이스 기준이라 위치가 드러나지 않는다.
없는 칸이면 종료 코드 2 와 있는 칸 목록.
"""
import argparse, importlib.util, json, os, pathlib, sys

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parent / "settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description="칸 하나 꺼내기")
    ap.add_argument("cell")
    ap.add_argument("--out")
    a = ap.parse_args()

    kb = S.kb_dir().resolve()
    w = kb / "wiki"
    d = (w / a.cell).resolve()
    if d.parent != w or a.cell.startswith(".") or not d.is_dir():
        have = sorted(p.name for p in w.iterdir() if p.is_dir() and not p.name.startswith(".")) if w.is_dir() else []
        fail(f"없는 칸: {a.cell} (있는 칸: {', '.join(have) or '없음'})")

    pages = [{"name": p.stem, "path": p.relative_to(kb).as_posix(), "text": p.read_text(encoding="utf-8")}
             for p in sorted(d.rglob("*.md")) if not any(x.startswith(".") for x in p.relative_to(d).parts)]
    data = json.dumps(pages, ensure_ascii=False, indent=1)

    if not a.out:
        print(data)
        return
    out = pathlib.Path(a.out).expanduser().resolve()
    if out == kb or kb in out.parents:
        fail("꺼낸 파일은 지식베이스 밖에 둔다")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f".{os.getpid()}.tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, out)
    print(f"꺼냄 {len(pages)}쪽 → {out}")


if __name__ == "__main__":
    main()
