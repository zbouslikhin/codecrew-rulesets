# The toolchain for the freecad-part ruleset: headless FreeCAD with its own Python,
# plus ruff and pytest. Build it once on the machine running codecrew:
#   docker build -t codecrew-freecad:1.1.3 codecrew-rulesets/freecad-part/toolchain
FROM debian:bookworm-slim

ARG FREECAD_VERSION=1.1.3
# FreeCAD's AppImage bundles everything but the C library; git and ca-certificates are for codecrew.
RUN apt-get -o Acquire::Retries=6 update \
 && apt-get -o Acquire::Retries=6 install -y --no-install-recommends ca-certificates curl git \
 && rm -rf /var/lib/apt/lists/*

# Extracted rather than run: an AppImage needs FUSE, which containers usually don't have.
# 820 MB: retried patiently, since DNS in Docker Desktop builds can drop out briefly.
WORKDIR /opt
RUN curl -fsSL --retry 8 --retry-all-errors --retry-delay 5 --connect-timeout 30 \
      -o /tmp/freecad.AppImage \
      "https://github.com/FreeCAD/FreeCAD/releases/download/${FREECAD_VERSION}/FreeCAD_${FREECAD_VERSION}-Linux-x86_64-py311.AppImage" \
 && chmod +x /tmp/freecad.AppImage \
 && /tmp/freecad.AppImage --appimage-extract > /dev/null \
 && mv /opt/squashfs-root /opt/freecad \
 && rm /tmp/freecad.AppImage

# `python` is FreeCAD's Python, with FreeCAD importable as a module
ENV PATH=/opt/freecad/usr/bin:$PATH \
    PYTHONPATH=/opt/freecad/usr/lib \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
RUN python -m pip install --no-cache-dir --retries 8 --timeout 60 "ruff>=0.9" "pytest>=8.3" \
 && python -c "import FreeCAD, Part; print('FreeCAD', '.'.join(FreeCAD.Version()[:3]))"
