"""
Visual Crop Health Assessment Engine - Day 40

Machine learning system for detecting and classifying plant health status
from drone imagery and canopy sensor data.

Supports:
- Heuristic (rule-based) inference without training
- Neural network inference for learned patterns
- Multiple plant health conditions
- Real-time anomaly detection
- Integration with Vryndara orchestration engine
"""

import numpy as np
from enum import Enum
from typing import Dict, Tuple, List, Optional

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Placeholder classes for when torch is unavailable
    class nn:
        class Module:
            pass


class PlantHealthStatus(Enum):
    """Plant health status classifications."""
    HEALTHY = "HEALTHY"
    STRESS_EARLY = "STRESS_EARLY"
    STRESS_MODERATE = "STRESS_MODERATE"
    STRESS_SEVERE = "STRESS_SEVERE"
    DISEASE_DETECTED = "DISEASE_DETECTED"
    CRITICAL = "CRITICAL"


class CropHealthSensor(Enum):
    """Available crop health sensor types."""
    RGB_CAMERA = "rgb_camera"
    NDVI_SENSOR = "ndvi_sensor"  # Normalized Difference Vegetation Index
    THERMAL_CAMERA = "thermal_camera"
    MULTISPECTRAL = "multispectral"
    LIDAR = "lidar"
    CHLOROPHYLL_METER = "chlorophyll_meter"


