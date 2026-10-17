"""The freecad-design tools, run with FreeCAD's Python (bin/fc finds it).

    fc setup [--install]       what's installed; --install adds ruff, pytest and Pillow
    fc new                     a new design project here, or adopt the one that's here
    fc check [files] [--warnings]
                               the model check (parts build, fit the bed, nothing overlaps,
                               enough thread) and ruff; every part and assembly when no files
    fc render <target> [--views iso,front,side,top] [--focus <component>]
    fc export [folder]         exports/<part>.stl turned onto its print face, and .step
    fc analysis                runs analysis/*.py and lists the results
    fc status                  the design flow: what's done and what's next

Hooks (Claude Code runs these): hook-start, hook-edit, hook-stop.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

LIB = Path(__file__).resolve().parent
PLUGIN = LIB.parent
FC = (PLUGIN / "bin" / "fc").as_posix()
MODEL_DIRS = ("parts", "assemblies", "concepts", "test_pieces")
WATCHED = (*MODEL_DIRS, "standards", "scripts", "reference")
STAGES = [
    ("grilling", "Grilling", "grill"),
    ("concept", "Concept", "concept"),
    ("risk", "Design risk", "risks"),
    ("test_pieces", "Test pieces", "pieces"),
    ("plan", "Plan", "plan"),
    ("cad", "Detailed CAD", "cad"),
    ("analysis", "Analysis and DFM", "analyse"),
    ("prototype", "Prototype", "prototype"),
    ("inspection", "Inspection", "inspect"),
    ("testing", "Testing", "test"),
    ("release", "Release", "release"),
]


# --------------------------------------------------------------------------- FreeCAD's Python
def _freecad_paths() -> list[str]:
    """Where FreeCAD's own modules are, next to the python that runs this."""
    exe = Path(sys.executable).resolve().parent
    found = [str(p) for p in (exe, exe.parent / "lib", exe.parent / "Mod") if p.is_dir()]
    if hasattr(os, "add_dll_directory"):  # Windows: FreeCAD's DLLs sit next to python.exe
        with contextlib.suppress(OSError):
            os.add_dll_directory(str(exe))
    return found


def _env(root: Path) -> dict[str, str]:
    paths = [str(root), str(LIB), *_freecad_paths()]
    old = os.environ.get("PYTHONPATH")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(paths + ([old] if old else []))
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _import_freecad() -> None:
    for p in reversed(_freecad_paths()):
        if p not in sys.path:
            sys.path.insert(0, p)
    import FreeCAD  # noqa: F401  before Part


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def is_project(root: Path) -> bool:
    return (root / "parts").is_dir() or (root / "design" / "decisions.md").is_file()


# --------------------------------------------------------------------------- the checks
def _has(module: str) -> bool:
    try:
        r = subprocess.run([sys.executable, "-c", f"import {module}"], capture_output=True)
        return r.returncode == 0
    except OSError:
        return False


def _ruff(root: Path, files: list[str]) -> list[dict]:
    """Format and fix in place; what's left are lint errors."""
    if not files or not _has("ruff"):
        return []
    run = [sys.executable, "-m", "ruff"]
    subprocess.run([*run, "format", "--quiet", *files], cwd=root, capture_output=True)
    r = subprocess.run(
        [*run, "check", "--fix", "--quiet", "--output-format", "json", *files],
        cwd=root,
        capture_output=True,
        text=True,
    )
    out = []
    with contextlib.suppress(json.JSONDecodeError):
        for d in json.loads(r.stdout or "[]"):
            rel = Path(d["filename"]).resolve().relative_to(root).as_posix()
            out.append(
                {
                    "file": rel,
                    "line": (d.get("location") or {}).get("row"),
                    "code": f"lint/{d.get('code')}",
                    "message": d.get("message", ""),
                    "severity": "error",
                }
            )
    return out


