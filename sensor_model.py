"""
v2/sensor_model.py
Models ultrasound observation geometry, dynamic 12th-rib acoustic shadowing,
Gaussian measurement noise, and physical transmission latency.
"""

from collections import deque
import numpy as np


class SyntheticObservationModel:
    def __init__(self, latency_ms=120.0, dt_ms=10.0, occlusion_threshold=13.5, noise_std=0.4):
        self.dt = dt_ms / 1000.0
        self.buffer_len = int(latency_ms / dt_ms)  # 12 steps for 120ms
        self.occlusion_threshold = occlusion_threshold
        self.noise_std = noise_std
        
        # FIFO buffer for delayed measurement stream
        self.fifo_queue = deque()

    def process_observation(self, t, true_pos_3d):
        """
        Takes ground-truth position, evaluates geometric rib shadow, adds sensor noise,
        and pushes to the FIFO queue to simulate hardware/processing latency.
        """
        x_val = true_pos_3d[0]
        
        # Acoustic shadowing constraint: 12th rib blocks US when X > threshold
        is_occluded = bool(x_val > self.occlusion_threshold)
        
        if not is_occluded:
            # Valid measurement with sensor noise
            noisy_x = x_val + np.random.normal(0.0, self.noise_std)
            raw_measurement = noisy_x
            is_valid = True
        else:
            # Acoustic dropout (shadow)
            raw_measurement = None
            is_valid = False
            
        # Push packet into delayed pipeline: (measurement, valid_flag, ground_truth_at_timestamp)
        packet = (raw_measurement, is_valid, true_pos_3d.copy(), t)
        self.fifo_queue.append(packet)
        
        # If queue hasn't filled yet during startup, return invalid
        if len(self.fifo_queue) <= self.buffer_len:
            return None, False, packet[2], t
            
        # Pop delayed observation
        delayed_measurement, delayed_valid, truth_at_obs_time, obs_timestamp = self.fifo_queue.popleft()
        return delayed_measurement, delayed_valid, truth_at_obs_time, obs_timestamp