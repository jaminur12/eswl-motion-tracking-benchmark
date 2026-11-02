"""
v2/motion_models.py
Generates deterministic and non-stationary respiratory trajectories for kidney stone motion.
Supports nominal breathing, frequency drift, amplitude modulation, coughing spikes, and apnea.
"""

import numpy as np


class PhysiologicalRespiratoryEngine:
    def __init__(self, dt=0.01, seed=42):
        self.dt = dt
        self.rng = np.random.default_rng(seed)

    def generate_trajectory(self, duration_sec=20.0, mode="nominal"):
        """
        Modes:
          - 'nominal': Standard periodic breathing (0.25 Hz, 18 mm baseline, 9 mm amplitude)
          - 'freq_drift': Frequency drifts continuously between 0.18 Hz and 0.32 Hz
          - 'amplitude_shift': Breathing amplitude shifts by +/-30% mid-sequence
          - 'cough': Sudden 25 mm transient spike at t = 10s
          - 'apnea': Breath-hold (zero motion) from t = 7s to t = 12s
          - 'complex': Combined non-stationary challenge
        """
        t = np.arange(0, duration_sec, self.dt)
        N = len(t)
        
        baseline = 10.0  # mm
        amplitude = 9.0  # mm
        nominal_freq = 0.25  # Hz
        
        pos_x = np.zeros(N)
        true_freq = np.zeros(N)
        true_amp = np.zeros(N)
        
        phase = 0.0
        
        for i in range(N):
            current_t = t[i]
            current_freq = nominal_freq
            current_amp = amplitude
            current_base = baseline
            transient = 0.0
            
            if mode == "freq_drift" or mode == "complex":
                # Frequency wanders between 0.18 Hz and 0.32 Hz
                current_freq = nominal_freq + 0.07 * np.sin(2 * np.pi * 0.05 * current_t)
                
            if mode == "amplitude_shift" or mode == "complex":
                # Amplitude increases after t = 8s
                if current_t > 8.0:
                    current_amp = amplitude * 1.3
                    
            if mode == "cough" or mode == "complex":
                # Sharp cough spike between 10.0s and 10.5s
                if 10.0 <= current_t <= 10.5:
                    transient = 15.0 * np.sin(np.pi * (current_t - 10.0) / 0.5)
                    
            if mode == "apnea" or mode == "complex":
                # Breath hold between 5.0s and 8.0s
                if 5.0 <= current_t <= 8.0:
                    current_amp = 0.5  # residual cardiac ripple
            
            phase += 2.0 * np.pi * current_freq * self.dt
            pos_x[i] = current_base + current_amp * np.sin(phase) + transient
            true_freq[i] = current_freq
            true_amp[i] = current_amp

        # 3D Position [Superior-Inferior (X), Lateral (Y), Anterior-Posterior (Z)]
        pos_3d = np.zeros((N, 3))
        pos_3d[:, 0] = pos_x
        pos_3d[:, 1] = 0.15 * (pos_x - baseline)  # lateral anatomical coupling
        pos_3d[:, 2] = 0.30 * (pos_x - baseline)  # AP anatomical coupling
        
        return t, pos_3d, true_freq, true_amp