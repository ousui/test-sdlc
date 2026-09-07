"""Generate original test WAV/PNG, not an artist recording or photograph."""
from pathlib import Path
import math,struct,wave,zlib
out=Path('sample-media');out.mkdir(exist_ok=True)
with wave.open(str(out/'generated-tone.wav'),'wb') as audio:
 audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(8000)
 audio.writeframes(b''.join(struct.pack('<h',int(2500*math.sin(2*math.pi*440*i/8000))) for i in range(4000)))
def chunk(kind,data):
 return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
pixels=b''.join(b'\0'+b'\x8f\x64\xab'*64 for _ in range(64))
(out/'generated-swatch.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',64,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
print('Created original test tone and color swatch in sample-media/. Upload through the administrator forms.')
