"""
Standalone tests for Visual Crop Health Assessment Engine
Tests without backend dependencies (no protobuf imports)
"""

import sys
import numpy as np
sys.path.insert(0, '.')

from ai.visual_crop_health import (
    VisualCropHealthEngine, 
    PlantHealthStatus, 
    CropHealthSensor
)


def test_engine_initialization():
    """Test engine initialization and configuration."""
    engine = VisualCropHealthEngine()
    assert engine.model is None
    assert engine.use_nn is False
    assert len(engine.sensor_types) > 0
    print("✓ Engine initialization test passed")


def test_sensor_types():
    """Test sensor type enumeration."""
    engine = VisualCropHealthEngine()
    expected_sensors = [
        "rgb_camera", "ndvi_sensor", "thermal_camera",
        "multispectral", "lidar", "chlorophyll_meter"
    ]
    assert engine.sensor_types == expected_sensors
    print("✓ Sensor types test passed")


def test_heuristic_predict():
    """Test heuristic-based health prediction."""
    engine = VisualCropHealthEngine()
    
    # Test healthy plant
    result = engine.predict_from_image_features(
        ndvi=0.85,
        chlorophyll_content=78,
        canopy_temperature=23,
        ambient_temperature=23,
        canopy_cover=92,
        leaf_area_index=4.5,
        color_index=0.88,
        biomass_estimate=0.88
    )
    
    assert "status" in result
    assert "health_score" in result
    assert result["status"] == PlantHealthStatus.HEALTHY.value
    assert result["health_score"] > 0.75
    print(f"✓ Heuristic prediction test passed")
    print(f"  Healthy plant: {result['health_score']}")


def test_health_conditions():
    """Test different health conditions."""
    engine = VisualCropHealthEngine()
    
    conditions = [
        ("healthy", 0.85, 75, 1, 0.80),
        ("stress_early", 0.70, 60, 3, 0.65),
        ("stress_moderate", 0.52, 42, 6, 0.45),
        ("stress_severe", 0.35, 27, 10, 0.25),
    ]
    
    for name, ndvi, chlorophyll, temp_diff, expected_min in conditions:
        result = engine.predict_from_image_features(
            ndvi=ndvi,
            chlorophyll_content=chlorophyll,
            canopy_temperature=22 + temp_diff,
            ambient_temperature=22,
            canopy_cover=80,
            leaf_area_index=3.5,
            color_index=ndvi,
            biomass_estimate=ndvi
        )
        assert result["health_score"] >= expected_min * 0.85  # Allow small margin
        print(f"  ✓ {name:20} → {result['status']:20} (score={result['health_score']})")
    
    print("✓ Health conditions test passed")


def test_health_recommendations():
    """Test health-based recommendations."""
    engine = VisualCropHealthEngine()
    
    statuses = [
        PlantHealthStatus.HEALTHY.value,
        PlantHealthStatus.STRESS_EARLY.value,
        PlantHealthStatus.DISEASE_DETECTED.value,
        PlantHealthStatus.CRITICAL.value
    ]
    
    for status in statuses:
        recommendations = engine.get_health_recommendations(status)
        assert "priority" in recommendations
        assert "actions" in recommendations
        assert "frequency_days" in recommendations
        assert len(recommendations["actions"]) > 0
        print(f"  ✓ {status:20} priority={recommendations['priority']} freq={recommendations['frequency_days']}d")
    
    print("✓ Health recommendations test passed")


def test_synthetic_dataset():
    """Test synthetic data generation."""
    engine = VisualCropHealthEngine()
    
    features, labels = engine.generate_synthetic_dataset(samples_per_condition=100)
    
    assert features.shape == (600, 7)
    assert labels.shape == (600,)
    assert np.all(features >= 0) and np.all(features <= 1)
    assert np.all(labels >= 0) and np.all(labels <= 1)
    
    print(f"✓ Synthetic dataset generation test passed")
    print(f"  Features shape: {features.shape}, Labels shape: {labels.shape}")
    print(f"  Feature range: [{features.min():.2f}, {features.max():.2f}]")
    print(f"  Label range: [{labels.min():.2f}, {labels.max():.2f}]")


