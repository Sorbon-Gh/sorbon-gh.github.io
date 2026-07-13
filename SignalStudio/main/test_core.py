import tempfile
from pathlib import Path

import numpy as np
import pytest

import core.config as config
from core import fft, signal_processor, wav_handler

class TestGenerateSignal:
    def test_sinusoidal_returns_correct_shape(self):
        t, y = signal_processor.generate_signal(
            'sinusoidal', freq=1000.0, sample_rate=44100.0, duration=0.1
        )
        assert t.shape == y.shape
        assert len(t) == 4410

    def test_invalid_sample_rate_raises(self):
        with pytest.raises(ValueError, match='sample_rate'):
            signal_processor.generate_signal(
                'sinusoidal', freq=1000.0, sample_rate=0, duration=0.1
            )

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError, match='duration'):
            signal_processor.generate_signal(
                'sinusoidal', freq=1000.0, sample_rate=44100.0, duration=0
            )

    def test_dc_constant_value(self):
        t, y = signal_processor.generate_signal(
            'dc', freq=1000.0, sample_rate=44100.0, duration=0.1, offset=0.5
        )
        np.testing.assert_array_almost_equal(y, np.full_like(y, 0.5))

    def test_noise_with_seed_reproducible(self):
        _, y1 = signal_processor.generate_signal(
            'noise', freq=0, sample_rate=1000.0, duration=0.01, noise_seed=42
        )
        _, y2 = signal_processor.generate_signal(
            'noise', freq=0, sample_rate=1000.0, duration=0.01, noise_seed=42
        )
        np.testing.assert_array_almost_equal(y1, y2)


class TestApplyFilter:
    def test_none_returns_unchanged(self):
        data = np.random.randn(1000).astype(np.float32)
        out = signal_processor.apply_filter(data, 44100.0, 'none', 1000.0)
        np.testing.assert_array_almost_equal(out, data)

    def test_empty_returns_empty(self):
        data = np.array([], dtype=np.float32)
        out = signal_processor.apply_filter(data, 44100.0, 'lowpass', 1000.0)
        assert out.size == 0

    def test_lowpass_returns_same_length(self):
        data = np.random.randn(2000).astype(np.float32)
        out = signal_processor.apply_filter(data, 44100.0, 'lowpass', 2000.0, order=3)
        assert out.shape == data.shape

class TestComputeFftSpectrum:
    def test_empty_signal_returns_placeholder(self):
        freq, db = fft.compute_fft_spectrum(np.array([]), 44100.0)
        assert freq.shape == (1,)
        assert db.shape == (1,)
        assert db[0] == -120.0

    def test_sinusoid_peak_near_freq(self):
        _, y = signal_processor.generate_signal(
            'sinusoidal', freq=440.0, sample_rate=44100.0, duration=0.1
        )
        freq, db = fft.compute_fft_spectrum(y, 44100.0, nperseg=2048)
        peak_idx = np.argmax(db)
        assert 400 <= freq[peak_idx] <= 500

    def test_zero_sample_rate_returns_placeholder(self):
        freq, db = fft.compute_fft_spectrum(np.array([1.0, 0.0]), 0.0)
        assert len(freq) == 1 and len(db) == 1


class TestComputeSpectrogram:
    def test_empty_returns_placeholder_arrays(self):
        f, t, s = fft.compute_spectrogram(np.array([]), 44100.0)
        assert f.shape == (1,) and t.shape == (1,) and s.ndim == 2

    def test_signal_returns_valid_shapes(self):
        _, y = signal_processor.generate_signal(
            'sinusoidal', freq=1000.0, sample_rate=44100.0, duration=0.05
        )
        f, t, s = fft.compute_spectrogram(y, 44100.0, nperseg=512)
        assert len(f) > 0 and len(t) > 0 and s.shape == (len(f), len(t))


class TestBuildAnalysisFrames:
    def test_empty_signal_returns_empty_frames(self):
        frames = fft.build_analysis_frames(np.array([]), 44100.0)
        assert frames.time_axis.size == 0
        assert frames.spectrum_freq.shape == (1,)
        assert frames.spectrum_db[0] == -120.0

    def test_signal_returns_filled_frames(self):
        _, y = signal_processor.generate_signal(
            'sinusoidal', freq=500.0, sample_rate=44100.0, duration=0.1
        )
        frames = fft.build_analysis_frames(y, 44100.0)
        assert frames.signal.size == y.size
        assert frames.spectrum_freq.size > 0
        assert frames.spectrogram_db.size > 0

class TestSaveLoadWav:
    def test_save_and_load_roundtrip(self):
        data, sr = np.random.randn(4410).astype(np.float32), 44100
        data = np.clip(data, -1.0, 1.0)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            path = f.name
        try:
            wav_handler.save_wav(path, data, sr, n_channels=1)
            loaded, loaded_sr, ch = wav_handler.load_wav(path)
            assert loaded_sr == sr and ch == 1
            assert loaded.size == data.size
            np.testing.assert_allclose(loaded.flatten(), data, atol=0.01)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError, match='не найден'):
            wav_handler.load_wav('/nonexistent/path/file.wav')

    def test_save_empty_raises(self):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            path = f.name
        try:
            with pytest.raises(ValueError, match='пусты'):
                wav_handler.save_wav(path, np.array([]), 44100, n_channels=1)
        finally:
            Path(path).unlink(missing_ok=True)

class TestConfig:
    def test_si_format_zero(self):
        assert config.si_format(0, "Hz") == "0 Hz"

    def test_si_format_kilo(self):
        assert "k" in config.si_format(5000, "Hz")

    def test_si_format_none_returns_dash(self):
        assert config.si_format(None) == "—"

    def test_si_format_inf_returns_dash(self):
        assert config.si_format(float('inf')) == "—"
