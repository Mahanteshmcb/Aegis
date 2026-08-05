"""Test adaptive energy scheduling with weather forecasts (Day 58).

This test validates the smart_adaptive_schedule function that incorporates
weather signals (precipitation, cloud cover, temperature) into charging decisions
and load-shifting recommendations.
"""
import pytest
from ai.energy_management import smart_adaptive_schedule, naive_charge_schedule


def test_adaptive_schedule_basic():
    """Test basic adaptive schedule without weather."""
    consumption = [1.0] * 24
    generation = [2.0] * 24
    
    result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.5,
    )
    
    assert result["ok"]
    assert "schedule" in result
    assert "metrics" in result
    assert "recommendations" in result
    assert len(result["schedule"]) == 24
    assert result["metrics"]["final_soc"] > 0.8  # Should be mostly charged
    assert len(result["recommendations"]) == 0  # No warnings needed


def test_adaptive_schedule_with_rain_forecast():
    """Test schedule adapts when rain forecast reduces solar generation."""
    consumption = [1.5] * 24
    generation = [3.0] * 12 + [0.5] * 12  # Morning sun, afternoon rain
    
    weather_forecast = []
    for i in range(24):
        if i >= 12:
            # Afternoon rain reduces confidence
            weather_forecast.append({
                "hour": i,
                "temp_c": 15,
                "precip_mm": 2.5,  # Significant rain
                "cloud_percent": 80,
            })
        else:
            # Morning clear sky
            weather_forecast.append({
                "hour": i,
                "temp_c": 12,
                "precip_mm": 0.0,
                "cloud_percent": 20,
            })
    
    result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.4,
        weather_forecast=weather_forecast,
        charge_threshold=0.3,
        discharge_threshold=0.7,
    )
    
    assert result["ok"]
    assert "schedule" in result
    
    # During rain period (hours 12-23), should have lower solar confidence
    afternoon_actions = result["schedule"][12:18]
    
    # At least one recommendation for capacity warning expected
    has_warning = any(r["type"] == "capacity_warning" for r in result["recommendations"])
    assert has_warning, "Should warn about insufficient generation during rain"


def test_adaptive_schedule_low_battery_recommendations():
    """Test recommendations when battery drops critically low."""
    consumption = [2.0] * 24  # High consumption
    generation = [0.5] * 24   # Low generation
    
    result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=5.0,
        soc=0.3,
        charge_threshold=0.25,
        discharge_threshold=0.75,
        max_charge_rate_kw=2.0,
    )
    
    assert result["ok"]
    assert result["metrics"]["min_soc"] < 0.2
    
    # Should have low battery warning
    has_low_battery = any(r["type"] == "low_battery_risk" for r in result["recommendations"])
    assert has_low_battery, "Should warn about low battery risk"


def test_adaptive_vs_naive_schedule_comparison():
    """Compare adaptive schedule with naive schedule to verify weather impact."""
    consumption = [1.0, 1.5, 2.0, 1.5, 1.0, 0.8, 0.9, 1.2] * 3
    generation = [0.0, 0.5, 2.0, 2.5, 2.0, 1.0, 0.2, 0.0] * 3
    
    # Weather forecast with afternoon rain
    weather_forecast = []
    for i in range(24):
        if 12 <= i <= 15:
            weather_forecast.append({
                "hour": i,
                "temp_c": 18,
                "precip_mm": 3.0,
                "cloud_percent": 90,
            })
        else:
            weather_forecast.append({
                "hour": i,
                "temp_c": 15,
                "precip_mm": 0.0,
                "cloud_percent": 30,
            })
    
    # Get naive schedule
    naive = naive_charge_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.5,
        weather_forecast=weather_forecast,
    )
    
    # Get adaptive schedule
    adaptive = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.5,
        weather_forecast=weather_forecast,
        charge_threshold=0.3,
        discharge_threshold=0.7,
    )
    
    # Both should be lists/dicts
    assert isinstance(naive, list)
    assert isinstance(adaptive, dict)
    assert len(naive) == 24
    assert len(adaptive["schedule"]) == 24
    
    # Adaptive should have recommendations due to rain
    assert len(adaptive["recommendations"]) > 0


def test_adaptive_schedule_priority_charging():
    """Test that adaptive schedule prioritizes charging during high-solar windows."""
    consumption = [1.5] * 24
    # Clear morning (high solar), cloudy afternoon
    generation = [3.0] * 8 + [0.5] * 8 + [2.0] * 8
    
    weather_forecast = []
    for i in range(24):
        if 8 <= i <= 15:
            # Cloudy afternoon
            weather_forecast.append({
                "hour": i,
                "temp_c": 20,
                "precip_mm": 0.0,
                "cloud_percent": 85,
            })
        else:
            # Clear morning/evening
            weather_forecast.append({
                "hour": i,
                "temp_c": 15,
                "precip_mm": 0.0,
                "cloud_percent": 20,
            })
    
    result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.4,
        weather_forecast=weather_forecast,
        charge_threshold=0.3,
        discharge_threshold=0.7,
        max_charge_rate_kw=3.0,
    )
    
    assert result["ok"]
    
    # Morning hours (0-7) should have more charging activity
    morning_schedule = result["schedule"][0:8]
    afternoon_schedule = result["schedule"][8:16]
    
    morning_charges = sum(1 for s in morning_schedule if "charge" in s.get("action", ""))
    afternoon_charges = sum(1 for s in afternoon_schedule if "charge" in s.get("action", ""))
    
    # Morning should have more charges than afternoon (due to better solar confidence)
    assert morning_charges >= afternoon_charges, "Should prioritize charging during clear weather"


def test_adaptive_schedule_with_temperature_efficiency():
    """Test that schedule accounts for PV efficiency changes with temperature."""
    consumption = [1.0] * 24
    generation = [2.0] * 24
    
    # Cold weather (better PV efficiency)
    cold_weather = [{"temp_c": 5, "cloud_percent": 20, "precip_mm": 0} for _ in range(24)]
    
    # Warm weather (worse PV efficiency)
    warm_weather = [{"temp_c": 35, "cloud_percent": 20, "precip_mm": 0} for _ in range(24)]
    
    cold_result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.5,
        weather_forecast=cold_weather,
    )
    
    warm_result = smart_adaptive_schedule(
        consumption=consumption,
        generation=generation,
        battery_capacity=10.0,
        soc=0.5,
        weather_forecast=warm_weather,
    )
    
    # Cold weather should result in higher final SOC due to better PV efficiency
    cold_final = cold_result["metrics"]["final_soc"]
    warm_final = warm_result["metrics"]["final_soc"]
    
    assert cold_final >= warm_final, "Cold weather should yield better solar efficiency"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
