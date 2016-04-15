# vim: set fileencoding: utf-8 -*-
# -*- coding: utf-8 -*-
import numpy as np
import visa
from collections import OrderedDict
from .force import *
from .force import (
                    DCForce,
                    StaircaseSweep,
                    PulsedSpot,
                    SPGU)
from .enums import *
from .measurement import *
from .measurement import (
                          MeasureSpot,
                          MeasureStaircaseSweep,
                          MeasurePulsedSpot,
                          MeasureSPGU)
from .setup import *
from .helpers import *
from logging import getLogger


query_logger = getLogger(__name__+":query")
write_logger = getLogger(__name__+":write")
exception_logger = getLogger(__name__+":ERRORS")


class B1500():
    def __init__(self, tester, auto_init=True):
        self.__rm = visa.ResourceManager()
        self._device = self.__rm.open_resource(tester)
        self.tests = OrderedDict()
        self.slots_installed={}
        self.sub_channels = []
        if auto_init:
            self.init()

    def init(self):
        """ Resets the connected tester, then checks all installed modules,
        querying their types and the available subchannels. It also
        stores the available input and measure_ranges in the slots_installed dict,
        with the slot number as key. sub channels is a list containing
        all available channels"""
        self._reset()
        self.slots_installed = self.__discover_slots()
        self.sub_channels = self.__discover_channels(self.slots_installed)
        self._check_err()

    def query(self, msg, delay=None,check_error=False):
        """ Writes the msg to the Tester, reads output buffer after delay and
        logs both to the query logger.Optionally checks for errors afterwards"""
        query_logger.info(msg)
        retval = self._device.query(msg, delay=delay)
        query_logger.info(str(retval)+"\n")
        if check_error:
            exception_logger.info(self._check_err())
        return retval

    def write(self, msg, check_error=False):
        """ Writes the msg to the Tester and logs it in the write
        logger.Optionally checks for errors afterwards"""
        write_logger.info(msg)
        retval = self._device.write(msg)
        write_logger.info(str(retval)+"\n")
        if check_error:
            exception_logger.info(self._check_err())
        return retval

    def read(self, check_error=False):
        """ Reads out the current output buffer and logs it to the query logger
        optionally checking for errors"""
        retval = self._device.read()
        query_logger.info(str(retval)+"\n")
        if check_error:
            exception_logger.info(self._check_err())
        return retval

    def measure(self, test_tuple, force_wait=False, autoread=False):
        """ Checks the channels defined in the test tuple and performs the
        measurement the Setup represents. Only one type of measurement is possible,
        otherwise it raises an exception."""
        channels = test_tuple.channels
        exc = None
        data = None
        XE_measurement=any([c.measurement and c.measurement.mode in(
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
        ) for c in channels])
        SPGU =any([x.spgu for x in channels])
        if [XE_measurement, SPGU,].count(True)>1:
            raise ValueError("Only one type of Measurement can be defined, please check your channel setups")
        # Measurements triggered by XE, read via NUB
        if XE_measurement:
            exc = self.write("XE")
            if force_wait:
                ready = 0
                while ready == 0:
                    ready = self._operations_completed()
            if autoread:
                if isSweep(channels):
                    data = self.__read_sweep(channels)
        # SPGU measurements
        elif SPGU:
            exc= self._SPGU_start()
            if force_wait:
                self._SPGU_wait()
        return (exc,self.__parse_output(test_tuple.format, data))


    def check_settings(self, parameter):
        """ Queries the tester for the specified parameter
        (see enums.py or tabcomplete for available parameters)"""
        ret = self.query("*LRN? {}".format(parameter))
        return ret


    def SPGU(self, input_channel, pulse_base, pulse_peak, pulse_width):
        """ Performs a simple SPGU pulse """
        pulse_channel=Channel(number=input_channel, spgu=SPGU(pulse_base, pulse_peak,pulse_width))
        test = TestSetup(channels=[pulse_channel])
        self.run_test(test)

    def DC_Sweep_V(self, input_channel, ground_channel, start,
        stop, step, compliance, input_range=None, sweepmode=SweepMode.linear_up_down,
        power_comp=None, measure_range=MeasureRanges_I.full_auto):
        """ Performs a quick Voltage staircase sweep measurement on the specified channels """
        return self._DC_Sweep(Targets.V, input_channel, ground_channel, start,
        stop, step, compliance, input_range, sweepmode,
        power_comp, measure_range)

    def DC_Sweep_I(self, input_channel, ground_channel, start,stop, step, compliance, input_range=None, sweepmode=SweepMode.linear_up_down,
            power_comp=None, measure_range=MeasureRanges_I.full_auto):
        """ Performs a quick Current staircase sweep measurement on the specified channels """
        return self._DC_Sweep(Targets.I, input_channel, ground_channel, start,
        stop, step, compliance, input_range, sweepmode,
        power_comp, measure_range)

    def PulsedSpot_I(self, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        """ Performs a quick PulsedSpot Current measurement the specified channels """
        return self._PulsedSpot(Targets.I, input_channel, ground_channel, base, pulse, width,compliance,measure_range, hold )

    def PulsedSpot_V(self, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        """ Performs a quick PulsedSpot Voltage measurement the specified channels """
        return self._PulsedSpot(Targets.V, input_channel, ground_channel, base, pulse, width,compliance,measure_range, hold )



    def DC_spot_I(self, input_channel, ground_channel, input_value,
            compliance, input_range=InputRanges_I.full_auto, power_comp=None,
            measure_range=MeasureRanges_V.full_auto):
        """ Performs a quick Spot Current measurement the specified channels """
        return self._DC_spot(Targets.I, input_channel, ground_channel, input_value,
            compliance, input_range, power_comp,
            measure_range)

    def DC_spot_V(self, input_channel, ground_channel, input_value,
            compliance, input_range = InputRanges_V.full_auto, power_comp=None,
            measure_range=MeasureRanges_I.full_auto):
        """ Performs a quick Spot Voltage measurement the specified channels """
        return self._DC_spot(Targets.V, input_channel, ground_channel, input_value,
            compliance, input_range, power_comp,
            measure_range)

    def run_test(self, test_tuple, force_wait=False, auto_read=False):
        """ Takes in a test tuple specifying channel setups and global parameters,
        setups up parameters, channels and measurements accordingly and then performs the specified test,
        returning gathered data if auto_read was specified. Allways
        cleans up any opened channels after being run (forces zero and disconnect)"""
        self._set_format(test_tuple.format, test_tuple.output_mode)
        self._set_filter(test_tuple.filter)
        self._enable_timestamp(True)
        self._set_adc_global(
            adc_modes=test_tuple.adc_modes,
            highspeed_adc_number=test_tuple.highspeed_adc_number,
            highspeed_adc_mode=test_tuple.highspeed_adc_mode)
        try:
            for channel in test_tuple.channels:
                self.setup_channel(channel)
                # resets timestamp, executes and optionally waits for answer,
                # returns data with elapsed
            ret = self.measure(test_tuple, force_wait,auto_read)
        finally:
            for channel in test_tuple.channels:
                self._teardown_channel(channel)
        return ret

    def _PulsedSpot(self, target, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        if target == Targets.V:
            input = Inputs.I
        else:
            input = Inputs.V
        if input_range is None:
            if input == Inputs.I:
                input_range = self._get_mincover_I(self.__channel_to_slot(input_channel),base, pulse)
            else:
                input_range = self._get_mincover_V(self.__channel_to_slot(input_channel),base, pulse)
        if measure_range is None:
            if target == Inputs.I:
                measure_range = self._get_mincover_I(self.__channel_to_slot(input_channel),compliance)
            else:
                measure_range = self._get_mincover_V(self.__channel_to_slot(input_channel),compliance)

        measure_setup = MeasurePulsedSpot(target=target,
                        side=MeasureSides.voltage_side,
                        range=measure_range)

        measure_channel = Channel(number=input_channel,
                                  pulsed_spot=PulsedSpot(input=input,
                                                         input_range=input_range,
                                                         base=base,
                                                         pulse=pulse,
                                                         width=width,
                                                         compliance=compliance,
                                                         hold=hold),
                                    measurement=measure_setup
                                  )
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[measure_channel, ground],)
        return self.run_test(test)

    def _DC_Sweep(self,target,input_channel,ground_channel,
        start,stop,step,compliance,input_range=None,sweepmode=SweepMode.linear_up_down,
        power_comp=None,measure_range=MeasureRanges_I.full_auto):
        if target == Targets.V:
            input = Inputs.I
        else:
            input = Inputs.V
        if input_range is None:
            if input == Inputs.I:
                input_range = self._get_mincover_I(self.__channel_to_slot(input_channel),start, stop)
            else:
                input_range = self._get_mincover_V(self.__channel_to_slot(input_channel),start,stop)
        if measure_range is None:
            if target == Inputs.I:
                measure_range = self._get_mincover_I(self.__channel_to_slot(input_channel),compliance)
            else:
                measure_range = self._get_mincover_V(self.__channel_to_slot(input_channel),compliance)
        measure_setup = MeasureStaircaseSweep(target=target,
                                              range=measure_range)
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
            staircase_sweep=sweep_setup,
            measurement=measure_setup)
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[in_channel, ground],)
        return self.run_test(test)

    def _DC_spot(self,target, input_channel, ground_channel, input_value,
            compliance, input_range=InputRanges_I.full_auto, power_comp=None,
            measure_range=MeasureRanges_V.full_auto):
        if target == Targets.V:
            input = Inputs.I
        else:
            input = Inputs.V
        if input_range is None:
            if input == Inputs.I:
                input_range = self._get_mincover_I(self.__channel_to_slot(input_channel),input_value)
            else:
                input_range = self._get_mincover_V(self.__channel_to_slot(input_channel),input_value)
        if measure_range is None:
            if target == Inputs.I:
                measure_range = self._get_mincover_I(self.__channel_to_slot(input_channel),compliance)
            else:
                measure_range = self._get_mincover_V(self.__channel_to_slot(input_channel),compliance)

        measure = MeasureSpot(target=target, range=measure_range)
        measure_channel = Channel(number=input_channel,
                          dcforce=DCForce(input=input,
                                           value=input_value,
                                           compliance=compliance,
                                           input_range=input_range,
                                           power_comp=power_comp),
                                  measurement=measure)
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance,
            input_range=InputRanges_V.full_auto)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[measure_channel, ground],)
        self.run_test(test)
