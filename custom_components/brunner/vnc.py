"""Minimal, dependency-free RFB (VNC) client for the Brunner touchdisplay.

The Brunner BWP 13 green touchdisplay runs an x11vnc server (RFB 3.8) on the
local network with security type 1 ("None" — no password) and a fixed 640x480
framebuffer. This module speaks just enough of the protocol to:

  * complete the handshake (None auth),
  * request a full framebuffer update in 32bpp truecolour Raw encoding,
  * return the frame as raw RGB bytes, and
  * send pointer (tap) events for screen navigation.

It intentionally has no third-party dependencies so it can run inside Home
Assistant without extra wheels. Pillow is used only by the caller to wrap the
returned RGB buffer into an image for OCR.

NOTE: the panel serves a single controller at a time. Each capture/tap briefly
takes over the local display (as the myBRUNNER cloud session does), so callers
should poll gently.
"""

from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass


@dataclass
class Frame:
    """A captured framebuffer."""

    width: int
    height: int
    rgb: bytes  # width*height*3 bytes, 8-bit R,G,B


class BrunnerVncError(Exception):
    """Raised on any protocol or socket error talking to the display."""


class BrunnerVnc:
    """Blocking RFB client. Open, use, close (or use as a context manager)."""

    def __init__(self, host: str, port: int = 5900, timeout: float = 10.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._sock: socket.socket | None = None
        self.width = 0
        self.height = 0
        self.name = ""

    # -- lifecycle -----------------------------------------------------------
    def __enter__(self) -> "BrunnerVnc":
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def connect(self) -> None:
        try:
            self._sock = socket.create_connection(
                (self._host, self._port), self._timeout
            )
            self._sock.settimeout(self._timeout)
            self._handshake()
        except (OSError, struct.error) as err:  # pragma: no cover - network
            self.close()
            raise BrunnerVncError(str(err)) from err

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    # -- protocol ------------------------------------------------------------
    def _recv(self, n: int) -> bytes:
        assert self._sock is not None
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise BrunnerVncError("connection closed by display")
            buf += chunk
        return bytes(buf)

    def _handshake(self) -> None:
        assert self._sock is not None
        server_ver = self._recv(12)
        if not server_ver.startswith(b"RFB"):
            raise BrunnerVncError(f"not an RFB server: {server_ver!r}")
        self._sock.sendall(b"RFB 003.008\n")

        count = self._recv(1)[0]
        if count == 0:
            reason_len = struct.unpack(">I", self._recv(4))[0]
            raise BrunnerVncError(self._recv(reason_len).decode("latin1"))
        sec_types = list(self._recv(count))
        if 1 not in sec_types:  # 1 == None
            raise BrunnerVncError(f"display requires auth; offered {sec_types}")
        self._sock.sendall(bytes([1]))
        result = struct.unpack(">I", self._recv(4))[0]
        if result != 0:
            raise BrunnerVncError(f"security handshake failed ({result})")

        # ClientInit: shared = 1
        self._sock.sendall(b"\x01")
        hdr = self._recv(24)
        self.width, self.height = struct.unpack(">HH", hdr[:4])
        name_len = struct.unpack(">I", hdr[20:24])[0]
        self.name = self._recv(name_len).decode("latin1")

        # SetPixelFormat: 32bpp, depth 24, little-endian, truecolour BGRA
        self._sock.sendall(
            struct.pack(
                ">Bxxx BBBB HHH BBB xxx",
                0, 32, 24, 0, 1, 255, 255, 255, 16, 8, 0,
            )
        )
        # SetEncodings: Raw(0) only
        self._sock.sendall(struct.pack(">BxH I", 2, 1, 0))

    def capture(self) -> Frame:
        """Request and decode one full framebuffer update (Raw encoding)."""
        assert self._sock is not None
        self._sock.sendall(
            struct.pack(">BBHHHH", 3, 0, 0, 0, self.width, self.height)
        )
        msg_type = self._recv(1)[0]
        if msg_type != 0:  # FramebufferUpdate
            raise BrunnerVncError(f"unexpected server message {msg_type}")
        self._recv(1)  # padding
        nrects = struct.unpack(">H", self._recv(2))[0]
        buf = bytearray(self.width * self.height * 4)
        for _ in range(nrects):
            x, y, rw, rh, enc = struct.unpack(">HHHHi", self._recv(12))
            if enc != 0:
                raise BrunnerVncError(f"unsupported encoding {enc}")
            data = self._recv(rw * rh * 4)
            for row in range(rh):
                dst = ((y + row) * self.width + x) * 4
                src = row * rw * 4
                buf[dst : dst + rw * 4] = data[src : src + rw * 4]
        # BGRA -> RGB
        rgb = bytearray(self.width * self.height * 3)
        for i in range(self.width * self.height):
            rgb[i * 3] = buf[i * 4 + 2]
            rgb[i * 3 + 1] = buf[i * 4 + 1]
            rgb[i * 3 + 2] = buf[i * 4]
        return Frame(self.width, self.height, bytes(rgb))

    def tap(self, x: int, y: int, settle: float = 1.0) -> None:
        """Send a pointer down+up (a tap) at (x, y) and wait for the UI."""
        assert self._sock is not None
        self._sock.sendall(struct.pack(">BBHH", 5, 0, x, y))  # move
        time.sleep(0.03)
        self._sock.sendall(struct.pack(">BBHH", 5, 1, x, y))  # down
        time.sleep(0.05)
        self._sock.sendall(struct.pack(">BBHH", 5, 0, x, y))  # up
        if settle:
            time.sleep(settle)


def tap_once(
    host: str, port: int, x: int, y: int, settle: float = 1.0, timeout: float = 10.0
) -> None:
    """Open a fresh session, send a single tap, close.

    The display's VNC server reliably honours one tap per connection but drops
    taps when many are sent over a single long-lived session, so navigation is
    done one tap at a time.
    """
    with BrunnerVnc(host, port, timeout) as vnc:
        vnc.tap(x, y, settle=settle)


def capture_once(host: str, port: int, timeout: float = 10.0) -> Frame:
    """Open a fresh session, capture one frame, close."""
    with BrunnerVnc(host, port, timeout) as vnc:
        return vnc.capture()
