# FreeCAD must be imported before Part: `import Part` on its own crashes FreeCAD 1.1.
# pytest loads this file before any test, so test files can import in any order.
import FreeCAD  # noqa: F401


def pytest_sessionfinish(session, exitstatus):
    # a new project has no parts, so no tests yet: that isn't a failure
    if exitstatus == 5:
        session.exitstatus = 0
