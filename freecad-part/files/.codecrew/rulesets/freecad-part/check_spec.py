"""Requirements as data: every part and assembly starts from a spec the checks can read.

    design/<name>.spec.toml

A part's spec says what it is for, how many are made, of what and by which process, the
envelope and mass it must stay within, what the design starts from (a description, a drawing,
existing CAD it must fit), its interfaces (what it mates with, and the parameters that realise
each), and its requirements, each with what proves it. An assembly's spec lists its parts
(this repository's, standard parts, reference CAD) and the joints between their interfaces.

Checked here, without building anything: the spec is complete, names what exists (parameters
in the part's Params, tests in its test file, files in the repository), every requirement is
proven by something, every interface is realised by a parameter. The targets themselves
(envelope, mass) are measured on the built part by validate.py.
One JSON object per line: file, line, code, message, severity.

    python check_spec.py                 check
    python check_spec.py --grandfather   list today's parts without a spec in design/legacy.toml:
                                         for those, a missing spec is a warning, not an error
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))  # the project's standards/ package, shipped with the ruleset
try:
    from standards import fasteners, materials, sizes
except ImportError:  # a project from before the standards library: those checks are skipped
    fasteners = materials = sizes = None  # type: ignore[assignment]
try:
    from standards import tolerances
except ImportError:
    tolerances = None  # type: ignore[assignment]
try:
    from standards import finishes
except ImportError:
    finishes = None  # type: ignore[assignment]
try:
    from standards import strength
except ImportError:
    strength = None  # type: ignore[assignment]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import loads as load_cases  # noqa: E402


def grip_kinds(root: Path) -> set[str]:
    kinds: set[str] = set()
    for path in (Path(__file__).resolve().parent / "ergonomics.toml", root / "design" / "ergonomics.toml"):
        try:
            kinds |= {k for k, val in tomllib.loads(path.read_text(encoding="utf-8")).items() if isinstance(val, dict)}
        except (OSError, tomllib.TOMLDecodeError):
            continue
    return kinds

def process_profiles(root: Path) -> dict[str, dict]:
    """The ruleset's process profiles with the project's own on top (design/processes.toml)."""
    profiles: dict[str, dict] = {}
    for path in (Path(__file__).resolve().parent / "processes.toml", root / "design" / "processes.toml"):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        for name, values in data.items():
            if isinstance(values, dict):
                profiles[name] = {**profiles.get(name, {}), **values}
    return profiles


THREAD = re.compile(r"\bM\d+(?:\.\d+)?\b")
DESIGN = "design"
LEGACY = "legacy.toml"
SOURCE_KINDS = ("text", "drawing", "cad", "datasheet", "part")
PROOFS = ("test", "param", "check")
CHECKS = ("envelope", "mass", "strength")  # what validate.py measures against the spec


def report(file: str, code: str, message: str, line: int | None = None, severity: str = "error") -> None:
    print(json.dumps({"file": file, "line": line, "code": code, "message": message, "severity": severity}))


def line_of(text: str, needle: str) -> int | None:
    """The line where `needle` first appears (an id, a key), to point at."""
    for n, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return n
    return None


def params_of(path: Path) -> set[str] | None:
    """The fields of the part's Params dataclass, read from its source (nothing is run)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Params":
            names |= {s.target.id for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
    return names


def tests_of(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test")}


def is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class Spec:
    def __init__(self, root: Path, path: Path) -> None:
        self.root, self.path = root, path
        self.rel = path.relative_to(root).as_posix()
        self.name = path.name.removesuffix(".spec.toml")
        self.text = path.read_text(encoding="utf-8")
        self.data: dict = {}
        self.ok = True
        self.broken = False  # not readable: reported once, and nothing else is concluded from it

    def say(self, code: str, message: str, near: str | None = None) -> None:
        self.ok = False
        report(self.rel, code, message, line_of(self.text, near) if near else 1)

    def load(self) -> bool:
        try:
            self.data = tomllib.loads(self.text)
        except tomllib.TOMLDecodeError as e:
            found = re.search(r"line (\d+)", str(e))
            report(self.rel, "spec-invalid", f"not valid TOML: {e}", int(found.group(1)) if found else 1)
            self.broken = True
            return False
        return True

    # --- shared -----------------------------------------------------------------
    def tables(self, key: str) -> list[dict]:
        value = self.data.get(key, [])
        if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
            self.say("spec-invalid", f"{key} must be a list of tables: write each as [[{key}]]", key)
            return []
        return value

    def ids(self, key: str, items: list[dict]) -> None:
        seen: set[str] = set()
        for item in items:
            ident = item.get("id")
            if not is_text(ident):
                self.say("spec-incomplete", f"every entry of {key} needs an id (e.g. {key[0].upper()}1)", key)
            elif ident in seen:
                self.say("duplicate-id", f"{key}: id {ident} is used twice", f'"{ident}"')
            else:
                seen.add(ident)

    def common(self) -> None:
        if self.data.get("name") != self.name:
            self.say(
                "spec-name",
                f'name must be "{self.name}", the file\'s name: a spec belongs to the part or assembly it is named after',
                "name",
            )
        if not is_text(self.data.get("purpose")):
            self.say("spec-incomplete", "purpose is missing: say in a sentence what it is for")

    def proposed(self, built: bool, what: str) -> bool:
        """A spec may be proposed: written and approved before anything is modelled. Then what
        it names needn't exist yet. Once the part is there, the mark comes off."""
        status = self.data.get("status")
        if status is None:
            return False
        if status != "proposed":
            self.say("spec-invalid", 'status is "proposed", or left out once the part is built', "status")
            return False
        if built:
            self.say(
                "spec-still-proposed",
                f'{what} exists: remove status = "proposed", so the spec is checked against what was built',
                "status",
            )
            return False
        report(
            self.rel,
            "spec-proposed",
            f"proposed: {what} isn't built yet. What the spec names is checked once it is.",
            line_of(self.text, "status"),
            "warning",
        )
        return True

    def requirements(self, proofs_for) -> None:
        items = self.tables("requirements")
        if not items:
            self.say("spec-incomplete", "no requirements: say what must be true of it, each with what proves it")
        self.ids("requirements", items)
        for r in items:
            ident = str(r.get("id") or "?")
            if not is_text(r.get("text")):
                self.say("spec-incomplete", f"requirement {ident} has no text", f'"{ident}"')
            proofs = r.get("proven_by", [])
            if not isinstance(proofs, list) or not proofs:
                self.say(
                    "requirement-unproven",
                    f"requirement {ident} is proven by nothing: give proven_by, e.g. "
                    '["test:test_hole_spacing"], ["param:hole_diameter_mm"] or ["check:envelope"]',
                    f'"{ident}"',
                )
                continue
            for proof in proofs:
                proofs_for(ident, str(proof))

    # --- a part ---------------------------------------------------------------------
    def part(self) -> None:
        d = self.data
        self.common()
        module = self.root / "parts" / f"{self.name}.py"
        proposed = self.proposed(module.is_file(), f"parts/{self.name}.py")
        if not module.is_file() and not proposed:
            self.say("spec-orphan", f"there is no parts/{self.name}.py for this spec")
        params = params_of(module) if module.is_file() else None
        tests = tests_of(self.root / "tests" / f"test_{self.name}.py")

        quantity = d.get("quantity")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            self.say("spec-incomplete", "quantity is missing: how many are made (it decides the process)", "quantity")
        material = None
        if not is_text(d.get("material")):
            self.say("spec-incomplete", "material is missing", "material")
        elif materials is not None:
            material = materials.get(d["material"])
            if material is None:
                self.say(
                    "unknown-material",
                    f"'{d['material']}' isn't in the materials library. Known: {', '.join(materials.MATERIALS)}",
                    "material",
                )
        processes = d.get("processes")
        if not isinstance(processes, list) or not processes or not all(is_text(p) for p in processes):
            self.say("spec-incomplete", 'processes is missing: how it is made, e.g. ["fdm"] or ["milling"]', "processes")
        elif materials is not None:
            profiles = process_profiles(self.root)
            for process in processes:
                profile = profiles.get(process)
                if profile is None:
                    self.say(
                        "unknown-process",
                        f"'{process}' has no profile: known are {', '.join(profiles)}. A process of your own "
                        "gets its limits in design/processes.toml",
                        "processes",
                    )
                elif (
                    material is not None
                    and process not in material.processes
                    and material.name not in profile.get("materials", [])
                ):
                    self.say(
                        "material-process",
                        f"{material.name} isn't made by {process}: it suits {', '.join(material.processes)}. "
                        "Change the material or the process.",
                        "processes",
                    )
        envelope = d.get("envelope_mm")
        if not isinstance(envelope, dict) or any(not is_number(envelope.get(a)) or envelope[a] <= 0 for a in "xyz"):
            self.say("spec-incomplete", "envelope_mm is missing: the x, y and z the part must stay within", "envelope_mm")
        orientation = d.get("orientation")
        if orientation is not None and (
            not isinstance(orientation, dict) or orientation.get("up") not in ("+x", "-x", "+y", "-y", "+z", "-z")
        ):
            self.say("spec-invalid", 'orientation needs up, one of "+x", "-x", "+y", "-y", "+z", "-z"', "orientation")
        mass = d.get("mass_g")
        has_mass = isinstance(mass, dict) and is_number(mass.get("max")) and mass["max"] > 0
        if mass is not None and not has_mass:
            self.say("spec-invalid", "mass_g needs max, the mass in grams it must stay under", "mass_g")

        sources = self.tables("sources")
        if not sources:
            self.say(
                "spec-incomplete",
                "no sources: say what the design starts from (a description, a drawing, CAD it must fit)",
            )
        for s in sources:
            kind, ref = s.get("kind"), s.get("ref")
            if kind not in SOURCE_KINDS:
                self.say("spec-invalid", f"a source's kind is one of {', '.join(SOURCE_KINDS)}, not {kind!r}", "sources")
            elif kind == "text" and not is_text(s.get("note")):
                self.say("spec-incomplete", "a text source needs a note: the description itself", "sources")
            elif kind != "text" and not is_text(ref):
                self.say("spec-incomplete", f"a {kind} source needs ref: the file, or attachment:<name>", "sources")
            elif is_text(ref) and not str(ref).startswith("attachment:") and not (self.root / str(ref)).is_file():
                self.say("source-missing", f"source {ref} is not in the repository", str(ref))

        interfaces = self.tables("interfaces")
        if not interfaces and d.get("standalone") is not True:
            self.say(
                "spec-incomplete",
                "no interfaces: say what the part mates with and which parameters realise it "
                "(a part that mates with nothing says standalone = true)",
            )
        self.ids("interfaces", interfaces)
        for i in interfaces:
            ident = str(i.get("id") or "?")
            if not is_text(i.get("mates_with")):
                self.say("spec-incomplete", f"interface {ident} doesn't say what it mates with", f'"{ident}"')
            names = i.get("parameters", [])
            if not isinstance(names, list) or not names:
                self.say(
                    "interface-unrealised",
                    f"interface {ident} is realised by no parameter: name the parameters of Params that "
                    "make it fit (a hole diameter, a spacing)",
                    f'"{ident}"',
                )
                continue
            for name in names:
                if params is not None and name not in params:
                    self.say("unknown-parameter", f"interface {ident}: Params has no parameter '{name}'", str(name))

        # which parameter follows which standard
        declared: dict[str, set[str]] = {}  # parameter -> the threads it's declared for
        for entry in self.tables("standards") if sizes is not None else []:
            name, kind, thread = entry.get("parameter"), entry.get("standard"), entry.get("thread")
            if not is_text(name) or (params is not None and name not in params):
                self.say("unknown-parameter", f"standards: Params has no parameter '{name}'", "standards")
                continue
            if kind not in sizes.KINDS:
                self.say(
                    "spec-invalid",
                    f"standards: '{kind}' isn't a standard. Known: {', '.join(sizes.KINDS)}",
                    str(name),
                )
                continue
            if kind in sizes.NEEDS_THREAD:
                if thread not in fasteners.THREADS:
                    self.say("spec-invalid", f"standards: {name} ({kind}) needs thread, e.g. \"M4\"", str(name))
                    continue
                declared.setdefault(str(name), set()).add(str(thread))
            if entry.get("fit") is not None and entry["fit"] not in fasteners.FITS:
                self.say("spec-invalid", f"standards: fit is {', '.join(fasteners.FITS)}", str(name))
        if sizes is not None:
            for i in interfaces:
                threads = set(THREAD.findall(str(i.get("mates_with") or "")))
                names = [n for n in i.get("parameters", []) if isinstance(n, str)] if isinstance(i.get("parameters"), list) else []
                for thread in sorted(threads & set(fasteners.THREADS)):
                    if not any(thread in declared.get(n, ()) for n in names):
                        ident = str(i.get("id") or "?")
                        self.say(
                            "interface-standard",
                            f"interface {ident} mates with {thread}, but none of its parameters is declared "
                            f'to follow a standard for {thread}: add [[standards]] with parameter, standard '
                            f'(e.g. "clearance_hole") and thread = "{thread}"',
                            f'"{ident}"',
                        )

        # tolerances: how far each made dimension may be off
        toleranced: set[str] = set(declared)  # a clearance hole to ISO 273 has its class
        general_class = d.get("general_tolerance")
        if tolerances is not None:
            if general_class is not None and general_class not in tolerances.GENERAL:
                self.say("spec-invalid", "general_tolerance is f, m, c or v (ISO 2768-1)", "general_tolerance")
                general_class = None
            for entry in self.tables("tolerances"):
                name = entry.get("parameter")
                if not is_text(name) or (params is not None and name not in params):
                    self.say("unknown-parameter", f"tolerances: Params has no parameter '{name}'", "tolerances")
                    continue
                ways = [k for k in ("fit", "general") if is_text(entry.get(k))]
                if "upper_mm" in entry or "lower_mm" in entry:
                    ways.append("limits")
                if len(ways) != 1:
                    self.say(
                        "spec-invalid",
                        f"tolerances: {name} needs exactly one of fit (\"H7\"), upper_mm with lower_mm, "
                        "or general (\"m\")",
                        str(name),
                    )
                    continue
                if ways[0] == "fit":
                    try:
                        tolerances.limits(str(entry["fit"]), 10.0)
                    except tolerances.UnknownClass as e:
                        self.say("unknown-fit", f"tolerances: {name}: {e}", str(name))
                        continue
                elif ways[0] == "general" and entry["general"] not in tolerances.GENERAL:
                    self.say("spec-invalid", f"tolerances: {name}: general is f, m, c or v", str(name))
                    continue
                elif ways[0] == "limits" and not (
                    is_number(entry.get("upper_mm")) and is_number(entry.get("lower_mm")) and entry["upper_mm"] > entry["lower_mm"]
                ):
                    self.say(
                        "spec-invalid",
                        f"tolerances: {name} needs upper_mm and lower_mm, the deviations from the number "
                        "(e.g. upper_mm = 0.1, lower_mm = -0.1), the upper above the lower",
                        str(name),
                    )
                    continue
                toleranced.add(str(name))
            if general_class is None:
                for i in interfaces:
                    names = i.get("parameters", []) if isinstance(i.get("parameters"), list) else []
                    bare = [n for n in names if isinstance(n, str) and n not in toleranced and (params is None or n in params)]
                    if bare:
                        ident = str(i.get("id") or "?")
                        self.say(
                            "interface-tolerance",
                            f"interface {ident}: {', '.join(bare)} {'has' if len(bare) == 1 else 'have'} no tolerance. "
                            "What mates must say how exact it is: add [[tolerances]] for it, or give the spec "
                            'a general_tolerance (ISO 2768-1: "f", "m", "c" or "v")',
                            f'"{ident}"',
                        )

        # appearance: is it seen, is it touched, and then: its colour and finish, what a hand holds
        look = d.get("appearance")
        if look is None:
            report(
                self.rel,
                "appearance-unstated",
                "the spec doesn't say whether the part is seen or touched ([appearance] visible, touched): "
                "the rules for edges, radii, colour and finish can't be applied",
                1,
                "warning",
            )
        elif not isinstance(look, dict) or any(not isinstance(look.get(k, False), bool) for k in ("visible", "touched")):
            self.say("spec-invalid", "[appearance] has visible and touched, each true or false", "appearance")
        else:
            if look.get("visible") is True:
                for key, why in (("colour", "e.g. \"RAL 7016\" or \"natural\""), ("finish", "e.g. \"as printed\"")):
                    if not is_text(look.get(key)):
                        self.say("spec-incomplete", f"a visible part says its {key} ([appearance] {key}, {why})", "appearance")
            if look.get("rests_on") is not None and look["rests_on"] not in ("+x", "-x", "+y", "-y", "+z", "-z"):
                self.say("spec-invalid", '[appearance] rests_on is one of "+x", "-x", "+y", "-y", "+z", "-z"', "rests_on")
            finish = look.get("finish")
            if is_text(finish) and finishes is not None:
                if finish not in finishes.FINISHES:
                    report(
                        self.rel,
                        "unknown-finish",
                        f"'{finish}' isn't a finish the library knows, so whether it suits the material can't be "
                        f"checked. Known: {', '.join(finishes.FINISHES)}",
                        line_of(self.text, str(finish)),
                        "warning",
                    )
                elif is_text(d.get("material")) and isinstance(processes, list):
                    wrong = finishes.problem(str(finish), str(d["material"]), [str(p) for p in processes])
                    if wrong:
                        self.say("finish-material", f"{wrong}. Choose a finish that suits it", str(finish))
        kinds = grip_kinds(self.root)
        for grip in self.tables("grips"):
            name, kind = grip.get("parameter"), grip.get("kind")
            if not is_text(name) or (params is not None and name not in params):
                self.say("unknown-parameter", f"grips: Params has no parameter '{name}'", "grips")
            elif kind not in kinds:
                self.say("spec-invalid", f"grips: {name}: kind is one of {', '.join(sorted(kinds))}", str(name))

        # loads: what it must carry, each calculable on the part's parameters
        cases = self.tables("loads")
        self.ids("loads", cases)
        if strength is not None:
            for case in cases:
                if not is_text(case.get("id")):
                    continue
                for code, message in load_cases.problems(d, case, params, fasteners.THREADS, strength.PROPERTY_CLASSES):
                    self.say(code, message, f'"{case["id"]}"')
        if "safety_factor" in d and not (is_number(d["safety_factor"]) and d["safety_factor"] >= load_cases.MIN_SAFETY_FACTOR):
            self.say("spec-invalid", f"safety_factor is a number, at least {load_cases.MIN_SAFETY_FACTOR:g}", "safety_factor")

        # what goes on the drawing as a critical dimension says how exact it must be
        if tolerances is not None and general_class is None:
            named = [str(e.get("parameter")) for e in self.tables("standards")]
            for r in self.tables("requirements"):
                proofs = r.get("proven_by", []) if isinstance(r.get("proven_by"), list) else []
                named += [str(t)[6:] for t in proofs if str(t).startswith("param:")]
            for name in dict.fromkeys(named):
                if name not in toleranced and (params is None or name in params):
                    self.say(
                        "dimension-untoleranced",
                        f"{name} is a critical dimension (it follows a standard, or proves a requirement) but has "
                        "no tolerance: the drawing can't say how exact it must be. Add [[tolerances]] for it, "
                        "or give the spec a general_tolerance",
                        name,
                    )

        def proof(ident: str, token: str) -> None:
            kind, _, what = token.partition(":")
            if kind not in PROOFS or not what:
                self.say(
                    "unknown-proof",
                    f"requirement {ident}: '{token}' isn't a proof. Use test:<function>, param:<name> "
                    f"or check:<{'|'.join(CHECKS)}>",
                    token,
                )
            elif kind == "test" and what not in tests and not proposed:
                self.say("unknown-test", f"requirement {ident}: tests/test_{self.name}.py has no {what}", token)
            elif kind == "param" and params is not None and what not in params:
                self.say("unknown-parameter", f"requirement {ident}: Params has no parameter '{what}'", token)
            elif kind == "check" and what not in CHECKS:
                self.say("unknown-proof", f"requirement {ident}: there is no check '{what}' ({', '.join(CHECKS)})", token)
            elif kind == "check" and what == "strength" and not cases:
                self.say(
                    "unknown-proof",
                    f"requirement {ident}: check:strength needs [[loads]] in this spec: what the part must carry",
                    token,
                )
            elif kind == "check" and what == "mass" and not has_mass:
                self.say("unknown-proof", f"requirement {ident}: check:mass needs mass_g.max in this spec", token)

        self.requirements(proof)

    # --- an assembly ------------------------------------------------------------------
    def assembly(self, specs: dict[str, Spec]) -> None:
        self.common()
        module = self.root / "assemblies" / f"{self.name}.py"
        proposed = self.proposed(module.is_file(), f"assemblies/{self.name}.py")
        if not module.is_file() and not proposed:
            self.say("spec-orphan", f"there is no assemblies/{self.name}.py for this spec")
        members = self.tables("parts")
        if len(members) < 2:
            self.say("spec-incomplete", "an assembly has at least two parts: list each as [[parts]]", "parts")
        own: set[str] = set()
        for m in members:
            kinds = [k for k in ("part", "standard", "reference") if is_text(m.get(k))]
            if len(kinds) != 1:
                self.say(
                    "spec-invalid",
                    "each entry of parts is one of: part (a part of this repository), standard (a standard "
                    "part's designation) or reference (CAD it must fit)",
                    "parts",
                )
                continue
            q = m.get("quantity", 1)
            if not isinstance(q, int) or isinstance(q, bool) or q < 1:
                self.say("spec-invalid", "quantity must be a whole number, 1 or more", "quantity")
            if kinds[0] == "standard" and fasteners is not None:
                known = fasteners.parse(str(m["standard"]))
                if known is None:
                    report(
                        self.rel,
                        "unknown-standard-part",
                        f"'{m['standard']}' isn't a standard part this library knows (ISO 4762 screws, ISO 4032 "
                        "nuts, ISO 7089 washers): it is listed, but nothing about it can be checked",
                        line_of(self.text, str(m["standard"])),
                        "warning",
                    )
                for problem in fasteners.problems(str(m["standard"])):
                    self.say("standard-part", f"{m['standard']}: {problem}", str(m["standard"]))
            if kinds[0] == "part":
                name = str(m["part"])
                own.add(name)
                other = specs.get(name)
                if other is not None and other.broken:
                    continue  # its own error says so
                if other is None or other.data.get("kind") != "part":
                    self.say("unknown-part", f"there is no part '{name}' with a spec in {DESIGN}/", name)
            elif kinds[0] == "reference" and not (self.root / str(m["reference"])).is_file():
                self.say("source-missing", f"reference {m['reference']} is not in the repository", str(m["reference"]))

        def end(joint: int, value: object) -> None:
            text = str(value or "")
            kind, _, rest = text.partition(":")
            if kind in ("standard", "reference") and rest:
                return
            part, _, ident = text.partition(":")
            other = specs.get(part)
            if other is not None and other.broken:
                return
            if part not in own or other is None:
                self.say("unknown-part", f"joint {joint}: '{part}' isn't a part of this assembly", text)
            elif ident not in {str(i.get("id")) for i in other.data.get("interfaces", []) if isinstance(i, dict)}:
                self.say("unknown-interface", f"joint {joint}: part '{part}' has no interface '{ident}'", text)

        joints = self.tables("joints")
        if not joints:
            self.say("spec-incomplete", "no joints: say which interface of which part meets which", "joints")
        for n, j in enumerate(joints, 1):
            if not is_text(j.get("a")) or not is_text(j.get("b")):
                self.say("spec-incomplete", f"joint {n} needs a and b, each <part>:<interface id>", "joints")
                continue
            end(n, j["a"])
            end(n, j["b"])
            kind = j.get("kind", "fixed")
            if kind not in ("fixed", "sliding", "rotating"):
                self.say("spec-invalid", f"joint {n}: kind is fixed, sliding or rotating, not {kind!r}", "joints")
            elif kind != "fixed" and not (is_number(j.get("clearance_mm")) and j["clearance_mm"] > 0):
                self.say(
                    "spec-incomplete",
                    f"joint {n} is {kind}: it needs clearance_mm, the gap the parts must keep to move",
                    "joints",
                )

        def dimension(where: str, value: object) -> None:
            """A part's parameter, written <part>:<parameter>."""
            text = str(value or "").lstrip("+-")
            part, _, param = text.partition(":")
            other = specs.get(part)
            if other is not None and other.broken:
                return
            if part not in own or other is None:
                self.say("unknown-part", f"{where}: '{part}' isn't a part of this assembly", text)
                return
            known = params_of(self.root / "parts" / f"{part}.py")
            if known is not None and param not in known:
                self.say("unknown-parameter", f"{where}: part '{part}' has no parameter '{param}'", text)

        for n, j in enumerate(joints, 1):
            fit = j.get("fit")
            if fit is None:
                continue
            if not isinstance(fit, dict) or not is_text(fit.get("hole")) or not is_text(fit.get("shaft")):
                self.say("spec-invalid", f"joint {n}: fit needs hole and shaft, each <part>:<parameter>", "fit")
                continue
            if fit.get("kind") not in ("clearance", "transition", "interference"):
                self.say("spec-invalid", f"joint {n}: fit needs kind: clearance, transition or interference", "fit")
            dimension(f"joint {n}'s fit", fit["hole"])
            dimension(f"joint {n}'s fit", fit["shaft"])
        stacks = self.tables("stacks")
        self.ids("stacks", stacks)
        for st in stacks:
            ident = str(st.get("id") or "?")
            terms = st.get("terms")
            if not isinstance(terms, list) or len(terms) < 2 or any(not is_text(t) or t[0] not in "+-" for t in terms):
                self.say(
                    "spec-invalid",
                    f'stack {ident}: terms is a list of signed dimensions, e.g. ["+housing:depth_mm", "-bush:length_mm"]',
                    f'"{ident}"',
                )
                continue
            if not is_number(st.get("min_mm")) and not is_number(st.get("max_mm")):
                self.say("spec-incomplete", f"stack {ident} needs min_mm or max_mm: what the result must stay within", f'"{ident}"')
            for t in terms:
                dimension(f"stack {ident}", t)

        tests = tests_of(self.root / "tests" / f"test_{self.name}.py")

        def proof(ident: str, token: str) -> None:
            kind, _, what = token.partition(":")
            if kind == "test" and what:
                if what not in tests and not proposed:
                    self.say("unknown-test", f"requirement {ident}: tests/test_{self.name}.py has no {what}", token)
            elif kind == "part" and what:
                part, _, req = what.partition(":")
                other = specs.get(part)
                if other is not None and other.broken:
                    return
                known = {str(r.get("id")) for r in (other.data.get("requirements", []) if other else []) if isinstance(r, dict)}
                if req not in known:
                    self.say("unknown-proof", f"requirement {ident}: part '{part}' has no requirement '{req}'", token)
            else:
                self.say(
                    "unknown-proof",
                    f"requirement {ident}: '{token}' isn't a proof. Use test:<function> or part:<part>:<requirement id>",
                    token,
                )

        self.requirements(proof)


def legacy(root: Path) -> set[str]:
    path = root / DESIGN / LEGACY
    try:
        return {str(p) for p in tomllib.loads(path.read_text(encoding="utf-8")).get("parts", [])}
    except (OSError, tomllib.TOMLDecodeError):
        return set()


def grandfather(root: Path) -> int:
    parts = sorted(p.stem for p in (root / "parts").glob("*.py") if p.name != "__init__.py")
    without = [p for p in parts if not (root / DESIGN / f"{p}.spec.toml").is_file()]
    (root / DESIGN).mkdir(exist_ok=True)
    listed = "".join(f'    "{p}",\n' for p in sorted(set(without) | legacy(root)))
    (root / DESIGN / LEGACY).write_text(
        "# Parts from before specs were required. For these, a missing spec is a warning.\n"
        "# Remove a part from this list once it has its design/<part>.spec.toml.\n"
        f"parts = [\n{listed}]\n",
        encoding="utf-8",
    )
    print(f"{len(without)} part(s) without a spec listed in {DESIGN}/{LEGACY}")
    return 0


def main() -> int:
    root = Path.cwd()
    if "--grandfather" in sys.argv:
        return grandfather(root)
    design = root / DESIGN
    specs: dict[str, Spec] = {}
    for path in sorted(design.glob("*.spec.toml")) if design.is_dir() else []:
        spec = Spec(root, path)
        spec.load()
        specs[spec.name] = spec
    for spec in specs.values():
        if spec.broken:
            continue
        kind = spec.data.get("kind")
        if kind == "part":
            spec.part()
        elif kind == "assembly":
            spec.assembly(specs)
        else:
            spec.say("spec-invalid", 'kind must be "part" or "assembly"', "kind")
    old = legacy(root)
    for path in sorted((root / "parts").glob("*.py")) if (root / "parts").is_dir() else []:
        if path.name == "__init__.py" or (design / f"{path.stem}.spec.toml").is_file():
            continue
        report(
            path.relative_to(root).as_posix(),
            "no-spec",
            f"no {DESIGN}/{path.stem}.spec.toml: a part starts from its spec (purpose, material, process, "
            "envelope, interfaces, requirements). The scaffold tool writes its skeleton.",
            1,
            "warning" if path.stem in old else "error",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
