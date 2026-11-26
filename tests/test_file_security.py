import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

from security.path_security import (
    resolve_and_verify_path,
    get_safe_roots,
    MAX_TEXT_READ_BYTES,
    MAX_TEXT_WRITE_BYTES,
)

from security.permissions import (
    requires_confirmation,
    get_tool_permission,
    PermissionLevel,
)

from tools.file_manager import (
    list_directory,
    read_text_file,
    write_text_file,
    delete_file_safely,
)

from tools.pdf_summarizer import extract_pdf_text


class TestAstraSecurity(unittest.TestCase):

    def setUp(self):
        roots = get_safe_roots()

        if not roots:
            self.fail("No approved directories found.")

        root = sorted(roots, key=str)[0]

        self.temp = tempfile.TemporaryDirectory(
            prefix="astra_test_",
            dir=str(root)
        )

        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name).resolve()
        self.sample = self.root / "sample.txt"

        self.sample.write_text(
            "ASTRA security test",
            encoding="utf-8"
        )

    def test_allowed_path(self):
        self.assertEqual(
            resolve_and_verify_path(str(self.sample)),
            self.sample
        )

    def test_env_blocked(self):
        with self.assertRaises(PermissionError):
            resolve_and_verify_path(str(self.root / ".env"))

    def test_windows_blocked(self):
        with self.assertRaises(PermissionError):
            resolve_and_verify_path(r"C:\Windows\System32")

    def test_traversal_blocked(self):
        with self.assertRaises(PermissionError):
            resolve_and_verify_path(str(self.root / ".."))

    def test_network_blocked(self):
        with self.assertRaises(PermissionError):
            resolve_and_verify_path(r"\\server\share\test.txt")

    def test_unknown_tool_restricted(self):
        self.assertEqual(
            get_tool_permission("unknown_tool"),
            PermissionLevel.RESTRICTED
        )

    def test_delete_permission(self):
        self.assertTrue(
            requires_confirmation("delete_file_safely")
        )

    def test_read_file(self):
        result = read_text_file(str(self.sample))
        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["content"],
            "ASTRA security test"
        )

    def test_directory_listing(self):
        result = list_directory(str(self.root))
        self.assertTrue(result["success"])

    def test_large_file_blocked(self):
        target = self.root / "large.txt"
        target.write_bytes(b"A" * (MAX_TEXT_READ_BYTES + 1))
        self.assertFalse(read_text_file(str(target))["success"])

    @patch("tools.file_manager.request_user_confirmation",
           return_value=False)
    def test_write_denied(self, confirmation):
        target = self.root / "denied.txt"
        result = write_text_file(str(target), "Test")
        self.assertFalse(result["success"])
        self.assertFalse(target.exists())

    @patch("tools.file_manager.request_user_confirmation",
           return_value=True)
    def test_write_approved(self, confirmation):
        target = self.root / "approved.txt"
        result = write_text_file(str(target), "Test")
        self.assertTrue(result["success"])
        self.assertEqual(target.read_text(), "Test")

    def test_overwrite_blocked(self):
        result = write_text_file(str(self.sample), "Changed")
        self.assertFalse(result["success"])
        self.assertEqual(
            self.sample.read_text(),
            "ASTRA security test"
        )

    def test_oversized_write(self):
        target = self.root / "large_write.txt"
        result = write_text_file(
            str(target),
            "A" * (MAX_TEXT_WRITE_BYTES + 1)
        )
        self.assertFalse(result["success"])
        self.assertFalse(target.exists())

    @patch("tools.file_manager.send2trash")
    @patch("tools.file_manager.request_user_confirmation",
           return_value=False)
    def test_delete_denied(self, confirmation, recycle):
        result = delete_file_safely(str(self.sample))
        self.assertFalse(result["success"])
        self.assertTrue(self.sample.exists())
        recycle.assert_not_called()

    @patch("tools.file_manager.send2trash")
    @patch("tools.file_manager.request_user_confirmation",
           return_value=True)
    def test_delete_approved(self, confirmation, recycle):
        result = delete_file_safely(str(self.sample))
        self.assertTrue(result["success"])
        recycle.assert_called_once_with(str(self.sample))

    def test_invalid_pdf(self):
        target = self.root / "invalid.pdf"
        target.write_text("Not a PDF")
        self.assertFalse(extract_pdf_text(str(target))["success"])

    def test_protected_pdf(self):
        result = extract_pdf_text(r"C:\Windows\test.pdf")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
