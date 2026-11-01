import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from notes import NoteStore


class NoteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "notes"
        self.store = NoteStore(self.root)

    def test_create_and_replace_utf8(self):
        result = self.store.save_note("ideas/日本語.md", "# メモ\n")
        self.assertEqual(result, {"path": "ideas/日本語.md", "bytes": 9})
        self.store.save_note("ideas/日本語.md", "更新")
        self.assertEqual((self.root / "ideas/日本語.md").read_text(), "更新")

    def test_reject_bad_paths(self):
        for name in [
            "",
            "/tmp/a.md",
            "../a.md",
            "x/../a.md",
            "./a.md",
            "a//b.md",
            "a.txt",
            "a.md/",
            "a\\b.md",
            ".git/a.md",
            "a\0.md",
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.store.save_note(name, "bad")

    def test_links_and_directory_rejected(self):
        self.root.mkdir()
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("original")
        (self.root / "file.md").symlink_to(outside)
        (self.root / "folder").symlink_to(outside.parent, target_is_directory=True)
        os.link(outside, self.root / "hard.md")
        (self.root / "directory.md").mkdir()
        for name in ["file.md", "folder/outside.md", "hard.md", "directory.md"]:
            with self.subTest(name=name), self.assertRaises((ValueError, OSError)):
                self.store.save_note(name, "bad")
        self.assertEqual(outside.read_text(), "original")

    def test_failure_preserves_previous_note(self):
        self.store.save_note("a.md", "original")
        with patch("notes.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.store.save_note("a.md", "replacement")
        self.assertEqual((self.root / "a.md").read_text(), "original")
        self.assertEqual([p.name for p in self.root.iterdir()], ["a.md"])

    def test_root_symlink_rejected(self):
        self.root.symlink_to(self.temp.name, target_is_directory=True)
        with self.assertRaises(OSError):
            self.store.save_note("a.md", "bad")
