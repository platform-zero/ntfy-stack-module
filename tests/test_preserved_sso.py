import hashlib,json,os,pathlib,subprocess,tempfile,unittest
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'stack.config/ntfy/init-users.sh'
STUB='''#!/usr/bin/env python3
import os,sys,json,hashlib
args=sys.argv[1:]
with open(os.environ['CALLS'],'a')as f:f.write(json.dumps({'args':args,'passwordSha256':hashlib.sha256(os.environ.get('NTFY_PASSWORD','').encode()).hexdigest()})+'\\n')
if args==['user','list']:
 print('user publisher (role: user)')
 if os.environ.get('EXISTING_SSO')=='1':print('user ntfy-sso (role: user)')
if 'add'in args and os.environ.get('FAIL_CREATE')=='1':sys.exit(17)
'''
class PreservedSso(unittest.TestCase):
 def invoke(self,missing=False,existing=False,failed=False,replay=False):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);(p/'auth.db').touch();(p/'.users_provisioned').touch();(p/'ntfy').write_text(STUB);(p/'ntfy').chmod(0o755)
   if replay:(p/'.sso_user_provisioned').touch()
   env=dict(os.environ,PATH=d+':'+os.environ['PATH'],NTFY_DATA_DIR=d,NTFY_USERNAME='publisher',NTFY_PASSWORD='fixture-publisher-only',NTFY_SSO_PASSWORD=''if missing else'fixture-sso-only',CALLS=str(p/'calls'),EXISTING_SSO='1'if existing else'0',FAIL_CREATE='1'if failed else'0')
   r=subprocess.run(['sh',str(SCRIPT)],env=env,capture_output=True,text=True)
   calls=[json.loads(s)for s in(p/'calls').read_text().splitlines()]if(p/'calls').exists()else[]
   flag=p/'.sso_user_provisioned';return r,calls,flag.exists(),flag.stat().st_mode&0o777 if flag.exists()else None
 def test_initial_add_preserves_publisher(self):
  r,c,f,m=self.invoke();self.assertEqual(r.returncode,0);self.assertTrue(f);self.assertEqual(m,0o600)
  adds=[x for x in c if'add'in x['args']];self.assertEqual(len(adds),1);self.assertEqual(adds[0]['args'],['user','add','--role=user','ntfy-sso']);self.assertEqual(adds[0]['passwordSha256'],hashlib.sha256(b'fixture-sso-only').hexdigest())
  self.assertIn(['access','ntfy-sso','*','read-only'],[x['args']for x in c]);self.assertNotIn('fixture-sso-only',r.stdout+r.stderr)
 def test_replay_does_not_rotate_or_reset_acls(self):
  r,c,f,m=self.invoke(replay=True);self.assertEqual(r.returncode,0);self.assertEqual(c,[])
 def test_missing_secret_refuses(self):
  r,c,f,m=self.invoke(missing=True);self.assertNotEqual(r.returncode,0);self.assertFalse(f);self.assertEqual(c,[])
 def test_unmanaged_existing_identity_preserved(self):
  r,c,f,m=self.invoke(existing=True);self.assertNotEqual(r.returncode,0);self.assertFalse(f);self.assertEqual([x['args']for x in c],[['user','list']])
 def test_creation_failure_does_not_commit_marker(self):
  r,c,f,m=self.invoke(failed=True);self.assertNotEqual(r.returncode,0);self.assertFalse(f);self.assertFalse(any(x['args'][0]=='access'for x in c))
if __name__=='__main__':unittest.main()
