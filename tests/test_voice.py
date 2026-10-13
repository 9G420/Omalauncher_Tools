import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('voice', ROOT/'voice/oma_voice.py')
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)

class VoiceTests(unittest.TestCase):
    def test_follow_and_completion(self):
        previous = voice.CACHE, voice.CONFIG, voice.SESSIONS
        try:
            with tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                voice.CACHE, voice.CONFIG, voice.SESSIONS = base/'cache', base/'config.json', base/'sessions'
                voice.SESSIONS.mkdir()
                def session(text):
                    ident = str(uuid.uuid4())
                    path = voice.SESSIONS/(ident+'.jsonl')
                    path.write_text(json.dumps({'payload': {'id': ident}})+'\n'+json.dumps({'type':'event_msg','timestamp':'2026-10-13T00:00:00Z','payload': {'type':'task_complete','turn_id': str(uuid.uuid4()),'last_agent_message':text}})+'\n')
                    return ident,path
                first,old = session('Old reply')
                reader = voice.Reader()
                reader.bind(first)
                reader.config['auto'] = False
                second,new = session('New reply')
                os.utime(new,(old.stat().st_mtime+10,old.stat().st_mtime+10))
                reader.poll()
                self.assertEqual(reader.config['thread'],second)
                self.assertEqual(reader.state['full'],'New reply')
                self.assertFalse(reader.state['playing'])
                with new.open('a') as f:
                    f.write(json.dumps({'type':'event_msg','payload':{'type':'task_started'}})+'\n')
                reader.poll()
                self.assertTrue(reader.state['awaiting'])
                with new.open('a') as f:
                    f.write(json.dumps({'type':'event_msg','timestamp':'2026-10-13T00:01:00Z','payload':{'type':'task_complete','turn_id':'next','last_agent_message':'Fresh completion'}})+'\n')
                reader.poll()
                self.assertEqual(reader.state['full'],'Fresh completion')
                self.assertFalse(reader.state['awaiting'])
                self.assertIsInstance(reader.state['reply_at'],float)
                reader.command({'action':'refresh'})
                self.assertFalse(reader.state['playing'])
                self.assertEqual(reader.state['full'],'Fresh completion')
        finally:
            voice.CACHE, voice.CONFIG, voice.SESSIONS = previous

    def test_ignores_nonfinal_events(self):
        self.assertIsNone(voice.completed_reply({'type':'event_msg','payload':{'type':'agent_message','message':'interim'}}))
        self.assertIsNone(voice.completed_reply({'type':'event_msg','payload':{'type':'turn_aborted'}}))

    def test_install_and_update_preserve_user_data(self):
        with tempfile.TemporaryDirectory(prefix='voice test ') as directory:
            home = Path(directory)
            config = home/'.config/omalauncher/voice.json'
            config.parent.mkdir(parents=True)
            config.write_text('{"auto":false}')
            env = dict(os.environ, HOME=directory)
            for _ in range(2):
                subprocess.run([sys.executable,str(ROOT/'install.py'),'--skip-deps'],env=env,check=True,stdout=subprocess.DEVNULL)
            self.assertEqual(config.read_text(),'{"auto":false}')
            tile = (home/'.config/omalauncher/widgets/46-speak.owl').read_text()
            self.assertNotIn('__HOME__',tile)
            self.assertNotIn('/root/',tile)
            self.assertIn(directory,tile)
            self.assertTrue(os.access(home/'.local/bin/oma-voice',os.X_OK))
            self.assertTrue(list((home/'.local/share/oma-voice/install-backups').rglob('oma_voice.py')))

if __name__ == '__main__':
    unittest.main()
