import os
from pathlib import Path

project = Path(SPECPATH).parent
version = os.environ.get("APP_VERSION", (project / "VERSION").read_text().strip())

a = Analysis([str(project / "app.py")], pathex=[str(project)])
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Easy CSV Cleaner",
    console=False,
    target_arch=os.environ.get("APP_ARCH") or None,
)
collection = COLLECT(exe, a.binaries, a.datas, name="Easy CSV Cleaner")
app = BUNDLE(
    collection,
    name="Easy CSV Cleaner.app",
    bundle_identifier="io.github.lewb-ox.easy-csv-cleaner",
    info_plist={
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "NSHighResolutionCapable": True,
    },
)
