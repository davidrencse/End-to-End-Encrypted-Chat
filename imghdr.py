"""
Minimal imghdr shim for Python 3.13+ where the stdlib module was removed.
Only implements imghdr.what used by PGPy; returns None if unknown.
"""

from typing import Optional


def what(file: Optional[str] = None, h: Optional[bytes] = None) -> Optional[str]:
    if h is None and file is not None:
        try:
            with open(file, "rb") as f:
                h = f.read(32)
        except OSError:
            return None
    if not h:
        return None
    if h.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if h.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if h.startswith(b"GIF87a") or h.startswith(b"GIF89a"):
        return "gif"
    if h.startswith(b"BM"):
        return "bmp"
    return None
