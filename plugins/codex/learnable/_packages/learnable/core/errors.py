from __future__ import annotations


class LearnableError(Exception):
    """Base exception for Learnable public API failures."""


class PathBoundaryError(LearnableError):
    """Raised when a path resolves outside its allowed root."""


class DeniedPathError(LearnableError):
    """Raised when a path looks too sensitive for Learnable material handling."""
