#!/usr/bin/env python3
"""Seed dist from the latest controlled release tag for one-version rollback."""
import shutil, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 try:
  tag=subprocess.check_output(['git','describe','--tags','--match','release-*','--abbrev=0','HEAD^'],cwd=ROOT,text=True).strip()
 except subprocess.CalledProcessError:
  print('No prior controlled release tag; no rollback ZIP to seed.')
  return
 with tempfile.TemporaryDirectory(prefix='kodi-emby-previous-') as td:
  worktree=Path(td)/'tree'
  subprocess.run(['git','worktree','add','--detach',str(worktree),tag],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
  try:
   subprocess.run(['python3','tools/build_repo.py'],cwd=worktree,check=True)
   dest=ROOT/'dist'; dest.mkdir(exist_ok=True)
   for addon in (worktree/'dist').iterdir():
    if addon.is_dir(): shutil.copytree(addon,dest/addon.name,dirs_exist_ok=True)
  finally:
   subprocess.run(['git','worktree','remove','--force',str(worktree)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
if __name__=='__main__': main()
