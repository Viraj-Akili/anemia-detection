"""Integration tests for POST /api/screening/analyze.

Tests the full screening pipeline end-to-end: request validation, pipeline
execution, response contract compliance, error handling, and latency benchmarks.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from models.database import SessionLocal, engine
from models.entities import Base, Beneficiary, Visit
from models.schemas import OverallPriority, RecommendedAction, RiskBand, Trajectory

# Test client
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create tables and seed test beneficiary."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean up existing test data
    db.query(Beneficiary).filter(Beneficiary.id == "B001").delete()

    # Create test beneficiary
    beneficiary = Beneficiary(
        id="B001",
        name="Test Child",
        age_months=36,
        sex="female",
        pregnancy=False,
    )
    db.add(beneficiary)
    db.commit()
    db.close()

    yield

    # Cleanup after tests
    db = SessionLocal()
    db.query(Beneficiary).filter(Beneficiary.id == "B001").delete()
    db.commit()
    db.close()


class TestScreeningEndpoint:
    """Integration tests for the screening endpoint."""

    def test_exact_example_payload_from_prompt(self):
        """The exact example payload from the prompt returns valid response."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Assert every field from Appendix A contract is present and typed correctly
        assert "anemia_risk" in data
        assert data["anemia_risk"] in ["low", "moderate", "high"]

        assert "nutrition_risk" in data
        assert data["nutrition_risk"] in ["low", "moderate", "high"]

        assert "overall_priority" in data
        assert data["overall_priority"] in ["low", "moderate", "high", "critical"]

        assert "confidence" in data
        assert isinstance(data["confidence"], float)
        assert 0.0 <= data["confidence"] <= 1.0

        assert "trajectory" in data
        assert data["trajectory"] in [
            "improving", "stable", "declining", "rapidly_declining", "insufficient_data"
        ]

        assert "contributors" in data
        assert isinstance(data["contributors"], list)

        assert "recommended_action" in data
        assert data["recommended_action"] in [
            "routine_monitoring",
            "nutrition_counselling",
            "confirmatory_testing",
            "immediate_referral",
            "manual_protocol_escalation",
        ]

        assert "safety_flags" in data
        assert isinstance(data["safety_flags"], list)

    def test_full_request_with_all_fields(self):
        """Full request with all optional fields returns valid response."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "high", "confidence": 0.91},
            "weight": 12.5,
            "height": 95.0,
            "muac": 11.8,
            "diet": {
                "iron_rich_food": True,
                "frequency": "often",
                "diversity": 7,
            },
            "pregnancy": False,
            "ifa": {"adherence": "good"},
            "symptoms": {
                "severe_pallor": True,
                "breathlessness": False,
                "bilateral_oedema": False,
                "fatigue": True,
            },
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have all required fields
        assert all(
            field in data
            for field in [
                "anemia_risk",
                "nutrition_risk",
                "overall_priority",
                "confidence",
                "trajectory",
                "contributors",
                "recommended_action",
                "safety_flags",
            ]
        )

    def test_contributors_structure(self):
        """Contributors list has correct structure."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)
        data = response.json()

        contributors = data["contributors"]
        if len(contributors) > 0:
            # Each contributor should have feature, label, importance
            contributor = contributors[0]
            assert "feature" in contributor
            assert "label" in contributor
            assert "importance" in contributor
            assert isinstance(contributor["feature"], str)
            assert isinstance(contributor["label"], str)
            assert isinstance(contributor["importance"], float)
            assert -1.0 <= contributor["importance"] <= 1.0

    def test_unknown_beneficiary_returns_404(self):
        """Unknown beneficiary ID returns 404."""
        payload = {
            "beneficiary_id": "UNKNOWN_ID",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Unknown beneficiary" in response.json()["detail"]

    def test_invalid_anthropometry_returns_422(self):
        """Invalid anthropometry measurements return 422."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": -5.0,  # Invalid: negative weight
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_required_field_returns_422(self):
        """Missing required field in request returns 422."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            # Missing weight, height, muac
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_enum_value_returns_422(self):
        """Invalid enum value returns 422."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "invalid_risk", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_confidence_out_of_range_returns_422(self):
        """Confidence value outside [0,1] returns 422."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 1.5},  # > 1.0
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_trajectory_insufficient_data_first_visit(self):
        """First visit for beneficiary returns insufficient_data trajectory."""
        # Create a new beneficiary with no visits
        db = SessionLocal()
        # Purge any orphaned visits from prior runs so this is truly the first visit
        db.query(Visit).filter(Visit.beneficiary_id == "B_NEW").delete()
        db.query(Beneficiary).filter(Beneficiary.id == "B_NEW").delete()
        new_beneficiary = Beneficiary(
            id="B_NEW",
            name="New Beneficiary",
            age_months=24,
            sex="male",
            pregnancy=False,
        )
        db.add(new_beneficiary)
        db.commit()
        db.close()

        payload = {
            "beneficiary_id": "B_NEW",
            "anemia": {"risk": "low", "confidence": 0.85},
            "weight": 12.0,
            "height": 85.0,
            "muac": 13.0,
            "diet": {"iron_rich_food": True},
        }

        response = client.post("/api/screening/analyze", json=payload)
        data = response.json()

        assert data["trajectory"] == "insufficient_data"

        # Cleanup
        db = SessionLocal()
        db.query(Beneficiary).filter(Beneficiary.id == "B_NEW").delete()
        db.commit()
        db.close()

    def test_safety_flags_escalate_to_critical(self):
        """Safety flags escalate overall_priority to critical."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 9.5,  # Very low weight for 36 months
            "height": 85.0,  # Low height
            "muac": 10.5,  # Very low MUAC
            "diet": {"iron_rich_food": False, "diversity": 1},
            "symptoms": {
                "severe_pallor": True,
                "breathlessness": True,
                "bilateral_oedema": True,
                "fatigue": True,
            },
        }

        response = client.post("/api/screening/analyze", json=payload)
        data = response.json()

        # Should trigger safety flags and escalate to critical
        if len(data["safety_flags"]) > 0:
            assert data["overall_priority"] == "critical"

    def test_cv_pipeline_input_handled_correctly(self):
        """CV pipeline anemia risk and confidence are used correctly."""
        payloads = [
            {
                "beneficiary_id": "B001",
                "anemia": {"risk": "low", "confidence": 0.95},
                "weight": 14.0,
                "height": 98.0,
                "muac": 13.5,
                "diet": {"iron_rich_food": True, "frequency": "often", "diversity": 8},
            },
            {
                "beneficiary_id": "B001",
                "anemia": {"risk": "high", "confidence": 0.88},
                "weight": 14.0,
                "height": 98.0,
                "muac": 13.5,
                "diet": {"iron_rich_food": True, "frequency": "often", "diversity": 8},
            },
        ]

        responses = [client.post("/api/screening/analyze", json=p) for p in payloads]

        # High CV risk should generally lead to higher anemia_risk in response
        low_risk_data = responses[0].json()
        high_risk_data = responses[1].json()

        # Both should succeed
        assert responses[0].status_code == status.HTTP_200_OK
        assert responses[1].status_code == status.HTTP_200_OK

        # High CV input should influence the final anemia_risk
        risk_order = {"low": 0, "moderate": 1, "high": 2}
        assert (
            risk_order[high_risk_data["anemia_risk"]]
            >= risk_order[low_risk_data["anemia_risk"]]
        )

    def test_response_types_match_schema(self):
        """Response field types match the schema exactly."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)
        data = response.json()

        # Type checks
        assert isinstance(data["anemia_risk"], str)
        assert isinstance(data["nutrition_risk"], str)
        assert isinstance(data["overall_priority"], str)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["trajectory"], str)
        assert isinstance(data["contributors"], list)
        assert isinstance(data["recommended_action"], str)
        assert isinstance(data["safety_flags"], list)

    def test_visit_persistence(self):
        """Visit is persisted to database after screening."""
        from models.entities import Visit

        db = SessionLocal()

        # Count visits before
        initial_count = db.query(Visit).filter(Visit.beneficiary_id == "B001").count()

        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        response = client.post("/api/screening/analyze", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # Count visits after
        final_count = db.query(Visit).filter(Visit.beneficiary_id == "B001").count()

        assert final_count == initial_count + 1

        # Verify visit data
        latest_visit = (
            db.query(Visit)
            .filter(Visit.beneficiary_id == "B001")
            .order_by(Visit.visit_date.desc())
            .first()
        )

        assert latest_visit is not None
        assert float(latest_visit.weight_kg) == 13.1
        assert float(latest_visit.height_cm) == 97
        assert float(latest_visit.muac_mm) == 127.0  # 12.7 cm -> 127 mm
        assert latest_visit.anemia_ai_risk == "moderate"
        assert float(latest_visit.anemia_ai_confidence) == 0.82

        db.close()


class TestLatencyBenchmark:
    """Latency benchmark tests — assert p95 < 500ms."""

    def test_p95_latency_under_500ms(self):
        """P95 latency is under 500ms for standard screening requests."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "moderate", "confidence": 0.82},
            "weight": 13.1,
            "height": 97,
            "muac": 12.7,
            "diet": {"iron_rich_food": False},
        }

        latencies = []
        num_requests = 100

        for _ in range(num_requests):
            start = time.perf_counter()
            response = client.post("/api/screening/analyze", json=payload)
            end = time.perf_counter()

            assert response.status_code == status.HTTP_200_OK
            latencies.append((end - start) * 1000)  # Convert to ms

        # Calculate p95
        latencies.sort()
        p95_index = int(0.95 * len(latencies))
        p95_latency = latencies[p95_index]

        print(f"\nLatency stats (ms):")
        print(f"  Min: {min(latencies):.2f}")
        print(f"  Median: {latencies[len(latencies)//2]:.2f}")
        print(f"  P95: {p95_latency:.2f}")
        print(f"  Max: {max(latencies):.2f}")

        assert p95_latency < 500.0, f"P95 latency {p95_latency:.2f}ms exceeds 500ms budget"

    def test_latency_with_full_payload(self):
        """Latency with all optional fields still meets budget."""
        payload = {
            "beneficiary_id": "B001",
            "anemia": {"risk": "high", "confidence": 0.91},
            "weight": 12.5,
            "height": 95.0,
            "muac": 11.8,
            "diet": {
                "iron_rich_food": True,
                "frequency": "often",
                "diversity": 7,
            },
            "pregnancy": False,
            "ifa": {"adherence": "good"},
            "symptoms": {
                "severe_pallor": True,
                "breathlessness": False,
                "bilateral_oedema": False,
                "fatigue": True,
            },
        }

        latencies = []
        num_requests = 50

        for _ in range(num_requests):
            start = time.perf_counter()
            response = client.post("/api/screening/analyze", json=payload)
            end = time.perf_counter()

            assert response.status_code == status.HTTP_200_OK
            latencies.append((end - start) * 1000)

        latencies.sort()
        p95_latency = latencies[int(0.95 * len(latencies))]

        print(f"\nFull payload P95 latency: {p95_latency:.2f}ms")

        assert p95_latency < 500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
