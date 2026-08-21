"""PRAHARI Multimodal Integration Layer.

This module coordinates non-invasive anemia screening across two distinct modalities:
1. Conjunctival Photograph / Computer Vision Model (from person1/app/ai)
2. Dual-Wavelength Optical PPG / Hardware MAX30102 Model (from ppg-anemia/src/ppg)

SCIENTIFIC PRINCIPLE:
Because no clinically paired dataset exists containing concurrent conjunctival photographs
and MAX30102 PPG signals on the same subject cohort, this coordinator does NOT perform
unvalidated mathematical or probabilistic fusion. Both modality results and their quality
metrics are preserved independently in the structured response.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Resolve workspace root directory (where person1 and ppg-anemia reside)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Ensure person1 and ppg-anemia/src are on sys.path for clean, non-destructive imports
PERSON1_ROOT = WORKSPACE_ROOT / "person1"
PPG_SRC_ROOT = WORKSPACE_ROOT / "ppg-anemia" / "src"

if str(PERSON1_ROOT) not in sys.path:
    sys.path.insert(0, str(PERSON1_ROOT))
if str(PPG_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(PPG_SRC_ROOT))

from integration.schemas import (
    FusionResult,
    ImageModalityResult,
    ModalityError,
    MultimodalScreeningRequest,
    MultimodalScreeningResponse,
    PatientDemographics,
    PPGModalityResult,
)

log = logging.getLogger(__name__)


class MultimodalScreeningEngine:
    """Production coordinator for multimodal anemia screening.
    
    Loads and manages the lifecycle of both the Image (Random Forest)
    and PPG (Lasso Regression) models, invoking their native inference
    pipelines without modifying or duplicating underlying logic.
    """

    def __init__(
        self,
        image_model_path: Optional[Union[str, Path]] = None,
        ppg_model_path: Optional[Union[str, Path]] = None,
        auto_load: bool = True,
    ):
        self.image_model_path = Path(
            image_model_path or (PERSON1_ROOT / "models" / "baseline_classifier.joblib")
        )
        self.ppg_model_path = Path(
            ppg_model_path or (WORKSPACE_ROOT / "ppg-anemia" / "models" / "best_ppg_hb_model.joblib")
        )
        self._image_engine = None
        self._is_loaded = False

        if auto_load:
            self.load()

    def load(self) -> "MultimodalScreeningEngine":
        """Load underlying model artifacts into memory once (idempotent)."""
        if self._is_loaded:
            return self

        # 1. Initialize & load Person 1 Image Inference Engine
        try:
            from app.ai.inference import AnemiaInferenceEngine

            self._image_engine = AnemiaInferenceEngine(model_path=self.image_model_path)
            self._image_engine.load()
            log.info("Image inference engine loaded successfully.")
        except Exception as exc:
            log.error("Failed to load Image inference engine: %s", exc)
            raise RuntimeError(f"Could not load image model from {self.image_model_path}: {exc}") from exc

        # 2. Verify PPG model artifact exists on disk
        if not self.ppg_model_path.exists():
            log.error("PPG model artifact not found at %s", self.ppg_model_path)
            raise FileNotFoundError(f"PPG model artifact not found at {self.ppg_model_path}")

        self._is_loaded = True
        return self

    def _process_image_modality(
        self,
        image_input: Optional[Union[str, Path, bytes, Any]]
    ) -> ImageModalityResult:
        """Run image inference pipeline with robust error and quality gate handling."""
        if image_input is None:
            return ImageModalityResult(
                available=False,
                status="NOT_PROVIDED"
            )

        if not self._is_loaded or self._image_engine is None:
            return ImageModalityResult(
                available=True,
                status="ERROR",
                error=ModalityError(
                    code="MODEL_NOT_LOADED",
                    message="Image inference engine is not loaded."
                )
            )

        try:
            t0 = time.perf_counter()
            result = self._image_engine.analyze(image_input)
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            q_info = result.get("image_quality") or {}
            quality_status = q_info.get("status")
            quality_score = q_info.get("score")
            quality_checks = q_info.get("checks")
            quality_reasons = q_info.get("reasons", [])

            # Check if quality gate rejected the image
            if not result.get("success", False):
                err_dict = result.get("error") or {}
                return ImageModalityResult(
                    available=True,
                    status="REJECTED",
                    quality_status=quality_status or "poor",
                    quality_score=quality_score,
                    quality_checks=quality_checks,
                    quality_reasons=quality_reasons,
                    error=ModalityError(
                        code=err_dict.get("code", "IMAGE_QUALITY_LOW"),
                        message=err_dict.get("message", "Image quality is insufficient for screening.")
                    ),
                    inference_latency_ms=latency_ms
                )

            # Successful inference
            pred = result["prediction"]
            inf_meta = result.get("inference") or {}

            return ImageModalityResult(
                available=True,
                status="SUCCESS",
                label=pred["label"],
                probability=pred["model_probability"],
                confidence=pred["model_confidence"],
                quality_status=quality_status or "good",
                quality_score=quality_score,
                quality_checks=quality_checks,
                quality_reasons=quality_reasons,
                model_name=inf_meta.get("model", self._image_engine.metadata["name"]),
                inference_latency_ms=latency_ms
            )

        except Exception as exc:
            err_code = getattr(exc, "code", type(exc).__name__)
            return ImageModalityResult(
                available=True,
                status="ERROR",
                error=ModalityError(
                    code=err_code,
                    message=str(exc)
                )
            )

    def _process_ppg_modality(
        self,
        ppg_csv_input: Optional[Union[str, Path, Any]],
        age: float = 25.0,
        gender: str = "Male",
        fs: float = 25.0
    ) -> PPGModalityResult:
        """Run PPG hardware inference pipeline with telemetry & quality checks."""
        if ppg_csv_input is None:
            return PPGModalityResult(
                available=False,
                status="NOT_PROVIDED"
            )

        try:
            from ppg.esp32 import predict_esp32_recording

            res = predict_esp32_recording(
                file_path_or_df=ppg_csv_input,
                model_bundle_path=self.ppg_model_path,
                age=age,
                gender=gender,
                fs=fs
            )

            # If signal quality is flagged as POOR, note status
            sig_qual = res.get("signal_quality", "UNKNOWN")
            mod_status = "SUCCESS"

            return PPGModalityResult(
                available=True,
                status=mod_status,
                predicted_hb_g_dl=float(res["predicted_hb_g_dl"]),
                signal_quality=sig_qual,
                sqi=float(res["sqi_score"]),
                sampling_rate_hz=float(res["effective_fs_hz"]),
                samples=int(res["sample_count"]),
                duration_sec=float(res["duration_sec"]),
                feature_count=int(res["feature_count"]),
                model_name=res.get("model_name", "Lasso Regression")
            )

        except Exception as exc:
            err_code = "PPG_VALIDATION_ERROR" if "Validation Error" in str(exc) else "PPG_INFERENCE_ERROR"
            return PPGModalityResult(
                available=True,
                status="ERROR" if "Validation Error" not in str(exc) else "REJECTED",
                error=ModalityError(
                    code=err_code,
                    message=str(exc)
                )
            )

    def screen(
        self,
        request: Union[MultimodalScreeningRequest, Dict[str, Any]],
    ) -> MultimodalScreeningResponse:
        """Execute multimodal screening from a request object or dictionary."""
        t0 = time.perf_counter()

        if isinstance(request, dict):
            req = MultimodalScreeningRequest(**request)
        else:
            req = request

        patient_demo = PatientDemographics(age=req.age, gender=req.gender)

        # Neither modality provided
        if req.image_path is None and req.ppg_csv_path is None:
            return MultimodalScreeningResponse(
                success=False,
                patient=patient_demo,
                image=ImageModalityResult(available=False, status="NOT_PROVIDED"),
                ppg=PPGModalityResult(available=False, status="NOT_PROVIDED"),
                fusion=FusionResult(status="NOT_VALIDATED"),
                execution_time_ms=0.0,
                error=ModalityError(
                    code="NO_MODALITIES_PROVIDED",
                    message="At least one modality (image_path or ppg_csv_path) must be provided."
                )
            )

        # Process each modality independently
        image_result = self._process_image_modality(req.image_path)
        ppg_result = self._process_ppg_modality(
            req.ppg_csv_path,
            age=req.age if req.age is not None else 25.0,
            gender=req.gender or "Male"
        )

        # Determine overall success: at least one modality processed successfully
        at_least_one_success = (
            (image_result.status == "SUCCESS") or (ppg_result.status == "SUCCESS")
        )

        top_error = None
        if not at_least_one_success:
            top_error = ModalityError(
                code="ALL_MODALITIES_FAILED",
                message="All supplied modalities failed processing or quality validation."
            )

        total_exec_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return MultimodalScreeningResponse(
            success=at_least_one_success,
            patient=patient_demo,
            image=image_result,
            ppg=ppg_result,
            fusion=FusionResult(status="NOT_VALIDATED"),
            execution_time_ms=total_exec_ms,
            error=top_error
        )


# Global singleton instance for easy import and usage
_default_engine: Optional[MultimodalScreeningEngine] = None


def get_screening_engine() -> MultimodalScreeningEngine:
    """Retrieve or create the global default MultimodalScreeningEngine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = MultimodalScreeningEngine()
    return _default_engine


def run_multimodal_screening(
    image_path: Optional[Union[str, Path, bytes, Any]] = None,
    ppg_csv_path: Optional[Union[str, Path, Any]] = None,
    age: Optional[float] = 25.0,
    gender: Optional[str] = "Male",
    engine: Optional[MultimodalScreeningEngine] = None,
) -> MultimodalScreeningResponse:
    """Unified entry point for multimodal anemia screening.
    
    Accepts:
        image_path: Path to conjunctival photograph (optional).
        ppg_csv_path: Path to ESP32 PPG CSV recording (optional).
        age: Patient age in years.
        gender: Patient gender ('Male', 'Female', 'Other').
        engine: Optional custom MultimodalScreeningEngine instance.
        
    Returns:
        MultimodalScreeningResponse containing structured image, PPG, and fusion status.
    """
    eng = engine or get_screening_engine()
    req = MultimodalScreeningRequest(
        image_path=str(image_path) if isinstance(image_path, Path) else image_path,
        ppg_csv_path=str(ppg_csv_path) if isinstance(ppg_csv_path, Path) else ppg_csv_path,
        age=age,
        gender=gender
    )
    return eng.screen(req)
