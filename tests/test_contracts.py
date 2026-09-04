import hashlib, json, shutil, subprocess, tempfile, unittest, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class RepositoryContracts(unittest.TestCase):
 def setUp(self): self.versions=json.loads((ROOT/'versions.json').read_text()); self.rows={x.attrib['id']:x for x in ET.parse(ROOT/'dist/addons.xml').getroot()}
 def test_checksum_and_exact_kodi_datadir_layout(self):
  self.assertEqual(hashlib.md5((ROOT/'dist/addons.xml').read_bytes()).hexdigest(),(ROOT/'dist/addons.xml.md5').read_text().strip())
  for addon,entry in self.versions.items():
   version=entry['upstream_version']+'.'+str(entry['custom_revision']); path=ROOT/'dist'/addon/f'{addon}-{version}.zip'
   self.assertTrue(path.is_file(),path); self.assertFalse((ROOT/'dist'/addon/version).exists())
  for path in (ROOT/'dist').rglob('*.zip'):
   sidecar=path.with_name(path.name+'.sha256'); self.assertTrue(sidecar.is_file(),sidecar)
   self.assertEqual(sidecar.read_text(),hashlib.sha256(path.read_bytes()).hexdigest()+'\n')
  rollback=json.loads((ROOT/'dist/rollback.json').read_text())
  self.assertTrue(all(rollback[a][0].endswith('.zip') for a in self.versions))
 def test_zip_identity_root_version_and_exclusions(self):
  for addon,entry in self.versions.items():
   version=entry['upstream_version']+'.'+str(entry['custom_revision']); archive=ROOT/'dist'/addon/f'{addon}-{version}.zip'
   with zipfile.ZipFile(archive) as z:
    names=z.namelist(); self.assertTrue(names); self.assertTrue(all(n.startswith(addon+'/') for n in names))
    self.assertFalse(any(any(x in n.lower() for x in ('/.git/','/.github/','/tests/','__pycache__')) or n.endswith(('.pyc','.bak','.git.broken-backup')) for n in names))
    xml=ET.fromstring(z.read(addon+'/addon.xml')); self.assertEqual((xml.attrib['id'],xml.attrib['version']),(addon,version))
 def test_version_sorting_and_repository_urls(self):
  self.assertLess(tuple(map(int,'12.4.23.1'.split('.'))),tuple(map(int,'12.4.23.2'.split('.'))))
  repo=ET.parse(ROOT/'repository/repository.drakefrog.kodi-emby/addon.xml').getroot()
  values=[x.text for x in repo.iter() if x.tag in ('info','checksum','datadir')]
  self.assertTrue(all(v.startswith('https://drakefrog.github.io/kodi-emby/') for v in values))
  self.assertTrue(any(v.endswith('/addons.xml') for v in values)); self.assertTrue(any(v.endswith('/addons.xml.md5') for v in values)); self.assertTrue(any(v.endswith('/kodi-emby/') for v in values))
 def test_license_attribution_and_cross_plugin_contract(self):
  ledger=(ROOT/'docs/UPSTREAMS.md').read_text(); self.assertIn('MediaBrowser',ledger); self.assertIn('faush01',ledger); self.assertIn('jurialmunkey',ledger)
  self.assertTrue((ROOT/'sources/emby-next-gen/LICENSE.txt').is_file()); self.assertTrue((ROOT/'sources/arctic-fuse-3/LICENSE.txt').is_file())
  embycon=(ROOT/'sources/embycon/plugin.video.embycon/resources/lib/detail_routes.py').read_text(); fuse=(ROOT/'sources/arctic-fuse-3/shortcuts/skinvariables-shortcut-searchwidgets.json').read_text()
  self.assertIn('OPEN_DETAIL',embycon); self.assertIn('plugin.video.embycon',fuse)
 def test_recommendation_dialog_does_not_use_person_text(self):
  root=ET.parse(ROOT/'sources/arctic-fuse-3/1080i/Includes_Labels.xml').getroot(); names={'Label_Overlay_1114_PlotBox','Label_Overlay_Header_1114_PlotBox'}
  conditions=[next(v.attrib['condition'] for v in variable if v.attrib.get('condition')) for variable in root.findall('variable') if variable.attrib['name'] in names]
  expected='String.IsEqual(Window.Property(emby_source),emby) + !String.IsEmpty(Window.Property(emby_person_id))'
  self.assertEqual(conditions,[expected,expected])
 def test_helper_provenance_and_service_dependency_closure(self):
  helper=json.loads((ROOT/'helpers.json').read_text())['plugin.video.emby-next-gen']; self.assertEqual(len(helper['sha256']),64); self.assertTrue(helper['source_url'].startswith('https://'))
  helper_xml=ET.parse(ROOT/'sources/plugin.video.emby-next-gen/addon.xml').getroot(); service_req=next(x.attrib['version'] for x in helper_xml.find('requires') if x.attrib['addon']=='plugin.service.emby-next-gen')
  service=json.loads((ROOT/'versions.json').read_text())['plugin.service.emby-next-gen']; published=service['upstream_version']+'.'+str(service['custom_revision'])
  def v(value): return tuple(int(x) for x in value.split('.'))
  self.assertGreaterEqual(v(published),v(service_req)); self.assertEqual(helper_xml.attrib['version'],helper['version'])
 def test_embycon_patch_queue_has_no_line_ending_churn(self):
  patch=(ROOT/'patches/embycon/0001-customizations.patch').read_text(); files=[line for line in patch.splitlines() if line.startswith('diff --git')]
  self.assertLessEqual(len(files),15); self.assertLess(len(patch.splitlines()),2000)
  self.assertNotIn('\r\n',patch)
 def test_clean_release_rebuild_retains_prior_zip(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); (root/'tools').mkdir(); shutil.copy2(ROOT/'tools/build_repo.py',root/'tools/build_repo.py'); shutil.copy2(ROOT/'tools/restore_previous_release.py',root/'tools/restore_previous_release.py')
   addon=root/'sources/demo.addon'; addon.mkdir(parents=True); (addon/'addon.xml').write_text('<addon id="demo.addon" version="1.0.0"/>')
   (root/'versions.json').write_text(json.dumps({'demo.addon':{'source':'sources/demo.addon','upstream_version':'1.0.0','custom_revision':1}})); subprocess.run(['git','init','-q'],cwd=root,check=True); subprocess.run(['git','add','.'],cwd=root,check=True); subprocess.run(['git','-c','user.name=t','-c','user.email=t@t','commit','-qm','first'],cwd=root,check=True); subprocess.run(['git','tag','release-first'],cwd=root,check=True)
   (root/'versions.json').write_text(json.dumps({'demo.addon':{'source':'sources/demo.addon','upstream_version':'1.0.0','custom_revision':2}})); subprocess.run(['git','add','versions.json'],cwd=root,check=True); subprocess.run(['git','-c','user.name=t','-c','user.email=t@t','commit','-qm','second'],cwd=root,check=True)
   subprocess.run(['python3','tools/restore_previous_release.py'],cwd=root,check=True); subprocess.run(['python3','tools/build_repo.py'],cwd=root,check=True)
   self.assertTrue((root/'dist/demo.addon/demo.addon-1.0.0.1.zip').is_file()); self.assertTrue((root/'dist/demo.addon/demo.addon-1.0.0.2.zip').is_file()); self.assertEqual(len(json.loads((root/'dist/rollback.json').read_text())['demo.addon']),2)
 def test_sync_fixture_success_and_failure_rollback(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); (root/'tools').mkdir(); shutil.copy2(ROOT/'tools/sync_upstream.py',root/'tools/sync_upstream.py'); upstream=root/'upstream'; upstream.mkdir(); (upstream/'file.txt').write_text('base\n'); subprocess.run(['git','init','-q'],cwd=upstream,check=True); subprocess.run(['git','add','.'],cwd=upstream,check=True); subprocess.run(['git','-c','user.name=t','-c','user.email=t@t','commit','-qm','base'],cwd=upstream,check=True); sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()
   branch=subprocess.check_output(['git','branch','--show-current'],cwd=upstream,text=True).strip(); (root/'vendor/foo').mkdir(parents=True); (root/'sources/foo').mkdir(parents=True); (root/'vendor/foo/file.txt').write_text('base\n'); (root/'sources/foo/file.txt').write_text('base\ncustom\n'); (root/'patches/foo').mkdir(parents=True); (root/'patches/foo/0001.patch').write_text('diff --git a/vendor/foo/file.txt b/sources/foo/file.txt\n--- a/vendor/foo/file.txt\n+++ b/sources/foo/file.txt\n@@ -1 +1,2 @@\n base\n+custom\n'); meta={'foo':{'url':str(upstream),'branch':branch,'upstream_commit':sha,'vendor':'vendor/foo','source':'sources/foo','patches':'patches/foo','patch_strip':3}}; (root/'upstreams.json').write_text(json.dumps(meta)); (root/'versions.json').write_text('{}')
   subprocess.run(['python3','tools/sync_upstream.py','foo','--commit',sha,'--root',str(root)],cwd=root,check=True); self.assertEqual((root/'sources/foo/file.txt').read_text(),'base\ncustom\n'); self.assertFalse((root/'.sync-backup').exists())
   (root/'patches/foo/0001.patch').write_text('diff --git a/vendor/foo/missing.txt b/sources/foo/missing.txt\n--- a/vendor/foo/missing.txt\n+++ b/sources/foo/missing.txt\n@@ -1 +1 @@\n-no\n+bad\n'); before=(root/'sources/foo/file.txt').read_text(); failed=subprocess.run(['python3','tools/sync_upstream.py','foo','--commit',sha,'--root',str(root)],cwd=root); self.assertEqual(failed.returncode,2); self.assertEqual((root/'sources/foo/file.txt').read_text(),before)
if __name__=='__main__': unittest.main()
