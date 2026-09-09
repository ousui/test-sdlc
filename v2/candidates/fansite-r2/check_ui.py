#!/usr/bin/env python3
"""Check the agreed frontend/source contract and generated media, not subjective UX."""
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import wave
import zlib

ROOT = Path(__file__).resolve().parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.sections = set()
        self.links = set()
        self.scripts = []
        self.forms = {}
        self.current = None
        self.controls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'data-section' in attrs:
            self.sections.add(attrs['data-section'])
        if tag == 'a':
            self.links.add(attrs.get('href'))
        if tag == 'script':
            self.scripts.append(attrs.get('src'))
        if tag == 'form':
            self.current = attrs.get('id')
            self.forms[self.current] = {'action': attrs.get('action'), 'method': attrs.get('method'), 'fields': set()}
        if self.current and tag in {'input', 'textarea', 'select'}:
            self.forms[self.current]['fields'].add(attrs.get('name'))
        if tag == 'input' and attrs.get('type') == 'file':
            self.controls.append(attrs.get('accept', ''))

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current = None


def main():
    raw = (ROOT / 'web/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'web/app.js').read_text(encoding='utf-8')
    page = Page()
    page.feed(raw)
    assert len(page.ids) == len(set(page.ids)), 'duplicate HTML IDs'
    assert page.sections == {'home', 'music', 'albums', 'login', 'register', 'profile', 'admin'}
    assert {'/', '/music', '/albums', '/login', '/register', '/profile', '/admin'} <= page.links
    assert page.scripts == ['/assets/app.js'], 'frontend scripts must be local and native'
    expected = {
        'register-form': ('/api/register', {'Email', 'Password', 'Name'}),
        'login-form': ('/api/login', {'Email', 'Password'}),
        'profile-form': ('/api/me', {'Name', 'Bio'}),
        'site-form': ('/api/admin/site', {'Title', 'Intro'}),
        'track-form': ('/api/admin/tracks', {'ID', 'Title', 'Published', 'Audio'}),
        'album-form': ('/api/admin/albums', {'ID', 'Title', 'Published', 'Description'}),
        'photo-form': ('/api/admin/photos', {'Album', 'Caption', 'Data'}),
    }
    for name, (endpoint, fields) in expected.items():
        assert page.forms[name] == {'action': endpoint, 'method': 'post', 'fields': fields}, name
        assert name in js, 'form has no JS binding: ' + name
    assert '非官方' in raw and '自产' in raw
    assert 'jQuery' not in js and 'innerHTML' not in js and 'textContent' in js
    assert 'fetch(' in js and 'X-CSRF-Token' in js
    assert 'controls = true' in js and 'image.alt' in js, 'missing playable audio or image labels'
    for endpoint in ['/api/session', '/api/logout', '/api/tracks', '/api/albums', '/api/admin/users', '/api/admin/content', '/api/admin/user-state', '/api/admin/delete']:
        assert endpoint in js, endpoint
    refs = set(re.findall(r"byId\('([^']+)'\)", js))
    assert refs <= set(page.ids), 'JS refers to missing HTML nodes'
    test_bytes = (ROOT / 'site_test.go').read_bytes()
    # Q2 authorizes this exact transport-helper span only; all other original bytes stay frozen.
    helper_start, helper_end = 1150, 2472
    assert hashlib.sha256(test_bytes[helper_start:helper_end]).hexdigest() == '5c09fe04b71db4a6ec6317ccb8103dcbffadd985eee7ad744b14cd15ea7c7f8f', 'approved Q2 transport helper changed'
    original_helper = b'func(c *client) post(path string,in any,code int)*httptest.ResponseRecorder{w:=c.request("POST",path,in,nil);c.expect(w,code);return w}\n'
    normalized_test_bytes = test_bytes[:helper_start] + original_helper + test_bytes[helper_end:]
    assert hashlib.sha256(normalized_test_bytes).hexdigest() == '067531f845ee51b9da5fe88cf90644369c5e20829a1a4c6853e61169d69328cc', 'original 24 assertions changed'
    tests = re.findall(rb'^func (Test\w+)\(', test_bytes, re.M)
    assert len(tests) == len(set(tests)) == 24
    vendor = ROOT / 'vendor/golang.org/x/crypto'
    assert hashlib.sha256((vendor / 'pbkdf2/pbkdf2.go').read_bytes()).hexdigest() == 'f46c5590b983ffae1d37e9a1a9cbfb47b2bcf4339cd7e7782d01f9e501e2cf17'
    assert (vendor / 'LICENSE').read_text().strip() and 'PBKDF2' in (ROOT / 'SOURCE.md').read_text()
    readme = (ROOT / 'README.md').read_text()
    for marker in ['go test -count=1 -v ./...', 'node --check web/app.js', 'FAN_ADMIN_PASSWORD', 'sample_media.py']:
        assert marker in readme, marker
    work = ROOT / '.check-work'
    work.mkdir(exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=work) as directory:
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'sample_media.py'), '--output', directory], capture_output=True, text=True, timeout=20)
            assert result.returncode == 0, result.stderr
            with wave.open(str(Path(directory) / 'generated-tone.wav'), 'rb') as sound:
                assert (sound.getnchannels(), sound.getsampwidth(), sound.getframerate(), sound.getnframes()) == (1, 2, 8000, 16000)
                assert any(sound.readframes(16000)), 'silent placeholder audio'
            image = (Path(directory) / 'generated-swatch.png').read_bytes()
            assert image[:8] == b'\x89PNG\r\n\x1a\n'
            assert struct.unpack('>II', image[16:24]) == (32, 32)
            offset = 8
            while offset < len(image):
                size = struct.unpack('>I', image[offset:offset + 4])[0]
                part = image[offset + 4:offset + 8 + size]
                crc = struct.unpack('>I', image[offset + 8 + size:offset + 12 + size])[0]
                assert zlib.crc32(part) & 0xffffffff == crc
                offset += size + 12
            assert offset == len(image)
    finally:
        work.rmdir()
    print('PASS: original 24 test identities/bytes; 7 page sections and 7 connected forms; native JS contracts; licensed vendor; generated WAV/PNG; usage instructions.')


if __name__ == '__main__':
    main()
