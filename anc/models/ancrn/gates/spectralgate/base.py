import numpy as np
from joblib import Parallel, delayed
import tempfile
from numba import jit
from functools import lru_cache
from tqdm.auto import tqdm


@jit(nopython = True)
def _smoothing_filter(n_grad_freq, n_grad_time):
    """
    Generates a filter to smooth the mask for the spectrogram.

    :param n_grad_freq: n_grad_freq {[type]} How many frequency channels to smooth over with the mask.
    :param n_grad_time: n_grad_time {[type]} How many time channels to smooth over with the mask.
    :return: Smoothing filter.
    """
    smoothing_filter = np.outer(
        np.concatenate(
            [
                np.linspace(0, 1, n_grad_freq + 1, endpoint=False),
                np.linspace(1, 0, n_grad_freq + 2),
            ]
        )[1:-1],

        np.concatenate(
            [
                np.linspace(0, 1, n_grad_time + 1, endpoint=False),
                np.linspace(1, 0, n_grad_time + 2),
            ]
        )[1:-1],
    )
    return smoothing_filter / np.sum(smoothing_filter)


class SpectralGate:
    def __init__(self, y, sr, prop_decrease, chunk_size, padding, n_fft, win_length, hop_length,
                 time_constant_s, freq_mask_smooth_hz, time_mask_smooth_ms, tmp_folder, use_tqdm, n_jobs):
        self.sr = sr
        # 1D single channel recording
        self.flat = False
        y = np.array(y)
        # reshape to (#channels, #frames)
        if len(y.shape) == 1:
            self.y = np.expand_dims(y, 0)
            self.flat = True
        elif len(y.shape) > 2:
            raise ValueError("Waveform must be in the following shape: [#frames, #channels]. ")
        else:
            self.y = y

        self._dtype = y.dtype
        # Statistics of the number of channels and frames in provided data
        self.n_channels, self.n_frames = y.shape
        self._chunk_size = chunk_size
        self.padding = padding
        self.n_jobs = n_jobs

        # Other initialization
        self.use_tqdm = use_tqdm
        # Temp folder for parallel execution and writing
        self._tmp_folder = tmp_folder

        # Spectral gating parameters
        self._n_fft = n_fft
        # window and hop lengths for stft
        if win_length is None:
            self._win_length = self._n_fft
        else:
            self._win_length = win_length

        if hop_length is None:
            self._hop_length = self._win_length // 4
        else:
            self._hop_length = hop_length

        self._time_constant_s = time_constant_s
        self.prop_decrease = prop_decrease

        if (freq_mask_smooth_hz is None) & (time_mask_smooth_ms is None):
            self.smooth_mask = False
        else:
            self._generate_mask_smoothing_filter(
                freq_mask_smooth_hz, time_mask_smooth_ms
            )

    def _generate_mask_smoothing_filter(self, freq_mask_smooth_hz, time_mask_smooth_ms):
        if freq_mask_smooth_hz is None:
            n_grad_freq = 1
        else:
            # filter to smooth the mask
            n_grad_freq = int(freq_mask_smooth_hz / (self.sr / (self._n_fft / 2)))
            if n_grad_freq < 1:
                raise ValueError(
                    "freq_mask_smooth_hz needs to be at least {}Hz".format(
                        int((self.sr / (self._n_fft / 2)))
                    )
                )

        if time_mask_smooth_ms is None:
            n_grad_time = 1
        else:
            n_grad_time = int(
                time_mask_smooth_ms / ((self._hop_length / self.sr) * 1000)
            )
            if n_grad_time < 1:
                raise ValueError(
                    "time_mask_smooth_ms needs to be at least {}ms".format(
                        int((self._hop_length / self.sr) * 1000)
                    )
                )
        if (n_grad_time == 1) & (n_grad_freq == 1):
            self.smooth_mask = False
        else:
            self.smooth_mask = True
            self._smoothing_filter = _smoothing_filter(n_grad_freq, n_grad_time)

    @lru_cache(maxsize = None)
    def _read_chunk(self, i, j):
        """
        Read chunk and pad with zeros.

        :param i: Start index.
        :param j: End index.
        :return: Padded chunk of data.
        """
        if i < 0:
            i1b = 0
        else:
            i1b = i
        if j > self.n_frames:
            i2b = self.n_frames
        else:
            i2b = j
        chunk = np.zeros((self.n_channels, j - i))
        chunk[:, i1b - i: i2b - i] = self.y[:, i1b:i2b]
        return chunk

    @lru_cache(maxsize = None)
    def _read_and_pad_chunk(self, start_frame, end_frame):
        """
        Read a chunk and apply padding.

        :param start_frame: Start frame index.
        :param end_frame: End frame index.
        :return: Padded chunk of data.
        """
        i1 = start_frame - self.padding
        i2 = end_frame + self.padding
        return self._read_chunk(i1, i2)

    def filter_chunk(self, start_frame, end_frame):
        """
        Pad and perform filtering on a chunk.

        :param start_frame: Start frame index.
        :param end_frame: End frame index.
        :return: Filtered chunk of data.
        """
        padded_chunk = self._read_and_pad_chunk(start_frame, end_frame)
        filtered_padded_chunk = self._do_filter(padded_chunk)
        return filtered_padded_chunk[:, start_frame: end_frame]

    def _get_filtered_chunk(self, ind):
        """Grabs a single chunk"""
        start0 = ind * self._chunk_size
        end0 = (ind + 1) * self._chunk_size
        return self.filter_chunk(start_frame = start0, end_frame = end0)

    def _do_filter(self, chunk):
        """Do the actual filtering"""
        raise NotImplementedError

    def _iterate_chunk(self, filtered_chunk, pos, end0, start0, ich):
        filtered_chunk0 = self._get_filtered_chunk(ich)
        filtered_chunk[:, pos: pos + end0 - start0] = filtered_chunk0[:, start0:end0]
        pos += end0 - start0

    def _initialize_chunk_parameters(self, start_frame, end_frame):
        """
        Initialize parameters required for chunk processing.

        :param start_frame: Start frame index.
        :param end_frame: End frame index.
        :return: Parameters required for chunk processing.
        """
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.n_frames

        ich1 = int(start_frame / self._chunk_size)
        ich2 = int((end_frame - 1) / self._chunk_size)
        pos_list, start_list, end_list = [], [], []

        pos = 0
        for ich in range(ich1, ich2 + 1):
            start0 = start_frame if ich == ich1 else 0
            end0 = end_frame if ich == ich2 else self._chunk_size
            pos_list.append(pos)
            start_list.append(start0)
            end_list.append(end0)
            pos += end0 - start0

        return pos_list, start_list, end_list, ich1, ich2

    def get_traces(self, start_frame = None, end_frame = None):
        """
        Grab filtered data iterating over chunks.

        :param start_frame: Start frame index. If None, starts from the beginning.
        :param end_frame: End frame index. If None, goes till the end.
        :return: Filtered data.
        """
        pos_list, start_list, end_list, ich1, ich2 = self._initialize_chunk_parameters(start_frame, end_frame)

        if self._chunk_size is not None and end_frame - start_frame > self._chunk_size:
            with tempfile.NamedTemporaryFile(prefix = self._tmp_folder) as fp:
                filtered_chunk = np.memmap(
                    fp,
                    dtype = self._dtype,
                    shape = (self.n_channels, int(end_frame - start_frame)),
                    mode = "w+",
                )

                Parallel(n_jobs = self.n_jobs)(
                    delayed(self._iterate_chunk)(
                        filtered_chunk, pos, end0, start0, ich
                    )
                    for pos, start0, end0, ich in zip(
                        tqdm(pos_list, disable = not self.use_tqdm),
                        start_list,
                        end_list,
                        range(ich1, ich2 + 1),
                    )
                )
                return filtered_chunk.astype(self._dtype).flatten() if self.flat else filtered_chunk.astype(self._dtype)

        # Directly return the result of filter_chunk when the condition is not met
        result = self.filter_chunk(start_frame = 0, end_frame = end_frame)
        return result.astype(self._dtype).flatten() if self.flat else result.astype(self._dtype)
