"""kb 스크립트 시험 — 임시 HOME 과 임시 지식베이스에서만 돈다. 실제 설정과 데이터를 건드리지 않는다.

  python3 -m unittest discover -s tests
"""
import concurrent.futures, json, os, pathlib, subprocess, sys, tempfile, unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "plugins/knowledge-base/skills/kb/scripts"
RULES = SCRIPTS.parent / "references/rules.md"
START = {"me", "business", "brands", "customers", "projects", "topics", "synthesis"}


class Base(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = pathlib.Path(self._t.name).resolve()
        self.home = self.root / "home"
        self.kb = self.root / "내 지식베이스"
        (self.home / ".config/knowledge-base").mkdir(parents=True)
        self.config({"kb": str(self.kb)})

    def config(self, cfg):
        (self.home / ".config/knowledge-base/config.json").write_text(json.dumps(cfg), encoding="utf-8")

    def env(self):
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                 GIT_CONFIG_GLOBAL=str(self.root / "no-gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        return e

    def run_py(self, script, *a):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, a)], env=self.env(),
                              capture_output=True, text=True, encoding="utf-8")

    def init(self):
        r = self.run_py("init.py")
        self.assertEqual(r.returncode, 0, r.stderr)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.kb), *a], env=self.env(), capture_output=True,
                              text=True, encoding="utf-8").stdout

    def write(self, rel, text="내용\n"):
        p = self.kb / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def lint(self):
        return self.run_py("lint.py").stdout


class Init(Base):
    def test_starts_with_rule_cells_and_no_journal(self):
        self.init()
        cells = {p.name for p in (self.kb / "wiki").iterdir() if p.is_dir()}
        self.assertEqual(cells, START)
        self.assertEqual((self.kb / "rules.md").read_text(encoding="utf-8"), RULES.read_text(encoding="utf-8"))
        self.assertIn("## me (나)", (self.kb / "wiki/index.md").read_text(encoding="utf-8"))
        self.assertIn("## synthesis (대화에서 얻은 결론)", (self.kb / "wiki/index.md").read_text(encoding="utf-8"))
        self.assertIn("rules.md", self.git("ls-files"))
        self.assertIn("wiki/inbox.md", self.git("ls-files"))
        self.assertIn("찾은 것 0개", self.lint())

    def test_keeps_my_rules_and_uses_their_cells(self):
        self.write("rules.md", "| 폴더 | 넣는 것 | 파일 |\n|---|---|---|\n| `recipes/` | 요리 — 메뉴 | 하나 |\n")
        self.init()
        self.assertTrue((self.kb / "wiki/recipes").is_dir())
        self.assertFalse((self.kb / "wiki/topics").exists())
        self.assertIn("## recipes (요리)", (self.kb / "wiki/index.md").read_text(encoding="utf-8"))

    def test_second_run_changes_nothing(self):
        self.init()
        self.write("wiki/index.md", "내가 고침\n")
        self.init()
        self.assertEqual((self.kb / "wiki/index.md").read_text(encoding="utf-8"), "내가 고침\n")


