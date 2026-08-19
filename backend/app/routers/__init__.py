from .beneficiaries import router as beneficiaries_router
from .screenings import router as screenings_router
from .measurements import router as measurements_router
from .results import router as results_router
from .followups import router as followups_router
from .history import router as history_router

__all__ = [
    "beneficiaries_router",
    "screenings_router",
    "measurements_router",
    "results_router",
    "followups_router",
    "history_router",
]