
TYPE_II = "II"
TYPE_PLETH = "Pleth"
WAVEFORM_COLUMNS = [TYPE_II, TYPE_PLETH]
# NUMERIC_COLUMNS = ['HR', 'RR', 'SpO2', 'btbRRInt_ms', 'NBPs', 'NBPd', 'Perf']
NUMERIC_COLUMNS = ['HR', 'RR', 'SpO2', '1min_HRV', '5min_HRV', 'NBPs', 'NBPd', 'Perf']
TARGET_FREQ = {
    TYPE_II: 500,
    #     TYPE_II: 125, // 125 is used for the self-supervised project
    TYPE_PLETH: 125,
}
VERBOSE = False

WAVEFORMS_OF_INTERST = {
    "II": {
        "orig_frequency": 500,
        "bandpass_type": 'filter',
        "bandpass_freq": [3, 45]
    },
    "Pleth": {
        "orig_frequency": 125,
        "bandpass_type": 'butter',
        "bandpass_freq": None
    },
    "Resp": {
        "orig_frequency": 62.5,
        "bandpass_type": 'cheby2',
        "bandpass_freq": [0.5, 10]
    }
}