class Docs(Base):
    def test_three_operations_and_conclusion_rule(self):
        skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        rules = RULES.read_text(encoding="utf-8")
        self.assertIn("「이 결론 저장해 줘」", skill.split("---")[1])
        self.assertIn("「이 결론 지식베이스에 저장해 줘」", skill.split("---")[1])
        self.assertNotIn("## Save", skill)
        self.assertNotIn("|save|", rules + skill + (SCRIPTS / "init.py").read_text(encoding="utf-8"))
        self.assertIn("대화나 기존 노트에서 나온 결론이면 `raw/` 에 넣지 않고 `synthesis/` 에 넣는다", rules)
        self.assertNotIn("꺼내기", skill + rules)
        self.assertIn("「이 결론 저장해 줘」", skill.split("---")[1])
        self.assertIn("「바로 정리해 줘」", skill.split("---")[1])
        self.assertIn("정리 전 자료", skill)


    def test_words_are_note_and_folder(self):
        names = [SCRIPTS.parent / "SKILL.md", RULES, SCRIPTS.parents[2] / "agents/tidier.md", SCRIPTS.parents[4] / "README.md",
                 SCRIPTS.parents[2] / ".claude-plugin/plugin.json"] + sorted(SCRIPTS.glob("*.py"))
        for p in names:
            t = p.read_text(encoding="utf-8")
            for ok in ("부르는 쪽", "어느 쪽"):
                t = t.replace(ok, "")
            self.assertNotRegex(t, "[칸쪽]", p.name)

    def test_project_rules_and_night_command(self):
        skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        rules = RULES.read_text(encoding="utf-8")
        self.assertIn("**프로젝트 하나 = 폴더 하나**", rules)
        self.assertIn("대표 노트만 올린다", rules)
        self.assertIn("지식베이스 전체에서 겹치면 안 된다", rules)
        self.assertIn("**한 명(한 곳) = 노트 하나**", rules)
        self.assertIn("대표 노트", skill)
        self.assertIn("「대기 자료 일괄 정리」", skill.split("---")[1])
        self.assertIn("대략 60줄", rules)
        self.assertIn("split_hold", rules + skill)
        self.assertIn("대기가 없어도 한다", skill)
        self.assertIn("(내용은 읽지 않는다)", skill)
        self.assertIn("한 실행에 3개까지", skill)


