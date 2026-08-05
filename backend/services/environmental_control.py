"""
HVAC Control Engine - Precision Climate Control Algorithms
PID-based heating/cooling with occupancy and weather-aware optimization
"""
import math
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class HVACState:
    """Current HVAC system state"""
    compressor_speed_hz: float
    fan_speed_percent: float
    mode: str  # heating, cooling, idle
    hvac_output_percent: float
    deadband_active: bool


class PIDController:
    """Proportional-Integral-Derivative controller for HVAC"""
    
    def __init__(self, kp=0.8, ki=0.05, kd=0.15, update_interval=30):
        """
        Initialize PID controller
        kp: Proportional gain (immediate response)
        ki: Integral gain (steady-state error correction)
        kd: Derivative gain (smooth response, prevent overshoot)
        update_interval: Sensor update interval in seconds
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = update_interval
        
        self.error_sum = 0.0
        self.last_error = 0.0
        self.integral_max = 500.0  # Anti-windup limit
        
        self.deadband_threshold = 0.3  # ±0.3°C deadband
        self.response_history = []
    
    def compute(self, current_temp: float, setpoint: float, 
                outdoor_temp: float) -> float:
        """
        Calculate HVAC output (-100 to +100%)
        Negative = cooling, Positive = heating
        """
        error = setpoint - current_temp
        
        # Proportional term - immediate response
        p_term = self.kp * error
        
        # Integral term - accumulated error correction
        self.error_sum += error * self.dt
        self.error_sum = max(-self.integral_max, 
                             min(self.integral_max, self.error_sum))
        i_term = self.ki * self.error_sum
        
        # Derivative term - smooth response, dampen oscillation
        d_term = self.kd * (error - self.last_error) / self.dt
        self.last_error = error
        
        # PID output
        hvac_output = p_term + i_term + d_term
        
        # Deadband reduction - prevent short-cycling
        if abs(error) < self.deadband_threshold:
            hvac_output *= 0.2  # Reduce output when near setpoint
        
        # Outdoor temperature efficiency adjustment
        if outdoor_temp < 5:  # Cold weather - boost heating
            hvac_output *= 1.1
        elif outdoor_temp > 35:  # Hot weather - boost cooling
            hvac_output *= 1.15
        
        # Clamp to valid range
        return max(-100, min(100, hvac_output))


class HVACEngine:
    """
    Main HVAC control engine
    Manages heating, cooling, ventilation, and efficiency optimization
    """
    
    def __init__(self):
        self.pid_controller = PIDController()
        self.min_compressor_hz = 30
        self.max_compressor_hz = 120
        self.min_fan_speed = 20  # Minimum 20% to prevent stagnation
        self.max_fan_speed = 100
        
        # System constants
        self.max_cfm = 1200  # Maximum ventilation capacity
        self.baseline_cfm = 500  # Baseline fresh air requirement
        self.system_history = []
    
    def calculate_hvac_output(self, current_temp: float, setpoint: float,
                              outdoor_temp: float) -> Dict:
        """
        Main control loop - calculate HVAC output based on conditions
        """
        hvac_output = self.pid_controller.compute(
            current_temp, setpoint, outdoor_temp
        )
        
        # Determine mode based on error
        error = setpoint - current_temp
        if abs(error) < 0.5:
            mode = "idle"
        elif hvac_output > 0:
            mode = "heating"
        else:
            mode = "cooling"
        
        # Calculate compressor speed (30-120 Hz for variable-speed)
        compressor_speed_hz = self._calculate_compressor_speed(hvac_output)
        
        # Calculate fan speed (independent, can run for circulation)
        fan_speed_percent = self._calculate_fan_speed(hvac_output)
        
        return {
            'hvac_output_percent': hvac_output,
            'compressor_speed_hz': compressor_speed_hz,
            'fan_speed_percent': fan_speed_percent,
            'mode': mode,
            'deadband_active': abs(error) < self.pid_controller.deadband_threshold,
            'cop_estimate': self._estimate_cop(outdoor_temp, hvac_output)
        }
    
    def _calculate_compressor_speed(self, hvac_output: float) -> float:
        """
        Convert HVAC output (-100 to +100) to compressor frequency (Hz)
        Typical range: 30-120 Hz for variable-speed inverter compressor
        """
        if abs(hvac_output) < 5:
            return 0  # Compressor off (deadband)
        
        # Linear mapping from 0-100 abs(hvac_output) → min_hz to max_hz
        speed_hz = self.min_compressor_hz + \
                   (abs(hvac_output) / 100) * (self.max_compressor_hz - self.min_compressor_hz)
        
        return speed_hz
    
    def _calculate_fan_speed(self, hvac_output: float) -> float:
        """
        Calculate supply fan speed (0-100% PWM)
        Independent of heating/cooling; can run for circulation/filtration
        """
        # Base fan speed follows HVAC demand
        base_speed = max(self.min_fan_speed, abs(hvac_output) * 0.8)
        return min(self.max_fan_speed, base_speed)
    
    def _estimate_cop(self, outdoor_temp: float, hvac_output: float) -> float:
        """
        Estimate Coefficient of Performance based on conditions
        COP = useful heating/cooling output / compressor power input
        """
        # Baseline COP values
        cop_heating = 3.5
        cop_cooling = 3.8
        
        # Temperature affects efficiency
        if hvac_output > 0:  # Heating mode
            # Heating COP decreases in cold weather
            if outdoor_temp < 5:
                cop_heating *= 0.9
            elif outdoor_temp > 20:
                cop_heating *= 1.1
            return cop_heating
        else:  # Cooling mode
            # Cooling COP decreases in hot weather
            if outdoor_temp > 35:
                cop_cooling *= 0.85
            elif outdoor_temp < 20:
                cop_cooling *= 1.1
            return cop_cooling


class AirQualityController:
    """
    Automated ventilation and air quality management
    """
    
    def __init__(self):
        self.baseline_cfm = 500
        self.max_cfm = 1200
        
        # Health thresholds (from EPA/ASHRAE standards)
        self.co2_thresholds = {
            'excellent': 800,
            'good': 1200,
            'fair': 1800,
            'poor': float('inf')
        }
        
        self.pm25_thresholds = {
            'good': 12,
            'moderate': 35,
            'sensitive': 55,
            'unhealthy': 150,
            'very_unhealthy': 250
        }
        
        self.humidity_optimal = (40, 60)  # 40-60% is optimal
        self.voc_threshold_high = 500  # ppb
        
        self.ashrae_cfm_per_person = 7.5  # ASHRAE Standard 62.2
    
    def calculate_ventilation_demand(self, co2_ppm: float, voc_ppb: float,
                                     pm25: float, humidity: float,
                                     occupancy_count: int) -> Dict:
        """
        Calculate required ventilation (CFM) based on multiple metrics
        """
        ventilation_cfm = self.baseline_cfm
        air_purifier_needed = False
        exhaust_boost = False
        alerts = []
        
        # CO₂-based demand (occupancy-driven) - ASHRAE 7.5 CFM per person baseline
        co2_ventilation = self.baseline_cfm + (occupancy_count * self.ashrae_cfm_per_person)
        
        # Excess CO₂ ramps up ventilation
        if co2_ppm > 800:
            excess_co2 = co2_ppm - 800
            co2_ventilation += (excess_co2 / 100) * 50  # ~50 CFM per 100 ppm excess
            
            severity = 'fair' if co2_ppm < 1800 else 'poor'
            alerts.append({
                'type': 'co2_high',
                'value': co2_ppm,
                'severity': severity
            })
        
        # VOC handling
        if voc_ppb > 200:
            co2_ventilation += (voc_ppb - 200) / 50  # ~4 CFM per 50 ppb
            
            if voc_ppb > self.voc_threshold_high:
                air_purifier_needed = True
                alerts.append({
                    'type': 'voc_high',
                    'value': voc_ppb,
                    'severity': 'high'
                })
        
        # PM2.5 handling
        if pm25 > self.pm25_thresholds['sensitive']:
            air_purifier_needed = True
            alerts.append({
                'type': 'pm25_high',
                'value': pm25,
                'severity': 'high' if pm25 > 150 else 'medium'
            })
        
        # Humidity control
        if humidity > 65:
            exhaust_boost = True
            ventilation_cfm += 100  # Extra exhaust
            alerts.append({
                'type': 'humidity_high',
                'value': humidity,
                'severity': 'medium'
            })
        elif humidity < 30:
            alerts.append({
                'type': 'humidity_low',
                'value': humidity,
                'severity': 'low'
            })
        
        # Calculate final ventilation - take maximum of baseline requirements
        ventilation_cfm = max(ventilation_cfm, co2_ventilation)
        ventilation_cfm = max(self.baseline_cfm, min(self.max_cfm, ventilation_cfm))
        
        # Convert to fan speed percentage
        fan_speed_percent = (ventilation_cfm / self.max_cfm) * 100
        fan_speed_percent = max(20, fan_speed_percent)  # Minimum 20%
        
        return {
            'ventilation_cfm': ventilation_cfm,
            'fan_speed_percent': fan_speed_percent,
            'exhaust_boost': exhaust_boost,
            'air_purifier_needed': air_purifier_needed,
            'fresh_air_fraction': min(1.0, ventilation_cfm / self.max_cfm),
            'alerts': alerts
        }
    
    def detect_anomalies(self, co2_ppm: float, voc_ppb: float,
                        pm25: float, room_type: str) -> list:
        """
        Detect pollution sources and anomalies
        """
        anomalies = []
        
        # High CO₂ spike - possible occupancy surge
        if co2_ppm > 1500 and room_type in ['kitchen', 'living_room']:
            anomalies.append({
                'source': 'high_occupancy_or_cooking',
                'severity': 'medium',
                'action': 'increase_ventilation'
            })
        
        # VOC spike - chemical off-gassing
        if voc_ppb > 300:
            anomalies.append({
                'source': 'chemical_emission',
                'severity': 'high' if voc_ppb > 500 else 'medium',
                'action': 'activate_air_purifier_and_ventilate'
            })
        
        # Kitchen-specific: rapid CO₂ increase (cooking)
        if room_type == 'kitchen' and co2_ppm > 2000:
            anomalies.append({
                'source': 'range_hood_activation_needed',
                'severity': 'high',
                'action': 'boost_exhaust_fan'
            })
        
        return anomalies
    
    def get_filter_status(self, runtime_hours: float, 
                         pressure_drop_pa: float) -> Dict:
        """
        Monitor filter health based on runtime and pressure differential
        """
        filter_life_percent = (runtime_hours / 3000) * 100  # 3000 hour service life
        
        # Determine status based on pressure drop (new=0.1", dirty=0.3")
        if pressure_drop_pa > 25:  # 0.3" wg = 25 Pa
            status = 'replace_immediately'
            alert_level = 'high'
            efficiency_loss = 0.15
        elif pressure_drop_pa > 20 or filter_life_percent > 80:
            status = 'replace_soon'
            alert_level = 'medium'
            efficiency_loss = 0.08
        else:
            status = 'operational'
            alert_level = 'none'
            efficiency_loss = 0.02
        
        return {
            'status': status,
            'life_percent': filter_life_percent,
            'alert_level': alert_level,
            'fan_efficiency_loss': efficiency_loss
        }


class CircadianOptimizer:
    """
    Integrate circadian rhythm for sleep optimization
    """
    
    def __init__(self):
        self.baseline_cct = 6500  # Kelvin (daylight)
        self.sleep_cct = 2700  # Kelvin (warm evening)
        self.baseline_temp = 22.0
        self.circadian_swing = 1.5  # ±1.5°C natural body temperature swing
    
    def calculate_circadian_temperature(self, current_time: datetime,
                                       wake_time: datetime,
                                       sleep_time: datetime) -> float:
        """
        Calculate optimal temperature following 24-hour circadian rhythm
        Core body temperature is highest at ~5 PM, lowest at ~5 AM
        """
        hours_since_wake = (current_time - wake_time).total_seconds() / 3600
        
        # Sine wave approximation of circadian cycle
        # Peak at ~13 hours after wake (assuming 9-hour sleep)
        circadian_phase = (hours_since_wake - 9) / 24.0
        circadian_offset = math.sin(2 * math.pi * circadian_phase) * self.circadian_swing
        
        return self.baseline_temp + circadian_offset
    
    def calculate_light_profile(self, current_time: datetime,
                               wake_time: datetime,
                               sleep_time: datetime) -> Dict:
        """
        Calculate optimal light color temperature and dimming
        """
        hours_to_sleep = (sleep_time - current_time).total_seconds() / 3600
        
        # Pre-sleep phase (2 hours before bed) - ramp down blue light
        if 0 < hours_to_sleep < 2:
            progress = (2 - hours_to_sleep) / 2.0  # 0 to 1 over 2 hours
            cct = self.baseline_cct - (progress * (self.baseline_cct - self.sleep_cct))
            dimming = 100 - (progress * 80)  # 100% → 20%
        else:
            # Normal daytime: bright, high CCT
            cct = self.baseline_cct
            dimming = 100
        
        return {
            'cct_kelvin': cct,
            'dimming_percent': dimming,
            'blue_light_reduced': hours_to_sleep < 2
        }
