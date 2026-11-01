"""지식베이스 커밋 — 이번 작업에서 바꾼 파일만, 세션이 겹쳐도 남의 작업이 섞이지 않게 커밋한다.

  python3 commit.py -m "ingest: 한 줄" wiki/log.md wiki/index.md raw/2026-11-01-메모.md

- 파일을 하나씩 적는다. 폴더 · 지식베이스 밖 경로는 받지 않는다.
- `git commit --only` 로 적은 파일만 넣는다. 다른 세션이 스테이징해 둔 파일은 그대로 남는다.
- lock 은 이 프로그램과 inbox.py 만 다룬다. 다른 프로그램이 lock 을 직접 잡지 않는다.
- 기록 저장소(.git) 나 git 이 없으면 건너뛰고 성공으로 끝낸다. 이름 · 이메일이 없으면 kb 이름으로 커밋한다.

마지막 줄: `커밋 <해시>` · `바뀐 것 없음` · `기록 저장소 없음` 중 하나. 실패하면 종료 코드 1, 경로가 틀리면 2.
"""
import argparse, importlib.util, os, pathlib, shutil, subprocess, sys, time

_s = importlib.util.spec_from_file_location("kbsettings", pathlib.Path(__file__).resolve().parent / "settings.py")
S = importlib.util.module_from_spec(_s); _s.loader.exec_module(S)   # 내 설정은 ~/.config/knowledge-base/

WAIT = 60      # lock 을 기다리는 초
STALE = 300    # 이보다 오래된 lock 은 멈춘 프로그램이 남긴 것으로 본다


def fail(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def git(kb, *a):
    return subprocess.run(["git", "--literal-pathspecs", "-C", str(kb), *a],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def relative(kb, name):
    """지식베이스 기준 경로로 바꾼다. 밖 · 폴더 · .git 은 거절한다(지운 파일은 있어도 없어도 된다)."""
    p = pathlib.Path(name).expanduser()
    p = (p if p.is_absolute() else kb / p).resolve()
    try:
        rel = p.relative_to(kb.resolve())
    except ValueError:
        fail(f"지식베이스 밖 경로: {name}", 2)
    if p.is_dir() or not rel.parts or rel.parts[0] == ".git":
        fail(f"파일만 적을 수 있어요: {name}", 2)
    return rel.as_posix()


def has_repo(kb):
    return bool(shutil.which("git")) and (kb / ".git").exists()


def lock_dir(kb):
    """lock 을 두는 곳 — 저장소가 있으면 .git 안, 없으면 지식베이스 폴더."""
    return pathlib.Path(git(kb, "rev-parse", "--absolute-git-dir").stdout.strip()) if has_repo(kb) else kb


class Lock:
    def __init__(self, kb):
        self.path = str(lock_dir(kb) / "kb-commit.lock")

    def __enter__(self):
        end = time.time() + WAIT
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > STALE:
                        os.unlink(self.path)
                        continue
                except OSError:
                    continue
                if time.time() > end:
                    fail("lock 을 못 잡음 — 커밋하지 않고 멈춤")
                time.sleep(0.2)

    def __exit__(self, *_):
        try:
            os.unlink(self.path)
        except OSError:
            pass


def retry(kb, *a):
    """git 이 잠깐 잡은 index.lock 에 걸리면 다시 한다."""
    for i in range(6):
        r = git(kb, *a)
        if r.returncode == 0 or "index.lock" not in r.stderr:
            return r
        time.sleep(0.5 * (i + 1))
    return r


def save(kb, msg, names):
    """적은 파일만 커밋하고 결과 한 줄을 돌려준다. lock 은 부르는 쪽이 잡는다."""
    if not has_repo(kb):
        return "기록 저장소 없음"
    files = sorted({relative(kb, f) for f in names})
    gone = git(kb, "diff", "--cached", "--no-renames", "--diff-filter=D", "--name-only", "-z", "--", *files).stdout.split("\0")   # git mv · git rm 으로 이미 빠진 경로
    add = [f for f in files if f not in gone]
    if add:
        r = retry(kb, "add", "--", *add)
        if r.returncode:
            fail("git add 실패: " + r.stderr.strip()[:300])
    if git(kb, "diff", "--cached", "--quiet", "--", *files).returncode == 0:
        return "바뀐 것 없음"
    who = []
    if not git(kb, "config", "user.name").stdout.strip() or not git(kb, "config", "user.email").stdout.strip():
        who = ["-c", "user.name=kb", "-c", "user.email=kb@localhost"]
    r = retry(kb, *who, "commit", "-q", "--only", "-m", msg, "--", *files)
    if r.returncode:
        fail("git commit 실패: " + (r.stderr or r.stdout).strip()[:300])
    return "커밋 " + git(kb, "rev-parse", "--short", "HEAD").stdout.strip()


def main():
    ap = argparse.ArgumentParser(description="바꾼 파일만 커밋")
    ap.add_argument("-m", required=True, dest="msg")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()

    kb = S.kb_dir()
    if not has_repo(kb):
        print("기록 저장소 없음")
        return
    for f in a.files:
        relative(kb, f)      # 잘못된 경로는 lock 전에 거절
    with Lock(kb):
        print(save(kb, a.msg, a.files))


if __name__ == "__main__":
    main()
