import numpy as np
from anc.models.ancrn.gates.spectralgate.base import SpectralGate
from librosa import stft, istft
from scipy.signal import fftconvolve
from .utils import _amp_to_db


class FFTConfig:
    def __init__(self, n_fft = 2048, hop_length = 512, win_length = None):
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length if win_length else n_fft


class NoiseConfig:
    def __init__(self, noise_thresh_stationary=0.15, prop_decrease=1.0, smooth_mask=True,
                 thresh_n_mult_stationary=0.25, sigmoid_slope_stationary=1.0):
        self.noise_thresh_stationary = noise_thresh_stationary
        self.prop_decrease = prop_decrease
        self.smooth_mask = smooth_mask
        self.thresh_n_mult_stationary = thresh_n_mult_stationary
        self.sigmoid_slope_stationary = sigmoid_slope_stationary


class SpectralGateStationary(SpectralGate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        noise_config_stationary = kwargs.get('noise_config_stationary')

        if noise_config_stationary:
            self.n_std_thresh_stationary = noise_config_stationary.n_std_thresh_stationary
            self.y_noise = self._prepare_noise(noise_config_stationary.y_noise, noise_config_stationary.clip_noise_stationary)
        else:
            self.n_std_thresh_stationary = kwargs.get('n_std_thresh_stationary')
            y_noise = kwargs.get('y_noise')
            self.y_noise = self._prepare_noise(y_noise, kwargs.get('clip_noise_stationary'))

        self.noise_thresh = self._compute_noise_threshold()

    def _prepare_noise(self, y_noise, clip_noise_stationary):
        """Prepares the noise waveform."""
        if y_noise is None:
            return self.y
        else:
            y_noise = np.array(y_noise)
            if len(y_noise.shape) == 1:
                y_noise = np.expand_dims(y_noise, 0)
            elif len(y_noise.shape) > 2:
                raise ValueError("Waveform must be in shape (# frames, # channels)")

            if clip_noise_stationary:
                y_noise = y_noise[:, :self.chunk_size]

            # Collapse y_noise to one channel
            return np.mean(y_noise, axis = 0)

    def _compute_noise_threshold(self):
        """Computes the threshold for noise."""
        abs_noise_stft = np.abs(
            stft(
                self.y_noise,
                n_fft = self._n_fft,
                hop_length = self._hop_length,
                win_length = self._win_length,
            )
        )
        noise_stft_db = _amp_to_db(abs_noise_stft)
        mean_freq_noise = np.mean(noise_stft_db, axis = 1)
        std_freq_noise = np.std(noise_stft_db, axis = 1)

        return mean_freq_noise + std_freq_noise * self.n_std_thresh_stationary

    def spectral_gating_stationary(self, chunk):
        """Stationary version of spectral gating."""
        denoised_channels = np.zeros_like(chunk)
        for ci, channel in enumerate(chunk):
            sig_stft, sig_stft_denoised = self._process_channel(channel)
            denoised_signal = istft(
                sig_stft_denoised,
                hop_length = self._hop_length,
                win_length = self._win_length,
            )
            denoised_channels[ci, :len(denoised_signal)] = denoised_signal
        return denoised_channels

    def _process_channel(self, channel):
        """Process an individual channel for denoising."""
        sig_stft = stft(
            channel,
            n_fft = self._n_fft,
            hop_length = self._hop_length,
            win_length = self._win_length,
        )
        sig_stft_db = _amp_to_db(np.abs(sig_stft))
        sig_mask = self._compute_mask(sig_stft_db)
        sig_stft_denoised = sig_stft * sig_mask
        return sig_stft, sig_stft_denoised

    def _compute_mask(self, sig_stft_db):
        """Compute the mask for spectral gating."""
        db_thresh = np.repeat(
            self.noise_thresh[:, np.newaxis],
            sig_stft_db.shape[1],
            axis = 1,
        )
        sig_mask = sig_stft_db > db_thresh
        sig_mask = sig_mask * self._prop_decrease + 1.0 - self._prop_decrease
        if self.smooth_mask:
            sig_mask = fftconvolve(sig_mask, self._smoothing_filter, mode = "same")
        return sig_mask

    def _do_filter(self, chunk):
        """Do the actual filtering."""
        return self.spectral_gating_stationary(chunk)
