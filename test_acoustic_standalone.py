"""Standalone test for acoustic pest recognition model.

This test file doesn't depend on backend or protobuf setup.
It tests the acoustic pest recognition engine in isolation.
"""

import numpy as np
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.acoustic_pest_recognition import AcousticPestRecognitionEngine


def test_engine_initialization():
    """Test engine initialization."""
    engine = AcousticPestRecognitionEngine()
    assert engine.trained == False
    assert len(engine.LABELS) == 11
    print("✓ Engine initialization test passed")


def test_pest_labels():
    """Test the pest type labels."""
    engine = AcousticPestRecognitionEngine()
    expected_labels = [
        "UNKNOWN", "APHID", "BEETLE", "CATERPILLAR", "WHITEFLY",
        "THRIPS", "SPIDER_MITE", "NEMATODE", "CUTWORM", "ARMYWORM", "LOCUST"
    ]
    assert engine.LABELS == expected_labels
    print("✓ Pest labels test passed")


def test_heuristic_predict():
    """Test heuristic-based prediction."""
    engine = AcousticPestRecognitionEngine()
    result = engine.predict_from_detection_features(
        frequency_hz=800.0,
        amplitude=0.5,
        background_noise=25.0,
        temperature_c=25.0,
        humidity_percent=60.0,
        wind_speed_ms=1.0
    )

    assert "pest_type" in result
    assert "confidence" in result
    assert "scores" in result
    assert result["pest_type"] in engine.LABELS
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["scores"]) == len(engine.LABELS)
    print(f"✓ Heuristic prediction test passed (detected: {result['pest_type']} @ {result['confidence']:.2f})")


def test_predict_signatures():
    """Test predictions with known pest frequency signatures."""
    engine = AcousticPestRecognitionEngine()

    signatures = {
        "APHID": 200.0,
        "BEETLE": 800.0,
        "CATERPILLAR": 2500.0,
        "WHITEFLY": 1200.0,
        "THRIPS": 1800.0,
        "SPIDER_MITE": 100.0,
        "NEMATODE": 60.0,
        "CUTWORM": 400.0,
        "ARMYWORM": 1000.0,
        "LOCUST": 1400.0,
    }

    for pest_name, frequency in signatures.items():
        result = engine.predict_from_detection_features(
            frequency_hz=frequency,
            amplitude=0.5,
            background_noise=25.0,
            temperature_c=25.0,
            humidity_percent=60.0,
            wind_speed_ms=1.0
        )
        assert result["pest_type"] in engine.LABELS
        print(f"  ✓ {pest_name:15} signature (freq={frequency:5.0f} Hz) → {result['pest_type']:15} @ {result['confidence']:.2f}")

    print("✓ Pest signature prediction test passed")


def test_synthetic_dataset():
    """Test synthetic dataset generation."""
    engine = AcousticPestRecognitionEngine()
    features, labels = engine.generate_synthetic_dataset(samples_per_label=50)

    assert features.shape == (550, 6)  # 11 labels * 50 samples
    assert labels.shape == (550,)
    assert np.all(labels >= 0) and np.all(labels < 11)
    assert features.dtype == np.float32
    assert labels.dtype == np.int64

    # Check label distribution
    unique, counts = np.unique(labels, return_counts=True)
    assert len(unique) == 11
    assert np.all(counts == 50)
    print("✓ Synthetic dataset generation test passed")


def test_feature_normalization():
    """Test feature normalization."""
    engine = AcousticPestRecognitionEngine()
    features = np.array([[500.0, 0.5, 30.0, 22.0, 55.0, 2.0]], dtype=np.float32)
    normalized = engine._normalize(features)

    assert normalized.shape == features.shape
    assert not np.allclose(normalized, features)
    print("✓ Feature normalization test passed")


def test_score_summation():
    """Test that prediction scores sum to 1.0."""
    engine = AcousticPestRecognitionEngine()
    result = engine.predict_from_detection_features(
        frequency_hz=500.0,
        amplitude=0.5,
        background_noise=25.0,
        temperature_c=25.0,
        humidity_percent=60.0,
        wind_speed_ms=1.0
    )
    total_score = sum(result["scores"].values())
    assert np.isclose(total_score, 1.0, atol=1e-5)
    print("✓ Score summation test passed")


def test_consistency():
    """Test prediction consistency."""
    engine = AcousticPestRecognitionEngine()
    test_input = {
        "frequency_hz": 600.0,
        "amplitude": 0.5,
        "background_noise": 25.0,
        "temperature_c": 25.0,
        "humidity_percent": 60.0,
        "wind_speed_ms": 1.0
    }

    result1 = engine.predict_from_detection_features(**test_input)
    result2 = engine.predict_from_detection_features(**test_input)

    assert result1["pest_type"] == result2["pest_type"]
    assert result1["confidence"] == result2["confidence"]
    print("✓ Prediction consistency test passed")


def test_extreme_conditions():
    """Test predictions with extreme environmental conditions."""
    engine = AcousticPestRecognitionEngine()

    extreme_cases = [
        {"freq": 1, "amp": 0.001, "noise": 80, "temp": 5, "hum": 10, "wind": 10},
        {"freq": 10000, "amp": 0.999, "noise": 0, "temp": 40, "hum": 100, "wind": 0},
        {"freq": 0, "amp": 0, "noise": 0, "temp": 0, "hum": 0, "wind": 0},
    ]

    for case in extreme_cases:
        result = engine.predict_from_detection_features(
            frequency_hz=case["freq"],
            amplitude=case["amp"],
            background_noise=case["noise"],
            temperature_c=case["temp"],
            humidity_percent=case["hum"],
            wind_speed_ms=case["wind"]
        )
        assert result["pest_type"] in engine.LABELS
        assert 0.0 <= result["confidence"] <= 1.0

    print("✓ Extreme conditions test passed")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ACOUSTIC PEST RECOGNITION MODEL - STANDALONE TESTS")
    print("="*70 + "\n")

    try:
        test_engine_initialization()
        test_pest_labels()
        test_heuristic_predict()
        test_predict_signatures()
        test_synthetic_dataset()
        test_feature_normalization()
        test_score_summation()
        test_consistency()
        test_extreme_conditions()

        print("\n" + "="*70)
        print("ALL TESTS PASSED! ✓")
        print("="*70 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
