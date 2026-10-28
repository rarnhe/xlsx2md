"""Generate a Markdown test report and GitHub Actions step summary."""
import os
from pathlib import Path

import pytest


def pytest_configure(config):
    config._xlsx2md_results = []


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when in ("setup", "teardown") and report.failed):
        pytest_configure_results = getattr(report, "nodeid", "unknown")
        # Each call is recorded once; setup/teardown errors are also captured.
        _RESULTS.append((pytest_configure_results, report.outcome, str(report.longrepr) if report.failed else ""))


_RESULTS = []


def pytest_sessionfinish(session, exitstatus):
    passed = exitstatus == 0
    status_text = "✅ 通过 (Passed)" if passed else "❌ 失败 (Failed - 需 Codex 介入修复)"
    count_passed = sum(outcome == "passed" for _, outcome, _ in _RESULTS)
    count_failed = sum(outcome == "failed" for _, outcome, _ in _RESULTS)
    count_skipped = sum(outcome == "skipped" for _, outcome, _ in _RESULTS)
    details = "\n".join(
        f"- **{nodeid}**: {outcome}" for nodeid, outcome, _ in _RESULTS
    ) or "- 没有执行任何测试"
    failures = "\n\n".join(
        f"#### {nodeid}\n\n```text\n{error}\n```"
        for nodeid, outcome, error in _RESULTS if outcome == "failed"
    ) or "无"
    report_content = f"""# 🧪 Python 自动化测试报告

- **执行时间**: 自动化流水线触发
- **整体状态**: {status_text}
- **测试框架**: Pytest (GitHub Actions)
- **退出状态码**: {int(exitstatus)}
- **测试统计**: 通过 {count_passed} / 失败 {count_failed} / 跳过 {count_skipped}

---

### 测试用例

{details}

### 失败详情

{failures}

### 🤖 给 Codex 的反馈指引

如果状态为失败，请结合上方控制台报错日志与本文件，分析代码逻辑并直接在下一次对话中输出修复后的代码。
"""
    Path("test_report.md").write_text(report_content, encoding="utf-8")
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as file:
            file.write(report_content)
