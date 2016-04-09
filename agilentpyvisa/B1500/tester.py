# vim: set fileencoding: utf-8 -*-
# -*- coding: utf-8 -*-
import visa
from collections import OrderedDict
from .force import *
from .enums import *
from .measurement import *
from .measurement import (Measurement, MeasureSpot, MeasureStaircaseSweep, )
from .setup import *
from .helpers import minCover_I, minCover_V




class B1500():
    def __init__(self, tester):
        self.__rm = visa.ResourceManager()
        self._device = self.__rm.open_resource(tester)
        self.tests = OrderedDict()

    def init(self):
        self.reset()
        self.check_err()


    def reset(self):
        return self._device.query("*RST?")

    def check_err(self):
        return self._device.query("ERR?")  # get errnumber, ermsg

    def operations_completed(self):
        return self._device.query("*OPC?")

    def add_test(name, test_tuple):
        self.tests[name] = test_tuple

    def enable_timestamp(self, state):
        if state:
            return self._device.write("TSC {}".format(1))
        else:
            return self._device.write("TSC {}".format(0))


    def zero_channel(self, channel_number):
        return self._device.write("DZ {}".format(channel_number))

    def restore_channel(self, channel_number):
        return self._device.write("RZ {}".format(channel_number))

    def DC_V_sweep(self, input_channel, ground_channel, start,
        stop, step, compliance, input_range=None, sweepmode=SweepMode.linear_up_down,
        power_comp=None, measure_range=None):
        measure_setup = Measurement(channel=input_channel, config=MeasureStaircaseSweep(target=Targets.I,
            side=MeasureSides.current_side,range=measure_range))
        if input_range is None:
            input_range = minCover_V(start, stop)
        if measure_range is None:
            measure_range = minCover_I(compliance)
        sweep_setup = StaircaseSweep(
            input=Inputs.V,
            start=start,
            stop=stop,
            step=step,
            sweepmode=sweepmode,
            compliance=compliance,
            auto_abort=AutoAbort.enabled,
            input_range=input_range,
            power_comp=power_comp)
        in_channel = Channel(
            number=input_channel,
            staircase_sweep=sweep_setup)
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[in_channel, ground],measurements=[measure_setup],)
        return self.run_test(test)

    def DC_I_spot(self,):
        measure_setup = MeasureSpot()
        assert False

    def DC_V_spot(self,):
        assert False

    def DC_I_sweep(
        self,
        input_channel,
        ground_channel,
        start,
        stop,
        step,
        compliance,
        input_range=None,
        sweepmode=SweepMode.linear_up_down,
        power_comp=None,
     measure_range=None):
        measure_setup = Measurement(
            channel=input_channel,
            config=MeasureStaircaseSweep(target=Targets.V,
            side=MeasureSides.current_side,
            range=measure_range))
        if input_range is None:
            input_range = minCover_I(start, stop)
        if measure_range is None:
            measure_range = minCover_V(compliance)
        sweep_setup = StaircaseSweep(
            input=Inputs.I,
            start=start,
            stop=stop,
            step=step,
            sweepmode=sweepmode,
            compliance=compliance,
            auto_abort=AutoAbort.enabled,
            input_range=input_range,
            power_comp=power_comp)
        in_channel = Channel(
            number=input_channel,
            staircase_sweep=sweep_setup)
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[in_channel, ground],measurements=[measure_setup],)
        return self.run_test(test)

    def run_test(self, test_tuple):
        self.set_format(test_tuple.format, test_tuple.output_mode)
        self.set_filter(test_tuple.filter)
        self.enable_timestamp(True)
        self.set_adc_global(
            adc_modes=test_tuple.adc_modes,
            highspeed_adc_number=test_tuple.highspeed_adc_number,
            highspeed_adc_mode=test_tuple.highspeed_adc_mode)
        for channel in test_tuple.channels:
            self.setup_channel(channel)
        for measurement in test_tuple.measurements:
            self.setup_channel(channel)
        try:
            # resets timestamp, executes and optionally waits for answer,
            # returns data with elapsed
            ret = self.execute(test_tuple.measurements)
        finally:
            for channel in test_tuple.channels:
                self.teardown_channel(channel)
        return ret

    def set_filter(self, filter):
        return self._device.write("FL {}".format(filter))

    def setup_channel(self, channel):
        # connect channel
        self._device.write("CN {}".format(channel.number))  # connect channel
        self._device.write(
            "SSR {},{}".format(
                channel.number,
                channel.series_resistance))  # connects or disconnects 1MOhm series
        self._device.write(
            "AAD {},{}".format(
                channel.number,
                channel.channel_adc))  # sets channel adc type
        # TODO add further channel and measurement setup
        if channel.dcforce is not None:
            return self.dc_force(channel.number, channel.dcforce)
        elif channel.staircase_sweep is not None:
            return self.staircase_sweep(channel.number, channel.staircase_sweep)
        elif channel.pulse_sweep is not None:
            return self.pulse_sweep(channel.number, channel.pulse_sweep)
        elif channel.pulse is not None:
            return self.pulse(channel.number, channel.pulse)
        elif channel.quasipulse is not None:
            return self.quasi_pulse(channel.number, channel.quasipulse)
        elif channel.highspeed_spot is not None:
            return self.highspeed_spot_setup(
                channel.number, channel.highspeed_spot)
        # everything below this comment is not yet implemented
        elif channel.spot is not None:
            return self.spot(channel.number, channel.spot)
        elif channel.SPGU is not None:
            return self.SPGU(channel.number, channel.SPGU)
        else:
            raise ValueError(
                "At least one force should be in the channel, maybe you forgot to force ground to 0?")

    def highspeed_spot_setup(self, channel_number, highspeed_setup):
        if highspeed_setup.target == Targets.C:
            pass  # IMP, FC?

    def highspeed_spot(self, channel_number, highspeed_setup):
        if highspeed_setup.target == Targets.I:
            self._device.write(
                "TTI {},{}".format(
                    channel_number,
                    highspeed_setup.irange))
        elif highspeed_setup.target == Targets.V:
            self._device.write(
                "TTV {},{}".format(
                    channel_number,
                    highspeed_setup.vrange))
        elif highspeed_setup.target == Targets.IV:
            self._device.write(
                "TTIV {},{}".format(
                    channel_number,
                    highspeed_setup.irange,
                    highspeed_setup.vrange))
        elif highspeed_setup.target == Targets.C:
            if highspeed_setup.mode == HighSpeedMode.fixed:
                self._device.write(
                    "TTC {},{},{}".format(
                        channel_number,
                        highspeed_setup.mode,
                        highspeed_setup.Rrange))
            else:
                self._device.write(
                    "TTC {},{}".format(
                        channel_number,
                        highspeed_setup.mode))

    def setup_measurement(self, measurement):
        if measurement.config.mode in [
            MeasureModes.spot,
            MeasureModes.staircase_sweep,
            MeasureModes.sampling,
            MeasureModes.multi_channel_sweep,
            MeasureModes.CV_sweep_dc_bias,
            MeasureModes.multichannel_pulsed_spot,
            MeasureModes.multichannel_pulsed_sweep,
            MeasureModes.pulsed_spot,
            MeasureModes.pulsed_sweep,
            MeasureModes.staircase_sweep_pulsed_bias,
            MeasureModes.quasi_pulsed_spot,
        ]:
            self.measure_single_setup(measurement.channel, measurement.config,)
        elif measurement.config.mode in [
            MeasureModes.spot_C,
            MeasureModes.pulsed_spot_C,
            MeasureModes.pulsed_sweep_CV,
            MeasureModes.sweep_Cf,
            MeasureModes.sweep_CV,
            MeasureModes.sampling_Ct,
        ]:
            self.setup_C_measure(measurement.channel, measurement.config, )
        elif measurement.config.mode == MeasureModes.quasi_static_cv:
            self.setup_quasi_static_cv(measurement.channel, measurement.config)
        elif measurement.config.mode in [MeasureModes.linear_search, MeasureModes.binary_search]:
            self.setup_search(measurement.channel, measurement.config)
        else:
            raise ValueError("Unknown Measuremode")

    def setup_search(self, channel, config):
        self.set_measure_mode(config.mode, channel)
        self.set_search_abort(config.mode,config.auto_abort)
        self.set_search_output(config.mode, config.data_output)
        self.set_search_timing(config.mode, config.hold, config.delay)
        self.set_search_monitor(config.mode, channel, config.search_mode, config.condition,
                                config.measure_range, config.target_value)
        self.set_search_source(config.mode, channel, config.input_range,
                               config.start, config.stop, config.compliance)
        self.set_search_synchronous_source(config.mode, channel, config.polarity,
                                           config.offset, config.compliance )

    def set_search_abort(self, mode, auto_abort):
        if mode == MeasuringModes.binary_search:
            self._device.write("BSM {}".format(auto_abort))
        else:
            self._device.write("LSM {}".format(auto_abort))

    def set_search_output(self, mode, data_output):
        if mode == MeasuringModes.binary_search:
            self._device.write("BSVM {}".format(data_output))
        else:
            self._device.write("LSVM {}".format(data_output))

    def set_search_timing(self, mode, hold, delay):
        if mode == MeasuringModes.binary_search:
            self._device.write("BST {}".format(hold, delay))
        else:
            self._device.write("LSTM {}".format(hold, delay))

    def set_search_monitor(self, mode, channel, search_mode, condition, measure_range, target_value):
        if mode == MeasuringModes.binary_search:
            self._device.write("BGI {}".format(channel, search_mode, condition, measure_range, target_value))
        else:
            self._device.write("LGI {}".format(channel, search_mode, condition, measure_range, target_value))

    def set_search_source(self, target, mode, channel, input_range, start, stop, compliance):
        if target == Targets.V:
            if mode == MeasuringModes.binary_search:
                self._device.write("BSV {}".format(channel, input_range, start, stop, compliance))
            else:
                self._device.write("LSV {}".format(channel, input_range, start, stop, compliance))
        else:
            if mode == MeasuringModes.binary_search:
                self._device.write("BSSI {}".format(channel, input_range, start, stop, compliance))
            else:
                self._device.write("LSSI {}".format(channel, input_range, start, stop, compliance))

    def set_search_synchronous_source(self, target, mode, channel, polarity,offset, compliance):
        if target == Targets.V:
            if mode == MeasuringModes.binary_search:
                self._device.write("BSSV {}".format(channel, polarity, offset, compliance))
            else:
                self._device.write("LSSV {}".format(channel, polarity, offset, compliance))
        else:
            if mode == MeasuringModes.binary_search:
                self._device.write("BSSI {}".format(channel, polarity, offset, compliance))
            else:
                self._device.write("LSSI {}".format(channel, polarity, offset, compliance))


    def setup_quasi_static_cv(self, channel, config):
        self.set_measure_mode(config.mode, channel)
        self.set_quasi_static_compatibility()
        self.set_quasi_static_leakage()
        self.set_quasi_static_abort()
        self.set_quasi_static_measure_range()
        self.set_quasi_static_timings()
        self.set_quasi_static_source()

    def set_quasi_static_compatibility(self, compat):
        self._device("QSC {}".format(compat))
    def set_quasi_static_leakage(self, output, compensation):
        self._device("QSL {}".format())
    def set_quasi_static_abort(self, abort):
        self._device("QSM {}".format(abort))
    def set_quasi_static_measure_range(self, range):
        self._device("QSR {}".format(range))
    def set_quasi_static_timings(self, C_integration, L_integration, hold, delay,delay1=0,delay2=0):
        self._device("QST {},{},{},{}".format())
    def set_quasi_static_source(self, channel, mode, vrange, start, stop, capacitive_measure_voltage, step, compliance):
        self._device("QSV {}".format())

    def setup_C_measure(self, channel, config):
        self.adjust_paste_compensation(channel, config.auto_compensation, config.compensation_data)
        self.set_C_ADC_samples(self, config.adc_mode, config.ADC_coeff)

    def set_C_ADC_samples(self, mode, coeff=None):
        self._device.write("ACT {}".format(",".join(["{}".format(x) for x in [adc_mode, coeff] if x])))

    def adjust_phase_compensation(self, channel, auto_compensation, compensation_data):
        self._device.write("ADJ {},{}".format(channel, config.auto_compensation))
        self._device.write("ADJ? {},{}".format(channel, config.compensation_data))

    def set_measure_mode(self, mode, channel):
        self._device.write(
        "MM {}".format(",".join(["{}".format(x) for x in [mode, channel]])))

    def set_measure_side(self, channel, side):
        self._device.write("CMM {},{}".format(channel, side))

    def set_measure_range(self, channel, target, range):
            if target == Inputs.V:
                self._device.write(
                    "RV {},{}".format(
                        channel,
                        range))  # sets channel adc type
            else:
                self._device.write(
                    "RI {},{}".format(
                        channel,
                        range))  # sets channel adc type


    def measure_single_setup(self, channel, config):
        self.set_measure_mode(config.mode, channel)
        if mode not in set([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_side(channel, config.side)
        if mode not in set([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_range(channel, config.target, config.range)

    def dc_force(self, channel_number, force_setup):
        force_query = ",".join(["{}".format(x) for x in force_setup[1:]])
        if force_setup.input == Inputs.V:
            return self._device.write(
                "DV {},{}".format(
                    channel_number,
                    force_query))
        if force_setup.input == Inputs.I:
            return self._device.write(
                "DI {},{}".format(
                    channel_number,
                    force_query))

    def staircase_sweep(self, channel_number, sweep_setup):
        self._device.write(
            "WT {},{}".format(
                sweep_setup.hold,
                sweep_setup.delay))
        self._device.write("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self._device.write("WV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -3]
                                               if isinstance(x, IntEnum)])))
        else:
            return self._device.write("WI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -3]
                                               if isinstance(x, IntEnum)])))

    def pulse_sweep(self, channel_number, sweep_setup):
        self._device.write(
            "PT {},{}".format(
                sweep_setup.hold,
                sweep_setup.width,
                sweep_setup.period))
        self._device.write("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self._device.write("PWV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -4] if x])))
        else:
            return self._device.write("PWI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -4] if x])))

    def quasi_pulse(self, channel_number, quasi_setup):
        self._device.write("BDT {},{}".format(
            *["{}".format(x) for x in quasi_setup[-2:]]))
        self._device.write("BDM {},{}".format(
            *["{}".format(x) for x in quasi_setup[0:2]]))
        self._device.write("BDV {},{}".format(
            channel_number, *["{}".format(x) for x in quasi_setup[2:6]]))

    def SPGU(channel_number):
        pass
    """
        ("CN " & sp_ch(0) & "," & sp_ch(1) & vbLf)
        (SIM 0" & vbLf)
        ("SPRM 2," & duration & vbLf)
        ("ODSW " & sp_ch(0) & ", 0" & vbLf)
        ("ODSW " & sp_ch(1) & ", 0" & vbLf)
        ("SER " & sp_ch(0) & "," & loadz & vbLf)
        ("SER " & sp_ch(1) & "," & loadz & vbLf)
        ("SPPER " & period & vbLf)
        ("SPM " & sp_ch(0) & ",1" & vbLf)
        ("SPT " & sp_ch(0) & ",1," & p1_del & "," & p1_wid & "," &
        p_lead & "," & p_trail & vbLf)
        ("SPV " & sp_ch(0) & ",1," & p1_base & "," & p1_peak & vbLf)
        ("SPM " & sp_ch(1) & ",3" & vbLf)
        ("SPT " & sp_ch(1) & ",1," & p2_del1 & "," & p2_wid1 & "," &
        p_lead & "," & p_trail & vbLf)
        ("SPT " & sp_ch(1) & ",2," & p2_del2 & "," & p2_wid2 & "," &
        p_lead & "," & p_trail & vbLf)
        ("SPV " & sp_ch(1) & ",1," & p2_base1 & "," & p2_peak1 & vbLf)
        ("SPV " & sp_ch(1) & ",2," & p2_base2 & "," & p2_peak2 & vbLf)
        ("SPUPD" & sp_ch(0) & "," & sp_ch(1) & vbLf)
        """

    def teardown_channel(self, channel):
        # force voltage to 0
        self._device.write("DZ {}".format(channel.number))
        # disconnect channel
        self._device.write("CL {}".format(channel.number))

    def set_format(self, format, output_mode):
        self._device.write("FMT {},{}".format(format, output_mode))

    def execute(self, measurements, force_wait=False, autoread=True):
        def inner():
            for measurement in measurements:
                if measurement in ["list", "XE", "activated", "measurements"]:
                    exc = self._device.query("XE")
                    if force_wait:
                        exc = self._device.write("*OPC?")
                    if autoread:
                        data = self._device.query("NUB?")
                        yield (exc, data)
                    else:
                        yield (exc, None)
                elif isinstance(measurement, HighSpeedSpot):
                    yield self.highspeed_spot(channel.number, measurement)
        return list(inner())

    def set_adc_global(
        self,
        adc_modes=[],
        highspeed_adc_number=None,
     highspeed_adc_mode=None):
        if adc_modes:
            [self._device.write(
                 "AIT {}".format(",".join(["{}".format(x) for x in setting])))
             for setting in adc_modes]
        else:
            if highspeed_adc_number is None or highspeed_adc_mode is None:
                raise ValueError(
                    "Either give complete adc mapping or specify highspeed ADC")
            self._device.write(
                "AV {}, {}".format(
                    highspeed_adc_number,
                    highspeed_adc_mode))

    def pulse(self, channel_number, pulse_setup):
        self._device.write(
            "PT {}, {}, {}, {}".format(*pulse_setup[-3:]))
        if pulse_setup.input == Inputs.V:
            self._device.write(
                "PV {},{},{},{},{}".format(channel_number, pulse_setup[1:-3]))
        else:
            self._device.write(
                "PI {},{},{},{},{}".format(channel_number, pulse_setup[1:-3]))
