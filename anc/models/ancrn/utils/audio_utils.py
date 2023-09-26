from scipy.signal import stft


def compute_stft(signal, n_fft, hop_length, win_length):
    """
    Compute the Short-Time Fourier Transform (STFT) of a given signal.

    Parameters:
    - signal: The input signal.
    - n_fft: The FFT size.
    - hop_length: Number of samples between successive frames.
    - win_length: Each frame of audio is windowed by `window()` of length `win_length`.

    Returns:
    - The computed STFT of the signal.
    """
    return stft(signal, nfft = n_fft, noverlap = hop_length, nperseg = win_length)
