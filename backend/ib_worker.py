"""
OptionsIQ — IB Worker Thread

Single ib_insync IB() instance isolated in a dedicated daemon thread.
Flask routes NEVER touch ib_insync directly — all IBKR calls go through submit().

Why: ib_insync uses asyncio internally. Calling from multiple Flask threads
causes event-loop conflicts. One thread = one IB() = safe.
"""
from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)


class _Stop:
    """Sentinel to shut down the worker loop."""


class _Request:
    __slots__ = ("fn", "args", "kwargs", "result_q")

    def __init__(self, fn: Callable, args: tuple, kwargs: dict) -> None:
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.result_q: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)


class IBWorker:
    """
    Single-thread IB() owner. All IBKR calls are serialised through this worker.

    Usage:
        worker = IBWorker()
        price = worker.submit(worker.provider.get_underlying_price, "AAPL", timeout=10)
    """

    def __init__(self) -> None:
        self._req_queue: queue.Queue[_Request | _Stop] = queue.Queue()
        self._provider = None  # IBKRProvider — created inside worker thread
        self._init_error: str | None = None
        self._ready = threading.Event()

        self._thread = threading.Thread(
            target=self._run, daemon=True, name="ib-worker"
        )
        self._thread.start()
        # Wait up to 8 s for provider init (ib_insync import can be slow)
        self._ready.wait(timeout=8.0)

    # ─── Worker thread ───────────────────────────────────────────────────────

    def _run(self) -> None:
        """Owns the IB() instance and processes all submitted requests."""
        try:
            import asyncio

            # ib_insync uses asyncio internally; each thread needs its own event loop.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            from ibkr_provider import IBKRProvider

            self._provider = IBKRProvider()
            logger.info("IBWorker: IBKRProvider ready")
        except Exception as exc:
            self._init_error = f"{type(exc).__name__}: {exc}"
            logger.warning("IBWorker: provider init failed — %s", self._init_error)
        finally:
            self._ready.set()

        while True:
            req = self._req_queue.get()
            if isinstance(req, _Stop):
                logger.info("IBWorker: shutting down")
                break
            try:
                result = req.fn(*req.args, **req.kwargs)
                req.result_q.put(("ok", result))
            except Exception as exc:
                req.result_q.put(("err", exc))

    # ─── Public API ──────────────────────────────────────────────────────────

    def submit(self, fn: Callable, *args: Any, timeout: float = 30.0, **kwargs: Any) -> Any:
        """
        Run *fn* in the worker thread. Blocks until done or timeout.
        Raises TimeoutError on timeout; re-raises provider exceptions.
        """
        req = _Request(fn, args, kwargs)
        self._req_queue.put(req)
        try:
            status, value = req.result_q.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f"IBWorker timed out after {timeout}s")
        if status == "err":
            raise value
        return value

    @property
    def provider(self):
        """The IBKRProvider instance (may be None if init failed)."""
        return self._provider

    @property
    def init_error(self) -> str | None:
        return self._init_error

    def is_connected(self) -> bool:
        if self._provider is None:
            return False
        try:
            return bool(self._provider.is_connected())
        except Exception:
            return False

    def stop(self) -> None:
        """Gracefully shut down the worker thread."""
        self._req_queue.put(_Stop())
