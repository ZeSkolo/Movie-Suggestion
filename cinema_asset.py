"""Read the original cinema artwork from lossless text-only source parts."""
import base64
import hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent
PART_COUNT = 10
EXPECTED_SHA256 = '0dc75f364a92638bd57a3e645e9deb3990f228f4e4566954c56ac12c652b956d'

def read_cinema():
    encoded = ''.join((ROOT / 'cinema-parts' / f'{i:03}.b64').read_text().strip() for i in range(1, PART_COUNT + 1))
    data = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Cinema artwork checksum mismatch; restore all source parts.')
    return data
