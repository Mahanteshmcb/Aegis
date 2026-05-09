"""Standalone tests for soil health prediction model.

This test file doesn't depend on backend or protobuf setup.
It tests the soil health prediction engine in isolation.
"""

import numpy as np
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.soil_health_prediction import SoilHealthPredictionEngine


def test_engine_initialization():
    """Test engine initialization."""
    engine = SoilHealthPredictionEngine()
    assert engine.trained == False
    assert len(engine.NUTRIENTS) == 3
    assert engine.NUTRIENTS == ["NITROGEN", "PHOSPHORUS", "POTASSIUM"]
    print("✓ Engine initialization test passed")


def test_sensor_types():
    """Test the supported mycelial sensor types."""
    engine = SoilHealthPredictionEngine()
    expected_sensors = [
        "MYCELIAL_BIOMASS",
        "NUTRIENT_TRANSPORT",
        "WATER_CONTENT",
        "PH_LEVEL",
        "ELECTRICAL_ACTIVITY",
        "SPORE_CONCENTRATION",
        "ROOT_COLONIZATION",
        "DECOMPOSITION_RATE"
    ]
    assert engine.SENSOR_TYPES == expected_sensors
    print("✓ Sensor types test passed")


def test_heuristic_predict():
    """Test heuristic-based prediction."""
    engine = SoilHealthPredictionEngine()
    result = engine.predict_from_mycelial_data(
        biomass=0.6,
        nutrient_transport=50.0,
        water_content=0.6,
        ph_level=6.5,
        electrical_activity=2.5,
        spore_concentration=500.0,
        root_colonization=0.5,
        decomposition_rate=0.05
    )

    assert "nitrogen" in result
    assert "phosphorus" in result
    assert "potassium" in result
    assert "status" in result
    assert "predictions" in result
    assert 0.0 <= result["nitrogen"] <= 1.0
    assert 0.0 <= result["phosphorus"] <= 1.0
    assert 0.0 <= result["potassium"] <= 1.0
    assert result["predictions"].shape == (3,)
    print(f"✓ Heuristic prediction test passed")
    print(f"  N={result['nitrogen']:.2f}, P={result['phosphorus']:.2f}, K={result['potassium']:.2f}")


def test_soil_conditions():
    """Test predictions with different soil conditions."""
    engine = SoilHealthPredictionEngine()

    conditions = {
        "healthy": {
            "biomass": 0.7,
            "nutrient_transport": 70.0,
            "water_content": 0.7,
            "ph_level": 6.8,
            "electrical_activity": 3.5,
            "spore_concentration": 800.0,
            "root_colonization": 0.7,
            "decomposition_rate": 0.08
        },
        "nitrogen_deficient": {
            "biomass": 0.3,
            "nutrient_transport": 20.0,
            "water_content": 0.5,
            "ph_level": 6.5,
            "electrical_activity": 1.5,
            "spore_concentration": 300.0,
            "root_colonization": 0.3,
            "decomposition_rate": 0.02
        },
        "degraded": {
            "biomass": 0.1,
            "nutrient_transport": 10.0,
            "water_content": 0.2,
            "ph_level": 5.5,
            "electrical_activity": 0.5,
            "spore_concentration": 100.0,
            "root_colonization": 0.1,
            "decomposition_rate": 0.01
        }
    }

    for condition_name, params in conditions.items():
        result = engine.predict_from_mycelial_data(**params)
        n, p, k = result["nitrogen"], result["phosphorus"], result["potassium"]
        status = result["status"]
        print(f"  ✓ {condition_name:20} → N={n:.2f} P={p:.2f} K={k:.2f} [{status}]")

    print("✓ Soil conditions test passed")


def test_rehabilitation_recommendations():
    """Test rehabilitation recommendations."""
    engine = SoilHealthPredictionEngine()

    predictions = {
        "nitrogen": 0.2,
        "phosphorus": 0.5,
        "potassium": 0.3,
        "status": {
            "NITROGEN": "DEFICIENT",
            "PHOSPHORUS": "OPTIMAL",
            "POTASSIUM": "DEFICIENT"
        }
    }

    recommendations = engine.get_rehabilitation_recommendations(predictions)
    assert len(recommendations) >= 1
    assert any(r["nutrient"] == "NITROGEN" for r in recommendations)
    assert any(r["nutrient"] == "POTASSIUM" for r in recommendations)

    for rec in recommendations:
        assert "action" in rec
        assert "dosage" in rec
        assert "priority" in rec
        assert rec["dosage"]["amount_kgha"] > 0
        print(f"  ✓ {rec['nutrient']:12} {rec['status']:12} priority={rec['priority']} ({rec['dosage']['amount_kgha']:.1f} kg/ha)")

    print("✓ Rehabilitation recommendations test passed")


