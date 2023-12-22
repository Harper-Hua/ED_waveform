# ED_waveform
1. Use waveform_label_extract.ipynb to extract labels and their collection time from 'labs_mon_2023_06_26_fixed_tz.csv' and 'vs_comb_2023_09_11.csv'
2. Use meta-info-filter.ipynb to filter in-signal waveform data from consolidated.2020_08_23_2023_05_31.fixed_tz.mrn.csv based on label collection time and the availability of ecg or ppg.
3. Use 'collcetion_time' from filtered condolidated files to dynamically download patient h5 files and preprocessing waveform with waveform_sampler.py.
## Dataset size:
  ### ECG (116184 CSN available)
  1. troponin : 25161 (episodes)
  2. potassium : 69937
  3. calcium : 67376
  ### PPG
  1. RR : 9384701
  2. SBP : 1011876
  3. DBP : 1011876
  4. lactate : 31783