def _model(root: Path, files: list[Path] | None) -> list[dict]:
    """The ruleset's model check (lib/check.py), for these part and assembly files or all."""
    os.chdir(root)
    _import_freecad()
    for p in (str(LIB), str(root)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import check  # lib/check.py

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bed = check.printer_bed(root)
        profile = check.dfm.load_profiles(root).get("fdm", {})
        if files is None:
            check.main()
        else:
            for path in files:
                rel = path.relative_to(root).as_posix()
                if rel.startswith("assemblies/"):
                    check.check_assembly(rel, path)
                else:
                    check.check_part(rel, path, bed, profile)
    out = []
    for line in buf.getvalue().splitlines():
        with contextlib.suppress(json.JSONDecodeError):
            out.append(json.loads(line))
    return out


def _tests(root: Path) -> list[dict]:
    if not list((root / "tests").glob("test_*.py")) or not _has("pytest"):
        return []
    r = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "-rfE", "-p", "no:cacheprovider"],
        cwd=root,
        capture_output=True,
        text=True,
        env=_env(root),
    )
    out = []
    for line in r.stdout.splitlines():
        if line.startswith(("FAILED ", "ERROR ")):
            kind, _, rest = line.partition(" ")
            out.append({"file": rest.split("::")[0], "code": "test", "message": rest, "severity": "error"})
    return out


def run_checks(root: Path, files: list[str] | None) -> list[dict]:
    if files is None:
        py = [
            p.relative_to(root).as_posix()
            for d in WATCHED
            for p in (root / d).rglob("*.py")
            if "__pycache__" not in p.parts
        ]
        return _ruff(root, py) + _model(root, None) + _tests(root)
    model = [root / f for f in files if f.endswith(".py") and f.split("/")[0] in MODEL_DIRS]
    return _ruff(root, [f for f in files if f.endswith(".py")]) + (_model(root, model) if model else [])


def report(diags: list[dict], warnings: bool = False) -> tuple[str, int]:
    errors = [d for d in diags if d.get("severity") == "error"]
    lines = []
    for d in errors:
        where = d.get("file", "") + (f":{d['line']}" if d.get("line") else "")
        lines.append(f"x {where} [{d.get('code')}] {d.get('message')}")
    warns = [d for d in diags if d.get("severity") == "warning"]
    if warnings:
        for d in warns:
            lines.append(f"! {d.get('file')} [{d.get('code')}] {d.get('message')}")
    elif warns:
        codes: dict[str, int] = {}
        for d in warns:
            code = str(d.get("code", "")).split("/")[-1]
            codes[code] = codes.get(code, 0) + 1
        files = len({d.get("file") for d in warns})
        lines.append(
            f"{len(warns)} warnings in {files} file(s): "
            + ", ".join(f"{n} {c}" for c, n in codes.items())
            + " (for the person, don't chase them; --warnings lists them)"
        )
    infos = [d for d in diags if d.get("severity") == "info" and str(d.get("code", "")).endswith("summary")]
    if warnings:
        lines += [f"  {d.get('file')}: {d.get('message')}" for d in infos]
    lines.append(f"{'FAIL' if errors else 'PASS'}: {len(errors)} error(s)")
    return "\n".join(lines), len(errors)


