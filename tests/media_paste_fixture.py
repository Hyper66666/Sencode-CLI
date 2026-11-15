"""Screenshot-shaped local media selection using real system-decoded video frames."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
from clipboard_attachment_fixture import png


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('probe', type=Path)
    parser.add_argument('video', type=Path)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    probe = args.probe.resolve()
    scratch = Path(tempfile.mkdtemp(prefix='sencode-media-中文-'))
    generated = []
    video = scratch / '产品示范.mp4'
    first, second = scratch / 'first picture.png', scratch / '第二张.png'
    bad = scratch / 'bad.mp4'
    try:
        video.write_bytes(args.video.read_bytes())
        first.write_bytes(png())
        second.write_bytes(png())
        bad.write_bytes(b'not a video')
        sources = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (video, first, second, bad)}

        def parse(text):
            p = subprocess.run([str(probe), '--cwd', str(scratch), '--prompt', text], capture_output=True, timeout=150)
            assert p.returncode == 0, (p.stdout, p.stderr)
            result = json.loads(p.stdout.decode('utf-8-sig'))
            generated.extend(result.get('generated', []))
            return result

        task = '这是产品设计，请参照视频和图片优化前端ui'
        result = parse(f'"{video}""{first}""{second}"{task}')
        assert result['matched'] and not result['blocked'] and len(result['paths']) == 5, result
        assert task in result['text'] and 'no audio' in result['text']
        assert '0 ms' in result['text'] and '1500 ms' in result['text'] and '2900 ms' in result['text']
        assert os.path.samefile(result['paths'][3], first) and os.path.samefile(result['paths'][4], second)
        for index, value in enumerate(result['paths'][:3]):
            frame = Path(value)
            assert frame.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
            assert not frame.is_relative_to(scratch)
            with Image.open(frame) as image:
                r, g, b = image.convert('RGB').getpixel((image.width // 2, image.height // 2))
                channels = [r, g, b]
                assert channels[index] > 180 and sum(channels) - channels[index] < 70, channels
        failures = [f'"{bad}""{first}"{task}', f'"{video}""{scratch / "missing.jpg"}"{task}',
                    ''.join([f'"{video}"'] * 3) + task]
        for text in failures:
            rejected = parse(text)
            assert not rejected['matched'] and rejected['blocked'] and not rejected['paths']
            assert rejected['text'] == text and rejected['status']
        prose = f'please inspect "{video}" and "{first}"'
        ordinary = parse(prose)
        assert not ordinary['matched'] and not ordinary['blocked'] and ordinary['text'] == prose
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in sources.items())
        assert set(scratch.iterdir()) == set(sources)
        evidence = {'result': 'passed', 'checks': ['adjacent-video-and-two-images-with-Chinese-task',
                    'three-real-red-green-blue-PNGs-with-actual-timestamps', 'malformed-missing-and-budget-rejection-retain-text',
                    'ordinary-prose-is-not-read', 'original-bytes-and-project-directory-unchanged'],
                    'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest()}
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2), encoding='utf8')
        print(json.dumps(evidence))
    finally:
        for entry in generated:
            directory = Path(entry['temporary_directory'])
            assert directory.name.startswith('SencodeCLI-video-') and directory.parent == Path(tempfile.gettempdir())
            for index, value in enumerate(entry['paths']):
                path = Path(value)
                assert path == directory / f'frame{index}.png' and not path.is_symlink()
                if path.exists():
                    path.unlink()
            directory.rmdir()
        for path in (video, first, second, bad):
            if path.exists():
                path.unlink()
        scratch.rmdir()


if __name__ == '__main__':
    main()