class Inbox(Base):
    def inbox(self, *a, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPTS / "inbox.py"), *map(str, a)], env=self.env(), input=stdin,
                              capture_output=True, text=True, encoding="utf-8")

    def waiting(self):
        return [ln for ln in (self.kb / "wiki/inbox.md").read_text(encoding="utf-8").splitlines() if ln.startswith("- raw/")]

    def receive(self, name, topic="주제"):
        src = self.root / "받은곳" / name
        src.parent.mkdir(exist_ok=True)
        src.write_bytes(b"data")
        r = self.inbox("add", "--file", src, "--topic", topic, "--facts", "핵심", "--source", "시험")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_receive_commits_only_raw_and_inbox(self):
        self.init()
        self.write("wiki/topics/손대는-중.md")
        r = self.receive("회의 메모.pdf", "회의 | 정산")
        self.assertIn("받음 raw/회의-메모.pdf", r.stdout)
        self.assertTrue((self.kb / "raw/회의-메모.pdf").is_file())
        shown = self.git("-c", "core.quotePath=false", "show", "--name-only", "--format=", "HEAD").split()
        self.assertEqual(sorted(shown), ["raw/회의-메모.pdf", "wiki/inbox.md"])
        self.assertEqual(self.waiting()[0].split(" | ")[3], "회의 / 정산")

    def test_stdin_text_keeps_source_line_and_images_go_to_assets(self):
        self.init()
        r = self.inbox("add", "--stdin", "--title", "문자 안내", "--topic", "치과", "--facts", "11월 5일", "--source", "문자", stdin="본문")
        self.assertEqual(r.returncode, 0, r.stderr)
        p = next((self.kb / "raw").glob("*문자-안내.md"))
        self.assertTrue(p.read_text(encoding="utf-8").startswith("> 출처: 문자"))
        self.receive("영수증.PNG")
        self.assertTrue((self.kb / "raw/assets/영수증.png").is_file())

    def test_existing_raw_and_bad_input(self):
        self.init()
        self.write("raw/있던것.md")
        self.assertEqual(self.inbox("add", "--raw", "raw/있던것.md", "--topic", "t", "--facts", "f").returncode, 0)
        self.assertEqual(self.inbox("add", "--raw", "raw/있던것.md", "--topic", "t", "--facts", "f").returncode, 2)
        self.assertEqual(self.inbox("add", "--raw", "wiki/log.md", "--topic", "t", "--facts", "f").returncode, 2)
        self.assertEqual(self.inbox("add", "--file", self.root / "없음", "--topic", "t", "--facts", "f").returncode, 2)
        self.assertEqual(len(self.waiting()), 1)

    def test_parallel_receive_same_name_keeps_everything(self):
        self.init()
        src = self.root / "같은이름.md"
        src.write_text("x", encoding="utf-8")
        with concurrent.futures.ThreadPoolExecutor(12) as ex:
            res = list(ex.map(lambda i: self.inbox("add", "--file", src, "--topic", f"주제{i}", "--facts", "f"), range(12)))
        self.assertEqual([r.returncode for r in res], [0] * 12, [r.stderr for r in res])
        self.assertEqual(len(self.waiting()), 12)
        self.assertEqual(len(list((self.kb / "raw").glob("같은이름*.md"))), 12)
        self.assertEqual({ln.split(" | ")[0] for ln in self.waiting()}.__len__(), 12)
        self.assertEqual(self.git("status", "--short"), "")

    def test_receive_while_commit_and_tidy_done(self):
        self.init()
        for i in range(6):
            self.receive(f"자료{i}.md")
        self.inbox("begin")
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            a = [ex.submit(self.receive, f"새것{i}.md") for i in range(4)]
            b = [ex.submit(self.inbox, "done", "-m", "ingest: 시험", f"raw/자료{i}.md") for i in range(4)]
            [f.result() for f in a]
            self.assertEqual([f.result().returncode for f in b], [0] * 4)
        self.assertEqual(len(self.waiting()), 6)
        self.assertEqual(self.git("status", "--short"), "")

    def test_no_history_repo(self):
        self.write("wiki/index.md", "")
        r = self.receive("자료.md")
        self.assertIn("기록 저장소 없음", r.stdout)
        self.assertEqual(len(self.waiting()), 1)

    def test_tidy_loop_removes_with_wiki_files_in_one_commit(self):
        self.init()
        self.receive("가.md")
        self.receive("나.md")
        self.assertEqual(self.inbox("begin").returncode, 0)
        self.assertTrue(self.inbox("next").stdout.startswith("raw/가.md"))
        self.write("wiki/topics/가-노트.md")
        r = self.inbox("done", "-m", "ingest: 가", "raw/가.md", "wiki/topics/가-노트.md")
        self.assertIn("대기 1개", r.stdout)
        shown = self.git("-c", "core.quotePath=false", "show", "--name-only", "--format=", "HEAD").split()
        self.assertEqual(sorted(shown), ["wiki/inbox.md", "wiki/topics/가-노트.md"])
        self.assertTrue(self.inbox("next").stdout.startswith("raw/나.md"))
        self.assertEqual(self.inbox("done", "-m", "x", "raw/없음.md").returncode, 2)
        self.inbox("end")
        self.assertFalse((self.kb / ".git/kb-tidy.lock").exists())

    def test_only_one_tidy_and_stopped_tidy_resumes(self):
        self.init()
        for n in ("가.md", "나.md", "다.md"):
            self.receive(n)
        self.inbox("begin")
        self.inbox("done", "-m", "ingest: 가", "raw/가.md")
        # 여기서 멈췄다 — end 없음
        self.assertEqual(self.inbox("begin").returncode, 3)
        lease = self.kb / ".git/kb-tidy.lock"
        os.utime(lease, (1, 1))
        self.assertEqual(self.inbox("begin").returncode, 0)
        self.assertTrue(self.inbox("next").stdout.startswith("raw/나.md"))
        self.assertEqual(len(self.waiting()), 2)

    def test_hold_is_skipped_stays_and_is_retried(self):
        self.init()
        self.receive("깨진.pdf")
        self.receive("멀쩡.md")
        self.inbox("begin")
        self.assertEqual(self.inbox("hold", "raw/깨진.pdf", "열리지 않음").returncode, 0)
        self.assertTrue(self.inbox("next").stdout.startswith("raw/멀쩡.md"))
        self.inbox("done", "-m", "ingest: x", "raw/멀쩡.md")
        self.assertEqual(self.inbox("next").stdout.strip(), "대기 없음")
        self.assertIn("보류 1개", self.inbox("end").stdout)
        self.assertIn("대기 보류", self.lint())
        self.inbox("begin")
        self.assertTrue(self.inbox("next").stdout.startswith("raw/깨진.pdf"))
        self.assertNotIn("보류", self.waiting()[0])


