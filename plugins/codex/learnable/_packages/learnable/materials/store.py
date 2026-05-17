from __future__ import annotations

from typing import Optional, Protocol, Union, runtime_checkable


SourceRefs = Optional[list[Union[str, dict[str, object]]]]


@runtime_checkable
class MaterialStore(Protocol):
    """Narrow material persistence API used by Learnable web handlers."""

    def init(self) -> None: ...

    def create_session(
        self,
        title: str,
        prompt: str,
        markdown: str,
        provenance: dict[str, object],
        source_refs: SourceRefs = None,
    ) -> dict[str, object]: ...

    def add_child(
        self,
        learnable_session_id: str,
        parent_node_id: str,
        title: str,
        prompt: str,
        markdown: str,
        provenance: dict[str, object],
        source_refs: SourceRefs = None,
    ) -> dict[str, object]: ...

    def load_tree(self, learnable_session_id: str) -> dict[str, object]: ...

    def load_node(
        self, learnable_session_id: str, node_id: str
    ) -> tuple[dict[str, object], str]: ...

    def list_sessions(self) -> list[dict[str, object]]: ...
