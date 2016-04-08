from enum import IntEnum

class Inputs(IntEnum):
    V = 0
    I = 1

class Targets(IntEnum):
    V = 0
    I = 1
    VI = 2
    C = 3

class InputRanges_V(IntEnum):
    full_auto = 0
    V0_2_limited = 2
    V2_limited = 20
    V5_limited = 50
    V20_limited = 200
    V40_limited = 400
    V100_limited = 1000
    V500_limited = 5000
    V1500_limited = 15000
    V3000_limited = 30000

class InputRanges_I(IntEnum):
    full_auto = 0
    # limited ranges
    pA1_limited = 8
    pA10_limited = 9
    pA100_limited = 10
    nA1_limited = 11
    nA10_limited = 12
    nA100_limited = 13
    uA1_limited = 14
    uA10_limited = 15
    uA100_limited = 16
    mA1_limited = 17
    mA10_limited = 18
    mA100_limited = 19
    A1_limited = 20
    A2_limited = 21
    A20_limited = 22
    A40_limited = 23

class OutputRanges_V(IntEnum):
    full_auto = 0
    V0_2_limited = 2
    V2_limited = 20
    V5_limited = 50
    V20_limited = 200
    V40_limited = 400
    V100_limited = 1000
    V500_limited = 5000
    V1500_limited = 15000
    V3000_limited = 30000

class OutputRanges_I(IntEnum):
    full_auto = 0
    # limited ranges
    pA1_limited = 8
    pA10_limited = 9
    pA100_limited = 10
    nA1_limited = 11
    nA10_limited = 12
    nA100_limited = 13
    uA1_limited = 14
    uA10_limited = 15
    uA100_limited = 16
    mA1_limited = 17
    mA10_limited = 18
    mA100_limited = 19
    A1_limited = 20
    A2_limited = 21
    A20_limited = 22
    A40_limited = 23


class MeasureModes(IntEnum):
    # MM
    spot = 1  # related source setup: DV,DI
    staircase_sweep = 2  # WI, WV, WT, WM, WSI, WSV
    pulsed_spot = 3  # PI, PV, PT
    pulsed_sweep = 4 # PWI, PWV, PT, WM, WSI, WSV
    staircase_sweep_pulsed_bias = 5 # WI, WV, WM, WSI,WSV, PI, PV, PT
    quasi_pulsed_spot = 9 # BDV, BDT, BDM
    sampling = 10 # MCC, MSC, ML, MT, MI, MV
    quasi_static_cv = 13 # QSV, QST, QSM
    linear_search = 14 # LSV, LSI, LGV, LGI, LSM, LSTM, LSSV, LSSI, LSVM
    binary_search = 15 # BSV, BSI, BGV, BGI, BSM, BST, BSSV, BSSI, BSVM
    multi_channel_sweep = 16 # WI, WV, WT, WM, WNX
    spot_C = 17 # FC, ACV, DCV
    CV_sweep_dc_bias = 18 # FC, ACV, WDCV, WMDCV, WTDCV
    pulsed_spot_C = 19 # PDCV, PTDCV
    pulsed_sweep_CV = 20 # PWDCV, PTDCV
    sweep_Cf = 22 # WFC, ACV, DCV, WMFC, WTFC
    sweep_CV_ac_level = 23 # FC, WACV, DCV, WMACV, WTACV
    sampling_Ct = 26 # MSC, MDCV, MTDCV
    multichannel_pulsed_spot = 27 # MCPT, MCPNT, MCPNX
    multichannel_pulsed_sweep = 28 # MCPT, MCPNT, MCPNX, MCPWS, MCPWNX, WNX


class MeasureSides(IntEnum):
    # CMM
    compliance_side = 0 # returns reverse of force
    current_side = 1
    voltage_side = 2
    force_side = 3 # returns force
    current_and_voltage = 4  # returns as "compliance_side" and "force_side"

class MeasureRanges_V(IntEnum):
    full_auto = 0
    pulse_compliance = 0 # 0, 8-23 with pulse is compliace range, minimum range that covers compliance value
    #limited auto ranging
    V0_2_limited = 2
    V2_limited = 20
    V5_limited = 50
    V20_limited = 200
    V40_limited = 400
    V100_limited = 1000
    V500_limited = 5000
    V1500_limited = 15000
    V3000_limited = 30000
    # fixed raning
    V0_2_fixed = -2
    V2_fixed = -20
    V5_fixed = -50
    V20_fixed = -200
    V40_fixed = -400
    V100_fixed = -1000
    V500_fixed = -5000
    V1500_fixed = -15000
    V3000_fixed = -30000

class MeasureRanges_I(IntEnum):
    # RI
    full_auto = 0
    pulse_compliance = 0 # 0, 8-23 with pulse is compliace range, minimum range that covers compliance value
    # limited ranges
    pA1_limited = 8
    pA10_limited = 9
    pA100_limited = 10
    nA1_limited = 11
    nA10_limited = 12
    nA100_limited = 13
    uA1_limited = 14
    uA10_limited = 15
    uA100_limited = 16
    mA1_limited = 17
    mA10_limited = 18
    mA100_limited = 19
    A1_limited = 20
    A2_limited = 21
    A20_limited = 22
    A40_limited = 23
    # fixed ranges
    pA1_fixed = -8
    pA10_fixed = -9
    pA100_fixed = -10
    nA1_fixed = -11
    nA10_fixed = -12
    nA100_fixed = -13
    uA1_fixed = -14
    uA10_fixed = -15
    uA100_fixed = -16
    mA1_fixed = -17
    mA10_fixed = -18
    mA100_fixed = -19
    A1_fixed = -20
    A2_fixed = -21
    A20_fixed = -22
    A40_fixed = -23
class SweepMode(IntEnum):
    #  up => sweeps from start to stop
    #  up_down => sweeps from start to stop to start
    linear_up = 1
    log_up = 2
    linear_up_down = 3
    log_up_down = 3

class AutoAbort(IntEnum):
    disabled = 1
    enabled = 2
class PulsePeriod(IntEnum):
    minimum = -1
    conservative = 0

class Polarity(IntEnum):
    like_input = 0
    auto = 0
    manual = 1

class SeriesResistance(IntEnum):
    disabled = 0
    enabled = 1

class Formats(IntEnum):
    ascii12_with_header_crl = 1 # compatible with 412B
    ascii12_no_header_crl = 2 # compatible with 412B
    binary4_crl = 3 # compatible with 412B
    binary4 = 4 # compatible with 412B
    ascii12_with_header_comma = 5 # compatible with 412B
    ascii13_with_header_crl = 11
    ascii13_no_header_crl_flex = 12
    binary8_crl = 13
    binary8 = 14
    ascii13_with_header_comma = 15
    ascii13_with_header_crl_flex = 21
    ascii13_no_header_crl_flex2 = 22
    ascii13_with_header_comma_flex = 25

class OutputModes(IntEnum):
    dataonly = 0
    default = 0
    with_primarysource = 1
    with_synchronoussource = 2  # comaptible with MM2, MM5
    # MM16, MM27, and MM28 1-10 select sweep source set by the WNX, MCPNX,
    # or MCPWNX command

class Filter(IntEnum):
    enabled = 0
    disabled = 1
class ADCTypes(IntEnum):
    highspeed = 0
    highresolution = 1
    highspeed_pulse =2

class ADCMode(IntEnum):
    auto = 0
    manual = 1