class LintInbox(Base):
    def test_mismatch_between_inbox_and_raw(self):
        self.init()
        src = self.root / "자료.md"
        src.write_text("x", encoding="utf-8")
        subprocess.run([sys.executable, str(SCRIPTS / "inbox.py"), "add", "--file", str(src), "--topic", "t", "--facts", "f"], env=self.env())
        self.assertIn("찾은 것 0개", self.lint())
        (self.kb / "raw/자료.md").unlink()
        self.write("raw/떠돌이.md")
        with (self.kb / "wiki/inbox.md").open("a", encoding="utf-8") as f:
            f.write("- 망가진 줄\n")
        out = self.lint()
        self.assertIn("대기에 있는데 raw 없음: raw/자료.md", out)
        self.assertIn("대기에도 노트에도 없는 raw: raw/떠돌이.md", out)
        self.assertIn("대기 줄 모양이 틀림", out)

    def test_fix_keeps_spoken_word_as_shown_name(self):
        self.init()
        self.write("wiki/topics/교회-집사님.md", "본문\n")
        self.write("wiki/topics/topic.md")
        self.write("wiki/me/topic-2.md")
        self.write("wiki/diary/2026-11-01.md")
        self.write("wiki/topics/다른-노트.md", "\n".join([
            "[[교회 집사님]]", "[[교회집사님]]", "[[교회-집사님]]", "[[교회 집사님|집사님]]", "[[교회-집사님#약속]]",
            "[[Topic]]", "[[없는 노트]]", "[[2026-11-01]]", "`[[교회-집사님]]`", "```", "[[교회-집사님]]", "```", ""]))
        r = self.run_py("lint.py", "--fix")
        self.assertIn("고침: wiki/topics/다른-노트.md", r.stdout)
        self.assertEqual((self.kb / "wiki/topics/다른-노트.md").read_text(encoding="utf-8").splitlines(), [
            "[[교회-집사님|교회 집사님]]", "[[교회-집사님|교회집사님]]", "[[교회-집사님|교회 집사님]]", "[[교회-집사님|집사님]]",
            "[[교회-집사님#약속|교회 집사님]]", "[[topic]]", "[[없는 노트]]", "[[2026-11-01]]",
            "`[[교회-집사님]]`", "```", "[[교회-집사님]]", "```"])
        self.assertIn("끊긴 링크", r.stdout)
        self.assertNotIn("보일 이름 없는 링크", r.stdout)

    def test_lint_flags_shown_hyphen_but_fix_is_stable(self):
        self.init()
        self.write("wiki/topics/가-나.md", "x\n")
        self.write("wiki/topics/다.md", "---\ntitle: [[가-나]]\n---\n[[가-나]]\n")
        self.assertIn("보일 이름 없는 링크: wiki/topics/다.md → [[가-나]]", self.lint())
        self.run_py("lint.py", "--fix")
        t = (self.kb / "wiki/topics/다.md").read_text(encoding="utf-8")
        self.assertEqual(t, "---\ntitle: [[가-나]]\n---\n[[가-나|가 나]]\n")
        self.assertNotIn("고침", self.run_py("lint.py", "--fix").stdout)

    def test_plain_lint_changes_nothing(self):
        self.init()
        self.write("wiki/topics/가-나.md", "x\n")
        self.write("wiki/topics/다.md", "[[가 나]]\n")
        self.lint()
        self.assertIn("[[가 나]]", (self.kb / "wiki/topics/다.md").read_text(encoding="utf-8"))


