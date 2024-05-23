from datetime import timedelta, datetime
from typing import Self
import pandas as pd
import mne
from utils.Channel import Channel


class EDFutils:
    def __init__(self, filepath, **kwargs) -> None:
        self.filepath = filepath
        self.time_range = (None, None)

        with mne.io.read_raw_edf(filepath, preload=False, **kwargs) as raw:
            self.channels = raw.ch_names
            self.start_ts = raw.info['meas_date'].replace(tzinfo=None)
            self.end_ts = self.start_ts + timedelta(seconds=raw.times[-1])

        self.channel_freqs = {ch: self.get_channel_frequency(ch) for ch in self.channels}

    def __getitem__(self, item) -> Channel:
        if item not in self.channels:
            raise KeyError(f"`{item}` not a channel in EDF file '{self.filepath}'")
        else:
            freq = self.get_channel_frequency(item)
            
            start_ts = self.start_ts
            # check for absolute date cutoffs
            start_idx, end_idx = self.time_range
            if start_idx and end_idx:
                start_ts = start_ts + timedelta(seconds=start_idx)
                start_idx = int(start_idx * freq)
                end_idx = int(end_idx * freq)

            with mne.io.read_raw_edf(self.filepath, include=[item], preload=False) as raw:
                signal, time = raw[0]

            return Channel(
                start_ts=start_ts,
                name=item,
                signal=signal[0],
                time=time,
                freq=freq
            )[start_idx:end_idx]
        
    def get_channel_frequency(self, ch_name):
        with mne.io.read_raw_edf(self.filepath, include=[ch_name], preload=False) as raw:
            freq = len(raw.crop(tmin=0, tmax=1).pick(ch_name).get_data()[0])-1
        return freq

    # TODO
    def resample(self, sfreq, ch_names=None) -> Self:
        """
        Resamples the EDF file to a new sampling frequency and optionally picks specific channels
        sfreq: sampling frequency to resample to
        ch_names: list of channel names to pick (if None, all channels are picked)
        """
        return

    def set_date_range(self, start: datetime, end: datetime) -> None:
        """
        After setting this threshold, any Channels accessed will be spliced
        according to these supplied dates.
        start: datetime object representing start date
        end: datetime object representing end date
        """
        # TODO update using Will's date slice code to accept strings
        front = (start - self.start_ts).total_seconds()
        back = (end - self.start_ts).total_seconds()
        self.time_range = (int(front), int(back))

    # TODO
    def to_DataFrame(self, frequency:int, channels:list=None) -> pd.DataFrame:
        """
        Exports channels to a pandas DataFrame wherein each channel is a column.
        frequency: the desired output frequency to sample all data to
        channels: channels to export, default exports all
        """
        pass

