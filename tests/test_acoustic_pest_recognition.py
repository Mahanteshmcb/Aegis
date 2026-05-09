"""Tests for acoustic pest recognition model.

Day 38: Acoustic pest recognition ML model development and testing.
"""

import pytest
import numpy as np
from ai.acoustic_pest_recognition import (
    AcousticPestRecognitionEngine,
    AcousticFeatureDataset,
    AcousticPestRecognitionModel
)


class TestAcousticFeatureDataset:
    """Test the acoustic feature dataset."""

    def test_dataset_creation(self):
        """Test creating a dataset with features and labels."""
        features = np.random.randn(100, 6).astype(np.float32)
        labels = np.random.randint(0, 11, 100).astype(np.int64)
        dataset = AcousticFeatureDataset(features, labels)
        assert len(dataset) == 100

    def test_dataset_getitem(self):
        """Test retrieving items from the dataset."""
        features = np.random.randn(10, 6).astype(np.float32)
        labels = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=np.int64)
        dataset = AcousticFeatureDataset(features, labels)
        feat, label = dataset[0]
        assert feat.shape == (6,)
        assert label.item() == 0


class TestAcousticPestRecognitionEngine:
    """Test the acoustic pest recognition engine."""

    def test_engine_initialization(self):
        """Test engine initialization without model."""
        engine = AcousticPestRecognitionEngine()
        assert engine.trained == False
        assert len(engine.LABELS) == 11

    def test_pest_labels(self):
        """Test the pest type labels."""
        engine = AcousticPestRecognitionEngine()
        expected_labels = [
            "UNKNOWN", "APHID", "BEETLE", "CATERPILLAR", "WHITEFLY",
            "THRIPS", "SPIDER_MITE", "NEMATODE", "CUTWORM", "ARMYWORM", "LOCUST"
        ]
        assert engine.LABELS == expected_labels

    def test_heuristic_predict(self):
        """Test heuristic-based prediction without trained model."""
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

    def test_predict_aphid_signature(self):
        """Test prediction with typical aphid frequency."""
        engine = AcousticPestRecognitionEngine()
        result = engine.predict_from_detection_features(
            frequency_hz=200.0,  # Aphid signature
            amplitude=0.3,
            background_noise=20.0,
            temperature_c=22.0,
            humidity_percent=55.0,
            wind_speed_ms=0.5
        )
        assert result["pest_type"] in engine.LABELS
        assert result["confidence"] > 0.0

    def test_predict_beetle_signature(self):
        """Test prediction with typical beetle frequency."""
        engine = AcousticPestRecognitionEngine()
        result = engine.predict_from_detection_features(
            frequency_hz=800.0,  # Beetle signature
            amplitude=0.7,
            background_noise=25.0,
            temperature_c=25.0,
            humidity_percent=60.0,
            wind_speed_ms=1.0
        )
        assert result["pest_type"] in engine.LABELS
        assert result["confidence"] > 0.0

    def test_synthetic_dataset_generation(self):
        """Test generating synthetic training data."""
        engine = AcousticPestRecognitionEngine()
        features, labels = engine.generate_synthetic_dataset(samples_per_label=50)

        assert features.shape == (550, 6)  # 11 labels * 50 samples each
        assert labels.shape == (550,)
        assert np.all(labels >= 0) and np.all(labels < 11)
        assert features.dtype == np.float32
        assert labels.dtype == np.int64

    def test_synthetic_dataset_label_distribution(self):
        """Test that synthetic dataset has balanced label distribution."""
        engine = AcousticPestRecognitionEngine()
        features, labels = engine.generate_synthetic_dataset(samples_per_label=100)

        unique, counts = np.unique(labels, return_counts=True)
        assert len(unique) == 11
        assert np.all(counts == 100)

    def test_feature_normalization(self):
        """Test feature normalization."""
        engine = AcousticPestRecognitionEngine()
        features = np.array([[500.0, 0.5, 30.0, 22.0, 55.0, 2.0]], dtype=np.float32)
        normalized = engine._normalize(features)

        # Features should be normalized to approximately zero mean
        assert normalized.shape == features.shape
        assert not np.allclose(normalized, features)

    def test_normalize_consistency(self):
        """Test that normalization is consistent."""
        engine = AcousticPestRecognitionEngine()
        features = np.random.randn(10, 6).astype(np.float32) * 100 + 50
        normalized1 = engine._normalize(features)
        normalized2 = engine._normalize(features)
        assert np.allclose(normalized1, normalized2)

    def test_predict_with_various_frequencies(self):
        """Test prediction with various frequency ranges."""
        engine = AcousticPestRecognitionEngine()
        frequencies = [50, 200, 400, 800, 1200, 1800, 2600]

        for freq in frequencies:
            result = engine.predict_from_detection_features(
                frequency_hz=float(freq),
                amplitude=0.5,
                background_noise=25.0,
                temperature_c=25.0,
                humidity_percent=60.0,
                wind_speed_ms=1.0
            )
            assert result["pest_type"] in engine.LABELS
            assert 0.0 <= result["confidence"] <= 1.0

    def test_score_summation(self):
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


