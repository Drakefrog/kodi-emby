import hashlib, json, unittest, zipfile
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
  rollback=json.loads((ROOT/'dist/rollback.json').read_text())
  self.assertTrue(all(rollback[a][0].endswith('.zip') for a in self.versions))
 def test_zip_identity_root_version_and_exclusions(self):
  for addon,entry in self.versions.items():
   version=entry['upstream_version']+'.'+str(entry['custom_revision']); archive=ROOT/'dist'/addon/f'{addon}-{version}.zip'
   with zipfile.ZipFile(archive) as z:
    names=z.namelist(); self.assertTrue(names); self.assertTrue(all(n.startswith(addon+'/') for n in names))
    self.assertFalse(any(any(x in n.lower() for x in ('/.git/','/.github/','/tests/','__pycache__','backup')) or n.endswith('.pyc') for n in names))
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
 def test_embycon_patch_queue_has_no_line_ending_churn(self):
  patch=(ROOT/'patches/embycon/0001-customizations.patch').read_text(); files=[line for line in patch.splitlines() if line.startswith('diff --git')]
  self.assertLessEqual(len(files),15); self.assertLess(len(patch.splitlines()),2000)
  self.assertNotIn('\r\n',patch)
if __name__=='__main__': unittest.main()
