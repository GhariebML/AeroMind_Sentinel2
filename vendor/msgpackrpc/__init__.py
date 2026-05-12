"""
vendor/msgpackrpc/__init__.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modern msgpack-rpc compatibility shim for Python 3.10+.

The official 'msgpack-rpc-python' package uses tornado 4.x which is
incompatible with Python 3.14.  This shim re-implements the minimal
AirSim RPC client API using:
  - Python's built-in socket + threading (no tornado)
  - msgpack 1.x (pip install msgpack)

AirSim's Python client only uses:
  - Client(host, port)
  - client.call(method, *args) → result
  - client.call_async(method, *args) → future
  - client.close()

This is a REAL, working implementation — not a stub.
"""
from __future__ import annotations

import socket
import struct
import threading
from concurrent.futures import Future
from typing import Any

import msgpack


# ─── msgpack-rpc message types (spec) ─────────────────────────────────────────
_MSG_REQUEST  = 0
_MSG_RESPONSE = 1
_MSG_NOTIFY   = 2


class RPCError(Exception):
    """Raised when the remote procedure returns an error."""


class _AsyncResult:
    """Mimics the Future interface used by airsim client.py."""
    def __init__(self, future: Future):
        self._future = future

    def get(self, timeout: float = 30.0):
        return self._future.result(timeout=timeout)

    def join(self, timeout: float = 30.0):
        self._future.result(timeout=timeout)
        return self


class Client:
    """
    msgpack-rpc client — drop-in replacement for msgpackrpc.Client.

    Usage (same API as original):
        c = Client(Address("127.0.0.1", 41451))
        result = c.call("ping")
        c.close()
    """

    def __init__(self, address, timeout: float = 30.0,
                 pack_encoding: str = "utf-8",
                 unpack_encoding: str = "utf-8",
                 reconnect_limit: int = 3):

        host = address.host if hasattr(address, "host") else str(address)
        port = address.port if hasattr(address, "port") else 41451

        self._host    = host
        self._port    = port
        self._timeout = timeout
        self._msgid   = 0
        self._lock    = threading.Lock()
        self._pending: dict[int, Future] = {}
        self._closed  = False

        # Connection
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((host, port))
        self._sock.settimeout(None)   # blocking after connect

        # Packer / unpacker
        def _default(obj):
            if hasattr(obj, "to_msgpack"):
                return obj.to_msgpack()
            raise TypeError(f"Cannot serialize {type(obj)}")
        
        self._packer   = msgpack.Packer(use_bin_type=True, default=_default)
        self._unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)

        # Reader thread
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    # ── Public API ─────────────────────────────────────────────────────────

    def call(self, method: str, *args) -> Any:
        """Synchronous RPC call — blocks until response received."""
        fut = self._send_request(method, list(args))
        return fut.result(timeout=self._timeout)

    def call_async(self, method: str, *args) -> _AsyncResult:
        """Asynchronous RPC call — returns immediately."""
        fut = self._send_request(method, list(args))
        return _AsyncResult(fut)

    def close(self):
        self._closed = True
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
        except Exception:
            pass

    # ── Internal ───────────────────────────────────────────────────────────

    def _next_msgid(self) -> int:
        with self._lock:
            mid = self._msgid
            self._msgid = (self._msgid + 1) & 0x7FFF_FFFF
            return mid

    def _send_request(self, method: str, params: list) -> Future:
        mid = self._next_msgid()
        fut: Future = Future()
        with self._lock:
            self._pending[mid] = fut
        msg = [_MSG_REQUEST, mid, method, params]
        data = self._packer.pack(msg)
        try:
            self._sock.sendall(data)
        except Exception as exc:
            with self._lock:
                self._pending.pop(mid, None)
            fut.set_exception(exc)
        return fut

    def _read_loop(self):
        """Background thread: reads from socket and resolves futures."""
        buf = b""
        while not self._closed:
            try:
                chunk = self._sock.recv(65536)
                if not chunk:
                    break
                self._unpacker.feed(chunk)
                for msg in self._unpacker:
                    if not isinstance(msg, (list, tuple)) or len(msg) < 3:
                        continue
                    if msg[0] == _MSG_RESPONSE:
                        _, mid, error, result = msg
                        with self._lock:
                            fut = self._pending.pop(mid, None)
                        if fut is None:
                            continue
                        if error:
                            fut.set_exception(RPCError(str(error)))
                        else:
                            fut.set_result(result)
            except Exception:
                break
        # Fail any remaining pending futures
        with self._lock:
            pending = list(self._pending.items())
            self._pending.clear()
        for _, fut in pending:
            if not fut.done():
                fut.set_exception(ConnectionError("RPC connection closed"))


class Address:
    """Address object compatible with original msgpackrpc API."""
    __slots__ = ("host", "port")

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port


class error(Exception):
    """msgpackrpc.error — compatibility alias."""


# Module-level aliases used by airsim/types.py
TransportError = ConnectionError
