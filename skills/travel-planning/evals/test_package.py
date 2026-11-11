"""Package integrity checks, not host discovery or agent behavior tests."""
import ast,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PackageTests(unittest.TestCase):
 def test_metadata(self):
  s=(ROOT/'SKILL.md').read_text();self.assertTrue(s.startswith('---\n'));head=s.split('---',2)[1]
  self.assertIn('name: '+ROOT.name,head)
  d=re.search(r'^description: (.+)$',head,re.M).group(1);self.assertTrue(d.startswith('Use when'));self.assertLessEqual(len(d),1024)
 def test_relative_links(self):
  for p in ROOT.rglob('*.md'):
   text=re.sub(r'```.*?```','',p.read_text(),flags=re.S)
   for dest in re.findall(r'\]\(([^)]+)\)',text):
    if '://' in dest or dest.startswith('#'):continue
    self.assertTrue((p.parent/dest.split('#')[0]).exists(),f'{p.name}: {dest}')
 def test_no_private_markers(self):
  for p in ROOT.rglob('*'):
   if p.is_file() and p.suffix in {'.md','.json'}:
    text=p.read_text();self.assertNotRegex(text,r'https://chatgpt\.com/space/page_[0-9a-f]+|sk-proj-[A-Za-z0-9]{12,}|/mnt/data/|user-[A-Za-z0-9]{16,}')
 def test_synthetic_fixture(self):
  p=json.loads((ROOT/'assets/synthetic-trip.json').read_text());self.assertIs(p['synthetic'],True);self.assertEqual(p['schema_version'],1)
 def test_license(self):self.assertIn('MIT License',(ROOT/'LICENSE').read_text())
 def test_standard_library_only(self):
  tree=ast.parse((ROOT/'scripts/check_trip.py').read_text());allowed={'argparse','json','math','datetime','decimal','pathlib'}
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):self.assertTrue(all(a.name.split('.')[0] in allowed for a in n.names))
   if isinstance(n,ast.ImportFrom):self.assertIn(n.module.split('.')[0],allowed)
if __name__=='__main__':unittest.main(verbosity=2)
