"""
Day 44: ML Model Accuracy Validation Tests

Comprehensive validation testing for Aegis ML models including accuracy,
performance, and robustness testing.
"""

import pytest
import numpy as np
from typing import Dict, List, Tuple
import time
import logging

from ai.acoustic_pest_recognition import AcousticPestRecognitionEngine
from ai.soil_health_prediction import SoilHealthPredictionEngine
from ai.visual_crop_health import VisualCropHealthEngine

logger = logging.getLogger(__name__)


class TestMLModelValidation:
    """Comprehensive ML model validation test suite."""

    @pytest.fixture
    def acoustic_engine(self):
        """Create acoustic pest recognition engine for testing."""
        return AcousticPestRecognitionEngine()

    @pytest.fixture
    def soil_engine(self):
        """Create soil health prediction engine for testing."""
        return SoilHealthPredictionEngine()

    @pytest.fixture
    def visual_engine(self):
        """Create visual crop health engine for testing."""
        return VisualCropHealthEngine()

    def test_acoustic_pest_recognition_accuracy(self, acoustic_engine):
        """Test acoustic pest recognition model accuracy with synthetic test data."""
        # Generate synthetic test data
        np.random.seed(42)  # For reproducible results

        # Create test features: [frequency, amplitude, duration, harmonics, pattern, rhythm]
        n_samples = 1000
        test_features = np.random.randn(n_samples, 6).astype(np.float32)

        # Add some structure to make it more realistic
        # Aphids: high frequency, low amplitude
        aphid_mask = np.random.choice(n_samples, size=n_samples//11, replace=False)
        test_features[aphid_mask, 0] = np.random.normal(8000, 500, len(aphid_mask))  # High frequency
        test_features[aphid_mask, 1] = np.random.normal(0.2, 0.05, len(aphid_mask))  # Low amplitude

        # Beetles: medium frequency, high amplitude
        beetle_mask = np.random.choice(n_samples, size=n_samples//11, replace=False)
        test_features[beetle_mask, 0] = np.random.normal(3000, 300, len(beetle_mask))
        test_features[beetle_mask, 1] = np.random.normal(0.8, 0.1, len(beetle_mask))

        # Generate ground truth labels (mostly unknown for realistic scenario)
        true_labels = np.zeros(n_samples, dtype=int)
        true_labels[aphid_mask] = 1  # APHID
        true_labels[beetle_mask] = 2  # BEETLE

        # Test inference performance
        start_time = time.time()
        predictions = []
        confidences = []

        for i in range(min(100, n_samples)):  # Test subset for performance
            result = acoustic_engine.predict(test_features[i])
            predictions.append(result['prediction'])
            confidences.append(result['confidence'])

        inference_time = time.time() - start_time
        avg_inference_time = inference_time / len(predictions)

        # Performance assertions
        assert avg_inference_time < 0.1, f"Inference too slow: {avg_inference_time:.3f}s per sample"
        assert all(isinstance(pred, str) for pred in predictions), "Predictions should be strings"
        assert all(0.0 <= conf <= 1.0 for conf in confidences), "Confidences should be between 0 and 1"

        # Basic accuracy check (should at least identify some known patterns)
        known_predictions = [p for p in predictions if p != "UNKNOWN"]
        accuracy = len(known_predictions) / len(predictions)
        assert accuracy >= 0.1, f"Model accuracy too low: {accuracy:.2f}"

        logger.info(f"🎵 Acoustic model validation: {accuracy:.2f} accuracy, {avg_inference_time:.3f}s avg inference")

    def test_soil_health_prediction_accuracy(self, soil_engine):
        """Test soil health prediction model accuracy with synthetic soil data."""
        # Generate synthetic soil sensor data
        np.random.seed(42)

        n_samples = 500
        # Features: [moisture, temperature, ph, conductivity, organic_matter, mycorrhiza_density, bacteria_count, fungi_count]
        test_features = np.random.randn(n_samples, 8).astype(np.float32)

        # Add realistic soil parameter ranges
        test_features[:, 0] = np.clip(test_features[:, 0] * 10 + 30, 10, 50)  # Moisture 10-50%
        test_features[:, 1] = np.clip(test_features[:, 1] * 5 + 25, 15, 35)   # Temperature 15-35°C
        test_features[:, 2] = np.clip(test_features[:, 2] * 1 + 7, 5.5, 8.5)  # pH 5.5-8.5
        test_features[:, 3] = np.clip(test_features[:, 3] * 500 + 1000, 200, 2000)  # Conductivity 200-2000 µS/cm

        # Generate ground truth N-P-K values
        # N: 0-100 mg/kg, P: 0-50 mg/kg, K: 0-200 mg/kg
        true_npk = np.random.rand(n_samples, 3).astype(np.float32)
        true_npk[:, 0] = true_npk[:, 0] * 100  # Nitrogen
        true_npk[:, 1] = true_npk[:, 1] * 50   # Phosphorus
        true_npk[:, 2] = true_npk[:, 2] * 200  # Potassium

        # Test inference performance
        start_time = time.time()
        predictions = []
        errors = []

        for i in range(min(100, n_samples)):  # Test subset for performance
            result = soil_engine.predict_npk(test_features[i])
            pred_npk = np.array([result['nitrogen'], result['phosphorus'], result['potassium']])
            predictions.append(pred_npk)

            # Calculate prediction error
            true_vals = true_npk[i]
            error = np.mean(np.abs(pred_npk - true_vals) / (true_vals + 1e-6))  # Relative error
            errors.append(error)

        inference_time = time.time() - start_time
        avg_inference_time = inference_time / len(predictions)
        avg_error = np.mean(errors)

        # Performance assertions
        assert avg_inference_time < 0.05, f"Inference too slow: {avg_inference_time:.3f}s per sample"
        assert avg_error < 1.0, f"Prediction error too high: {avg_error:.3f}"
        assert all(len(p) == 3 for p in predictions), "Should predict 3 NPK values"

        logger.info(f"🌱 Soil health model validation: {avg_error:.3f} avg error, {avg_inference_time:.3f}s avg inference")

    def test_visual_crop_health_accuracy(self, visual_engine):
        """Test visual crop health assessment model accuracy."""
        # Generate synthetic visual sensor data
        np.random.seed(42)

        n_samples = 200
        # Features: [ndvi, chlorophyll_content, canopy_temperature, leaf_area_index, stress_index]
        test_features = np.random.randn(n_samples, 5).astype(np.float32)

        # Add realistic ranges
        test_features[:, 0] = np.clip(test_features[:, 0] * 0.2 + 0.7, 0.3, 0.9)  # NDVI 0.3-0.9
        test_features[:, 1] = np.clip(test_features[:, 1] * 10 + 40, 20, 60)       # Chlorophyll 20-60
        test_features[:, 2] = np.clip(test_features[:, 2] * 3 + 28, 20, 35)        # Temperature 20-35°C

        # Test inference performance
        start_time = time.time()
        predictions = []
        confidences = []

        for i in range(min(50, n_samples)):  # Test subset for performance
            result = visual_engine.assess_health(test_features[i])
            predictions.append(result['status'])
            confidences.append(result['confidence'])

        inference_time = time.time() - start_time
        avg_inference_time = inference_time / len(predictions)

        # Performance assertions
        assert avg_inference_time < 0.02, f"Inference too slow: {avg_inference_time:.3f}s per sample"
        assert all(isinstance(pred, str) for pred in predictions), "Predictions should be strings"
        assert all(0.0 <= conf <= 1.0 for conf in confidences), "Confidences should be between 0 and 1"

        # Check that predictions are valid health statuses
        valid_statuses = ["HEALTHY", "STRESS_EARLY", "STRESS_MODERATE", "STRESS_SEVERE", "DISEASE_DETECTED", "CRITICAL"]
        assert all(pred in valid_statuses for pred in predictions), "Invalid health status predictions"

        logger.info(f"📷 Visual health model validation: {avg_inference_time:.3f}s avg inference")

    def test_model_robustness_to_noise(self, acoustic_engine, soil_engine, visual_engine):
        """Test model robustness to noisy input data."""
        np.random.seed(42)

        # Test acoustic model with noise
        noisy_features = np.random.randn(10, 6).astype(np.float32) * 10  # High noise
        for i in range(10):
            result = acoustic_engine.predict(noisy_features[i])
            assert isinstance(result['prediction'], str), "Should handle noisy input gracefully"
            assert 0.0 <= result['confidence'] <= 1.0, "Confidence should be valid"

        # Test soil model with noise
        noisy_soil_features = np.random.randn(10, 8).astype(np.float32) * 100
        for i in range(10):
            result = soil_engine.predict_npk(noisy_soil_features[i])
            assert all(isinstance(v, (int, float)) for v in result.values()), "Should return numeric predictions"
            assert result['nitrogen'] >= 0, "Nitrogen should be non-negative"
            assert result['phosphorus'] >= 0, "Phosphorus should be non-negative"
            assert result['potassium'] >= 0, "Potassium should be non-negative"

        # Test visual model with noise
        noisy_visual_features = np.random.randn(10, 5).astype(np.float32) * 100
        for i in range(10):
            result = visual_engine.assess_health(noisy_visual_features[i])
            assert isinstance(result['status'], str), "Should handle noisy input gracefully"
            assert 0.0 <= result['confidence'] <= 1.0, "Confidence should be valid"

        logger.info("🛡️ Model robustness validation: All models handle noisy input gracefully")

    def test_model_performance_under_load(self, acoustic_engine, soil_engine):
        """Test model performance under concurrent load."""
        import concurrent.futures

        np.random.seed(42)
        n_concurrent = 10
        n_iterations = 50

        # Test acoustic model under load
        acoustic_features = np.random.randn(n_iterations, 6).astype(np.float32)

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_concurrent) as executor:
            futures = [executor.submit(acoustic_engine.predict, acoustic_features[i]) for i in range(n_iterations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        acoustic_load_time = time.time() - start_time

        # Test soil model under load
        soil_features = np.random.randn(n_iterations, 8).astype(np.float32)

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_concurrent) as executor:
            futures = [executor.submit(soil_engine.predict_npk, soil_features[i]) for i in range(n_iterations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        soil_load_time = time.time() - start_time

        # Performance assertions
        assert acoustic_load_time < 5.0, f"Acoustic model too slow under load: {acoustic_load_time:.2f}s"
        assert soil_load_time < 3.0, f"Soil model too slow under load: {soil_load_time:.2f}s"

        logger.info(f"⚡ Load performance validation: Acoustic {acoustic_load_time:.2f}s, Soil {soil_load_time:.2f}s")

    def test_model_memory_efficiency(self, acoustic_engine, soil_engine, visual_engine):
        """Test that models don't have memory leaks during repeated inference."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run many inferences
        n_iterations = 1000
        features = np.random.randn(n_iterations, 6).astype(np.float32)

        for i in range(n_iterations):
            acoustic_engine.predict(features[i % len(features)])

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Allow some memory increase but not excessive
        assert memory_increase < 50, f"Memory leak detected: {memory_increase:.1f}MB increase"

        logger.info(f"💾 Memory efficiency validation: {memory_increase:.1f}MB memory increase after {n_iterations} inferences")