@pytest.mark.skipif(
    not pytest.importorskip("torch", minversion=None),
    reason="PyTorch not available"
)
class TestAcousticPestRecognitionTorch:
    """Test torch-dependent functionality."""

    def test_model_creation(self):
        """Test creating the neural network model."""
        try:
            import torch
            model = AcousticPestRecognitionModel(input_dim=6, output_dim=11)
            assert model is not None
        except ImportError:
            pytest.skip("PyTorch not installed")

    def test_model_forward_pass(self):
        """Test forward pass through the model."""
        try:
            import torch
            model = AcousticPestRecognitionModel(input_dim=6, output_dim=11)
            x = torch.randn(32, 6)
            output = model(x)
            assert output.shape == (32, 11)
        except ImportError:
            pytest.skip("PyTorch not installed")


class TestAcousticPestRecognitionIntegration:
    """Integration tests for the acoustic pest recognition engine."""

    def test_full_prediction_pipeline(self):
        """Test the complete prediction pipeline."""
        engine = AcousticPestRecognitionEngine()

        test_cases = [
            {
                "frequency_hz": 200.0,
                "amplitude": 0.3,
                "background_noise": 20.0,
                "temperature_c": 22.0,
                "humidity_percent": 55.0,
                "wind_speed_ms": 0.5,
                "description": "Low frequency pest"
            },
            {
                "frequency_hz": 1500.0,
                "amplitude": 0.8,
                "background_noise": 30.0,
                "temperature_c": 26.0,
                "humidity_percent": 70.0,
                "wind_speed_ms": 2.0,
                "description": "Mid-high frequency pest"
            },
            {
                "frequency_hz": 2500.0,
                "amplitude": 0.9,
                "background_noise": 25.0,
                "temperature_c": 24.0,
                "humidity_percent": 65.0,
                "wind_speed_ms": 1.5,
                "description": "High frequency pest"
            }
        ]

        for test_case in test_cases:
            desc = test_case.pop("description")
            result = engine.predict_from_detection_features(**test_case)
            assert result["pest_type"] in engine.LABELS, f"Failed for {desc}"
            assert 0.0 <= result["confidence"] <= 1.0, f"Invalid confidence for {desc}"

    def test_detector_consistency(self):
        """Test that the same input always produces the same output."""
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


class TestAcousticPestRecognitionEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_frequencies(self):
        """Test prediction with extreme frequencies."""
        engine = AcousticPestRecognitionEngine()

        extreme_frequencies = [1, 5000, 10000]
        for freq in extreme_frequencies:
            result = engine.predict_from_detection_features(
                frequency_hz=float(freq),
                amplitude=0.5,
                background_noise=25.0,
                temperature_c=25.0,
                humidity_percent=60.0,
                wind_speed_ms=1.0
            )
            assert result["pest_type"] in engine.LABELS

    def test_extreme_amplitude(self):
        """Test prediction with extreme amplitudes."""
        engine = AcousticPestRecognitionEngine()

        amplitudes = [0.0, 0.001, 0.999, 1.0]
        for amp in amplitudes:
            result = engine.predict_from_detection_features(
                frequency_hz=500.0,
                amplitude=amp,
                background_noise=25.0,
                temperature_c=25.0,
                humidity_percent=60.0,
                wind_speed_ms=1.0
            )
            assert result["pest_type"] in engine.LABELS

    def test_zero_features(self):
        """Test prediction with zero features."""
        engine = AcousticPestRecognitionEngine()
        result = engine.predict_from_detection_features(
            frequency_hz=0.0,
            amplitude=0.0,
            background_noise=0.0,
            temperature_c=0.0,
            humidity_percent=0.0,
            wind_speed_ms=0.0
        )
        assert result["pest_type"] in engine.LABELS
        assert 0.0 <= result["confidence"] <= 1.0
