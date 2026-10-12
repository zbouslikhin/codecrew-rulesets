import pytest


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    # a new project has no code yet, so no tests: that isn't a failure
    if exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = pytest.ExitCode.OK
