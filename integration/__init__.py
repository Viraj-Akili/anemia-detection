"""PRAHARI Multimodal Integration Package.

Provides a unified, non-destructive integration layer for:
- Conjunctival image-based anemia screening (person1)
- MAX30102 dual-wavelength optical PPG hardware pipeline (ppg-anemia)

Exports:
- run_multimodal_screening
- MultimodalScreeningEngine
- MultimodalScreeningRequest
- MultimodalScreeningResponse
- ImageModalityResult
- PPGModalityResult
- FusionResult
"""

from integration.schemas import (
    MultimodalScreeningRequest,
    MultimodalScreeningResponse,
    ImageModalityResult,
    PPGModalityResult,
    FusionResult,
    PatientDemographics,
    ModalityError,
)
from integration.multimodal import (
    MultimodalScreeningEngine,
    get_screening_engine,
    run_multimodal_screening,
)

__all__ = [
    "MultimodalScreeningEngine",
    "MultimodalScreeningRequest",
    "MultimodalScreeningResponse",
    "ImageModalityResult",
    "PPGModalityResult",
    "FusionResult",
    "PatientDemographics",
    "ModalityError",
    "get_screening_engine",
    "run_multimodal_screening",
]
