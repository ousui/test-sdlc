#!/usr/bin/env python3
"""Generate only original sine audio and a simple colored square."""
import argparse
import math
from pathlib import Path
import struct
import wave
import zlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with wave.open(str(args.output / 'generated-tone.wav'), 'wb') as sound:
        sound.setparams((1, 2, 8000, 16000, 'NONE', 'not compressed'))
        sound.writeframes(b''.join(struct.pack('<h', int(5000 * math.sin(2 * math.pi * 440 * n / 8000))) for n in range(16000)))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    rows = b''.join(b'\x00' + bytes((120, 40, 90)) * 32 for _ in range(32))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 32, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')
    (args.output / 'generated-swatch.png').write_bytes(png)
    print('Created original tone and color square; no artist media.')


if __name__ == '__main__':
    main()
