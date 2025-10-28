"""Infrastructure helper for batching shared control access.

This module provides :class:`SharedControlsService`, a lightweight adapter over
``multiprocessing.Manager``-backed dictionaries. It snapshots the shared state
once per iteration and records mutations so they can be flushed back to the
Manager with a single ``update`` call.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Mapping, MutableMapping, Optional, Set


class SharedControlsService:
    """Cache accesses and batch mutations to a shared controls mapping."""

    __slots__ = ("_source", "_cache", "_updates", "_removals")

    def __init__(self, shared_controls: Optional[MutableMapping[str, Any]]):
        self._source: Optional[MutableMapping[str, Any]] = shared_controls
        self._updates: Dict[str, Any] = {}
        self._removals: Set[str] = set()
        self._cache: Dict[str, Any] = {}
        if shared_controls is None:
            return

        snapshot: Optional[Dict[str, Any]] = None
        if hasattr(shared_controls, "items"):
            try:
                snapshot = dict(shared_controls.items())
            except Exception:  # pragma: no cover - defensive fallback
                snapshot = None
        if snapshot is None:
            try:
                snapshot = dict(shared_controls)
            except Exception:  # pragma: no cover - defensive fallback
                snapshot = {}
        self._cache = snapshot

    # Mapping-like helpers -------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if self._cache.get(key) != value:
            self._cache[key] = value
            self._updates[key] = value
            self._removals.discard(key)

    def pop(self, key: str, default: Any = None) -> Any:
        if key in self._cache:
            value = self._cache.pop(key)
            self._updates.pop(key, None)
            self._removals.add(key)
            return value
        return default

    def update(self, other: Mapping[str, Any]) -> None:
        for key, value in dict(other).items():
            self.__setitem__(key, value)

    def __contains__(self, key: object) -> bool:  # type: ignore[override]
        return key in self._cache

    def items(self) -> Iterable[tuple[str, Any]]:
        return self._cache.items()

    def keys(self) -> Iterable[str]:
        return self._cache.keys()

    def __iter__(self) -> Iterator[str]:
        return iter(self._cache)

    def __len__(self) -> int:
        return len(self._cache)

    # Commit ----------------------------------------------------------------
    def apply(self) -> None:
        if self._source is None:
            return
        if self._updates:
            self._source.update(self._updates)
        if self._removals:
            for key in self._removals:
                self._source.pop(key, None)

    def __enter__(self) -> "SharedControlsService":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.apply()
        return False
