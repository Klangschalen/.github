from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "gitleaks-scan.yml"


class GitleaksWorkflowScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_exact_trigger_commit_is_checked_out_without_credentials(self):
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            self.text,
        )
        self.assertIn("fetch-depth: 0", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_pull_request_scans_only_base_to_head_range(self):
        self.assertIn('LOG_OPTS="${PR_BASE_SHA}..${PR_HEAD_SHA}"', self.text)
        self.assertIn('SCOPE_KIND="pull_request_change"', self.text)
        self.assertIn('git cat-file -e "${PR_BASE_SHA}^{commit}"', self.text)
        self.assertIn('git cat-file -e "${PR_HEAD_SHA}^{commit}"', self.text)

    def test_push_scans_only_the_new_change(self):
        self.assertIn('LOG_OPTS="${PUSH_BEFORE_SHA}..${CURRENT_SHA}"', self.text)
        self.assertIn('SCOPE_KIND="push_change"', self.text)

    def test_scheduled_scan_stays_on_current_branch_history(self):
        self.assertIn('LOG_OPTS="HEAD"', self.text)
        self.assertIn('SCOPE_KIND="current_branch_history"', self.text)

    def test_current_git_command_receives_explicit_log_options(self):
        self.assertIn("ARGS=(git --redact -v --no-banner)", self.text)
        self.assertIn('ARGS+=(--log-opts="$LOG_OPTS")', self.text)
        self.assertIn('gitleaks "${ARGS[@]}" .', self.text)
        self.assertNotIn("ARGS=(detect --source .", self.text)

    def test_no_executable_all_refs_scope_can_reintroduce_foreign_branches(self):
        executable_all = re.findall(
            r"^\s*(?!#).*?(?:LOG_OPTS|ARGS|gitleaks).*--all.*$",
            self.text,
            flags=re.MULTILINE,
        )
        self.assertEqual([], executable_all)

    def test_scan_scope_is_visible_in_the_job_summary(self):
        self.assertIn("- Scan-Art:", self.text)
        self.assertIn("- Git-Bereich:", self.text)


if __name__ == "__main__":
    unittest.main()
