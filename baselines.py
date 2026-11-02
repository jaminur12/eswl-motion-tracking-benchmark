"""
v2/baselines.py
Standard state-of-the-art predictive tracking baselines for fair benchmarking.
"""

import numpy as np


class ZeroOrderHoldBaseline:
    """Baseline 0: Uncompensated Zero-Order Hold (holds last valid measurement)."""
    def __init__(self):
        self.last_pos = 10.0

    def update_and_predict(self, meas, is_valid):
        if is_valid and meas is not None:
            self.last_pos = meas
        # No forward latency projection, variance assumed static
        return float(self.last_pos), 2.0


class ConstantVelocityKalmanBaseline:
    """Baseline 1: Standard Cartesian Constant-Velocity Kalman Filter with projection."""
    def __init__(self, dt=0.01, latency_sec=0.12):
        self.dt = dt
        self.steps = int(latency_sec / dt)
        self.x = np.array([10.0, 0.0])  # [pos, vel]
        self.P = np.eye(2) * 2.0
        self.F = np.array([[1.0, dt], [0.0, 1.0]])
        self.H = np.array([[1.0, 0.0]])
        self.Q = np.array([[1e-4, 0.0], [0.0, 1e-2]])
        self.R = np.array([[0.16]])

    def update_and_predict(self, meas, is_valid):
        # Predict
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        # Update
        if is_valid and meas is not None:
            y = meas - self.H @ self.x
            S = self.H @ self.P @ self.H.T + self.R
            K = self.P @ self.H.T / S[0, 0]
            self.x = self.x + K.flatten() * y[0]
            self.P = (np.eye(2) - K @ self.H) @ self.P
        else:
            # Occluded: dampen velocity to prevent boundary blowup
            self.x[1] *= 0.90

        # Project forward across latency horizon
        x_proj = self.x.copy()
        for _ in range(self.steps):
            x_proj = self.F @ x_proj
            
        pred_pos = np.clip(float(x_proj[0]), 0.0, 35.0)
        return pred_pos, float(np.trace(self.P))