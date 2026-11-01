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
        self.assertIn("찾은 것 0개", self.lint())

    def test_keeps_my_rules_and_uses_their_cells(self):
        self.write("rules.md", "| 칸 | 넣는 것 | 파일 |\n|---|---|---|\n| `recipes/` | 요리 — 메뉴 | 하나 |\n")
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
        self.assertIn("index 에 칸 머리 없음: wiki/recipes", self.lint())
        with (self.kb / "wiki/index.md").open("a", encoding="utf-8") as f:
            f.write("\n## recipes (요리)\n김치찌개 — 저녁\n")
        out = self.lint()
        self.assertNotIn("칸 머리", out)
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
        names = [f"wiki/topics/쪽-{i}.md" for i in range(12)]
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
