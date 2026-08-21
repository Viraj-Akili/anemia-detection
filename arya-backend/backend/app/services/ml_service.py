"""ML inference execution service for Image/CV and Optical PPG models."""

from __future__ import annotations

import io
import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Ensure sibling directories (integration, person1, ppg-anemia) are on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(WORKSPACE_ROOT / "person1") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "person1"))
if str(WORKSPACE_ROOT / "ppg-anemia" / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "ppg-anemia" / "src"))

# Unify app namespace with person1/app so app.ai can be resolved without collision
try:
    import app as arya_app
    person1_app_path = str(WORKSPACE_ROOT / "person1" / "app")
    if person1_app_path not in arya_app.__path__:
        arya_app.__path__.append(person1_app_path)
except Exception as exc:
    logger.warning(f"Namespace unification notice: {exc}")

try:
    from integration.schemas import (
        MultimodalScreeningRequest,
        MultimodalScreeningResponse,
        PatientDemographics,
        ImageModalityResult,
        PPGModalityResult,
        FusionResult,
    )
    from integration.multimodal import MultimodalScreeningEngine
except ImportError as exc:
    logger.error(f"Failed to import integration layer: {exc}")
    raise


class MLService:
    """Service wrapper for executing Image and PPG ML models via the integration coordinator."""

    def __init__(self):
        self.engine = MultimodalScreeningEngine(
            auto_load=True,
        )

    def evaluate_modalities(
        self,
        *,
        patient_id: Optional[str] = None,
        age_years: float,
        gender: str,
        is_pregnant: bool = False,
        trimester: Optional[int] = None,
        image_bytes: Optional[bytes] = None,
        ppg_csv_text: Optional[str] = None,
    ) -> MultimodalScreeningResponse:
        """Run multimodal screening on supplied patient image and/or PPG data.

        Preserves independent modality outputs without mathematical fusion.
        """
        t0 = time.perf_counter()
        patient_demo = PatientDemographics(
            age=float(age_years),
            gender=gender,
        )

        image_input = image_bytes if image_bytes else None

        ppg_input = None
        if ppg_csv_text is not None:
            try:
                import pandas as pd
                ppg_input = pd.read_csv(io.StringIO(ppg_csv_text))
            except Exception:
                # If unparseable, pass raw text or empty DF so error handling catches it
                ppg_input = ppg_csv_text

        image_result = self.engine._process_image_modality(image_input)
        ppg_result = self.engine._process_ppg_modality(
            ppg_input,
            age=float(age_years),
            gender=gender,
        )

        at_least_one_success = (
            (image_result.status == "SUCCESS") or (ppg_result.status == "SUCCESS")
        )

        total_exec_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return MultimodalScreeningResponse(
            success=at_least_one_success,
            patient=patient_demo,
            image=image_result,
            ppg=ppg_result,
            fusion=FusionResult(status="NOT_VALIDATED"),
            execution_time_ms=total_exec_ms,
        )


# Singleton instance
ml_service = MLService()
