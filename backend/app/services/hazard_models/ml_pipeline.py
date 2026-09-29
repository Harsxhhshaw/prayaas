"""Machine Learning Landslide Susceptibility Pipeline.

Uses RandomForestClassifier to model non-linear interactions among terrain,
hydrology, and proximity geofactors.

Strict scientific constraints:
- If sufficient verified real inventory is absent: production model is marked
  UNTRAINED / INSUFFICIENT_REAL_DATA. Never fakes production metrics.
- Employs spatial block splitting to prevent spatial autocorrelation leakage.
- Exposes model-native feature importances for deterministic explainability.
"""

from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

FEATURE_NAMES = ["slope", "rainfall", "elevation", "road_distance"]


class MLSusceptibilityPipeline:
    """RandomForest-based hazard susceptibility training and inference pipeline."""

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_split=4,
            random_state=random_state,
        )
        self.is_trained: bool = False
        self.status: str = "UNTRAINED / INSUFFICIENT_REAL_DATA"
        self.validation_metrics: dict[str, Any] | None = None
        self.feature_importances: dict[str, float] = {}
        self.feature_names: list[str] = list(FEATURE_NAMES)

    def spatial_block_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        coords: np.ndarray,
        split_ratio: float = 0.75,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Performs a spatial block split based on geographic longitude/easting.

        Prevents naive random cross-validation leakage where geographically adjacent
        cells appear in both train and validation sets.
        """
        # Sort indices by longitude (coords[:, 0])
        sorted_idx = np.argsort(coords[:, 0])
        split_point = int(len(sorted_idx) * split_ratio)

        train_idx = sorted_idx[:split_point]
        val_idx = sorted_idx[split_point:]

        return X[train_idx], X[val_idx], y[train_idx], y[val_idx]

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        coords: np.ndarray | None = None,
        use_spatial_holdout: bool = True,
        feature_names: list[str] | None = None,
        spatial_blocks: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Trains model and evaluates strictly on holdout partition.

        Returns validation metrics and feature importances.
        """
        if feature_names is not None:
            self.feature_names = list(feature_names)

        n_samples = len(X)
        if n_samples < 20:
            return {
                "status": "INSUFFICIENT_DATA_FOR_RELIABLE_SPATIAL_VALIDATION",
                "training_count": n_samples,
                "validation_count": 0,
                "roc_auc": None,
                "accuracy": None,
                "feature_importances": {},
            }

        if spatial_blocks is not None:
            unique_blocks = np.unique(spatial_blocks)
            if len(unique_blocks) > 1:
                val_block = unique_blocks[-1]
                val_mask = spatial_blocks == val_block
                train_mask = ~val_mask
                X_train, X_val = X[train_mask], X[val_mask]
                y_train, y_val = y[train_mask], y[val_mask]
                spatial_used = True
            else:
                from sklearn.model_selection import train_test_split
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.25, random_state=self.random_state, stratify=y
                )
                spatial_used = False
        elif use_spatial_holdout and coords is not None and len(coords) == n_samples:
            X_train, X_val, y_train, y_val = self.spatial_block_split(X, y, coords)
            spatial_used = True
        else:
            from sklearn.model_selection import train_test_split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.25, random_state=self.random_state, stratify=y
            )
            spatial_used = False

        self.model.fit(X_train, y_train)
        self.is_trained = True
        self.status = "CALIBRATED_TEST_FIXTURE"

        # Predictions on validation holdout
        y_pred = self.model.predict(X_val)
        y_prob = self.model.predict_proba(X_val)[:, 1] if len(np.unique(y_train)) > 1 else y_pred

        roc_auc = float(roc_auc_score(y_val, y_prob)) if len(np.unique(y_val)) > 1 else None
        acc = float(accuracy_score(y_val, y_pred))
        prec = float(precision_score(y_val, y_pred, zero_division=0))
        rec = float(recall_score(y_val, y_pred, zero_division=0))
        f1 = float(f1_score(y_val, y_pred, zero_division=0))

        # Model-native feature importances
        names = self.feature_names if len(self.feature_names) == len(self.model.feature_importances_) else [f"f_{i}" for i in range(len(self.model.feature_importances_))]
        importances = dict(zip(names, [round(float(v), 4) for v in self.model.feature_importances_]))
        self.feature_importances = importances

        metrics = {
            "status": "VALIDATED",
            "training_count": len(X_train),
            "validation_count": len(X_val),
            "roc_auc": round(roc_auc, 3) if roc_auc is not None else None,
            "accuracy": round(acc, 3),
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
            "spatial_holdout_used": spatial_used,
            "feature_importances": importances,
        }
        self.validation_metrics = metrics
        return metrics

    def predict_susceptibility(self, features: dict[str, float] | list[float] | np.ndarray) -> dict[str, Any]:
        """Predicts susceptibility probability (0-100) and top driver features.

        Strict rule: Returns UNTRAINED status if no verified training occurred.
        """
        if not self.is_trained:
            return {
                "score": None,
                "status": "UNTRAINED / INSUFFICIENT_REAL_DATA",
                "reason": "Insufficient verified landslide inventory to train production ML model",
                "feature_importances": {},
            }

        if isinstance(features, dict):
            vec = [float(features.get(f, 0.0)) for f in self.feature_names]
            X = np.array(vec, dtype=float).reshape(1, -1)
        else:
            X = np.array(features, dtype=float).reshape(1, -1)

        prob = float(self.model.predict_proba(X)[0, 1])
        score = round(prob * 100.0, 1)

        return {
            "score": score,
            "status": self.status,
            "feature_importances": self.feature_importances,
            "model_type": "RandomForestClassifier (n=100, max_depth=6)",
        }

    def predict(self, feature_vector: list[float] | np.ndarray) -> dict[str, Any]:
        """Backward-compatible predict delegating to predict_susceptibility."""
        return self.predict_susceptibility(feature_vector)

