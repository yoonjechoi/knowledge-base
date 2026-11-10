"""knowledge-base 시험 — 임시 HOME 에서만 돈다(실제 지식베이스 · 설정을 건드리지 않는다).

  python3 -m unittest tests.test_wiki
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1] / "plugins" / "knowledge-base"
WIKI = PLUGIN / "scripts" / "wiki.py"


class Base(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp()).resolve()
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_wiki(self, *a):
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                   GIT_CONFIG_GLOBAL=str(self.root / "nogit"), GIT_CONFIG_NOSYSTEM="1")
        return subprocess.run([sys.executable, str(WIKI), *map(str, a)], env=env, capture_output=True, text=True, encoding="utf-8")

    @property
    def kb(self):
        return self.home / "knowledge-base"


class Setup(Base):
    def test_setup_makes_three_layers(self):
        r = self.run_wiki("setup")
        self.assertEqual(r.returncode, 0, r.stderr)
        for d in ("raw", "raw/assets", "wiki/sources", "wiki/entities", "wiki/concepts", "wiki/analyses"):
            self.assertTrue((self.kb / d).is_dir(), d)
        for f in ("CLAUDE.md", "wiki/index.md", "wiki/log.md", "wiki/overview.md"):
            self.assertTrue((self.kb / f).is_file(), f)
        log = (self.kb / "wiki/log.md").read_text(encoding="utf-8")
        self.assertRegex(log, r"## \[\d{4}-\d{2}-\d{2}\] setup \| ")
        self.assertNotIn("{{오늘}}", log + (self.kb / "wiki/overview.md").read_text(encoding="utf-8"))
        if shutil.which("git"):
            self.assertTrue((self.kb / ".git").exists())

    def test_setup_keeps_existing_files(self):
        self.run_wiki("setup")
        (self.kb / "CLAUDE.md").write_text("내 schema", encoding="utf-8")
        r = self.run_wiki("setup")
        self.assertIn("없음(이미 있었어요)", r.stdout)
        self.assertEqual((self.kb / "CLAUDE.md").read_text(encoding="utf-8"), "내 schema")

    def test_setup_other_folder_sets_config(self):
        other = (self.root / "다른 곳").resolve()
        self.run_wiki("setup", other)
        self.assertTrue((other / "wiki/index.md").exists())
        self.assertIn(str(other), self.run_wiki("where").stdout)
        cfg = json.loads((self.home / ".config/knowledge-base/config.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["kb"], str(other))

    def test_where_before_setup(self):
        self.assertIn("setup 부터", self.run_wiki("where").stdout)


class Config(Base):
    def test_other_values_kept_and_not_printed(self):
        conf = self.home / ".config/knowledge-base/config.json"
        conf.parent.mkdir(parents=True)
        conf.write_text(json.dumps({"kb": "~/knowledge-base", "ntfy_topic": "비밀-주제"}), encoding="utf-8")
        out = self.run_wiki("setup", self.root / "새곳").stdout + self.run_wiki("where").stdout
        self.assertNotIn("비밀-주제", out)
        cfg = json.loads(conf.read_text(encoding="utf-8"))
        self.assertEqual(cfg["ntfy_topic"], "비밀-주제")
        if os.name != "nt":
            self.assertEqual(conf.stat().st_mode & 0o777, 0o600)


class OldFormat(Base):
    def make_old(self):
        (self.kb / "wiki").mkdir(parents=True)
        (self.kb / "rules.md").write_text("옛 규칙", encoding="utf-8")
        (self.kb / "wiki/inbox.md").write_text("# 대기 목록\n", encoding="utf-8")
        (self.kb / "wiki/index.md").write_text("# 목록\n", encoding="utf-8")

    def test_old_format_is_detected_and_not_overwritten(self):
        self.make_old()
        self.assertIn("옛 구조", self.run_wiki("where").stdout)
        r = self.run_wiki("setup")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.kb / "CLAUDE.md").exists())

    def test_move_old_then_setup(self):
        self.make_old()
        r = self.run_wiki("move-old")
        self.assertEqual(r.returncode, 0, r.stderr)
        olds = [p for p in self.home.iterdir() if p.name.startswith("knowledge-base-old-")]
        self.assertEqual(len(olds), 1)
        self.assertEqual((olds[0] / "rules.md").read_text(encoding="utf-8"), "옛 규칙")
        self.assertEqual(self.run_wiki("setup").returncode, 0)
        self.assertTrue((self.kb / "CLAUDE.md").exists())
        self.assertNotEqual(self.run_wiki("move-old").returncode, 0)   # 새 구조는 옮기지 않는다


class Pending(Base):
    def test_pending_lists_raw_not_in_any_source_page(self):
        self.run_wiki("setup")
        (self.kb / "raw/한글 글.md").write_text("본문", encoding="utf-8")
        (self.kb / "raw/b.md").write_text("본문", encoding="utf-8")
        (self.kb / "raw/assets/그림.png").write_bytes(b"x")
        (self.kb / "wiki/sources/b.md").write_text("---\nsources: [raw/b.md]\n---\n# b\n", encoding="utf-8")
        out = self.run_wiki("pending").stdout
        self.assertIn("raw/한글 글.md", out)
        self.assertNotIn("raw/b.md", out)
        self.assertNotIn("그림.png", out)
        (self.kb / "wiki/sources/a.md").write_text("---\nsources: [raw/한글 글.md]\n---\n", encoding="utf-8")
        self.assertIn("모두 ingest 됨", self.run_wiki("pending").stdout)


class Docs(unittest.TestCase):
    def test_skills_and_agent(self):
        for s in ("setup", "ingest", "query", "lint"):
            t = (PLUGIN / "skills" / s / "SKILL.md").read_text(encoding="utf-8")
            head = t.split("---")[1]
            self.assertIn(f"name: {s}", head)
            self.assertIn("description:", head)
            self.assertIn("CLAUDE.md", t)
            self.assertIn("../../scripts/wiki.py", t)
        agent = (PLUGIN / "agents" / "batch-ingester.md").read_text(encoding="utf-8")
        self.assertNotIn("\nmodel:", agent.split("---")[1])   # 쓰는 사람의 기본 설정 모델로 돈다
        ingest = (PLUGIN / "skills/ingest/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("knowledge-base:batch-ingester", ingest)
        self.assertIn("run_in_background: true", ingest)
        self.assertIn("## 테스트 시나리오", ingest)

    def test_kb_entrance_routes_to_operations(self):
        kb = (PLUGIN / "skills/kb/SKILL.md").read_text(encoding="utf-8")
        for s in ("knowledge-base:query", "knowledge-base:ingest", "knowledge-base:lint", "knowledge-base:setup"):
            self.assertIn(s, kb)
        self.assertIn("결론 저장", kb)
        self.assertNotIn("llm-wiki", "".join(p.read_text(encoding="utf-8") for p in PLUGIN.rglob("*.md")))

    def test_windows_forbidden_filename_chars_rule(self):
        for f in ("templates/schema.md", "skills/ingest/SKILL.md", "skills/query/SKILL.md"):
            self.assertIn('`\\ / : * ? " < > |`', (PLUGIN / f).read_text(encoding="utf-8"), f)

    def test_log_prefix_is_gist_form(self):
        for f in ("templates/log.md", "templates/schema.md", "skills/ingest/SKILL.md", "skills/query/SKILL.md", "skills/lint/SKILL.md"):
            self.assertRegex((PLUGIN / f).read_text(encoding="utf-8"), r"## \[(YYYY-MM-DD|오늘|\{\{오늘\}\})\] (ingest|query|lint|setup) \|", f)

    def test_no_wiki_word_to_people(self):
        for s in ("setup", "ingest", "query", "lint"):
            self.assertIn("「지식베이스」", (PLUGIN / "skills" / s / "SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