# --------------------------------------------------------------------------- state
def _state_file(root: Path) -> Path:
    key = hashlib.sha1(str(root).lower().encode()).hexdigest()[:16]
    d = Path.home() / ".cache" / "freecad-design"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def fingerprint(root: Path) -> str:
    h = hashlib.sha1()
    for d in WATCHED:
        for p in sorted((root / d).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                st = p.stat()
                h.update(f"{p.relative_to(root).as_posix()}:{st.st_size}:{st.st_mtime_ns}".encode())
    printer = root / "design" / "printer.toml"
    if printer.is_file():
        h.update(printer.read_bytes())
    return h.hexdigest()


def _passed(root: Path, fp: str | None = None) -> None:
    _state_file(root).write_text(json.dumps({"passed": fp or fingerprint(root)}))


def _last_pass(root: Path) -> str | None:
    with contextlib.suppress(OSError, json.JSONDecodeError):
        return json.loads(_state_file(root).read_text()).get("passed")
    return None


# --------------------------------------------------------------------------- the design flow
def flow(root: Path) -> dict:
    path = root / "design" / "flow.toml"
    with contextlib.suppress(OSError, tomllib.TOMLDecodeError):
        return tomllib.loads(path.read_text(encoding="utf-8"))
    return {}


def flow_line(root: Path) -> tuple[str, str | None]:
    stages = flow(root).get("stages", {})
    if not stages:
        return "no design/flow.toml yet (run /freecad-design:start)", "start"
    parts, nxt = [], None
    for sid, title, cmd in STAGES:
        st = stages.get(sid, "todo")
        mark = {"done": "done", "skipped": "skipped", "off": "off", "active": "NOW"}.get(st, "to do")
        parts.append(f"{title}: {mark}")
        if nxt is None and st in ("todo", "active"):
            nxt = cmd
    return " · ".join(parts), nxt


# --------------------------------------------------------------------------- commands
def cmd_check(args: list[str]) -> int:
    root = project_root()
    warnings = "--warnings" in args
    files = [Path(a).resolve().relative_to(root).as_posix() for a in args if not a.startswith("--")]
    text, n = report(run_checks(root, files or None), warnings)
    print(text)
    if not files and n == 0:
        _passed(root)
    return 1 if n else 0


def hook_edit() -> int:
    """After Claude writes or edits a file: check that one file, and tell Claude what's wrong."""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    root = Path(data.get("cwd") or project_root()).resolve()
    if not is_project(root):
        return 0
    path = (data.get("tool_input") or {}).get("file_path") or ""
    try:
        rel = Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return 0
    if not rel.endswith(".py") or rel.split("/")[0] not in (*WATCHED, "analysis", "tests"):
        return 0
    try:
        diags = run_checks(root, [rel])
    except Exception as e:  # a broken check must not block the work
        print(f"freecad-design: the check couldn't run on {rel}: {e}", file=sys.stderr)
        return 0
    text, n = report([d for d in diags if d.get("severity") == "error"])
    if n:
        print(f"The model check found problems in {rel}. Fix them before going on:\n{text}", file=sys.stderr)
        return 2
    return 0


def hook_stop() -> int:
    """Before Claude ends its turn: the full check, when anything modelled changed since it passed."""
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}
    root = Path(data.get("cwd") or project_root()).resolve()
    if not is_project(root) or not any((root / d).glob("*.py") for d in ("parts", "assemblies")):
        return 0
    fp = fingerprint(root)
    if _last_pass(root) == fp:
        return 0
    try:
        text, n = report(run_checks(root, None))
    except Exception as e:
        print(json.dumps({"systemMessage": f"freecad-design: the full check couldn't run: {e}"}))
        return 0
    if n and not data.get("stop_hook_active"):
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": "Before you finish: the full model check found errors. Fix them, or "
                    "if fixing one needs a decision from the person, ask them.\n" + text,
                }
            )
        )
        return 0
    if n:
        print(json.dumps({"systemMessage": "freecad-design: the model check still fails:\n" + text}))
        return 0
    _passed(root, fp)
    print(json.dumps({"systemMessage": "freecad-design: " + text.splitlines()[-1].replace("PASS: 0 error(s)", "checks pass")}))
    return 0


def hook_start() -> int:
    root = project_root()
    if not is_project(root):
        return 0
    line, nxt = flow_line(root)
    print(
        "freecad-design is on for this project.\n"
        f'- Tools (FreeCAD\'s Python): bash "{FC}" <command>, with check [files], render <target>, '
        "export [folder], analysis, status. Run check after you change geometry; the checks also "
        "run by themselves after each edit and before you finish.\n"
        f"- Design flow: {line}.\n"
        + (f"- Next: /freecad-design:{nxt}\n" if nxt else "")
        + "- design/decisions.md holds the person's decisions: read it before each step."
    )
    return 0


def cmd_render(args: list[str]) -> int:
    root = project_root()
    if not args:
        print("fc render <parts/x.py | assemblies/x.py | reference/x.step> [--views iso,front,side,top]")
        return 2
    r = subprocess.run([sys.executable, "-B", str(LIB / "render.py"), *args], cwd=root, env=_env(root))
    return r.returncode


def cmd_export(args: list[str]) -> int:
    root = project_root()
    script = root / "scripts" / "export.py"
    if not script.is_file():
        script = LIB / "template" / "scripts" / "export.py"
        shutil.copy(script, root / "scripts" / "export.py") if (root / "scripts").is_dir() else None
    r = subprocess.run([sys.executable, "-B", str(script), *args], cwd=root, env=_env(root))
    return r.returncode