def test_synthetic_dataset():
    """Test synthetic dataset generation."""
    engine = SoilHealthPredictionEngine()
    features, labels = engine.generate_synthetic_dataset(samples_per_condition=50)

    assert features.shape == (300, 8)  # 6 conditions * 50 samples
    assert labels.shape == (300, 3)  # N, P, K
    assert features.dtype == np.float32
    assert labels.dtype == np.float32
    assert np.all(labels >= 0.0) and np.all(labels <= 1.0)

    print(f"✓ Synthetic dataset generation test passed")
    print(f"  Features shape: {features.shape}, Labels shape: {labels.shape}")
    print(f"  Feature range: [{features.min():.2f}, {features.max():.2f}]")
    print(f"  Label range: [{labels.min():.2f}, {labels.max():.2f}]")


def test_feature_normalization():
    """Test feature normalization."""
    engine = SoilHealthPredictionEngine()
    features = np.array([[0.5, 50.0, 0.6, 6.5, 2.5, 500.0, 0.5, 0.05]], dtype=np.float32)
    normalized = engine._normalize(features)

    assert normalized.shape == features.shape
    # Normalized features should be close to zero mean
    assert np.abs(normalized.mean()) < 0.5

    print("✓ Feature normalization test passed")


def test_nutrient_status_classification():
    """Test nutrient status classification."""
    engine = SoilHealthPredictionEngine()

    test_cases = [
        ([0.15, 0.65, 0.75], {"NITROGEN": "CRITICAL", "PHOSPHORUS": "OPTIMAL", "POTASSIUM": "OPTIMAL"}),
        ([0.30, 0.20, 0.30], {"NITROGEN": "DEFICIENT", "PHOSPHORUS": "DEFICIENT", "POTASSIUM": "DEFICIENT"}),
        ([0.80, 0.85, 0.80], {"NITROGEN": "OPTIMAL", "PHOSPHORUS": "EXCESS", "POTASSIUM": "OPTIMAL"}),
    ]

    for predictions, expected_status in test_cases:
        pred_array = np.array(predictions)
        status = engine._classify_status(pred_array)
        assert status == expected_status, f"Got {status}, expected {expected_status}"
        print(f"  ✓ Predictions {predictions} → {status}")

    print("✓ Nutrient status classification test passed")


def test_extreme_conditions():
    """Test predictions with extreme environmental conditions."""
    engine = SoilHealthPredictionEngine()

    extreme_cases = [
        {"biomass": 0.0, "nutrient_transport": 0.0, "water_content": 0.0, "ph_level": 4.0, "electrical_activity": 0.0, "spore_concentration": 0.0, "root_colonization": 0.0, "decomposition_rate": 0.0},
        {"biomass": 1.0, "nutrient_transport": 100.0, "water_content": 1.0, "ph_level": 8.5, "electrical_activity": 10.0, "spore_concentration": 2000.0, "root_colonization": 1.0, "decomposition_rate": 0.5},
    ]

    for i, case in enumerate(extreme_cases):
        result = engine.predict_from_mycelial_data(**case)
        assert 0.0 <= result["nitrogen"] <= 1.0
        assert 0.0 <= result["phosphorus"] <= 1.0
        assert 0.0 <= result["potassium"] <= 1.0
        print(f"  ✓ Extreme case {i+1}: N={result['nitrogen']:.2f} P={result['phosphorus']:.2f} K={result['potassium']:.2f}")

    print("✓ Extreme conditions test passed")


def test_consistency():
    """Test prediction consistency."""
    engine = SoilHealthPredictionEngine()
    test_input = {
        "biomass": 0.5,
        "nutrient_transport": 50.0,
        "water_content": 0.5,
        "ph_level": 6.5,
        "electrical_activity": 2.5,
        "spore_concentration": 500.0,
        "root_colonization": 0.5,
        "decomposition_rate": 0.05
    }

    result1 = engine.predict_from_mycelial_data(**test_input)
    result2 = engine.predict_from_mycelial_data(**test_input)

    assert result1["nitrogen"] == result2["nitrogen"]
    assert result1["phosphorus"] == result2["phosphorus"]
    assert result1["potassium"] == result2["potassium"]
    print("✓ Prediction consistency test passed")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SOIL HEALTH PREDICTION MODEL - STANDALONE TESTS")
    print("="*70 + "\n")

    try:
        test_engine_initialization()
        test_sensor_types()
        test_heuristic_predict()
        test_soil_conditions()
        test_rehabilitation_recommendations()
        test_synthetic_dataset()
        test_feature_normalization()
        test_nutrient_status_classification()
        test_extreme_conditions()
        test_consistency()

        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✓")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
