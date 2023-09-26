from anc.models.ancrn.gates.spectralgate.nonstationary import SpectralGateNonStationary


def test_nonstationary_initialization():
    sg = SpectralGateNonStationary(thresh_n_mult_nonstationary=2, sigmoid_slope_nonstationary=0.5)
    assert sg._thresh_n_mult_nonstationary == 2
    assert sg._sigmoid_slope_nonstationary == 0.5


def test_spectral_gating_nonstationary():
    sg = SpectralGateNonStationary(thresh_n_mult_nonstationary=2, sigmoid_slope_nonstationary=0.5)
    chunk = [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    result = sg.spectral_gating_nonstationary(chunk)
    assert result.shape == (2, 3)
