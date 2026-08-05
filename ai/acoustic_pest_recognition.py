"""Acoustic pest recognition model for Aegis.

This module implements a PyTorch-based acoustic pest classification pipeline.
It can generate synthetic training data, train a lightweight classifier,
and infer pest labels from acoustic sensor features.
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

try:
    import librosa
except ImportError:
    librosa = None

logger = logging.getLogger(__name__)


class AcousticFeatureDataset(Dataset):
    def __init__(self, features: np.ndarray, labels: np.ndarray):
        if TORCH_AVAILABLE:
            self.features = torch.from_numpy(features).float()
            self.labels = torch.from_numpy(labels).long()
        else:
            self.features = features
            self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class AcousticPestRecognitionModel(nn.Module if TORCH_AVAILABLE else object):
    def __init__(self, input_dim: int, output_dim: int):
        if TORCH_AVAILABLE:
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.BatchNorm1d(64),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim)
            )
        else:
            self.network = None

    def forward(self, x):
        if TORCH_AVAILABLE and self.network is not None:
            return self.network(x)
        else:
            raise RuntimeError("PyTorch is required for model forward pass")



class AcousticPestRecognitionEngine:
    LABELS = [
        "UNKNOWN",
        "APHID",
        "BEETLE",
        "CATERPILLAR",
        "WHITEFLY",
        "THRIPS",
        "SPIDER_MITE",
        "NEMATODE",
        "CUTWORM",
        "ARMYWORM",
        "LOCUST"
    ]

    FEATURE_MEAN = np.array([500.0, 0.5, 30.0, 22.0, 55.0, 2.0], dtype=np.float32)
    FEATURE_STD = np.array([500.0, 0.25, 20.0, 7.0, 20.0, 1.5], dtype=np.float32)

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.trained = False
        self.device = torch.device("cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu") if TORCH_AVAILABLE else None
        self.model = None

        if TORCH_AVAILABLE and model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def _normalize(self, features: np.ndarray) -> np.ndarray:
        return (features - self.FEATURE_MEAN) / np.maximum(self.FEATURE_STD, 1e-6)

    def _build_model(self) -> Optional[AcousticPestRecognitionModel]:
        if not TORCH_AVAILABLE:
            return None
        model = AcousticPestRecognitionModel(input_dim=6, output_dim=len(self.LABELS))
        return model.to(self.device)

    def _heuristic_predict(self, features: np.ndarray) -> Dict[str, Any]:
        frequency_hz, amplitude, background_noise, temperature_c, humidity_percent, wind_speed_ms = features

        score_map: Dict[str, float] = {}
        score_map["UNKNOWN"] = 0.5
        score_map["APHID"] = max(0.0, 1.0 - abs(frequency_hz - 200) / 300) * (1.0 - amplitude)
        score_map["BEETLE"] = max(0.0, 1.0 - abs(frequency_hz - 800) / 500) * amplitude
        score_map["CATERPILLAR"] = max(0.0, 1.0 - abs(frequency_hz - 2600) / 900) * (0.5 + amplitude / 2)
        score_map["WHITEFLY"] = max(0.0, 1.0 - abs(frequency_hz - 1200) / 600) * (0.8 - background_noise / 100)
        score_map["THRIPS"] = max(0.0, 1.0 - abs(frequency_hz - 1800) / 700) * (humidity_percent / 100)
        score_map["SPIDER_MITE"] = max(0.0, 1.0 - abs(frequency_hz - 90) / 200) * (1.0 - wind_speed_ms / 10)
        score_map["NEMATODE"] = max(0.0, 1.0 - abs(frequency_hz - 50) / 100) * (1.0 - temperature_c / 40)
        score_map["CUTWORM"] = max(0.0, 1.0 - abs(frequency_hz - 400) / 400) * amplitude
        score_map["ARMYWORM"] = max(0.0, 1.0 - abs(frequency_hz - 1000) / 700) * (0.4 + amplitude / 2)
        score_map["LOCUST"] = max(0.0, 1.0 - abs(frequency_hz - 1400) / 800) * (humidity_percent / 100)

        total = sum(score_map.values())
        if total <= 0:
            score_map = {key: 1.0 for key in score_map}
            total = len(score_map)

        probabilities = {key: value / total for key, value in score_map.items()}
        pest_type = max(probabilities, key=probabilities.get)
        confidence = float(probabilities[pest_type])

        return {
            "pest_type": pest_type,
            "confidence": confidence,
            "scores": probabilities
        }

    def predict_from_detection_features(
        self,
        frequency_hz: float,
        amplitude: float,
        background_noise: float,
        temperature_c: float,
        humidity_percent: float,
        wind_speed_ms: float
    ) -> Dict[str, Any]:
        features = np.asarray([
            frequency_hz,
            amplitude,
            background_noise,
            temperature_c,
            humidity_percent,
            wind_speed_ms
        ], dtype=np.float32)

        if self.trained and self.model is not None:
            self.model.eval()
            normalized = self._normalize(features)[None, :]
            x = torch.from_numpy(normalized).float().to(self.device)
            with torch.no_grad():
                logits = self.model(x)
                probabilities = torch.softmax(logits, dim=-1).cpu().numpy()[0]

            best_idx = int(np.argmax(probabilities))
            return {
                "pest_type": self.LABELS[best_idx],
                "confidence": float(probabilities[best_idx]),
                "scores": {label: float(prob) for label, prob in zip(self.LABELS, probabilities)}
            }

        return self._heuristic_predict(features)

    def extract_mel_spectrogram(
        self,
        audio_path: str,
        sr: int = 22050,
        n_mels: int = 64,
        n_fft: int = 2048,
        hop_length: int = 512
    ) -> np.ndarray:
        if librosa is None:
            raise RuntimeError("librosa is required for audio feature extraction")

        signal, sample_rate = librosa.load(audio_path, sr=sr, mono=True)
        mel_spec = librosa.feature.melspectrogram(
            y=signal,
            sr=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            fmin=20,
            fmax=sample_rate // 2
        )
        mel_db = librosa.power_to_db(mel_spec, ref=np.max)
        return mel_db.astype(np.float32)

    def generate_synthetic_dataset(self, samples_per_label: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        if samples_per_label <= 0:
            raise ValueError("samples_per_label must be a positive integer")

        features: List[np.ndarray] = []
        labels: List[int] = []

        label_generators = {
            "APHID": lambda: [np.random.normal(220, 80), np.random.uniform(0.1, 0.6), np.random.uniform(10, 40), np.random.uniform(18, 28), np.random.uniform(50, 80), np.random.uniform(0, 2)],
            "BEETLE": lambda: [np.random.normal(800, 250), np.random.uniform(0.2, 0.9), np.random.uniform(15, 45), np.random.uniform(20, 30), np.random.uniform(35, 75), np.random.uniform(0, 3)],
            "CATERPILLAR": lambda: [np.random.normal(2500, 700), np.random.uniform(0.3, 1.0), np.random.uniform(20, 50), np.random.uniform(18, 32), np.random.uniform(40, 85), np.random.uniform(0, 4)],
            "WHITEFLY": lambda: [np.random.normal(1200, 350), np.random.uniform(0.2, 0.8), np.random.uniform(10, 35), np.random.uniform(22, 32), np.random.uniform(45, 90), np.random.uniform(0, 3)],
            "THRIPS": lambda: [np.random.normal(1800, 400), np.random.uniform(0.1, 0.7), np.random.uniform(5, 30), np.random.uniform(20, 30), np.random.uniform(50, 90), np.random.uniform(0, 4)],
            "SPIDER_MITE": lambda: [np.random.normal(100, 50), np.random.uniform(0.05, 0.5), np.random.uniform(0, 25), np.random.uniform(20, 30), np.random.uniform(35, 70), np.random.uniform(0, 3)],
            "NEMATODE": lambda: [np.random.normal(60, 30), np.random.uniform(0.02, 0.4), np.random.uniform(0, 20), np.random.uniform(18, 25), np.random.uniform(40, 70), np.random.uniform(0, 2)],
            "CUTWORM": lambda: [np.random.normal(400, 150), np.random.uniform(0.2, 0.9), np.random.uniform(10, 40), np.random.uniform(18, 28), np.random.uniform(40, 80), np.random.uniform(0, 4)],
            "ARMYWORM": lambda: [np.random.normal(1000, 300), np.random.uniform(0.3, 0.95), np.random.uniform(15, 45), np.random.uniform(18, 30), np.random.uniform(40, 85), np.random.uniform(0, 4)],
            "LOCUST": lambda: [np.random.normal(1400, 450), np.random.uniform(0.2, 0.8), np.random.uniform(20, 50), np.random.uniform(22, 35), np.random.uniform(45, 85), np.random.uniform(0, 5)],
            "UNKNOWN": lambda: [np.random.uniform(20, 3000), np.random.uniform(0.0, 1.0), np.random.uniform(0, 80), np.random.uniform(15, 35), np.random.uniform(20, 90), np.random.uniform(0, 6)]
        }

        for label_name in self.LABELS:
            generator = label_generators.get(label_name, label_generators["UNKNOWN"])
            for _ in range(samples_per_label):
                features.append(np.asarray(generator(), dtype=np.float32))
                labels.append(self.LABELS.index(label_name))

        return np.vstack(features), np.asarray(labels, dtype=np.int64)

    def train(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        epochs: int = 20,
        batch_size: int = 32,
        learning_rate: float = 1e-3
    ) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for training the acoustic pest recognition model")

        if features.ndim != 2 or features.shape[1] != 6:
            raise ValueError("Features must be a 2D array with 6 columns")

        dataset = AcousticFeatureDataset(self._normalize(features), labels)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model = self._build_model()
        assert self.model is not None
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.CrossEntropyLoss()

        self.model.train()
        for epoch in range(epochs):
            epoch_loss = 0.0
            for batch_features, batch_labels in dataloader:
                batch_features = batch_features.to(self.device)
                batch_labels = batch_labels.to(self.device)

                optimizer.zero_grad()
                logits = self.model(batch_features)
                loss = criterion(logits, batch_labels)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            logger.info(f"[AcousticPestRecognition] Epoch {epoch+1}/{epochs} loss={epoch_loss / len(dataloader):.4f}")

        self.trained = True
        if self.model_path:
            self.save_model(self.model_path)

    def save_model(self, path: str) -> None:
        if not TORCH_AVAILABLE or self.model is None:
            raise RuntimeError("No PyTorch model is available to save")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.model.state_dict(), path)
        logger.info(f"Saved acoustic pest recognition model to {path}")

    def load_model(self, path: str) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to load the acoustic pest recognition model")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model path does not exist: {path}")

        self.model = self._build_model()
        assert self.model is not None
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.trained = True
        logger.info(f"Loaded acoustic pest recognition model from {path}")

    def predict_from_audio_file(self, audio_path: str) -> Dict[str, Any]:
        if librosa is None:
            raise RuntimeError("librosa is required for audio prediction")

        mel_spec = self.extract_mel_spectrogram(audio_path)
        features = np.asarray([
            np.mean(mel_spec),
            np.std(mel_spec),
            np.max(mel_spec),
            np.min(mel_spec),
            np.median(mel_spec),
            float(mel_spec.shape[0])
        ], dtype=np.float32)

        return self._heuristic_predict(features)

    def predict(self, features: Union[list, tuple, np.ndarray]) -> Dict[str, Any]:
        """Compatibility wrapper used by tests: accepts a feature vector and
        returns a simple dict with `prediction`, `confidence`, and `scores`.
        """
        arr = np.asarray(features, dtype=np.float32).flatten()
        # If a long duration-style feature was passed (e.g. mel spec stats),
        # try to pick the first 6 values; otherwise, pad/truncate to 6.
        if arr.size >= 6:
            f = arr[:6]
        else:
            f = np.zeros(6, dtype=np.float32)
            f[: arr.size] = arr

        res = self.predict_from_detection_features(
            float(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[4]), float(f[5])
        )

        return {
            "prediction": res.get("pest_type", "UNKNOWN"),
            "confidence": float(res.get("confidence", 0.0)),
            "scores": res.get("scores", {})
        }

