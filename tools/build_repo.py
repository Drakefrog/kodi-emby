#!/usr/bin/env python3
"""Create an atomic Kodi repository tree from staged sources."""
import hashlib, json, shutil, tempfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", ".github", "tests", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".bak", "~"}

def version(entry):
    parts = entry["upstream_version"].split(".")
    if len(parts) != 3 or not all(x.isdigit() for x in parts): raise ValueError("version must be three numeric fields")
    return entry["upstream_version"] + "." + str(entry["custom_revision"])

def allowed(path):
    return not any(x in EXCLUDED_DIRS for x in path.parts) and not any(str(path).endswith(x) for x in EXCLUDED_SUFFIXES) and "backup" not in path.name.lower()

def main():
    versions=json.loads((ROOT/"versions.json").read_text())
    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        out=Path(td)/"dist"; out.mkdir()
        rows=[]
        for addon_id, entry in versions.items():
            source=ROOT/entry["source"]; addon_xml=source/"addon.xml"; root=ET.parse(addon_xml).getroot()
            if root.attrib["id"] != addon_id: raise ValueError(f"{source}: id mismatch")
            v=version(entry); root.attrib["version"]=v
            # Kodi joins datadir with addon id and archive name: never insert a
            # version directory between them.
            target=out/addon_id; target.mkdir(parents=True)
            stage=Path(td)/"stage"/addon_id; stage.parent.mkdir(exist_ok=True); shutil.copytree(source, stage, ignore=shutil.ignore_patterns(".git", ".github", "tests", "__pycache__", "*.pyc", "*.bak", "*backup*"))
            ET.ElementTree(root).write(stage/"addon.xml", encoding="utf-8", xml_declaration=True)
            archive=target/f"{addon_id}-{v}.zip"
            with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
                for p in stage.rglob("*"):
                    if p.is_file() and allowed(p.relative_to(stage)): z.write(p, p.relative_to(stage.parent))
            rows.append(root)
        addons=ET.Element("addons")
        for row in sorted(rows,key=lambda x:x.attrib["id"]): addons.append(row)
        ET.indent(addons); ET.ElementTree(addons).write(out/"addons.xml",encoding="utf-8",xml_declaration=True)
        (out/"addons.xml.md5").write_text(hashlib.md5((out/"addons.xml").read_bytes()).hexdigest()+"\n")
        dest=ROOT/"dist"; backup=ROOT/".dist-previous"
        if backup.exists(): shutil.rmtree(backup)
        if dest.exists(): dest.rename(backup)
        shutil.move(str(out),dest)
        if backup.exists(): shutil.rmtree(backup)
if __name__ == "__main__": main()
