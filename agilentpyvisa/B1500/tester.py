# from itertools import zip_longest
from collections import OrderedDict
from .tests import *


class DummyTester():

    def __init__(self):
        pass

    def query(*args, **kwargs):
        print([x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)
        return False

    def write(*args, **kwargs):
        print([x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)


class B1500():

    def __init__(self):
        self._device = DummyTester()  # open pyvisa device
        self.tests = OrderedDict()

    def init(self):
        self.reset()
        self.check_err()

    def reset(self):
        return self._device.query("*RST?")

    def operations_completed(self):
        return self._device.query("*OPC?")

    def add_test(name, test_tuple):
        self.tests[name] = test_tuple

    def enable_timestamp(self, state):
        if state:
            return self._device.query("TSC {}".format(1))
        else:
            return self._device.query("TSC {}".format(0))

    def check_err(self):
        return self._device.query("ERR?")  # get errnumber, ermsg

    def zero_channel(self, channel_number):
        return self._device.query("DZ {}".format(channel_number))

    def restore_channel(self, channel_number):
        return self._device.query("RZ {}".format(channel_number))

    def DC_V_sweep(
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
            target=Targets.I,
            mode=MeasureModes.staircase_sweep,
            side=MeasureSides.current_side,
            range=measure_range)
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
        test = TestSetup(
            channels=[in_channel, ground],
            measurements=[measure_setup],
                         )
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
        return self._device.query("FL {}".format(filter))

    def setup_channel(self, channel):
        # connect channel
        self._device.query("CN {}".format(channel.number))  # connect channel
        self._device.query(
            "SSR {},{}".format(
                channel.number,
                channel.series_resistance))  # connects or disconnects 1MOhm series
        self._device.query(
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
        if measurement.mode in ONE_CHANNEL:
            self._device.query(
                "MM {}".format(",".join(["{}".format(x) for x in [measurement.mode, measurement.channel]])))
        elif  measurement.mode in OPTIONAL_CHANNEL:
                "MM {}".format(",".join(["{}".format(x) for x in [measurement.mode, measurement.channel] if x]))
        elif measurement.mode in ONE_TO_TEN_CHANNELS:
            self._device.query(
                "MM {}".format(",".join(["{}".format(x) for x in [measurement.mode]+measurement.channel if x])))
            for c in measurement.channel:
                # connects or disconnects 1MOhm series
                self._device.query("CMM {},{}".format(c, measurement.side))
        elif measurement.mode in NO_CHANNEL:
            self._device.query("MM {}".format(measurement.mode,))  # connect channel
        if measurement.target == Inputs.V:
            return self._device.query(
                "RV {},{}".format(
                    channel_number,
                    measurement.range))  # sets channel adc type
        else:
            return self._device.query(
                "RI {},{}".format(
                    channel_number,
                    measurement.range))  # sets channel adc type

    def dc_force(self, channel_number, force_setup):
        force_query = ",".join(["{}".format(x) for x in force_setup[1:]])
        if force_setup.input == Inputs.V:
            return self._device.query(
                "DV {},{}".format(
                    channel_number,
                    force_query))
        if force_setup.input == Inputs.I:
            return self._device.query(
                "DI {},{}".format(
                    channel_number,
                    force_query))

    def staircase_sweep(self, channel_number, sweep_setup):
        self._device.query(
            "WT {},{}".format(
                sweep_setup.hold,
                sweep_setup.delay))
        self._device.query("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self._device.query("WV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -3]
                                               if isinstance(x, IntEnum)])))
        else:
            return self._device.query("WI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -3]
                                               if isinstance(x, IntEnum)])))

    def pulse_sweep(self, channel_number, sweep_setup):
        self._device.query(
            "PT {},{}".format(
                sweep_setup.hold,
                sweep_setup.width,
                sweep_setup.period))
        self._device.query("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self._device.query("PWV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -4] if x])))
        else:
            return self._device.query("PWI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -4] if x])))

    def quasi_pulse(self, channel_number, quasi_setup):
        self._device.query("BDT {},{}".format(
            *["{}".format(x) for x in quasi_setup[-2:]]))
        self._device.query("BDM {},{}".format(
            *["{}".format(x) for x in quasi_setup[0:2]]))
        self._device.query("BDV {},{}".format(
            channel_number, *["{}".format(x) for x in quasi_setup[2:6]]))

    def SPGU(channel_number):
        pass
        """
        session.WriteString("CN " & sp_ch(0) & "," & sp_ch(1) & vbLf) ’SPGU ch on
        ’37
        session.WriteString("SIM 0" & vbLf)
        ’PG mode
        session.WriteString("SPRM 2," & duration & vbLf)
        ’Duration mode
        session.WriteString("ODSW " & sp_ch(0) & ", 0" & vbLf) ’Disables pulse switch ’40
        session.WriteString("ODSW " & sp_ch(1) & ", 0" & vbLf)
        session.WriteString("SER " & sp_ch(0) & "," & loadz & vbLf)
        ’Load impedance
        session.WriteString("SER " & sp_ch(1) & "," & loadz & vbLf)
        session.WriteString("SPPER " & period & vbLf)
        ’Pulse period
        session.WriteString("SPM " & sp_ch(0) & ",1" & vbLf)
        ’2-level pulse setup
        ’45
        session.WriteString("SPT " & sp_ch(0) & ",1," & p1_del & "," & p1_wid & "," &
        p_lead & "," & p_trail & vbLf)
        session.WriteString("SPV " & sp_ch(0) & ",1," & p1_base & "," & p1_peak & vbLf)
        session.WriteString("SPM " & sp_ch(1) & ",3" & vbLf)
        ’3-level pulse setup
        ’48
        session.WriteString("SPT " & sp_ch(1) & ",1," & p2_del1 & "," & p2_wid1 & "," &
        p_lead & "," & p_trail & vbLf)
        session.WriteString("SPT " & sp_ch(1) & ",2," & p2_del2 & "," & p2_wid2 & "," &
        p_lead & "," & p_trail & vbLf)
        session.WriteString("SPV " & sp_ch(1) & ",1," & p2_base1 & "," & p2_peak1 & vbLf)
        session.WriteString("SPV " & sp_ch(1) & ",2," & p2_base2 & "," & p2_peak2 & vbLf)
        session.WriteString("SPUPD" & sp_ch(0) & "," & sp_ch(1) & vbLf) ’Apply setup ’53
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
