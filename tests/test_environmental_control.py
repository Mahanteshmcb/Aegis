"""
Tests for Living Quarters Environmental Control System
PID control, air quality, comfort optimization, API integration
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import math

from backend.services.environmental_control import (
    PIDController, HVACEngine, AirQualityController, CircadianOptimizer
)


class TestPIDController:
    """Test PID control algorithm for HVAC"""
    
    def test_pid_initialization(self):
        """Test PID controller initialization with correct parameters"""
        pid = PIDController(kp=0.8, ki=0.05, kd=0.15, update_interval=30)
        
        assert pid.kp == 0.8
        assert pid.ki == 0.05
        assert pid.kd == 0.15
        assert pid.dt == 30
        assert pid.error_sum == 0.0
        assert pid.last_error == 0.0
    
    def test_pid_heating_mode(self):
        """Test PID output for heating (temperature below setpoint)"""
        pid = PIDController()
        current_temp = 18.0
        setpoint = 22.0
        outdoor_temp = 5.0
        
        output = pid.compute(current_temp, setpoint, outdoor_temp)
        
        # Should be positive (heating)
        assert output > 0, "Should output positive for heating"
        # With 4°C error, should be moderate response
        assert output > 5, "Heating output should be moderate for 4°C error"
    
    def test_pid_cooling_mode(self):
        """Test PID output for cooling (temperature above setpoint)"""
        pid = PIDController()
        current_temp = 26.0
        setpoint = 22.0
        outdoor_temp = 35.0
        
        output = pid.compute(current_temp, setpoint, outdoor_temp)
        
        # Should be negative (cooling)
        assert output < 0, "Should output negative for cooling"
        # With 4°C error, should be moderate response
        assert output < -5, "Cooling output should be moderate for 4°C error"
    
    def test_pid_deadband(self):
        """Test PID deadband prevents short-cycling near setpoint"""
        pid = PIDController()
        current_temp = 21.85  # Within ±0.3°C deadband
        setpoint = 22.0
        outdoor_temp = 20.0
        
        output = pid.compute(current_temp, setpoint, outdoor_temp)
        
        # Deadband should reduce output
        assert abs(output) < 2, "Deadband should minimize output near setpoint"
    
    def test_pid_integral_windup_prevention(self):
        """Test anti-windup limits on integral term"""
        pid = PIDController()
        
        # Accumulate large error
        for _ in range(100):
            pid.compute(10.0, 25.0, 20.0)
        
        # Integral term should be capped
        assert abs(pid.error_sum) <= pid.integral_max


class TestHVACEngine:
    """Test HVAC control engine"""
    
    def test_hvac_initialization(self):
        """Test HVAC engine initialization"""
        engine = HVACEngine()
        
        assert engine.min_compressor_hz == 30
        assert engine.max_compressor_hz == 120
        assert engine.min_fan_speed == 20
        assert engine.max_fan_speed == 100
    
    def test_compressor_speed_calculation(self):
        """Test compressor frequency calculation from HVAC output"""
        engine = HVACEngine()
        
        # Zero output = zero speed
        assert engine._calculate_compressor_speed(0) == 0
        
        # 50% heating = mid-range speed
        speed_50 = engine._calculate_compressor_speed(50)
        assert 30 < speed_50 < 120
        
        # 100% = maximum speed
        speed_100 = engine._calculate_compressor_speed(100)
        assert speed_100 == 120
        
        # Negative (cooling) should give same magnitude
        speed_neg_50 = engine._calculate_compressor_speed(-50)
        assert speed_50 == speed_neg_50
    
    def test_fan_speed_calculation(self):
        """Test supply fan speed calculation"""
        engine = HVACEngine()
        
        # Low HVAC output = low fan speed (minimum 20%)
        fan_low = engine._calculate_fan_speed(5)
        assert fan_low >= engine.min_fan_speed
        
        # 100% HVAC output = high fan speed
        fan_high = engine._calculate_fan_speed(100)
        assert fan_high > fan_low
    
    def test_cop_estimation(self):
        """Test Coefficient of Performance estimation"""
        engine = HVACEngine()
        
        # Heating in moderate weather should have good COP
        cop_moderate = engine._estimate_cop(outdoor_temp=15, hvac_output=50)
        assert cop_moderate > 3.0
        
        # Heating in cold weather should have lower COP
        cop_cold = engine._estimate_cop(outdoor_temp=-5, hvac_output=50)
        assert cop_cold < cop_moderate
        
        # Cooling in hot weather should have lower COP
        cop_hot = engine._estimate_cop(outdoor_temp=40, hvac_output=-50)
        assert cop_hot > 2.5
    
    def test_hvac_output_calculation(self):
        """Test full HVAC control loop calculation"""
        engine = HVACEngine()
        
        result = engine.calculate_hvac_output(
            current_temp=20.0,
            setpoint=22.0,
            outdoor_temp=15.0
        )
        
        # Check output structure
        assert 'hvac_output_percent' in result
        assert 'compressor_speed_hz' in result
        assert 'fan_speed_percent' in result
        assert 'mode' in result
        assert 'deadband_active' in result
        assert 'cop_estimate' in result
        
        # Should be heating mode
        assert result['mode'] == 'heating'
        assert result['hvac_output_percent'] > 0


class TestAirQualityController:
    """Test air quality monitoring and ventilation control"""
    
    def test_aq_controller_initialization(self):
        """Test air quality controller initialization"""
        aq = AirQualityController()
        
        assert aq.baseline_cfm == 500
        assert aq.max_cfm == 1200
        assert aq.co2_thresholds['excellent'] == 800
        assert aq.humidity_optimal == (40, 60)
    
    def test_ventilation_baseline(self):
        """Test baseline ventilation demand with good air quality"""
        aq = AirQualityController()
        
        result = aq.calculate_ventilation_demand(
            co2_ppm=600,      # Excellent
            voc_ppb=50,        # Low
            pm25=10,           # Good
            humidity=50,       # Optimal
            occupancy_count=1
        )
        
        # Should be at or above baseline with occupancy adjustment
        # Baseline = 500 + (1 * 7.5) = 507.5
        assert result['ventilation_cfm'] >= aq.baseline_cfm
        assert result['air_purifier_needed'] == False
        assert len(result['alerts']) == 0
    
    def test_high_co2_ventilation_ramp(self):
        """Test ventilation increases with high CO₂"""
        aq = AirQualityController()
        
        result_low = aq.calculate_ventilation_demand(
            co2_ppm=800, voc_ppb=50, pm25=10,
            humidity=50, occupancy_count=1
        )
        
        result_high = aq.calculate_ventilation_demand(
            co2_ppm=1500, voc_ppb=50, pm25=10,
            humidity=50, occupancy_count=1
        )
        
        # Higher CO₂ should require more ventilation
        # CO2=1500: excess 700 ppm → 700/100 * 50 = 350 CFM additional
        assert result_high['ventilation_cfm'] > result_low['ventilation_cfm']
        assert result_high['ventilation_cfm'] > 600  # Should be significantly higher
        
        # Should generate alert
        assert len(result_high['alerts']) > 0
        assert result_high['alerts'][0]['type'] == 'co2_high'
    
    def test_voc_spike_purifier_activation(self):
        """Test air purifier activation on VOC spike"""
        aq = AirQualityController()
        
        result = aq.calculate_ventilation_demand(
            co2_ppm=800,
            voc_ppb=600,       # High VOC (>500 ppb threshold)
            pm25=20,
            humidity=50,
            occupancy_count=1
        )
        
        assert result['air_purifier_needed'] == True
        assert any(a['type'] == 'voc_high' for a in result['alerts'])
    
    def test_high_humidity_exhaust_boost(self):
        """Test exhaust boost activation for high humidity"""
        aq = AirQualityController()
        
        result = aq.calculate_ventilation_demand(
            co2_ppm=800,
            voc_ppb=50,
            pm25=10,
            humidity=70,       # >65% = high
            occupancy_count=1
        )
        
        assert result['exhaust_boost'] == True
        assert result['ventilation_cfm'] > aq.baseline_cfm
    
    def test_filter_status_operational(self):
        """Test filter status when operational"""
        aq = AirQualityController()
        
        status = aq.get_filter_status(
            runtime_hours=500,
            pressure_drop_pa=10
        )
        
        assert status['status'] == 'operational'
        assert status['life_percent'] < 20
        assert status['alert_level'] == 'none'
    
    def test_filter_status_needs_replacement(self):
        """Test filter status when needs replacement"""
        aq = AirQualityController()
        
        status = aq.get_filter_status(
            runtime_hours=2500,
            pressure_drop_pa=26
        )
        
        assert status['status'] == 'replace_immediately'
        assert status['alert_level'] == 'high'
    
    def test_anomaly_detection_kitchen_high_co2(self):
        """Test anomaly detection for kitchen cooking"""
        aq = AirQualityController()
        
        anomalies = aq.detect_anomalies(
            co2_ppm=2100,
            voc_ppb=150,
            pm25=20,
            room_type='kitchen'
        )
        
        assert len(anomalies) > 0
        assert anomalies[0]['source'] == 'high_occupancy_or_cooking'
    
    def test_occupancy_ventilation_requirement(self):
        """Test ASHRAE ventilation standard (7.5 CFM per person)"""
        aq = AirQualityController()
        
        # Single occupant: 500 + 7.5 = 507.5
        result_1 = aq.calculate_ventilation_demand(
            co2_ppm=800, voc_ppb=50, pm25=10,
            humidity=50, occupancy_count=1
        )
        
        # Four occupants: 500 + (4 * 7.5) = 530
        result_4 = aq.calculate_ventilation_demand(
            co2_ppm=800, voc_ppb=50, pm25=10,
            humidity=50, occupancy_count=4
        )
        
        # More people = more ventilation
        assert result_4['ventilation_cfm'] > result_1['ventilation_cfm']
        # Should have 4 extra people * 7.5 CFM/person = 30 CFM more
        assert result_4['ventilation_cfm'] - result_1['ventilation_cfm'] >= 20


class TestCircadianOptimizer:
    """Test circadian rhythm integration"""
    
    def test_circadian_temperature_peak(self):
        """Test temperature peaks in afternoon (highest body temp)"""
        optimizer = CircadianOptimizer()
        
        # Set wake time to 7 AM
        wake_time = datetime.now().replace(hour=7, minute=0, second=0)
        sleep_time = datetime.now().replace(hour=23, minute=0, second=0)
        
        # Peak circadian temp should be ~13 hours after wake (8 PM)
        afternoon_time = wake_time + timedelta(hours=13)
        temp_afternoon = optimizer.calculate_circadian_temperature(
            afternoon_time, wake_time, sleep_time
        )
        
        # Should be higher than baseline
        assert temp_afternoon > optimizer.baseline_temp
    
    def test_circadian_temperature_low_at_night(self):
        """Test temperature is lower at night (lower body temp during sleep)"""
        optimizer = CircadianOptimizer()
        
        wake_time = datetime.now().replace(hour=7, minute=0, second=0)
        sleep_time = datetime.now().replace(hour=23, minute=0, second=0)
        
        # Early morning (5 AM) should have lowest temp
        night_time = wake_time - timedelta(hours=2)
        temp_night = optimizer.calculate_circadian_temperature(
            night_time, wake_time, sleep_time
        )
        
        # Should be lower than baseline
        assert temp_night < optimizer.baseline_temp
    
    def test_light_profile_presleep(self):
        """Test light profile dims before sleep"""
        optimizer = CircadianOptimizer()
        
        wake_time = datetime.now().replace(hour=7, minute=0, second=0)
        sleep_time = datetime.now().replace(hour=23, minute=0, second=0)
        
        # 1 hour before sleep
        one_hour_before = sleep_time - timedelta(hours=1)
        profile = optimizer.calculate_light_profile(one_hour_before, wake_time, sleep_time)
        
        # CCT should be reduced (warmer light)
        assert profile['cct_kelvin'] < optimizer.baseline_cct
        # Dimming should be reduced
        assert profile['dimming_percent'] < 100
        assert profile['blue_light_reduced'] == True
    
    def test_light_profile_daytime(self):
        """Test light profile during day"""
        optimizer = CircadianOptimizer()
        
        wake_time = datetime.now().replace(hour=7, minute=0, second=0)
        sleep_time = datetime.now().replace(hour=23, minute=0, second=0)
        
        # Midday
        midday = wake_time + timedelta(hours=6)
        profile = optimizer.calculate_light_profile(midday, wake_time, sleep_time)
        
        # Should be bright with high CCT
        assert profile['cct_kelvin'] == optimizer.baseline_cct
        assert profile['dimming_percent'] == 100
        assert profile['blue_light_reduced'] == False


class TestEnvironmentalIntegration:
    """Integration tests for environmental control"""
    
    def test_full_control_loop_heating(self):
        """Test full control loop for heating scenario"""
        engine = HVACEngine()
        aq = AirQualityController()
        
        # Cold room, needs heating
        hvac_result = engine.calculate_hvac_output(
            current_temp=18.0,
            setpoint=22.0,
            outdoor_temp=5.0
        )
        
        # Air quality adjustment
        aq_result = aq.calculate_ventilation_demand(
            co2_ppm=1000,
            voc_ppb=100,
            pm25=20,
            humidity=45,
            occupancy_count=2
        )
        
        # Both should indicate active system
        assert hvac_result['mode'] == 'heating'
        assert hvac_result['compressor_speed_hz'] > 30  # Running at some speed
        assert aq_result['ventilation_cfm'] > aq.baseline_cfm
    
    def test_full_control_loop_cooling(self):
        """Test full control loop for cooling scenario"""
        engine = HVACEngine()
        aq = AirQualityController()
        
        # Hot room, needs cooling
        hvac_result = engine.calculate_hvac_output(
            current_temp=28.0,
            setpoint=22.0,
            outdoor_temp=35.0
        )
        
        # Air quality adjustment (high PM2.5 from heat)
        aq_result = aq.calculate_ventilation_demand(
            co2_ppm=1100,
            voc_ppb=150,
            pm25=45,
            humidity=60,
            occupancy_count=3
        )
        
        # Both should indicate cooling
        assert hvac_result['mode'] == 'cooling'
        assert hvac_result['hvac_output_percent'] < 0
        assert hvac_result['compressor_speed_hz'] > 30
        assert aq_result['air_purifier_needed'] == False  # PM2.5 = 45 < 55 threshold


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================
# These tests require FastAPI TestClient fixtures and environmental zone setup
# To enable, add the following to conftest.py:
#   - Create EnvironmentalZone fixtures
#   - Add environmental_zone route to main.py app.include_router()
#   - Create auth_headers fixture for authenticated requests


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
