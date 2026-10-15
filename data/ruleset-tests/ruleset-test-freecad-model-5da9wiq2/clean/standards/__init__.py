"""Standards for mechanical parts: fasteners, standard sizes, materials.

Shipped and pinned by the freecad-part ruleset: don't edit it here; a correction goes into the
ruleset. Parts and assemblies take their numbers from these tables instead of typing them:

    from standards import fasteners, materials, sizes
    hole_diameter_mm: float = fasteners.clearance_hole("M4")          # 4.5, ISO 273 medium

`standards.strength` has the hand calculations for load cases (beams, screws in shear, snap
arms). `standards.shapes` builds standard parts as geometry (it needs FreeCAD); the rest is
plain data.
The tables hold the common metric sizes. Check a value against your own copy of the standard
before it goes to manufacture: the standard is the authority, this is a convenience.
"""
