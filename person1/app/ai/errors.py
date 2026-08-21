"""Typed errors for the PRAHARI inference engine.

Each error carries a stable ``code`` the API layer can translate into an
HTTP response (e.g. 400 INVALID_IMAGE, 422 IMAGE_QUALITY_LOW, 503
MODEL_NOT_LOADED). The engine raises these for hard failures; quality
rejection is returned as a structured result by ``analyze``.
"""

from __future__ import annotations


class InferenceError(Exception):
    """Base class for all inference errors."""

    code = "INFERENCE_FAILED"
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidImageError(InferenceError):
    code = "INVALID_IMAGE"
    status_code = 400


class ImageTooLargeError(InferenceError):
    code = "IMAGE_TOO_LARGE"
    status_code = 400


class ImageCorruptedError(InferenceError):
    code = "IMAGE_CORRUPTED"
    status_code = 400


class UnsupportedImageError(InferenceError):
    code = "UNSUPPORTED_IMAGE"
    status_code = 415


class ImageQualityLowError(InferenceError):
    """Raised by ``predict`` when the quality gate rejects an image."""

    code = "IMAGE_QUALITY_LOW"
    status_code = 422


class ModelNotLoadedError(InferenceError):
    code = "MODEL_NOT_LOADED"
    status_code = 503


class ModelConfigError(InferenceError):
    code = "MODEL_CONFIG_ERROR"
    status_code = 500