def cmd_analysis(_: list[str]) -> int:
    root = project_root()
    rows, failed = [], 0
    for path in sorted((root / "analysis").glob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(root).as_posix()
        r = subprocess.run(
            [sys.executable, "-B", rel], cwd=root, capture_output=True, text=True, env=_env(root)
        )
        if r.returncode:
            rows.append(f"x {rel}: {(r.stderr.strip().splitlines() or ['failed'])[-1]}")
            failed += 1
        for line in r.stdout.splitlines():
            with contextlib.suppress(json.JSONDecodeError):
                d = json.loads(line)
                ok = "ok  " if d.get("ok") else "FAIL"
                failed += 0 if d.get("ok") else 1
                rows.append(
                    f"{ok} {d.get('id')}: {d.get('value')} {d.get('unit', '')} (limit {d.get('limit')}) "
                    f"[{rel}]"
                )
    print("\n".join(rows) or "No analysis/*.py yet.")
    return 1 if failed else 0


def cmd_status(_: list[str]) -> int:
    root = project_root()
    line, nxt = flow_line(root)
    print(line.replace(" · ", "\n"))
    if nxt:
        print(f"\nNext: /freecad-design:{nxt}")
    return 0


def cmd_new(_: list[str]) -> int:
    """A new project from the template; a project that's already here only gets what's missing
    (CLAUDE.md, design/flow.toml, the export script, .gitignore lines). Nothing is overwritten."""
    root = project_root()
    tpl = LIB / "template"
    existing = is_project(root)
    added = []
    for src in sorted(tpl.rglob("*")):
        rel = src.relative_to(tpl)
        dst = root / rel
        if src.is_dir() or dst.exists() or "__pycache__" in rel.parts:
            continue
        if existing and rel.parts[0] not in ("CLAUDE.md", "design", "scripts", ".gitignore"):
            continue
        if existing and rel.as_posix() == "design/decisions.md":
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        added.append(rel.as_posix())
    gi = root / ".gitignore"
    want = ["exports/", "__pycache__/", ".pytest_cache/", ".ruff_cache/"]
    have = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    missing = [w for w in want if w not in have]
    if missing:
        gi.write_text("\n".join([*have, *missing]) + "\n", encoding="utf-8")
    print(("Adopted the project here" if existing else "New design project here") + ":")
    print("\n".join(f"  + {a}" for a in added) or "  (nothing to add)")
    return 0


def cmd_setup(args: list[str]) -> int:
    print(f"FreeCAD's Python: {sys.executable}")
    try:
        _import_freecad()
        import FreeCAD

        print("FreeCAD " + ".".join(FreeCAD.Version()[:3]))
    except Exception as e:
        print(f"x FreeCAD doesn't import: {e}")
        return 1
    need = {"numpy": "numpy", "PIL": "pillow", "ruff": "ruff", "pytest": "pytest"}
    missing = [pkg for mod, pkg in need.items() if not _has(mod)]
    for mod, pkg in need.items():
        print(f"{'ok' if pkg not in missing else 'missing'}: {pkg}")
    if missing and "--install" in args:
        r = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True)
        if r.returncode:
            subprocess.run([sys.executable, "-m", "ensurepip", "--user"])
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", *missing])
        return r.returncode
    if missing:
        print(f'Install them with: bash "{FC}" setup --install')
        return 1 if "pillow" in missing or "numpy" in missing else 0
    return 0


COMMANDS = {
    "check": cmd_check,
    "render": cmd_render,
    "export": cmd_export,
    "analysis": cmd_analysis,
    "status": cmd_status,
    "new": cmd_new,
    "setup": cmd_setup,
}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a code page
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "hook-edit":
        return hook_edit()
    if cmd == "hook-stop":
        return hook_stop()
    if cmd == "hook-start":
        return hook_start()
    if cmd not in COMMANDS:
        print(f"Unknown command {cmd}.\n{__doc__}")
        return 2
    os.chdir(project_root())
    return COMMANDS[cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
