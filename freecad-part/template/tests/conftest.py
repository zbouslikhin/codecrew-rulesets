# FreeCAD must be imported before Part: `import Part` on its own crashes FreeCAD 1.1.
# pytest loads this file before any test, so test files can import in any order.
import FreeCAD  # noqa: F401
