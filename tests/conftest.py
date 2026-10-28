"""Write test_report.md and GitHub Actions Step Summary after each pytest run."""
import os
from pathlib import Path

import pytest

_RESULTS = []


def pytest_configure(config):
    _RESULTS.clear()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    # Capture call results, plus failures in setup/teardown.
    if report.when == "call" or (
        report.when in ("setup", "teardown") and report.failed
    ):
        _RESULTS.append(
            (report.nodeid, report.outcome, str(report.longrepr) if report.failed else "")
        )


def pytest_sessionfinish(session, exitstatus):
    passed = exitstatus == 0
    status = "✅ 通过 (Passed)" if passed else "❌ 失败 (Failed - 需 Codex 介入修复)"
    counts = {key: sum(outcome == key for _, outcome, _ in _RESULTS)
              for key in ("passed", "failed", "skipped")}
    details = "\n".join(
        f"- **{name}**: {outcome}" for name, outcome, _ in _RESULTS
    ) or "- 没有执行测试（可能发生了收集或导入错误，请查看 Actions 日志）"
    errors = "\n\n".join(
        f"#### {name}\n\n```text\n{message}\n```"
        for name, outcome, message in _RESULTS if outcome == "failed"
    ) or "无测试用例失败；如整体状态为失败，请查看收集错误或控制台日志。"
    content = f"""# 🧪 Python 自动化测试报告

- **执行时间**: 自动化流水线触发
- **整体状态**: {status}
- **测试框架**: Pytest (GitHub Actions)
- **退出状态码**: {int(exitstatus)}
- **测试统计**: 通过 {counts['passed']} / 失败 {counts['failed']} / 跳过 {counts['skipped']}

---

### 测试用例

{details}

### 失败详情

{errors}

### 🤖 给 Codex 的反馈指引

如果状态为失败，请结合 Actions 控制台日志与本文件定位并修复代码。
"""
    Path("test_report.md").write_text(content, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(content)