# methods ideally used indirectly, but might want to be used for finegrained
# control or for convenvience

    def _operations_completed(self):
        """ Queries tester for pending operations. Timeout needs to be set to
        infinite, since tester will only respond after finishing current
        operation"""
        old_timeout = self._device.timeout
        self._device.timeout = None
        ready = int(self.query("*OPC?").strip())
        self._device.timeout = old_timeout
        return ready

    def _enable_timestamp(self, state):
        """ Enable Timestamp during measurements"""
        if state:
            return self.write("TSC {}".format(1))
        else:
            return self.write("TSC {}".format(0))

    def _reset_timestamp(self):
        """ Clears Timestamp counter, if 100us resolution call this at least
        every 100s for FMT 1,2 or 5, every 1000 for FMT 11,12,15,21,22,25"""
        self.write("TSR")


    def _restore_channel(self, channel_number):
        """ Restores the channel parameters before the last force_zero command"""
        return self.write("RZ {}".format(channel_number))

    def _get_mincover_V(self, slot, val1, val2=None):
        """ This returns the smallest voltage range covering the largest given
        values. Only returns auto or limited, in order to be used both for measure and input ranges.
        Takes into account the slots which will be used"""
        val = val1
        if val2:
            val= max(abs(val),abs(val2))
        cov =[(k,v) for k,v in MeasureRanges_V.__members__.items() if v>=10*val
          and MeasureRanges_V[k] in self.slots_installed[slot]["InputRanges"]]
        if cov:
            mincov =min(cov,key=lambda x:x.__getitem__(1))
            return MeasureRanges_V[mincov[0]]
        else:
            return MeasureRanges_V.full_auto

    def _get_mincover_I(self, slot, val1, val2=None):
        """ This returns the smallest voltage range covering the largest given
        values. Only returns auto or limited, in order to be used both for measure and input ranges.
        Takes into account the slots which will be used"""
        val = val1
        if val2:
            val= max(abs(val),abs(val2))
        def valid(y):
            covered= MeasureRanges_I[y].value >0 and MeasureRanges_I[y].value <=20
            return covered and MeasureRanges_I[y] in self.slots_installed[slot]["InputRanges"]
        range_map={round(1e-12*pow(10,i),12):x for i,x in enumerate(
                (y for y in MeasureRanges_I.__members__ if valid(y)))
                }
        range_map[2]=MeasureRanges_I.A2_limited
        range_map[20]=MeasureRanges_I.A20_limited
        range_map[40]=MeasureRanges_I.A40_limited
        cov = [x for x in range_map.keys() if x >= val]
        if cov:
            mincov = min(cov)
            return range_map[mincov]
        else:
            return MeasureRanges_I.full_auto

    def setup_channel(self, channel):
        """ Configures channel with any parameters which can be set before
        the acutal measurement or without any measurement at all"""
        self._open_channel(channel.number)
        self._set_series_resistance(channel.number, channel.series_resistance)
        self._set_channel_ADC_type(channel.number, channel.channel_adc)
        if channel.measurement:
            self._setup_measurement(channel.number, channel.measurement)

        if channel.dcforce is not None:
            self._setup_dc_force(channel.number, channel.dcforce)
        elif channel.staircase_sweep is not None:
            self._setup_staircase_sweep(channel.number, channel.staircase_sweep)
        elif channel.pulse_sweep is not None:
            self._setup_pulse_sweep(channel.number, channel.pulse_sweep)
        elif channel.pulsed_spot is not None:
            self._setup_pulsed_spot(channel.number, channel.pulsed_spot)
        elif channel.quasipulse is not None:
            raise NotImplementedError("Quasipulse measurements not yet implemented")
        elif channel.highspeed_spot is not None:
            raise NotImplementedError("HighSpeedSpot measurements not yet implemented")
        elif channel.spgu is not None:
            self._setup_spgu(channel.number, channel.spgu)
        else:
            raise ValueError(
                "At least one setup should be in the channel, maybe you forgot to force ground to 0?")
        errors = []
        ret = self._check_err()
        if ret[:2]=='+0':
            return ret
        else:
            while ret[:2]!='+0':
                errors.append(ret)
                ret=self._check_err()
            return errors


    def _setup_measurement(self,channel, measurement):
        """ Sets up all parameters containing to the measurement. This is a
        dispatcher function, since a lot fo measurements have overlapping setup.
        Parameters Concerning the channel setup are handled in the respective
        setup_X functions, this function and its callees are only concerned with
        the measurements themselves."""
        if measurement.mode in [
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
            self.measure_single_setup(channel, measurement)
        elif measurement.mode in [
            MeasureModes.spot_C,
            MeasureModes.pulsed_spot_C,
            MeasureModes.pulsed_sweep_CV,
            MeasureModes.sweep_Cf,
            MeasureModes.sweep_CV,
            MeasureModes.sampling_Ct,
        ]:
            raise NotImplemented("CapacitanceMeasurement not yet implemented")
        elif measurement.mode == MeasureModes.quasi_static_cv:
            raise NotImplemented("QuasistatiCV measurement not yet implemented")
        elif measurement.mode in [MeasureModes.linear_search, MeasureModes.binary_search]:
            raise NotImplemented("Search  measurement not yet implemented")
        else:
            raise ValueError("Unknown Measuremode")

    def _measure_single_setup(self, channel, config):
        """ Configures most XE triggered measurements. """
        self._set_measure_mode(config.mode, channel)
        if config.mode not in set([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self._set_measure_side(channel, config.side)
        if config.mode not in set([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self._set_measure_range(channel, config.target, config.range)

    def _setup_dc_force(self, channel_number, force_setup):
        """ Sets up the channel configuration for forcing a DC force or current."""
        if force_setup.input_range not in self.slots_installed.get(channel_number)["InputRanges"]:
            raise ValueError("Input range {} of channel {} not available in installed module {}".format(
                repr(force_setup.input_range),channel_number,self.slots_installed[channel_number]))
        if force_setup.input == Inputs.V:
            return self.write(format_command("DV",channel_number,
                                           force_setup.input_range,
                                           force_setup.value,
                                           force_setup.compliance,
                                           force_setup.polarity,
                                           force_setup.compliance_range,
                                           force_setup.power_comp))
        if force_setup.input == Inputs.I:
            return self.write(format_command("DI",channel_number,
                                           force_setup.input_range,
                                           force_setup.value,
                                           force_setup.compliance,
                                           force_setup.polarity,
                                           force_setup.compliance_range,
                                           force_setup.power_comp))

    def _setup_staircase_sweep(self, channel_number, sweep_setup):
        self.write(
            "WT {},{}".format(
                sweep_setup.hold,
                sweep_setup.delay))
        self.write("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self.write("WV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in [channel_number]+list(sweep_setup[1: -3])
                                               if x is not None])))
        else:
            return self.write("WI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in [channel_number]+list(sweep_setup[1: -3])
                                               if x is not None])))

    def _setup_pulse_sweep(self, channel_number, sweep_setup):
        self.write(
            "PT {},{}, {}".format(
                sweep_setup.hold,
                sweep_setup.width,
                sweep_setup.period))
        self.write("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self.write("PWV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -4] if x])))
        else:
            return self.write("PWI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -4] if x])))



    def _setup_spgu(self, channel_number, spgu_setup):
        self._SPGU_set_wavemode(spgu_setup.wavemode)
        self._SPGU_set_output_mode(spgu_setup.output_mode, spgu_setup.condition)
        self._SPGU_set_pulse_switch(channel_number, spgu_setup.switch_state, spgu_setup.switch_normal, spgu_setup.switch_delay, spgu_setup.switch_width)   #ODSW
        self._SPGU_set_pulse_period(spgu_setup.pulse_period)  # SPPER
        if spgu_setup.wavemode == SPGUModes.Pulse:
            self._SPGU_set_pulse_levels(channel_number, spgu_setup.pulse_level_sources, spgu_setup.pulse_base, spgu_setup.pulse_peak, spgu_setup.pulse_src)  # SPM, SPV, check if pulse_src==source
        else:
            raise NotImplementedError("Arbitrary Linear Wavemode will be added in a later release")
        self._SPGU_set_pulse_timing(channel_number, spgu_setup.timing_source, spgu_setup.pulse_delay, spgu_setup.pulse_width, spgu_setup.pulse_leading, spgu_setup.pulse_trailing,)  # SPT
        self._SPGU_set_apply(channel_number)  # SPUPD
        if spgu_setup.loadZ == SPGUOutputImpedance.full_auto:
            self._SPGU_set_loadimpedance_auto(channel_number)
        else:
            self._SPGU_set_loadimpedance(channel_number, spgu_setup.loadZ)  # SER

    def _setup_pulsed_spot(self, channel_number, pulse_setup):
        pt_ret = self.write(
            format_command("PT",pulse_setup.hold , pulse_setup.width, pulse_setup.period))
        if pulse_setup.input == Inputs.V:
            return [pt_ret,self.write(format_command("PV",channel_number, pulse_setup.input_range, pulse_setup.base, pulse_setup.pulse,pulse_setup.compliance))]
        else:
            return [pt_ret,self.write(format_command("PI",channel_number, pulse_setup.input_range, pulse_setup.base, pulse_setup.pulse,pulse_setup.compliance))]

    # individual commands (grouped only for input/target types, i.e. V/I

    def _set_filter(self, filter):
        """ Sets the spike and overshoot filter on the SMU output."""
        return self.write("FL {}".format(filter))

    def _open_channel(self, number):
        """ Connects the SMU source to the specified channel"""
        if number not in self.sub_channels:
            raise ValueError("Channel {} not available on device, only \n{}\n are available".format(number,self.sub_channels))
        return self.write("CN {}".format(number))  # connect channel

    def _set_series_resistance(self, channel, state):
        """Enables or disables the ~1MOhm SMU series resistor"""
        return self.write(
            "SSR {},{}".format(
                channel,
                state))  # connects or disconnects 1MOhm series

    def _set_channel_ADC_type(self, channel, adc):
        """ Selects which ADC to use for the specified channe. Available are
        highspeed = 0
        highresolution = 1
        highspeed_pulse =2
        Default is highspeed
        """
        return self.write(
            "AAD {},{}".format(
                channel,
                adc))  # sets channel adc type

    def _set_measure_mode(self, mode, channel):
        """ Defines which measurement to perform on the channel. Not used for all measurements,
        check enums.py  or MeasureModes for a full list of measurements"""
        self.write(
        "MM {}".format(",".join(["{}".format(x) for x in [mode, channel]])))

    def _set_measure_side(self, channel, side):
        """ Specify whether the sensor should read on the current, voltage,
        compliance or force side. See MeasureSides"""
        self.write("CMM {},{}".format(channel, side))

    def _set_measure_range(self, channel, target, range):
        """ Sets measure ranges out of available Ranges. The less range changes,
        the faster the measurement. Thus the spees increases from full_auto to
        limited to fixed. See MeasureRanges_X for availble values"""
        if target == Inputs.V:
            self.write(
                "RV {},{}".format(
                    channel,
                    range))  # sets channel adc type
        else:
            self.write(
                "RI {},{}".format(
                    channel,
                    range))  # sets channel adc type



    def _SPGU_set_apply(self, channel):
        """ Applys the recently set configuration to SPGU, immediately staring to force
        base voltage"""
        self.write("SPUPD {}".format(channel))

    def _SPGU_set_pulse_timing(self, channel, source, delay, width, leading, trailing):
        self.write(format_command("SPT",channel, source, delay, width, leading, trailing))

    def _SPGU_set_pulse_levels(self, channel, level_sources, base, peak, pulse_src):
        self.write(format_command("SPM",channel, level_sources))
        self.write(format_command("SPV",channel, pulse_src, base, peak))


    def _SPGU_set_loadimpedance(self, channel, loadZ):
            self.write(format_command("SER",channel, loadZ))

    def _SPGU_set_loadimpedance_auto(self, channel,update_impedance=1, delay=0, interval=5e-6,count=1 ):
            self.write(format_command("CORRSER?",channel, update_impedance, delay, interval, count ))
            # execute a single measurement and set the output load

    def _SPGU_set_pulse_period(self, pulse_period):
        self.write(format_command("SPPER",pulse_period))

    def _SPGU_set_pulse_switch(self, channel, switch_state, switch_normal, switch_delay, width):
        self.write(format_command("ODSW",channel, switch_state, switch_normal, switch_delay, width ))

    def _SPGU_set_output_mode(self, output_mode, condition):
        self.write(format_command("SPRM",output_mode, condition))

    def _SPGU_set_wavemode(self, mode):
        """ Changes betwee pulsed and arbitrary linear wave mode"""
        self.write("SIM {}".format(mode))


    def _SPGU_start(self):
        """Starts SPGU output"""
        self.write("SPR")

    def _SPGU_wait(self):
        """ Queries SPGU and blocks until it has finished pulsing"""
        busy = 1
        while busy==1:
            busy = self.query("SPST?")

    def _set_adc_global(
        self,
        adc_modes=[], # list of (adctype,admode) tuples, maximum 3, see enums.py
        highspeed_adc_number=None,
     highspeed_adc_mode=None):
        """ Set the configration for the different ADC types, switching between
        manual and auto modes for all ADCs and specifying samples/integration time
        for the highspeed ADC"""
        if adc_modes:
            return [self.write(format_command("AIT",adctype,adcmode)) for adctype,adcmode in adc_modes]
        else:
            if highspeed_adc_number is None or highspeed_adc_mode is None:
                raise ValueError(
                    "Either give complete adc mapping or specify highspeed ADC")
            return self.write(
                "AV {}, {}".format(
                    highspeed_adc_number,
                    highspeed_adc_mode))

    def _set_format(self, format, output_mode):
        """ Specifies output mode and format to use for testing. Check
        Formats enum for more details"""
        self.write("FMT {},{}".format(format, output_mode))

    def _check_modules(self, mainframe=False):
        """ Queries for installed modules and optionally mainframes connected"""
        if mainframe:
            return self.query("UNT? 1")
        else:
            return self.query("UNT? 0")


    def _reset(self):
        """ Reset Tester"""
        query = "*RST"
        return self.write(query)


    def _check_err(self, all=False):
        """ check for single error, or all errors in stack"""
        query = "ERRX?"
        ret = self.query(query)
        if all:
            results = []
            while ret[:2]!='+0':
                exception_logger.warn(ret)
                results.append(ret)
                ret = self.query(query)
            return results
        if ret[:2]!='+0':
            exception_logger.warn(ret)
        return ret

    def _zero_channel(self, channel):
        """ Force Channel voltage to zero, saving previous parameters"""
        self.write("DZ {}".format(channel))

    def _close_channel(self, channel):
        """ Disconnect channel"""
        self.write("CL {}".format(channel))

    def __channel_to_slot(self, channel):
        """ Converts a subchannel to its slot, in order to access the stored
        available Ranges"""
        if not channel in self.sub_channels:
            raise ValueError("Invalid Channel value")
        return self.slots_installed[int(str(channel)[0])]

    def _teardown_channel(self, channel):
        """ Force Channel to zero and then disconnect """
        if channel.number not in self.sub_channels:
            exception_logger.warn("No channel {} installed, only have \n{}\n, proceeding with teardown but call check_err and verify your setup".format(channel, self.sub_channels))
            self._zero_channel(channel.number)
            self._close_channel(channel.number)

    def _set_DIO_control(self, mode, state):
        ret = self.write("ERMOD {},{}".format(mode, state))
        return ret

    def _check_DIO_control(self):
        ret = self.query("ERMOD?")
        return ret
    # methods only used in discovery,intended to be used only by via public calls,
    # not directly
    def __discover_slots(self):
        """ Queries installed modules, then checks their type and their available ranges"""
        slots = {}
        ret = self._check_modules()
        for i,x in enumerate(ret.strip().split(";")):
            if x!="0,0":
                slots[i+1]={"type":x.split(",")[0],"revision":x.split(",")[1]}
        for k in slots.keys():
            if slots[k]:
                exception_logger.info("Checking Ranges for Slot {}".format(k))
                slots[k]["InputRanges"]=availableInputRanges(slots[k]["type"])
                #slots[k]["MeasureRanges"]=availableMeasureRanges(slots[k]["type"])
        return slots

    def __discover_channels(self, slots):
        channels= []
        for i in slots.keys():
            try:
                ret = self.check_settings(i)
                channels.extend([int(x.replace("CL","")) for x in ret.strip().split(";")])
            except visa.VisaIOError as e:
                self._check_err()
                exception_logger.warn("Caught exception\n {} \n as part of discovery prodecure, assuming no module in slot {}".format(e,i))
        exception_logger.info("Found the folliwing channels\n{}".format(channels))
        return tuple(channels)

    def __read_sweep(self, channels):
        for c in channels:
            if isinstance(c.measurement,StaircaseSweep):
                results = []
                for i in range(test_tuple.measurement.steps):
                    ret = self._device.read()
                    results.append(ret)
                return results

    def _check_module_operation(self, explain=False):
        ret = self.query("LOP?")
        if explain:
            raise NotImplementedError("Explanation functionality\
to annotate error codes will come in a future release")
        return ret

    def __parse_output(self, format, output):
        try:
            terminator = getTerminator(format)
            lines = [x for x in output.split(terminator) if x]
            if hasHeader(format):
                header, lines = splitHeader(lines,terminator)
                dtypes = {"names": header,"formats": [np.float]*len(header)}
                return np.array(lines, dtype=dyptes)
            else:
                return np.array(lines,dtype=np.float)
        except Exception as e:
            exception_logger.warn(e)
            return output
