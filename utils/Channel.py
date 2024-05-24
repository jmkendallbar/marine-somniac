import numpy as np
import pandas as pd
from datetime import timedelta
import inspect
from typing import Self
import mne
import wfdb.processing
from sleepecg import detect_heartbeats
from scipy.integrate import simpson
from scipy.signal import welch
from scipy.signal.windows import hann


class Channel:
    def __init__(self, start_ts, name: str, signal: np.array, end_ts=None, time:np.array=None, freq=None) -> None:
        self.name = name
        self.time = time
        self.signal = signal
        self.freq = freq

        self.start_ts = start_ts
        self.end_ts = end_ts if end_ts else self.start_ts + timedelta(seconds=time[-1])
        
        # TODO store reference to parent EDFutils obj and have each 
        # construction trigger storage in cache
            
    def __getitem__(self, slice) -> Self:
        """
        Enables object indexing, returns a new Channel instance with signal 
        and time attributes indexed according to the supplied slice
        """
        freq = self.freq
        if slice.step:
            freq = freq / slice.step
            if freq.is_integer():
                freq = int(freq)

        slice_time = self.time[slice]
        slice_signal = self.signal[slice]
        return Channel(
            name=self.name,
            signal=slice_signal,
            time=slice_time,
            freq=freq,
            start_ts=self.start_ts,
            end_ts=self.end_ts
        )
    
    def time_slice(self, start_time, end_time, unit='second') -> Self:
        """
        Slices the data by time, returns a new Channel instance
        start_time: start time in the form of a number
        end_time: end time in the form of a number
        unit: unit of time to slice by, options are 'second', 'minute', 'hour'
        """
        mod = None
        match unit:
            case 'second':
                mod = 1
            case 'minute':
                mod = 60
            case 'hour':
                mod = 3600
            case _:
                raise ValueError(
                    f'Only accepts second, minute, and hour, not {unit}')
        
        start = mod * self.freq * start_time
        end = mod * self.freq * end_time
        return self[start:end]
    
    def date_slice(self, start_date, end_date) -> Self:
        """
        Slices the data by date, returns a new Channel instance
        start_date: start date in the form of a string or datetime object
        end_date: end date in the form of a string or datetime object
        """
        recording_start_ts = self.start_ts.timestamp()
        start_ts = pd.to_datetime(start_date).timestamp()
        end_ts = pd.to_datetime(end_date).timestamp()

        relative_start_ts = start_ts - recording_start_ts
        relative_end_ts = end_ts - recording_start_ts

        start_idx = np.searchsorted(self.time, relative_start_ts)
        end_idx = np.searchsorted(self.time, relative_end_ts, side='right')

        slice_signal = self.signal[start_idx:end_idx]
        slice_time = self.time[start_idx:end_idx]

        return Channel(
            name=self.name,
            signal=slice_signal,
            time=slice_time,
            freq=self.freq,
            start_ts=self.start_ts,
            end_ts=self.end_ts
        )

    
    def _return(self, new_signal, step_size) -> Self:
        """
        Used to generalize the return of window functions to minimize
        copy-pasting. Takes name of the process/method that calls it and uses 
        that to assign the name of the returned Channel object. 
        Calculates new frequency values based on input process modifications.
        new_signal: the new array to be assigned to Channel.signal
        step_size: step size of the window function used to calculate the new freq
        """
        # inspect.stack()[1][3] returns the name of the function
        # traced back before this function call
        new_name = f'{self.name}.{inspect.stack()[1][3]}'
        new_time = self.time[::self.freq//step_size]
        new_freq = 1/step_size
        return Channel(
            start_ts=self._start_ts,
            name=new_name,
            signal=new_signal,
            time=new_time,
            freq=int(new_freq)  # should never be a float...
            # TODO support for non-integer frequencies?
        )
    
    def to_DataFrame(self) -> pd.DataFrame:
        """
        Returns 2-column pandas DataFrame of time and signal
        """
        assert len(self.signal) == len(self.time)
        return pd.DataFrame(
            data=np.array([self.time, self.signal]).T,
            columns=['time', self.name]
        )

    def get_rolling_mean(self, window_sec=30, step_size=1) -> Self:
        """
        Calculate rolling mean over Channel.signal. Returns new Channel instance
        window_sec: window size for rolling mean in seconds
        step_size: step over which to resample the output Channel
        """
        rolling_mean = pd.Series(self.signal).rolling(window_sec*self.freq, center=True)\
            .mean()[::self.freq].values
        return self._return(rolling_mean, step_size)

    def get_rolling_std(self, window_sec=30, step_size=1) -> Self:
        """
        Calculate rolling standard deviation over Channel.signal. 
        Returns new Channel instance
        window_sec: window size for rolling std in seconds
        step_size: step over which to resample the output Channel
        """
        rolling_std = pd.Series(self.signal).rolling(window_sec*self.freq, center=True)\
            .std()[::self.freq].values
        return self._return(rolling_std, step_size)
    
    def _apply_rolling(self, window_sec, step_size, process) -> np.array:
        """
        Generalized pattern to apply a transformation over a rolling window.
        window_sec: window size for applied process in seconds
        step_size: step over which to resample the signal frequency
        process: function to apply over the rolling window
        """
        window_length = window_sec * self.freq
        step_idx = int(step_size * self.freq)

        accum = []
        for i in range(0, len(self.signal), step_idx):
            window_start = i - window_length//2
            window_end = i + window_length//2
            if window_start < 0:
                accum.append(np.nan)
            elif window_end > len(self.signal):
                accum.append(np.nan)
            else:
                accum.append(process(self.signal, window_start, window_end))
        return np.array(accum)

    def get_rolling_band_power_multitaper(self, freq_range=(0.5, 4), ref_power=1e-13,
                                          window_sec=2, step_size=1, in_dB=True) -> Self:
        """
        Gets rolling band power for specified frequency range, data frequency and window size
        freq_range: range of frequencies in form of (lower, upper) to calculate power of
        ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
        window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
        step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
        in_dB: boolean for whether to convert the output into decibals
        """
        def get_band_power_multitaper(a, start, end) -> np.array:
            a = a[start:end]
            # TODO: maybe edit this later so there is a buffer before and after?
            psd, freqs = mne.time_frequency.psd_array_multitaper(a, sfreq=self.freq,
                                                                 fmin=freq_range[0], fmax=freq_range[1], adaptive=True, 
                                                                 normalization='full', verbose=False)
            freq_res = freqs[1] - freqs[0]
            # Find the index corresponding to the delta frequency range
            delta_idx = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
            # Integral approximation of the spectrum using parabola (Simpson's rule)
            delta_power = psd[delta_idx] / ref_power
            if in_dB:
                delta_power = simpson(10 * np.log10(delta_power), dx=freq_res)
            else:
                delta_power = np.mean(delta_power)
            # Sum the power within the delta frequency range
            return delta_power

        rolling_band_power = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_band_power_multitaper
        )
        return self._return(rolling_band_power, step_size=step_size)

    def get_rolling_zero_crossings(self, window_sec=1, step_size=1) -> Self:
        """
        Get the zero-crossings of an array with a rolling window
        window_sec: window in seconds
        step_size: step size in seconds (step_size of 1 would mean returend data will be 1 Hz)
        """

        def get_crossing(a, start, end):
            return ((a[start:end-1] * a[start+1:end]) < 0).sum()
        
        rolling_zero_crossings = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_crossing
        )
        return self._return(rolling_zero_crossings, step_size=step_size)
  
    def get_rolling_band_power_fourier_sum(self, freq_range=(0.5, 4), ref_power=0.001, window_sec=2, step_size=1) -> Self:
        """
        Gets rolling band power for specified frequency range, data frequency and window size
        freq_range: range of frequencies in form of (lower, upper) to calculate power of
        ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
        window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
        step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
        """
        def get_band_power_fourier_sum(a, start, end) -> np.array:
            a = a[start:end]
            """
            Helper function to get delta spectral power for one array
            """
            # Perform Fourier transform
            fft_data = np.fft.fft(a)
            # Compute the power spectrum
            power_spectrum = np.abs(fft_data)**2
            # Frequency resolution
            freq_resolution = self.freq / len(a)
            # Find the indices corresponding to the delta frequency range
            delta_freq_indices = np.where((np.fft.fftfreq(len(a), 1/self.freq) >= freq_range[0]) &
                                          (np.fft.fftfreq(len(a), 1/self.freq) <= freq_range[1]))[0]
            # Compute the delta spectral power
            delta_power = np.sum(power_spectrum[delta_freq_indices] / ref_power) * freq_resolution

            return delta_power

        rolling_band_power = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_band_power_fourier_sum
        )
        return self._return(rolling_band_power, step_size=step_size)
    
    def get_rolling_band_power_welch(self, freq_range=(0.5, 4), ref_power=0.001, window_sec=2, step_size=1) -> Self:
        """
        Gets rolling band power for specified frequency range, data frequency and window size
        freq_range: range of frequencies in form of (lower, upper) to calculate power of
        ref_power: arbitrary reference power to divide the windowed delta power by (used for scaling)
        window_sec: window size in seconds to calculate delta power (if the window is longer than the step size there will be overlap)
        step_size: step size in seconds to calculate delta power in windows (if 1, function returns an array with 1Hz power calculations)
        """
        def get_band_power_welch(a, start, end):
            lower_freq = freq_range[0]
            upper_freq = freq_range[1]
            window_length = int(window_sec * self.freq)
            # TODO: maybe edit this later so there is a buffer before and after?
            windowed_data = a[start:end] * hann(window_length)
            freqs, psd = welch(windowed_data, window='hann', fs=self.freq,
                               nperseg=window_length, noverlap=window_length//2)
            freq_res = freqs[1] - freqs[0]
            # Find the index corresponding to the delta frequency range
            delta_idx = (freqs >= lower_freq) & (freqs <= upper_freq)
            # Integral approximation of the spectrum using parabola (Simpson's rule)
            delta_power = simpson(
                10 * np.log10(psd[delta_idx] / ref_power), dx=freq_res)
            # Sum the power within the delta frequency range
            return delta_power

        rolling_band_power = self._apply_rolling(
            window_sec=window_sec,
            step_size=step_size,
            process=get_band_power_welch
        )
        return self._return(rolling_band_power, step_size=step_size)
    

    def get_heart_rate(self, search_radius=200):
        """
        Gets heart rate at 1 Hz and extrapolates it to the same frequency as input data
        search_radius: search radius to look for peaks (200 ~= 150 bpm upper bound)
        """
        rpeaks = detect_heartbeats(self.signal, self.freq)  # using sleepecg
        rpeaks_corrected = wfdb.processing.correct_peaks(
            self.signal, rpeaks, search_radius=search_radius, smooth_window_size=50, peak_dir="up"
        )
        # MIGHT HAVE TO UPDATE search_radius
        heart_rates = [60 / ((rpeaks_corrected[i+1] - rpeaks_corrected[i]) / self.freq) for i in range(len(rpeaks_corrected) - 1)]
        # Create a heart rate array matching the frequency of the ECG trace
        hr_data = np.zeros_like(self.signal)
        # Assign heart rate values to the intervals between R-peaks
        for i in range(len(rpeaks_corrected) - 1):
            start_idx = rpeaks_corrected[i]
            end_idx = rpeaks_corrected[i+1]
            hr_data[start_idx:end_idx] = heart_rates[i]

        return self._return(hr_data, step_size=1)
    
    def visualize(self):
        """
        """
        pass

    

class ECGChannel(Channel):
    def visualize(self):
        pass