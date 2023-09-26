from ...ancrn.model_utils.audio_utils import compute_stft
import numpy as np


def test_compute_stft():
    signal = np.array([0.5, 0.5, 0.5, 0.5])
    result = compute_stft(signal, 4, 2, 4)
    assert result is not None
