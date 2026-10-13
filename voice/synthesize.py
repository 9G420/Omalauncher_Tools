"""Edge TTS without API keys; local Piper/Sherpa fallback. Reads text on stdin."""
import asyncio
import json
import os
import subprocess
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).parent

def offline(text, output):
    runtime = ROOT / 'tts/sherpa-onnx-v1.13.8-linux-aarch64-shared-cpu/bin/sherpa-onnx-offline-tts'
    model = ROOT / 'tts/vits-piper-zh_CN-huayan-medium'
    if runtime.exists() and (model / 'zh_CN-huayan-medium.onnx').exists():
        Path(str(output)+'.backend').write_text('離線神經語音')
        os.execv(str(runtime), [str(runtime), '--vits-model='+str(model/'zh_CN-huayan-medium.onnx'),
                 '--vits-tokens='+str(model/'tokens.txt'), '--vits-data-dir='+str(model/'espeak-ng-data'),
                 '--num-threads=2', '--output-filename='+str(output), '--', text])
    Path(str(output)+'.backend').write_text('離線基本語音')
    os.execvp('espeak-ng', ['espeak-ng', '-v', 'cmn', '-s', '175', '-w', str(output), '--', text])

async def online(text, output):
    import edge_tts
    mp3 = output.with_suffix('.mp3')
    try:
        voice = 'zh-CN-XiaoxiaoNeural' if any('\u3400' <= c <= '\u9fff' for c in text) else 'en-US-AriaNeural'
        await asyncio.wait_for(edge_tts.Communicate(text, voice=voice, rate='-5%').save(str(mp3)), timeout=25)
        if not shutil.which('mpg123'):
            raise RuntimeError('mpg123 is required for online speech')
        subprocess.run(['mpg123', '-q', '-w', str(output), str(mp3)], check=True, timeout=30)
        Path(str(output)+'.backend').write_text('自然語音（線上）')
    finally:
        mp3.unlink(missing_ok=True)

if __name__ == '__main__':
    output = Path(sys.argv[1])
    text = sys.stdin.read().strip()
    if not text:
        raise SystemExit('沒有可播放的文字')
    config = json.loads((Path.home()/'.config/omalauncher/voice.json').read_text())
    if config.get('engine') != 'offline':
        try:
            asyncio.run(online(text, output))
            raise SystemExit(0)
        except Exception as error:
            print('線上語音暫時不可用，改用離線：'+type(error).__name__, file=sys.stderr)
            output.unlink(missing_ok=True)
    offline(text, output)
