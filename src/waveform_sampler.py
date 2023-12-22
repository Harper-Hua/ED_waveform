import pandas as pd
import numpy as np
import boto3
import matplotlib.pyplot as plt
from utils.waveform_extraction import get_waveform
from utils.constants import TARGET_FREQ, WAVEFORMS_OF_INTERST
import os
from datetime import datetime, timedelta
import h5py

# Static Constants
OUTPUT_DIR = "/home/ubuntu/ED_processed/waveform/sampled_waveform"
H5_DOWNLOAD_DIR = "/home/ubuntu/ED_processed/waveform/s3_download_buffer_zone"
SAMPLING_RATE_ii = 500  # Hz
SAMPLING_RATE_ppg = 125  # Hz
EPISODE_LENGTH = 600  # seconds (10 minutes)
TOKEN_LENGTH_ii = 1 * SAMPLING_RATE_ii  # 2 seconds * samples per second
TOKEN_LENGTH_ppg = 1 * SAMPLING_RATE_ppg  # 2 seconds * samples per second

consolidated_info = pd.read_csv('/home/ubuntu/ED_processed/waveform/consolidated/ecg_ppg_trop_consolidated.csv')
s3_client = boto3.client('s3')

falied_ii_count = 0
falied_ppg_count = 0

for index, row in consolidated_info.iterrows():
    CSN = str(row['patient_id'])
    consolidated_csn_data = consolidated_info[consolidated_info['patient_id']==int(CSN)]
    h5_file_path = os.path.join(H5_DOWNLOAD_DIR, f'{CSN}.h5')
    output_file_path = os.path.join(OUTPUT_DIR, f'processed/patient-data/{CSN[-2:]}/')

    # Ensure output directory exists
    os.makedirs(output_file_path, exist_ok=True)

    # Download .h5 file from S3
    s3_client.download_file('stanford-ed', f'processed/patient-data/{CSN[-2:]}/{CSN}.h5', h5_file_path)

    with h5py.File(h5_file_path, "r") as f:
        # Load the waveforms
        waveforms_ii = f.get('waveforms')["II"][()]
        waveforms_ppg = f.get('waveforms')["Pleth"][()]
    
    collection_time = pd.to_datetime(consolidated_csn_data['Collection_time'])
    waveform_start = pd.to_datetime(consolidated_csn_data['waveform_start_time'], utc=True)

    episode_length = 10 * 60
    episode_start_time = collection_time - timedelta(seconds=episode_length)
    episode_start_index_ii = ((episode_start_time - waveform_start).dt.total_seconds() * SAMPLING_RATE_ii).astype(int)
    episode_start_index_ppg = ((episode_start_time - waveform_start).dt.total_seconds() * SAMPLING_RATE_ppg).astype(int)



    ii_waveform, ii_quality = get_waveform(waveforms_ii, int(episode_start_index_ii),
                                    episode_length * 500,
                                    500,
                                    should_normalize=False,
                                    bandpass_type=WAVEFORMS_OF_INTERST["II"]["bandpass_type"],
                                    bandwidth=WAVEFORMS_OF_INTERST["II"]["bandpass_freq"],
                                    target_fs=TARGET_FREQ["Pleth"], # downsample 500 Hz to 125 Hz
                                    waveform_type="II",
                                    skewness_max=0.87,
                                    msq_min=0.27)
    
    ppg_waveform, ppg_quality = get_waveform(waveforms_ppg, int(episode_start_index_ppg),
                                    episode_length * 125,
                                    125,
                                    should_normalize=False,
                                    bandpass_type=WAVEFORMS_OF_INTERST["Pleth"]["bandpass_type"],
                                    bandwidth=WAVEFORMS_OF_INTERST["Pleth"]["bandpass_freq"],
                                    target_fs=TARGET_FREQ["Pleth"],
                                    waveform_type="Pleth",
                                    skewness_max=0.87,
                                    msq_min=0.27)
    
    if ii_quality==0:
        print(f"CSN doesn't have qualified II ECG episode")
        falied_ii_count += 1
        continue
    elif ppg_quality==0:
        print(f"CSN doesn't have qualified PPG episode")
        falied_ppg_count += 1
        continue


    # Tokenize the episode into 2-second intervals
    tokens_ii = [ii_waveform[i:i + TOKEN_LENGTH_ii] for i in range(0, len(ii_waveform), TOKEN_LENGTH_ii)]
    tokens_ppg = [ppg_waveform[i:i + TOKEN_LENGTH_ppg] for i in range(0, len(ppg_waveform), TOKEN_LENGTH_ppg)]

    tokens_ii = pd.DataFrame(tokens_ii)
    csv_file_path = os.path.join(output_file_path, f'{CSN}_tokens_ii.csv')
    tokens_ii.to_csv(csv_file_path, index=False)

    tokens_ppg = pd.DataFrame(tokens_ppg)
    csv_file_path = os.path.join(output_file_path, f'{CSN}_tokens_ppg.csv')
    tokens_ppg.to_csv(csv_file_path, index=False)

    os.remove(h5_file_path)
    print(f"Processed and cleaned CSN: {CSN}")

print(f"Total number of CSNs that failed to generate II waveform: {falied_ii_count}")
print(f"Total number of CSNs that failed to generate PPG waveform: {falied_ppg_count}")
print(f"Total number of CSNs: {len(consolidated_info)}")