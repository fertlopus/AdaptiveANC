import numpy as np
from librosa.core import amplitude_to_db, db_to_amplitude
from numba import jit

# CONSTANTS for optimization purposes
# TODO: If in future we will need more flexibility feel free to add more flexible choice for arguments
_REF = 1.0
_AMIN = 1e-20
_TOP_DB = 80.0


@jit(nopython = True)
def sigmoid(x, shift, mult):
    """
    Sigmoid function to overpowering the network.
    :param x: Input Tensor
    :param shift: Value to shift the sigmoid curve along the x-axis
    :param mult: Value to scale the steepness of the sigmoid curve
    :return: Tensor after applying the sigmoid function
    """
    return 1 / (1 + np.exp(-(x + shift) * mult))


@jit(nopython = True)
def _amp_to_db(x):
    """
    Convert the input tensor from amplitude to decibel scale.

    :param x: Input amplitude tensor.
    :return: Tensor in decibel scale.
    """
    return amplitude_to_db(x, ref = _REF, amin = _AMIN, top_db = _TOP_DB)


@jit(nopython = True)
def _db_to_amp(x):
    """
    Convert the input tensor from decibel scale to amplitude.

    :param x: Input decibel tensor.
    :return: Tensor in amplitude scale.
    """
    return db_to_amplitude(x, ref = _REF)
