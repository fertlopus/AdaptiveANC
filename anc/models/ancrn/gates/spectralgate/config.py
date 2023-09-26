class FFTConfig:
    def __init__(self, n_fft = 2048, hop_length = 512, win_length = None):
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length if win_length else n_fft


class NoiseConfig:
    def __init__(self, noise_thresh_stationary = 0.15, prop_decrease = 1.0, smooth_mask = True,
                 thresh_n_mult_stationary = 0.25, sigmoid_slope_stationary = 1.0):
        self.noise_thresh_stationary = noise_thresh_stationary
        self.prop_decrease = prop_decrease
        self.smooth_mask = smooth_mask
        self.thresh_n_mult_stationary = thresh_n_mult_stationary
        self.sigmoid_slope_stationary = sigmoid_slope_stationary


class NoiseConfigNonStationary:
    def __init__(self, thresh_n_mult_nonstationary, sigmoid_slope_nonstationary):
        self.thresh_n_mult_nonstationary = thresh_n_mult_nonstationary
        self.sigmoid_slope_nonstationary = sigmoid_slope_nonstationary


class NoiseConfigStationary:
    def __init__(self, n_std_thresh_stationary, y_noise, clip_noise_stationary):
        self.n_std_thresh_stationary = n_std_thresh_stationary
        self.y_noise = y_noise
        self.clip_noise_stationary = clip_noise_stationary