class Rules(Base):
    def test_my_rules_win_then_default(self):
        self.assertEqual(self.run_py("settings.py", "rules").stdout.strip(), str(RULES))
        self.write("rules.md")
        self.assertEqual(self.run_py("settings.py", "rules").stdout.strip(), str(self.kb / "rules.md"))

    def test_show_never_prints_other_values(self):
        self.config({"kb": str(self.kb), "ntfy_topic": "secret-topic", "ntfy_token": "secret-token"})
        r = self.run_py("settings.py", "show")
        self.assertIn("kb:", r.stdout)
        self.assertNotIn("secret", r.stdout + r.stderr)


class Lint(Base):
    def test_new_folder_needs_only_index_head(self):
        self.init()
        self.write("wiki/recipes/김치찌개.md")
        self.assertIn("index 에 폴더 머리 없음: wiki/recipes", self.lint())
        with (self.kb / "wiki/index.md").open("a", encoding="utf-8") as f:
            f.write("\n## recipes (요리)\n김치찌개 — 저녁\n")
        out = self.lint()
        self.assertNotIn("폴더 머리", out)
        self.assertNotIn("규칙에 없는", out)

    def test_dated_pages_skip_links_and_index_in_any_folder(self):
        self.init()
        self.write("wiki/diary/2026-11-01.md")
        out = self.lint()
        self.assertNotIn("2026-11-01", out)

    def test_folder_without_notes_any_cell(self):
        self.init()
        (self.kb / "wiki/projects/빈-폴더").mkdir()
        (self.kb / "wiki/brands/morningkong/assets").mkdir(parents=True)
        self.write("wiki/brands/morningkong/모닝콩.md")
        out = self.lint()
        self.assertIn("노트 없는 폴더: wiki/projects/빈-폴더", out)
        self.assertNotIn("assets", out)

    def test_project_folder_needs_only_main_note_in_index(self):
        self.init()
        self.write("wiki/projects/winter-menu/겨울-메뉴.md", "[[겨울-메뉴-회의록|회의록]]\n")
        self.write("wiki/projects/winter-menu/겨울-메뉴-회의록.md", "[[겨울-메뉴|겨울 메뉴]]\n")
        self.assertIn("index 에 대표 노트 없음: wiki/projects/winter-menu", self.lint())
        with (self.kb / "wiki/index.md").open("a", encoding="utf-8") as f:
            f.write("\n겨울-메뉴 — 대표 노트\n")
        self.assertIn("찾은 것 0개", self.lint())

    def main_note(self, rel, name, n, extra=""):
        self.write(rel, f"---\ntitle: x\n{extra}---\n" + "줄\n" * (n - 3 - bool(extra)))
        with (self.kb / "wiki/index.md").open("a", encoding="utf-8") as f:
            f.write(f"\n{name} — 요약\n")

    def test_long_main_note_warns_only_and_applies_to_brands(self):
        self.init()
        self.main_note("wiki/projects/a/겨울-메뉴.md", "겨울-메뉴", 61)
        self.main_note("wiki/projects/b/딱-맞음.md", "딱-맞음", 60)
        self.main_note("wiki/brands/c/모닝콩.md", "모닝콩", 61)
        before = (self.kb / "wiki/projects/a/겨울-메뉴.md").read_text(encoding="utf-8")
        out = self.run_py("lint.py", "--fix").stdout
        self.assertIn("긴 대표 노트: wiki/projects/a/겨울-메뉴.md (61줄)", out)
        self.assertIn("긴 대표 노트: wiki/brands/c/모닝콩.md (61줄)", out)
        self.assertNotIn("딱-맞음.md (", out)
        self.assertEqual((self.kb / "wiki/projects/a/겨울-메뉴.md").read_text(encoding="utf-8"), before)

    def test_sub_and_flat_notes_are_not_main(self):
        self.init()
        self.main_note("wiki/projects/a/겨울-메뉴.md", "겨울-메뉴", 10)
        self.write("wiki/projects/a/메뉴.md", "줄\n" * 100)      # 이름이 대표 노트 이름 안에 들어 있어도 대표가 아니다
        self.main_note("wiki/customers/김-고객.md", "김-고객", 100)
        self.assertNotIn("긴 대표 노트", self.lint())

    def test_split_hold_stops_retry_until_note_grows(self):
        self.init()
        self.main_note("wiki/projects/a/겨울-메뉴.md", "겨울-메뉴", 80, "split_hold: 80 표 하나로 이어짐\n")
        out = self.lint()
        self.assertIn("나누기 보류: wiki/projects/a/겨울-메뉴.md (80줄) — 표 하나로 이어짐", out)
        self.assertNotIn("긴 대표 노트", out)
        p = self.kb / "wiki/projects/a/겨울-메뉴.md"
        p.write_text(p.read_text(encoding="utf-8") + "줄\n" * 30, encoding="utf-8")
        self.assertIn("긴 대표 노트", self.lint())

    def test_moved_finds_lost_lines(self):
        self.init()
        self.write("wiki/projects/a/겨울-메뉴.md", "---\ntitle: x\nupdated: 1\n---\n# 겨울\n## 회의\n첫 줄\n둘째 줄\n")
        self.git("add", "-A")
        self.git("-c", "user.name=a", "-c", "user.email=a@a", "commit", "-qm", "x")
        self.write("wiki/projects/a/겨울-메뉴.md", "---\ntitle: x\nupdated: 2\n---\n# 겨울\n[[겨울-메뉴-회의|회의]] — 요약\n")
        self.write("wiki/projects/a/겨울-메뉴-회의.md", "## 회의\n첫 줄\n")
        r = self.run_py("lint.py", "--moved", "wiki/projects/a/겨울-메뉴.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("빠진 줄: 둘째 줄", r.stdout)
        self.write("wiki/projects/a/겨울-메뉴-회의.md", "## 회의\n첫 줄\n둘째 줄\n")
        self.assertEqual(self.run_py("lint.py", "--moved", "wiki/projects/a/겨울-메뉴.md").returncode, 0)
        self.assertEqual(self.run_py("lint.py", "--moved", self.kb / "wiki/projects/a/겨울-메뉴.md").returncode, 0)
        self.assertEqual(self.run_py("lint.py", "--moved", "wiki/없는-노트.md").returncode, 2)
        self.assertEqual(self.run_py("lint.py", "--moved", self.root / "밖.md").returncode, 2)
        self.write("wiki/projects/a/겨울-메뉴-회의.md", "## 회의\n첫 줄\n")
        self.write("wiki/topics/다른-폴더.md", "둘째 줄\n")      # 다른 폴더에 같은 줄이 있어도 빠진 것이다
        self.assertEqual(self.run_py("lint.py", "--moved", "wiki/projects/a/겨울-메뉴.md").returncode, 1)

    def test_customer_note_still_needs_index(self):
        self.init()
        self.write("wiki/customers/김-고객.md", "x\n")
        self.assertIn("index 에 없음: wiki/customers/김-고객.md", self.lint())

    def test_same_note_name_in_two_folders(self):
        self.init()
        self.write("wiki/projects/가/회의록.md")
        self.write("wiki/projects/나/회의록.md")
        self.write("wiki/topics/겨울-메뉴.md")
        self.write("wiki/me/겨울 메뉴.md")
        self.write("wiki/diary/2026-11-01.md")
        self.write("wiki/work/2026-11-01.md")
        out = self.lint()
        self.assertIn("노트 이름 겹침: wiki/projects/가/회의록.md · wiki/projects/나/회의록.md", out)
        self.assertIn("노트 이름 겹침: wiki/me/겨울 메뉴.md · wiki/topics/겨울-메뉴.md", out)
        self.assertNotIn("겹침: wiki/diary", out)

    def test_hidden_folders_ignored(self):
        self.init()
        self.write("wiki/.obsidian/이름 있는 파일.md")
        self.assertIn("찾은 것 0개", self.lint())


class Commit(Base):
    def commit(self, *a):
        return self.run_py("commit.py", *a)

    def test_only_named_files_and_others_stay_staged(self):
        self.init()
        self.write("wiki/topics/내-것.md")
        self.write("wiki/topics/남의-것.md")
        self.git("add", "--", "wiki/topics/남의-것.md")
        self.write("raw/대기.md")
        r = self.commit("-m", "ingest: 시험", "wiki/topics/내-것.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("커밋 "))
        shown = self.git("-c", "core.quotePath=false", "show", "--name-only", "--format=", "HEAD")
        self.assertIn("내-것", shown)
        self.assertNotIn("남의-것", shown)
        status = self.git("-c", "core.quotePath=false", "status", "--short")
        self.assertIn("A  wiki/topics/남의-것.md", status)
        self.assertIn("raw/", status)

    def test_refuses_folders_outside_and_git_dir(self):
        self.init()
        for bad in ("wiki", ".", "../밖.md", self.root / "밖.md", ".git/config"):
            r = self.commit("-m", "x", bad)
            self.assertEqual(r.returncode, 2, bad)

    def test_nothing_changed(self):
        self.init()
        r = self.commit("-m", "x", "wiki/log.md")
        self.assertEqual(r.stdout.strip(), "바뀐 것 없음")

    def test_no_history_repo_is_success(self):
        self.write("wiki/log.md")
        r = self.commit("-m", "x", "wiki/log.md")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "기록 저장소 없음"))

    def test_deletion_and_odd_names(self):
        self.init()
        self.write("raw/이름[1]*.md")
        self.assertEqual(self.commit("-m", "더함", "raw/이름[1]*.md").returncode, 0)
        (self.kb / "raw/이름[1]*.md").unlink()
        r = self.commit("-m", "지움", "raw/이름[1]*.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.git("ls-files", "raw"), "")

    def test_moved_file_commits_both_paths(self):
        self.init()
        self.write("wiki/projects/겨울-메뉴.md")
        self.commit("-m", "더함", "wiki/projects/겨울-메뉴.md")
        (self.kb / "wiki/projects/winter-menu").mkdir()
        self.git("mv", "--", "wiki/projects/겨울-메뉴.md", "wiki/projects/winter-menu/겨울-메뉴.md")
        r = self.commit("-m", "옮김", "wiki/projects/겨울-메뉴.md", "wiki/projects/winter-menu/겨울-메뉴.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.git("status", "--short"), "")
        self.assertEqual(self.commit("-m", "x", "없는/파일.md").returncode, 1)

    def test_stale_lock_is_taken_over(self):
        self.init()
        lock = self.kb / ".git/kb-commit.lock"
        lock.touch()
        os.utime(lock, (1, 1))
        self.write("wiki/topics/가.md")
        self.assertEqual(self.commit("-m", "x", "wiki/topics/가.md").returncode, 0)
        self.assertFalse(lock.exists())

    def test_parallel_sessions_do_not_mix(self):
        self.init()
        names = [f"wiki/topics/노트-{i}.md" for i in range(12)]
        for n in names:
            self.write(n)
        with concurrent.futures.ThreadPoolExecutor(12) as ex:
            res = list(ex.map(lambda n: self.commit("-m", "ingest: " + n, n), names))
        self.assertEqual([r.returncode for r in res], [0] * 12, [r.stderr for r in res])
        self.assertEqual(self.git("status", "--short"), "")
        log = self.git("-c", "core.quotePath=false", "log", "--format=@%s", "--name-only").split("@")
        one = [c for c in log if c.startswith("ingest: ")]
        self.assertEqual(len(one), 12)
        for c in one:
            head, *files = [x for x in c.splitlines() if x]
            self.assertEqual(files, [head.split(": ")[1]])


if __name__ == "__main__":
    unittest.main()
