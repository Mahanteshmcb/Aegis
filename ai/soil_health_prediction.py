"""Soil health prediction model for Aegis.

This module implements a PyTorch-based soil nutrient prediction pipeline.
It predicts N-P-K (Nitrogen, Phosphorus, Potassium) levels from mycelial sensor data,
generates training data, and provides soil rehabilitation recommendations.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None
    DataLoader = None
    # Provide a placeholder Dataset class for when torch is not available
    class Dataset:
        pass

logger = logging.getLogger(__name__)


class SoilNutrientDataset(Dataset):
    def __init__(self, features: np.ndarray, labels: np.ndarray):
        if TORCH_AVAILABLE:
            self.features = torch.from_numpy(features).float()
            self.labels = torch.from_numpy(labels).float()
        else:
            self.features = features
            self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class SoilHealthPredictionModel(nn.Module if TORCH_AVAILABLE else object):
    def __init__(self, input_dim: int = 8, output_dim: int = 3):
        if TORCH_AVAILABLE:
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.BatchNorm1d(64),
                nn.Dropout(0.2),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, output_dim),
                nn.Sigmoid()  # Output normalized to [0, 1]
            )
        else:
            self.network = None

    def forward(self, x):
        if TORCH_AVAILABLE and self.network is not None:
            return self.network(x)
        else:
            raise RuntimeError("PyTorch is required for model forward pass")


class SoilHealthPredictionEngine:
    """
    ML engine for predicting soil nutrient levels (N, P, K) from mycelial sensor data.
    """

    # Mycelial sensor data types (from gRPC sensors.proto)
    SENSOR_TYPES = [
        "MYCELIAL_BIOMASS",
        "NUTRIENT_TRANSPORT",
        "WATER_CONTENT",
        "PH_LEVEL",
        "ELECTRICAL_ACTIVITY",
        "SPORE_CONCENTRATION",
        "ROOT_COLONIZATION",
        "DECOMPOSITION_RATE"
    ]

    # Nutrient types to predict
    NUTRIENTS = ["NITROGEN", "PHOSPHORUS", "POTASSIUM"]

    # Feature normalization parameters (derived from soil monitoring data)
    FEATURE_MEAN = np.array([0.5, 50.0, 0.6, 6.5, 2.5, 500.0, 0.5, 0.05], dtype=np.float32)
    FEATURE_STD = np.array([0.3, 40.0, 0.3, 0.8, 1.5, 300.0, 0.3, 0.03], dtype=np.float32)

    # Optimal nutrient levels for healthy crops
    OPTIMAL_LEVELS = {
        "NITROGEN": 0.7,
        "PHOSPHORUS": 0.6,
        "POTASSIUM": 0.7
    }

    # Critical thresholds for intervention (< 30% of optimal)
    CRITICAL_THRESHOLD = 0.3

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.trained = False
        self.device = torch.device("cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu") if TORCH_AVAILABLE else None
        self.model = None

        if TORCH_AVAILABLE and model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def _normalize(self, features: np.ndarray) -> np.ndarray:
        """Normalize features using mean and std."""
        return (features - self.FEATURE_MEAN) / np.maximum(self.FEATURE_STD, 1e-6)

    def _build_model(self) -> Optional[SoilHealthPredictionModel]:
        if not TORCH_AVAILABLE:
            return None
        model = SoilHealthPredictionModel(input_dim=8, output_dim=3)
        return model.to(self.device)

    def _heuristic_predict(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Heuristic-based N-P-K prediction without trained model.
        Uses correlations between mycelial data and nutrient availability.
        """
        biomass, nut_transport, water_content, ph_level, elec_activity, spores, root_col, decomp = features

        # Nitrogen: Correlates with mycelial biomass, nutrient transport, decomposition
        nitrogen = (
            0.3 * biomass +
            0.4 * (nut_transport / 100.0) +
            0.2 * (1.0 - abs(ph_level - 6.8) / 2.0) +
            0.1 * decomp / 0.1
        )
        nitrogen = min(1.0, max(0.0, nitrogen))

        # Phosphorus: Correlates with electrical activity, pH, water content
        phosphorus = (
            0.3 * (elec_activity / 5.0) +
            0.3 * water_content +
            0.25 * (1.0 - abs(ph_level - 6.5) / 1.5) +
            0.15 * root_col
        )
        phosphorus = min(1.0, max(0.0, phosphorus))

        # Potassium: Correlates with water content, electrical activity, spore concentration
        potassium = (
            0.35 * water_content +
            0.35 * (elec_activity / 5.0) +
            0.15 * (spores / 1000.0) +
            0.15 * root_col
        )
        potassium = min(1.0, max(0.0, potassium))

        predictions = np.array([nitrogen, phosphorus, potassium], dtype=np.float32)

        return {
            "nitrogen": float(nitrogen),
            "phosphorus": float(phosphorus),
            "potassium": float(potassium),
            "predictions": predictions,
            "status": self._classify_status(predictions)
        }

    def _classify_status(self, predictions: np.ndarray) -> Dict[str, str]:
        """Classify nutrient status based on predicted levels."""
        status = {}
        for i, nutrient in enumerate(self.NUTRIENTS):
            level = predictions[i]
            optimal = self.OPTIMAL_LEVELS[nutrient]

            if level < self.CRITICAL_THRESHOLD * optimal:
                status[nutrient] = "CRITICAL"
            elif level < 0.5 * optimal:
                status[nutrient] = "DEFICIENT"
            elif level < 0.85 * optimal:
                status[nutrient] = "SUBOPTIMAL"
            elif level > 1.2 * optimal:
                status[nutrient] = "EXCESS"
            else:
                status[nutrient] = "OPTIMAL"

        return status

    def predict_from_mycelial_data(
        self,
        biomass: float,
        nutrient_transport: float,
        water_content: float,
        ph_level: float,
        electrical_activity: float,
        spore_concentration: float,
        root_colonization: float,
        decomposition_rate: float
    ) -> Dict[str, Any]:
        """
        Predict N-P-K levels from mycelial sensor data.

        Args:
            biomass: Mycelial biomass density (0-1)
            nutrient_transport: Nutrient transport rate (0-100 μg/min)
            water_content: Water content percentage (0-1)
            ph_level: Soil pH (0-14, typically 4-8)
            electrical_activity: Electrical conductivity (0-10 μS/cm)
            spore_concentration: Spore count (0-10000 spores/m³)
            root_colonization: Root colonization ratio (0-1)
            decomposition_rate: Decomposition rate (0-0.5 g/day)

        Returns:
            Dictionary with N, P, K predictions and status
        """
        features = np.asarray([
            biomass,
            nutrient_transport,
            water_content,
            ph_level,
            electrical_activity,
            spore_concentration,
            root_colonization,
            decomposition_rate
        ], dtype=np.float32)

        if self.trained and self.model is not None:
            self.model.eval()
            normalized = self._normalize(features)[None, :]
            x = torch.from_numpy(normalized).float().to(self.device)
            with torch.no_grad():
                predictions = self.model(x).cpu().numpy()[0]

            return {
                "nitrogen": float(predictions[0]),
                "phosphorus": float(predictions[1]),
                "potassium": float(predictions[2]),
                "predictions": predictions,
                "status": self._classify_status(predictions)
            }

        result = self._heuristic_predict(features)
        result["method"] = "heuristic"
        return result

    def predict_npk(self, features: Union[list, tuple, np.ndarray]) -> Dict[str, Any]:
        """Compatibility wrapper used by tests: accepts a feature vector and
        returns nitrogen/phosphorus/potassium predictions as a dict.
        """
        arr = np.asarray(features, dtype=np.float32).flatten()
        if arr.size >= 8:
            f = arr[:8]
        else:
            # If shorter, pad with zeros
            f = np.zeros(8, dtype=np.float32)
            f[: arr.size] = arr

        res = self.predict_from_mycelial_data(
            float(f[0]), float(f[1]), float(f[2]), float(f[3]),
            float(f[4]), float(f[5]), float(f[6]), float(f[7])
        )

        # Return only numeric fields expected by tests
        return {
            "nitrogen": float(res.get("nitrogen", 0.0)),
            "phosphorus": float(res.get("phosphorus", 0.0)),
            "potassium": float(res.get("potassium", 0.0)),
        }

    def get_rehabilitation_recommendations(self, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate soil rehabilitation recommendations based on nutrient predictions.

        Returns:
            List of recommended actions with priority and dosage
        """
        status = predictions.get("status", {})
        recommendations = []

        # Nitrogen recommendations
        n_level = predictions.get("nitrogen", 0.5)
        n_status = status.get("NITROGEN", "SUBOPTIMAL")
        if n_status in ["CRITICAL", "DEFICIENT"]:
            recommendations.append({
                "nutrient": "NITROGEN",
                "status": n_status,
                "priority": 9 if n_status == "CRITICAL" else 7,
                "action": "Apply nitrogen fertilizer",
                "dosage": self._calculate_fertilizer_dosage("NITROGEN", n_level),
                "method": "broadcast" if n_status == "CRITICAL" else "targeted"
            })

        # Phosphorus recommendations
        p_level = predictions.get("phosphorus", 0.5)
        p_status = status.get("PHOSPHORUS", "SUBOPTIMAL")
        if p_status in ["CRITICAL", "DEFICIENT"]:
            recommendations.append({
                "nutrient": "PHOSPHORUS",
                "status": p_status,
                "priority": 8 if p_status == "CRITICAL" else 6,
                "action": "Apply phosphorus fertilizer",
                "dosage": self._calculate_fertilizer_dosage("PHOSPHORUS", p_level),
                "method": "targeted"
            })

        # Potassium recommendations
        k_level = predictions.get("potassium", 0.5)
        k_status = status.get("POTASSIUM", "SUBOPTIMAL")
        if k_status in ["CRITICAL", "DEFICIENT"]:
            recommendations.append({
                "nutrient": "POTASSIUM",
                "status": k_status,
                "priority": 8 if k_status == "CRITICAL" else 6,
                "action": "Apply potassium fertilizer",
                "dosage": self._calculate_fertilizer_dosage("POTASSIUM", k_level),
                "method": "broadcast"
            })

        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x["priority"], reverse=True)

        return recommendations

    def _calculate_fertilizer_dosage(self, nutrient: str, current_level: float) -> Dict[str, float]:
        """
        Calculate fertilizer dosage based on current nutrient level.
        Returns dosage in kg/hectare.
        """
        optimal = self.OPTIMAL_LEVELS.get(nutrient, 0.7)
        deficit = max(0.0, optimal - current_level)

        # Base dosage adjusted by deficit magnitude
        base_dosages = {
            "NITROGEN": 100.0,  # kg/ha
            "PHOSPHORUS": 50.0,  # kg/ha (P2O5 equivalent)
            "POTASSIUM": 60.0  # kg/ha (K2O equivalent)
        }

        base = base_dosages.get(nutrient, 50.0)
        dosage = base * (deficit / optimal) if optimal > 0 else 0.0

        return {
            "amount_kgha": float(dosage),
            "product": f"{nutrient.lower()}_fertilizer",
            "application_rate": float(dosage / 100.0)  # Normalized 0-1
        }

    def generate_synthetic_dataset(self, samples_per_condition: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic mycelial sensor data with corresponding N-P-K labels.

        Returns:
            features: shape (N, 8), mycelial sensor readings
            labels: shape (N, 3), N-P-K normalized levels
        """
        if samples_per_condition <= 0:
            raise ValueError("samples_per_condition must be positive")

        features_list: List[np.ndarray] = []
        labels_list: List[np.ndarray] = []

        # Generate data for different soil conditions
        soil_conditions = {
            "healthy": {"n": 0.75, "p": 0.70, "k": 0.75},
            "nitrogen_deficient": {"n": 0.25, "p": 0.60, "k": 0.65},
            "phosphorus_deficient": {"n": 0.70, "p": 0.20, "k": 0.70},
            "potassium_deficient": {"n": 0.70, "p": 0.60, "k": 0.25},
            "degraded": {"n": 0.15, "p": 0.20, "k": 0.20},
            "rich": {"n": 0.90, "p": 0.85, "k": 0.90}
        }

        for condition, target_npk in soil_conditions.items():
            for _ in range(samples_per_condition):
                # Generate correlated mycelial data based on target NPK
                n_target = target_npk["n"]
                p_target = target_npk["p"]
                k_target = target_npk["k"]

                biomass = np.clip(n_target + np.random.normal(0, 0.15), 0, 1)
                nut_transport = np.clip((n_target + p_target) / 2 * 100 + np.random.normal(0, 15), 0, 100)
                water_content = np.clip(k_target + np.random.normal(0, 0.2), 0, 1)
                ph_level = 6.5 + np.random.normal(0, 0.5)
                elec_activity = (p_target + k_target) / 2 * 5 + np.random.normal(0, 0.5)
                elec_activity = np.clip(elec_activity, 0, 10)
                spores = int(np.clip(500 + n_target * 500 + np.random.normal(0, 100), 0, 2000))
                root_col = np.clip((n_target + p_target) / 2 + np.random.normal(0, 0.2), 0, 1)
                decomp = np.clip(n_target * 0.1 + np.random.normal(0, 0.02), 0, 0.5)

                features = np.array([
                    biomass, nut_transport, water_content, ph_level,
                    elec_activity, float(spores), root_col, decomp
                ], dtype=np.float32)

                labels = np.array([n_target, p_target, k_target], dtype=np.float32)

                features_list.append(features)
                labels_list.append(labels)

        return np.vstack(features_list), np.vstack(labels_list)

    def train(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        epochs: int = 30,
        batch_size: int = 32,
        learning_rate: float = 1e-3
    ) -> None:
        """
        Train the neural network model.

        Args:
            features: Training features, shape (N, 8)
            labels: Training labels (N-P-K), shape (N, 3)
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for training the soil health prediction model")

        if features.ndim != 2 or features.shape[1] != 8:
            raise ValueError("Features must be a 2D array with 8 columns")

        if labels.ndim != 2 or labels.shape[1] != 3:
            raise ValueError("Labels must be a 2D array with 3 columns (N, P, K)")

        dataset = SoilNutrientDataset(self._normalize(features), labels)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model = self._build_model()
        assert self.model is not None
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(epochs):
            epoch_loss = 0.0
            for batch_features, batch_labels in dataloader:
                batch_features = batch_features.to(self.device)
                batch_labels = batch_labels.to(self.device)

                optimizer.zero_grad()
                predictions = self.model(batch_features)
                loss = criterion(predictions, batch_labels)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            logger.info(f"[SoilHealthPrediction] Epoch {epoch+1}/{epochs} loss={avg_loss:.4f}")

        self.trained = True
        if self.model_path:
            self.save_model(self.model_path)

    def save_model(self, path: str) -> None:
        """Save the trained model to disk."""
        if not TORCH_AVAILABLE or self.model is None:
            raise RuntimeError("No PyTorch model is available to save")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.model.state_dict(), path)
        logger.info(f"Saved soil health prediction model to {path}")

    def load_model(self, path: str) -> None:
        """Load a trained model from disk."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to load the soil health prediction model")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model path does not exist: {path}")

        self.model = self._build_model()
        assert self.model is not None
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.trained = True
        logger.info(f"Loaded soil health prediction model from {path}")
