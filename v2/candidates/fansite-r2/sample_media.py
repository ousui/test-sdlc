#!/usr/bin/env python3
"""Create original test media without artist recordings, photos or dependencies."""
import argparse
import math
from pathlib import Path
import struct
import wave
import zlib


def create(output):
    output.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output / 'generated-tone.wav'), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b''.join(struct.pack('<h', int(6000 * math.sin(2 * math.pi * 440 * i / 8000))) for i in range(16000)))
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    pixels = b''.join(b'\x00' + bytes((118, 63 + row * 2, 98)) * 32 for row in range(32))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 32, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')
    (output / 'generated-swatch.png').write_bytes(png)
    print('Created original 440 Hz PCM WAV and 32 x 32 PNG swatch.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('sample-media'))
    create(parser.parse_args().output)
