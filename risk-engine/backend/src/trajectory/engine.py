"""Trajectory engine — risk-band trend over the last ≤5 visits (Hour 7).

The differentiator: catches decline before severity. Risk bands map to
numbers (low=1, moderate=2, high=3, critical=4); the slope over the last
3 points classifies improving / stable / declining / rapidly_declining,
with ``insufficient_data`` when fewer than 2 visits exist. Also implements
the early-intervention rule (2 consecutive visits trending toward a higher
band → auto-escalate).
"""

from __future__ import annotations

RISK_BAND_TO_NUMERIC = {"low": 1, "moderate": 2, "high": 3, "critical": 4}


def compute(visits: list[dict]) -> dict:
    """Return ``{"trajectory": str, "early_intervention": bool}``.

    Args:
        visits: List of visit dicts ordered by date (most recent last),
                each containing at minimum {"overall_priority": str}.

    Returns:
        Dict with keys:
        - trajectory: One of improving/stable/declining/rapidly_declining/insufficient_data
        - early_intervention: True if 2 consecutive visits trend toward higher risk band
    """
    if len(visits) < 2:
        return {"trajectory": "insufficient_data", "early_intervention": False}

    # Take last 5 visits only
    recent_visits = visits[-5:]

    # Map risk bands to numeric values
    risk_values = []
    for v in recent_visits:
        priority = v.get("overall_priority", "low")
        risk_values.append(RISK_BAND_TO_NUMERIC.get(priority, 1))

    # Early intervention rule: check last 2 consecutive visits
    early_intervention = False
    if len(risk_values) >= 2:
        # If last 2 visits show increasing risk (each higher than previous)
        if risk_values[-1] > risk_values[-2]:
            early_intervention = True

    # Calculate slope over last 3 points (or all if fewer than 3)
    if len(risk_values) < 3:
        points = risk_values
    else:
        points = risk_values[-3:]

    if len(points) < 2:
        return {"trajectory": "insufficient_data", "early_intervention": early_intervention}

    # Slope = (last - first) / (n - 1)
    slope = (points[-1] - points[0]) / (len(points) - 1)

    # Classify trajectory based on slope thresholds
    if slope > 0.5:
        trajectory = "rapidly_declining"
    elif slope > 0.1:
        trajectory = "declining"
    elif slope < -0.1:
        trajectory = "improving"
    else:
        trajectory = "stable"

    return {"trajectory": trajectory, "early_intervention": early_intervention}
