#!/usr/bin/env python3
import argparse, json, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def numeric(v): return len(v.split("."))==4 and all(p.isdigit() for p in v.split("."))
def main():
    p=argparse.ArgumentParser(); p.add_argument("--sources-only",action="store_true"); a=p.parse_args()
    versions=json.loads((ROOT/"versions.json").read_text())
    for addon_id,e in versions.items():
        root=ET.parse(ROOT/e["source"]/"addon.xml").getroot(); assert root.attrib["id"]==addon_id
        assert numeric(e["upstream_version"]+"."+str(e["custom_revision"]))
    if a.sources_only: return
    rows=ET.parse(ROOT/"dist/addons.xml").getroot(); found={x.attrib["id"]:x.attrib["version"] for x in rows}
    for addon_id,e in versions.items():
        v=e["upstream_version"]+"."+str(e["custom_revision"]); assert found[addon_id]==v
        z=ROOT/"dist"/addon_id/v/f"{addon_id}-{v}.zip"; assert z.exists()
        with zipfile.ZipFile(z) as f:
            names=f.namelist(); assert all(n.startswith(addon_id+"/") for n in names); assert not any("/.git/" in n or "/tests/" in n or n.endswith(".pyc") for n in names)
            xml=ET.fromstring(f.read(addon_id+"/addon.xml")); assert xml.attrib["id"]==addon_id and xml.attrib["version"]==v
    assert (ROOT/"dist/addons.xml.md5").read_text().strip()
if __name__=="__main__": main()
