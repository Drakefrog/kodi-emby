#!/usr/bin/env python3
"""Prepare a reviewable vendor/source update by replaying our patch queue.

The live sources are untouched unless every patch applies cleanly.  A failed
replay leaves `UPSTREAM_SYNC_REPORT.md` plus the temporary reject files for
review, and exits non-zero.
"""
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def run(*args, cwd=None): return subprocess.run(args,cwd=cwd,text=True,capture_output=True)
def main():
 p=argparse.ArgumentParser(); p.add_argument('component'); p.add_argument('--commit'); a=p.parse_args()
 meta=json.loads((ROOT/'upstreams.json').read_text())[a.component]
 with tempfile.TemporaryDirectory(prefix='kodi-emby-sync-') as td:
  td=Path(td); clone=td/'clone'; result=run('git','clone','--filter=blob:none','--no-checkout',meta['url'],str(clone))
  if result.returncode: raise SystemExit(result.stderr)
  tip=a.commit or run('git','rev-parse',f"origin/{meta['branch']}",cwd=clone).stdout.strip()
  staged=td/'staged'; staged.mkdir(); import tarfile, io
  raw=subprocess.run(['git','archive',tip],cwd=clone,capture_output=True,check=True).stdout
  import tarfile, io; tarfile.open(fileobj=io.BytesIO(raw)).extractall(staged)
  staged=staged/meta.get('upstream_subdir','.')
  report=[]
  for patch in sorted((ROOT/meta['patches']).glob('*.patch')):
   r=run('git','apply',f"-p{meta['patch_strip']}",'--reject',str(patch),cwd=staged)
   report.append(f"{patch.name}: {'applied' if r.returncode == 0 else 'CONFLICT'}")
   if r.returncode:
    (ROOT/'UPSTREAM_SYNC_REPORT.md').write_text('# Upstream sync conflict\n\n'+ '\n'.join(report)+'\n\n'+r.stderr)
    raise SystemExit(2)
  # regenerate the patch queue against the new pure vendor before changing sources.
  raw=subprocess.run(['git','archive',tip],cwd=clone,capture_output=True,check=True).stdout; tarfile.open(fileobj=io.BytesIO(raw)).extractall(pure:=td/'pure-all'); pure=pure/meta.get('upstream_subdir','.')
  old_vendor=ROOT/meta['vendor']; old_source=ROOT/meta['source']; new_patch=td/'custom.patch'
  d=subprocess.run(['git','diff','--no-index',str(pure),str(staged)],capture_output=True)
  # Rewrite only the temporary path labels into stable, reviewable paths.
  # `git diff --no-index` otherwise embeds the random temporary directory.
  body=d.stdout.replace(str(pure).encode(),meta['vendor'].encode()).replace(str(staged).encode(),meta['source'].encode())
  new_patch.write_bytes(body)
  # Assemble every replacement before touching canonical paths.  Rename is
  # atomic per path; the backup is retained until all replacements succeed.
  txn=ROOT/'.sync-transaction'; backup=ROOT/'.sync-backup'
  if txn.exists(): shutil.rmtree(txn)
  if backup.exists(): raise RuntimeError('existing .sync-backup: recover or remove it first')
  (txn/'vendor').parent.mkdir(parents=True); shutil.copytree(pure,txn/'vendor')
  shutil.copytree(staged,txn/'source'); (txn/'patches').mkdir(); shutil.copy2(new_patch,txn/'patches'/'0001-customizations.patch')
  allmeta=json.loads((ROOT/'upstreams.json').read_text()); allmeta[a.component]['upstream_commit']=tip; (txn/'upstreams.json').write_text(json.dumps(allmeta,indent=2)+'\n')
  versions=json.loads((ROOT/'versions.json').read_text())
  for addon_id,entry in versions.items():
   if entry['source'] == meta['source']:
    upstream_version=ET.parse(staged/'addon.xml').getroot().attrib['version']
    if len(upstream_version.split('.')) != 3 or not all(x.isdigit() for x in upstream_version.split('.')): raise ValueError(f'{addon_id}: unsupported upstream version {upstream_version}')
    entry['upstream_version']=upstream_version
  (txn/'versions.json').write_text(json.dumps(versions,indent=2)+'\n')
  (txn/'UPSTREAM_SYNC_REPORT.md').write_text(f'# Upstream sync prepared\n\n- {a.component}: `{meta["upstream_commit"]}` → `{tip}`\n- Patch queue replayed cleanly; review vendor, sources and patches before merge.\n')
  queue=ROOT/meta['patches']; backup.mkdir()
  paths=[(old_vendor,txn/'vendor'),(old_source,txn/'source'),(queue,txn/'patches'),(ROOT/'upstreams.json',txn/'upstreams.json'),(ROOT/'versions.json',txn/'versions.json'),(ROOT/'UPSTREAM_SYNC_REPORT.md',txn/'UPSTREAM_SYNC_REPORT.md')]
  moved=[]
  try:
   for old,new in paths:
    if old.exists(): old.rename(backup/old.name)
    new.rename(old); moved.append((old,backup/old.name))
  except Exception:
   for old,prior in reversed(moved):
    if old.exists(): shutil.rmtree(old) if old.is_dir() else old.unlink()
    if prior.exists(): prior.rename(old)
   raise
  shutil.rmtree(backup); shutil.rmtree(txn)
if __name__=='__main__': main()