class VisualCropHealthEngine:
    """Machine learning engine for plant health assessment from visual data."""
    
    def __init__(self):
        """Initialize the visual crop health engine."""
        self.model = None
        self.use_nn = False
        self.sensor_types = [sensor.value for sensor in CropHealthSensor]
        self.health_thresholds = {
            "ndvi": 0.6,  # Normalized Difference Vegetation Index threshold
            "chlorophyll": 50.0,  # SPAD units
            "temperature_stress": 5.0,  # °C deviation from optimal
            "canopy_cover": 75.0,  # %
            "leaf_area_index": 3.5,  # m²/m²
        }
    
    def predict_from_image_features(
        self,
        ndvi: float,  # Normalized Difference Vegetation Index (0-1)
        chlorophyll_content: float,  # SPAD units (0-100)
        canopy_temperature: float,  # °C
        ambient_temperature: float,  # °C
        canopy_cover: float,  # % (0-100)
        leaf_area_index: float,  # m²/m² (0-10)
        color_index: float = 0.5,  # RGB color health index (0-1)
        biomass_estimate: float = 0.5  # Estimated dry biomass (0-1)
    ) -> Dict[str, str]:
        """
        Predict crop health status from visual and image analysis features.
        
        Args:
            ndvi: Vegetation index (0-1, higher is healthier)
            chlorophyll_content: Leaf chlorophyll level (0-100 SPAD)
            canopy_temperature: Canopy surface temperature (°C)
            ambient_temperature: Ambient air temperature (°C)
            canopy_cover: Percent of ground covered by canopy (0-100)
            leaf_area_index: Leaf area per unit ground area (0-10)
            color_index: Visual color health metric (0-1)
            biomass_estimate: Estimated plant biomass (0-1)
        
        Returns:
            Dictionary with health status and confidence scores
        """
        # Normalize inputs
        # Temperature difference: optimal around 0°C, range -10 to +10°C maps to 0-1
        temp_diff = canopy_temperature - ambient_temperature
        temp_diff_norm = min(max((temp_diff + 10.0) / 20.0, 0), 1)  # clamp to 0-1
        
        features = np.array([
            ndvi,
            chlorophyll_content / 100.0,  # normalize to 0-1
            temp_diff_norm,
            canopy_cover / 100.0,
            leaf_area_index / 10.0,
            color_index,
            biomass_estimate
        ])
        
        # Use neural network if available, otherwise use heuristic
        if self.use_nn and self.model is not None:
            return self._predict_nn(features)
        else:
            return self._predict_heuristic(features)
    
    def _predict_heuristic(self, features: np.ndarray) -> Dict[str, str]:
        """Rule-based health prediction without neural network."""
        ndvi, chlorophyll, temp_diff_norm, canopy_norm, lai_norm, color, biomass = features
        
        # Calculate health indicators
        vegetation_health = ndvi * 0.4 + chlorophyll * 0.3 + color * 0.3
        
        # Temperature stress: 0.5 is optimal (0°C diff), lower or higher values = stress
        # Convert 0-1 scale to stress where 0.5 = 0 stress
        temp_stress = abs(temp_diff_norm - 0.5) * 2.0  # Range 0-1 where 0 is optimal
        
        # Canopy structure health
        canopy_health = canopy_norm * 0.5 + lai_norm * 0.5
        
        # Overall health score (weighted average)
        health_score = (vegetation_health * 0.45 + 
                       (1.0 - temp_stress) * 0.25 + 
                       canopy_health * 0.30)
        
        # Classify health status
        if health_score >= 0.80:
            status = PlantHealthStatus.HEALTHY.value
        elif health_score >= 0.65:
            status = PlantHealthStatus.STRESS_EARLY.value
        elif health_score >= 0.45:
            status = PlantHealthStatus.STRESS_MODERATE.value
        elif health_score >= 0.25:
            status = PlantHealthStatus.STRESS_SEVERE.value
        elif health_score >= 0.10:
            status = PlantHealthStatus.DISEASE_DETECTED.value
        else:
            status = PlantHealthStatus.CRITICAL.value
        
        return {
            "status": status,
            "health_score": round(health_score, 3),
            "vegetation_health": round(vegetation_health, 3),
            "temperature_stress": round(temp_stress, 3),
            "canopy_health": round(canopy_health, 3)
        }
    
    def _predict_nn(self, features: np.ndarray) -> Dict[str, str]:
        """Neural network-based health prediction."""
        if self.model is None:
            return self._predict_heuristic(features)
        
        try:
            tensor = torch.FloatTensor(features).unsqueeze(0)
            with torch.no_grad():
                output = self.model(tensor)
            
            # Output is health score (0-1)
            health_score = float(output[0, 0])
            
            # Classify based on score
            if health_score >= 0.85:
                status = PlantHealthStatus.HEALTHY.value
            elif health_score >= 0.70:
                status = PlantHealthStatus.STRESS_EARLY.value
            elif health_score >= 0.50:
                status = PlantHealthStatus.STRESS_MODERATE.value
            elif health_score >= 0.30:
                status = PlantHealthStatus.STRESS_SEVERE.value
            elif health_score >= 0.10:
                status = PlantHealthStatus.DISEASE_DETECTED.value
            else:
                status = PlantHealthStatus.CRITICAL.value
            
            return {
                "status": status,
                "health_score": round(health_score, 3)
            }
        except Exception:
            return self._predict_heuristic(features)
    
    def get_health_recommendations(self, status: str) -> Dict[str, any]:
        """
        Generate agronomic recommendations based on health status.
        
        Args:
            status: Plant health status
        
        Returns:
            Dictionary with recommended actions and priorities
        """
        recommendations = {
            PlantHealthStatus.HEALTHY.value: {
                "status": "Healthy",
                "priority": 0,
                "actions": ["Continue routine monitoring", "Maintain current care"],
                "frequency_days": 7
            },
            PlantHealthStatus.STRESS_EARLY.value: {
                "status": "Early Stress",
                "priority": 3,
                "actions": ["Increase irrigation monitoring", "Check nutrient levels", "Inspect for pests"],
                "frequency_days": 3
            },
            PlantHealthStatus.STRESS_MODERATE.value: {
                "status": "Moderate Stress",
                "priority": 6,
                "actions": ["Adjust irrigation schedule", "Apply foliar nutrients", "Remove affected leaves", "Monitor disease"],
                "frequency_days": 2
            },
            PlantHealthStatus.STRESS_SEVERE.value: {
                "status": "Severe Stress",
                "priority": 8,
                "actions": ["Emergency irrigation", "Heavy nutrient application", "Prune severely affected areas", "Isolate if diseased"],
                "frequency_days": 1
            },
            PlantHealthStatus.DISEASE_DETECTED.value: {
                "status": "Disease Detected",
                "priority": 9,
                "actions": ["Apply fungicide/pesticide", "Isolate plant immediately", "Increase airflow", "Remove infected parts"],
                "frequency_days": 1
            },
            PlantHealthStatus.CRITICAL.value: {
                "status": "Critical",
                "priority": 10,
                "actions": ["Immediate intervention required", "Consider harvesting", "Remove from biosphere", "Quarantine zone"],
                "frequency_days": 1
            }
        }
        
        return recommendations.get(status, recommendations[PlantHealthStatus.HEALTHY.value])
    
    def generate_synthetic_dataset(self, samples_per_condition: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic training data for different crop health conditions.
        
        Args:
            samples_per_condition: Number of samples per health condition
        
        Returns:
            Tuple of (features array, labels array)
        """
        conditions = {
            "healthy": {
                "ndvi": (0.75, 0.95),
                "chlorophyll": (65, 85),
                "temp_diff": (-2, 2),
                "canopy": (80, 100),
                "lai": (3.5, 5.0),
                "color": (0.75, 1.0),
                "biomass": (0.75, 1.0),
                "label": 0.9
            },
            "stress_early": {
                "ndvi": (0.60, 0.75),
                "chlorophyll": (50, 65),
                "temp_diff": (2, 5),
                "canopy": (65, 80),
                "lai": (2.5, 3.5),
                "color": (0.60, 0.75),
                "biomass": (0.60, 0.75),
                "label": 0.70
            },
            "stress_moderate": {
                "ndvi": (0.45, 0.60),
                "chlorophyll": (35, 50),
                "temp_diff": (5, 8),
                "canopy": (50, 65),
                "lai": (1.5, 2.5),
                "color": (0.45, 0.60),
                "biomass": (0.45, 0.60),
                "label": 0.50
            },
            "stress_severe": {
                "ndvi": (0.25, 0.45),
                "chlorophyll": (20, 35),
                "temp_diff": (8, 12),
                "canopy": (30, 50),
                "lai": (0.5, 1.5),
                "color": (0.25, 0.45),
                "biomass": (0.25, 0.45),
                "label": 0.25
            },
            "disease": {
                "ndvi": (0.10, 0.25),
                "chlorophyll": (5, 20),
                "temp_diff": (-5, -10),  # Can be cooler with disease
                "canopy": (10, 30),
                "lai": (0.1, 0.5),
                "color": (0.10, 0.25),
                "biomass": (0.10, 0.25),
                "label": 0.15
            },
            "critical": {
                "ndvi": (0.0, 0.10),
                "chlorophyll": (0, 5),
                "temp_diff": (-15, -8),  # Dead tissue cooler
                "canopy": (0, 10),
                "lai": (0.0, 0.1),
                "color": (0.0, 0.10),
                "biomass": (0.0, 0.10),
                "label": 0.05
            }
        }
        
        all_features = []
        all_labels = []
        
        for condition, params in conditions.items():
            for _ in range(samples_per_condition):
                ndvi = np.random.uniform(*params["ndvi"])
                chlorophyll = np.random.uniform(*params["chlorophyll"])
                temp_diff = np.random.uniform(*params["temp_diff"])
                canopy = np.random.uniform(*params["canopy"])
                lai = np.random.uniform(*params["lai"])
                color = np.random.uniform(*params["color"])
                biomass = np.random.uniform(*params["biomass"])
                
                # Normalize features
                features = np.array([
                    ndvi,
                    chlorophyll / 100.0,
                    (temp_diff + 20) / 40.0,  # normalize to 0-1
                    canopy / 100.0,
                    lai / 10.0,
                    color,
                    biomass
                ])
                
                all_features.append(features)
                all_labels.append(params["label"])
        
        return np.array(all_features), np.array(all_labels)
    
    def train(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        epochs: int = 20,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> Tuple[List[float], Optional['nn.Module']]:
        """
        Train neural network model on provided data.
        
        Args:
            features: Input features array (N, 7)
            labels: Health score labels array (N,)
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
        
        Returns:
            Tuple of (loss history, trained model)
        """
        if not TORCH_AVAILABLE:
            return [], None
        
        # Create model
        model = CropHealthNN(input_size=7, hidden_size=32)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        loss_fn = nn.MSELoss()
        
        features_tensor = torch.FloatTensor(features)
        labels_tensor = torch.FloatTensor(labels).unsqueeze(1)
        
        losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            for i in range(0, len(features), batch_size):
                batch_features = features_tensor[i:i+batch_size]
                batch_labels = labels_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = loss_fn(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / (len(features) // batch_size + 1)
            losses.append(avg_loss)
        
        self.model = model
        self.use_nn = True
        
        return losses, model
    
    def load_model(self, model: Optional['nn.Module']) -> None:
        """Load a pre-trained model."""
        self.model = model
        self.use_nn = model is not None


class CropHealthNN(nn.Module if TORCH_AVAILABLE else object):
    """Neural network for crop health prediction."""
    
    def __init__(self, input_size: int = 7, hidden_size: int = 32):
        """Initialize the network."""
        if TORCH_AVAILABLE:
            super().__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_size, 16)
            self.fc3 = nn.Linear(16, 1)
            self.sigmoid = nn.Sigmoid()
        else:
            self.fc1 = None
    
    def forward(self, x) -> 'torch.Tensor':
        """Forward pass through network."""
        if self.fc1 is None:
            return None
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.sigmoid(self.fc3(x))  # Output 0-1
        return x


if __name__ == "__main__":
    # Example usage
    engine = VisualCropHealthEngine()
    
    # Test heuristic prediction
    print("Testing heuristic prediction...")
    result = engine.predict_from_image_features(
        ndvi=0.75,
        chlorophyll_content=70,
        canopy_temperature=25,
        ambient_temperature=22,
        canopy_cover=85,
        leaf_area_index=4.0,
        color_index=0.8,
        biomass_estimate=0.8
    )
    print(f"Health Status: {result}")
    
    # Test recommendations
    print(f"\nRecommendations: {engine.get_health_recommendations(result['status'])}")
    
    # Test dataset generation
    print("\nGenerating synthetic dataset...")
    features, labels = engine.generate_synthetic_dataset(samples_per_condition=50)
    print(f"Features shape: {features.shape}, Labels shape: {labels.shape}")
