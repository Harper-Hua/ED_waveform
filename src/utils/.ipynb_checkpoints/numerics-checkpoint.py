from datetime import datetime

import numpy as np
import time

from utils.constants import NUMERIC_COLUMNS


def get_numerics_averaged_by_second(numerics_obj, start_epoch, end_epoch, average_window_sec=60):
    start = int(start_epoch)
    end = int(end_epoch)
    range_len = end - start
    output = {}
    for col in NUMERIC_COLUMNS:
        if col not in numerics_obj:
            output[col] = np.full(int((end - start) / average_window_sec), np.NaN)
            output[f"{col}-time"] = np.full(int((end - start) / average_window_sec), np.NaN)
            output[f"{col}-length"] = 0
            continue
        second_to_vals = {}
        vals = np.array(numerics_obj[col])
        times = np.array(numerics_obj[f"{col}-time"])
        assert len(times) == len(vals)

        indices_of_interest = np.squeeze(np.argwhere(np.logical_and(times >= start, times <= end)), axis=-1)
        if len(indices_of_interest) > 1:
            vals = vals[indices_of_interest]
            times = times[indices_of_interest]
        elif len(indices_of_interest) == 1:
            vals = vals[[indices_of_interest]]
            times = times[[indices_of_interest]]
        else:
            # There are no usable numerics here
            output[col] = np.full(int((end - start) / average_window_sec), np.NaN)
            output[f"{col}-time"] = np.full(int((end - start) / average_window_sec), np.NaN)
            output[f"{col}-length"] = 0
            continue

        assert all(times[i] <= times[ i +1] for i in range(len(times) - 1)), "Times are not sorted!"

        for idx, t in enumerate(times):
            # e.g.
            # start = 1634840005
            # t     = 1634840068
            # average_window_sec = 60

            # offset = 63
            offset = int(t) - start

            # Determine the bucket - e.g. if we are grouping every 60 seconds,
            # we want to have buckets that begin on the 60 second marks
            # e.g. offset = 63 - 63 % 60 = 63 - 3 = 60
            # We would have buckets from 0, 60, 120, ...
            offset = offset - offset % average_window_sec
            if offset not in second_to_vals:
                second_to_vals[offset] = []
            second_to_vals[offset].append(vals[idx])

        output[col] = np.full(int((end - start) / average_window_sec), np.NaN)
        output[f"{col}-time"] = np.full(int((end - start) / average_window_sec), np.NaN)

        last_val = np.NaN
        valid_vals = 0
        curr = 0
        idx = 0
        while curr < range_len:
            actual_time = start + curr
            if curr in second_to_vals and len(second_to_vals[curr]) > 0:
                output[col][idx] = np.nanmean(second_to_vals[curr])
                valid_vals += 1
            elif not np.isnan(last_val):
                # Attempt to carry-forward the last value
                output[col][idx] = last_val
                valid_vals += 1
            last_val = output[col][idx]
            output[f"{col}-time"][idx] = actual_time
            curr += average_window_sec
            idx += 1
        output[f"{col}-length"] = valid_vals
    return output


def get_numerics_obj(csn: int, df_numerics, start: datetime, end: datetime):
    numerics = {}

    before = int(time.time())

    df_filtered = df_numerics[(df_numerics["CSN"] == csn) & (df_numerics["Source"] == "Monitor") & (df_numerics["Time"] >= start.strftime('%Y-%m-%dT%H:%M:%SZ')) & (df_numerics["Time"] < end.strftime('%Y-%m-%dT%H:%M:%SZ'))]
    df_filtered = df_filtered.sort_values("Time")

    print(f"Filtering numerics - elapsed {int(time.time()) - before} sec")

    applicable_numerics = set(NUMERIC_COLUMNS)
    for measure in applicable_numerics:
        if measure == "SBP":
            col = "NBPs"
        elif measure == "DBP":
            col = "NBPd"
        else:
            col = measure
        numerics[col] = []
        numerics[f"{col}-time"] = []

    for i, row in df_filtered.iterrows():
        dt = datetime.strptime(row["Time"], "%Y-%m-%dT%H:%M:%S%z")
        measure = row["Measure"]
        val = row["Value"]
        if measure == "SBP":
            col = "NBPs"
        elif measure == "DBP":
            col = "NBPd"
        elif measure not in applicable_numerics:
            continue
        else:
            col = measure
        numerics[col].append(val)
        numerics[f"{col}-time"].append(dt.timestamp())

    print(f"Finished iterating through rows - elapsed {int(time.time()) - before} sec")
    return numerics