def test_feature_normalization():
    """Test input feature normalization and scaling."""
    engine = VisualCropHealthEngine()
    
    test_cases = [
        (0.15, 10, 10, 22, 10, 0.2, 0.1),  # Very stressed
        (0.80, 75, 24, 22, 85, 4.0, 0.8),  # Healthy
        (0.50, 50, 27, 22, 50, 2.0, 0.5),  # Moderate stress
    ]
    
    for ndvi, chloro, can_temp, amb_temp, canopy, lai, color in test_cases:
        result = engine.predict_from_image_features(
            ndvi=ndvi,
            chlorophyll_content=chloro,
            canopy_temperature=can_temp,
            ambient_temperature=amb_temp,
            canopy_cover=canopy,
            leaf_area_index=lai,
            color_index=color,
            biomass_estimate=color
        )
        
        assert isinstance(result["health_score"], float)
        assert 0 <= result["health_score"] <= 1
        print(f"  ✓ Predictions [{ndvi}, {chloro}, {can_temp}] → {result['status']:20} (score={result['health_score']})")
    
    print("✓ Feature normalization test passed")


def test_health_status_enum():
    """Test health status classification enum."""
    engine = VisualCropHealthEngine()
    
    statuses = [
        PlantHealthStatus.HEALTHY.value,
        PlantHealthStatus.STRESS_EARLY.value,
        PlantHealthStatus.STRESS_MODERATE.value,
        PlantHealthStatus.STRESS_SEVERE.value,
        PlantHealthStatus.DISEASE_DETECTED.value,
        PlantHealthStatus.CRITICAL.value
    ]
    
    for status in statuses:
        assert isinstance(status, str)
        assert status in [
            "HEALTHY", "STRESS_EARLY", "STRESS_MODERATE",
            "STRESS_SEVERE", "DISEASE_DETECTED", "CRITICAL"
        ]
    
    print(f"✓ Health status enum test passed ({len(statuses)} statuses)")


def test_extreme_conditions():
    """Test behavior with extreme input values."""
    engine = VisualCropHealthEngine()
    
    # Minimum values
    result_min = engine.predict_from_image_features(
        ndvi=0.0,
        chlorophyll_content=0,
        canopy_temperature=10,  # Very cold
        ambient_temperature=25,  # Much hotter than canopy
        canopy_cover=0,
        leaf_area_index=0.0,
        color_index=0.0,
        biomass_estimate=0.0
    )
    
    # With extreme values, should be in critical state
    severe_statuses = [
        PlantHealthStatus.STRESS_SEVERE.value,
        PlantHealthStatus.DISEASE_DETECTED.value,
        PlantHealthStatus.CRITICAL.value
    ]
    assert result_min["status"] in severe_statuses, f"Expected severe status, got {result_min['status']}"
    assert result_min["health_score"] <= 0.35
    print(f"  ✓ Extreme case 1 (all zeros/cold): {result_min['status']} (score={result_min['health_score']})")
    
    # Maximum values (optimal conditions)
    result_max = engine.predict_from_image_features(
        ndvi=1.0,
        chlorophyll_content=100,
        canopy_temperature=24,
        ambient_temperature=24,  # Perfect temperature match
        canopy_cover=100,
        leaf_area_index=10.0,
        color_index=1.0,
        biomass_estimate=1.0
    )
    
    assert result_max["status"] == PlantHealthStatus.HEALTHY.value
    assert result_max["health_score"] > 0.85
    print(f"  ✓ Extreme case 2 (all max): {result_max['status']} (score={result_max['health_score']})")
    
    print("✓ Extreme conditions test passed")


def test_consistency():
    """Test prediction consistency across multiple calls."""
    engine = VisualCropHealthEngine()
    
    params = {
        "ndvi": 0.75,
        "chlorophyll_content": 70,
        "canopy_temperature": 25,
        "ambient_temperature": 22,
        "canopy_cover": 85,
        "leaf_area_index": 4.0,
        "color_index": 0.8,
        "biomass_estimate": 0.8
    }
    
    results = [engine.predict_from_image_features(**params) for _ in range(5)]
    
    # All results should be identical
    for i, result in enumerate(results[1:], 1):
        assert result["status"] == results[0]["status"]
        assert result["health_score"] == results[0]["health_score"]
    
    print(f"✓ Prediction consistency test passed (5 consistent predictions)")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("VISUAL CROP HEALTH ASSESSMENT - STANDALONE TESTS")
    print("="*70 + "\n")
    
    tests = [
        test_engine_initialization,
        test_sensor_types,
        test_heuristic_predict,
        test_health_conditions,
        test_health_recommendations,
        test_synthetic_dataset,
        test_feature_normalization,
        test_health_status_enum,
        test_extreme_conditions,
        test_consistency,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    if failed == 0:
        print("ALL TESTS PASSED! ✓")
    else:
        print(f"TESTS FAILED: {failed}/{len(tests)}")
    print("="*70 + "\n")
