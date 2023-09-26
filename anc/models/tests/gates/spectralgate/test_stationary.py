from anc.models.ancrn.gates.spectralgate.stationary import SpectralGateStationary


def test_stationary_initialization():
    sg = SpectralGateStationary(y_noise=[0.1, 0.2], n_std_thresh_stationary=2, clip_noise_stationary=True)
    assert sg.n_std_thresh_stationary == 2
    assert sg.y_noise is not None
    assert sg.noise_thresh is not None


def test_spectral_gating_stationary():
    sg = SpectralGateStationary(y_noise=[0.1, 0.2], n_std_thresh_stationary=2, clip_noise_stationary=True)
    chunk = [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]  # Mocked chunk input
    result = sg.spectral_gating_stationary(chunk)
    assert result.shape == (2, 3)  # Ensure the output shape is same as input
