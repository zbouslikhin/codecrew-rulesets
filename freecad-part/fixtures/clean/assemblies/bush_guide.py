"""Bush guide: the spacer bush in the guide block's bore, its lower end flush with the block."""

import Part

from parts import guide_block, spacer_bush


def build() -> dict[str, Part.Shape]:
    block = guide_block.build()
    bush = spacer_bush.build()
    bush.translate(guide_block.bore_centre())  # on the bore's axis, standing on the underside
    return {"guide_block": block, "spacer_bush": bush}
