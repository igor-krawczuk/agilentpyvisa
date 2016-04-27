# vim: set fileencoding: utf-8 -*-
# -*- coding: utf-8 -*-
import visa
from itertools import cycle, starmap, compress
import pandas as pd
import numpy as np
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
                          )
from .setup import *
from .helpers import *
from .SMUs import *
from .dummy import DummyTester
from .loggers import exception_logger,write_logger, query_logger




class B1500():
    def __init__(self, tester, auto_init=True, default_check_err=True):
        self.__test_addr = tester
        self._device=None
        self.tests = OrderedDict()
        self.__last_channel_setups={}
        self.__last_channel_measurements={}
        self.slots_installed={}
        self._DIO_control_mode={}
        self.sub_channels = []
        self.__filter_all = None
        self.__ADC={}
        self.__TSC = None
        self.__channels={}
        self._recording = False
        self.__HIGHSPEED_ADC={"number":None,"mode":None}
        self.default_check_err=default_check_err
        self.programs={}
        self.__format = None
        self.__outputMode = None
        self.last_program=None
        self.__no_store=("*RST","DIAG?","*TST?","CA","AB","RCV","WZ?","ST","END",
                         "SCR","VAR","LST?","CORRSER?","SER?","SIM?","SPM?",
                         "SPPER?","ERMOD?","ERSSP?","ERRX?","ERR?","EMG?",
                         "*LRN?","*OPC?","UNT?","WNU?","*SRE?","*STB?",)
        if auto_init:
            self.init()

    def close(self):
        if self._device:
            self._device.close()
            self.__rm.close()
            self.__rm=None
            self._device=None
            self.__keep_open = False

    def __del__(self):
        self.close()

    def init(self):
        """ Resets the connected tester, then checks all installed modules,
        querying their types and the available subchannels. It also
        stores the available input and measure_ranges in the slots_installed dict,
        with the slot number as key. sub channels is a list containing
        all available channels"""
        self.open()
        self._reset()
        self.slots_installed = self.__discover_slots()
        self.sub_channels = []
        for s,mod in self.slots_installed.items():
            self.sub_channels.extend(mod.channels)
        self.__channels = {i:self.slots_installed[self.__channel_to_slot(i)] for i in self.sub_channels}
        self.enable_SMUSPGU()
        self._check_err()
        self.close()

    def open(self, keep_open=False):
        if not self._device:
            try:
                self.__rm = visa.ResourceManager()
                self._device = self.__rm.open_resource(self.__test_addr)
                self.__keep_open =True
            except OSError as e:
                exception_logger.warn("Could not find VISA driver, setting _device to std_out")
                self._device = DummyTester()

    def diagnostics(self, item):
        """ from the manual:
            - before using DiagnosticItem.trigger_IO , connect a BNC cable between the Ext Trig In and
            Out connectors.
            - After executing DiagnosticItem.high_voltage_LED confirm the status of LED. Then enter the AB
            command
            If the LED does not blink, the B1500 must be repaired.
            - Before executing DiagnosticItem.digital_IO, disconnect any cable from the import digital I/O port.
            - Before executing interlock_open or interlock_closed , open and close the
            interlock circuit respectively
            """
        return self.query(format_command("DIAG?", item))

    def query(self, msg, delay=None,check_error=False):
        """ Writes the msg to the Tester, reads output buffer after delay and
        logs both to the query logger.Optionally checks for errors afterwards"""
        query_logger.info(msg)
        retval=[]
        if self._recording and any([x in msg for x in self.__no_store]):
            self.programs[self.last_program]["config_nostore"].append(msg)
            exception_logger.warn("Skipped query '{}' since not allowed while recording".format(msg))
        else:
            self.open()
            retval = self._device.query(msg, delay=delay)
            query_logger.info(str(retval)+"\n")
            err =self._check_err()
            if err[:2]!="+0":
                exception_logger.warn(err)
                exception_logger.warn(msg)
            if  not self.__keep_open:
                self.close()
        return retval

    def write(self, msg, check_error=False):
        """ Writes the msg to the Tester and logs it in the write
        logger.Optionally checks for errors afterwards"""
        write_logger.info(msg)
        if self._recording and any([x in msg for x in self.__no_store]):
            self.programs[self.last_program]["config_nostore"].append(msg)
            exception_logger.warn("Skipped query '{}' since not allowed while recording".format(msg))
        else:
            self.open()
            retval = self._device.write(msg)
        write_logger.info(str(retval)+"\n")
        if check_error or self.default_check_err:
            err =self._check_err()
            if err[:2]!="+0":
                exception_logger.warn(err)
                exception_logger.warn(msg)
            if  not self.__keep_open:
                self.close()
        return retval

    def read(self, check_error=False, lines=1):
        """ Reads out the current output buffer and logs it to the query logger
        optionally checking for errors"""
        retval=None
        self.open()
        if "ascii" in repr(self.__format):
            retval = self._device.read()
        elif "binary4" in reps(self.__format):
            retval = self._device.read_raw()
        elif "binary8" in reps(self.__format):
            retval = self._device.read_raw()
        else:
            raise ValueError("Unkown format {0}".format(self.__format))
        if lines>1:
            retval=[retval]
            for i in range(1,lines):
                try:
                    if "ascii" in repr(self.__format):
                        retval = self._device.read()
                    elif "binary4" in reps(self.__format):
                        retval = self._device.read_raw()
                    elif "binary8" in reps(self.__format):
                        retval = self._device.read_raw()
                    else:
                        raise ValueError("Unkown format {0}".format(self.__format))
                except Exception as e:
                    exception_logger.warn("Read error after {} lines".format(i))
                    raise e
                finally:
                    query_logger.info(str(retval)+"\n")
                    if check_error:
                        exception_logger.info(self._check_err())
                    return retval
        query_logger.info(str(retval)+"\n")
        if check_error:
            exception_logger.info(self._check_err())
        if  not self.__keep_open:
            self.close()
        return retval

    def measure(self, test_tuple, force_wait=False, autoread=False):
        """ Checks the channels defined in the test tuple and performs the
        measurement the Setup represents. Only one type of measurement is possible,
        otherwise it raises an exception."""
        channels = test_tuple.channels
        exc = None
        data = None
        num_meas = len([c for c in channels if c.measurement])
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
        spgu_channels = [x.number for x in channels if x.spgu]
        SPGU =any(spgu_channels)
        search = any([x.binarysearch or x.linearsearch for x in channels])
        if [XE_measurement, SPGU,search].count(True)>1:
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
                    data = self._read_sweep(channels)
                elif isSpot(channels):
                    data = self._read_spot()
        # SPGU measurements
        elif SPGU:
            for x in spgu_channels:
                self.__channels[x].start_pulses()
            if force_wait:
                self._SPGU_wait()
        elif search:
            self.write("XE")
        parsed_data = self.__parse_output(test_tuple.format, data, num_meas, self.__TSC) if data else data
        return (exc,parsed_data)

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

    def DC_Sweep_I(self, input_channel, ground_channel, start,
        stop, step, compliance, input_range=None, sweepmode=SweepMode.linear_up_down,
        power_comp=None, measure_range=MeasureRanges_I.full_auto):
        """ Performs a quick Voltage staircase sweep measurement on the specified channels """
        return self._DC_Sweep(Targets.I, input_channel, ground_channel, start,
        stop, step, compliance, input_range, sweepmode,
        power_comp, measure_range)


        """ Performs a quick Current staircase sweep measurement on the specified channels """
        return self._DC_Sweep(Targets.I, input_channel, ground_channel, start,
        stop, step, compliance, input_range, sweepmode,
        power_comp, measure_range)

    def Pulsed_Spot_I(self, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        """ Performs a quick PulsedSpot Current measurement the specified channels """
        return self._Pulsed_Spot(Targets.I, input_channel, ground_channel, base, pulse, width,compliance,measure_range, hold )

    def Pulsed_Spot_V(self, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        """ Performs a quick PulsedSpot Voltage measurement the specified channels """
        return self._Pulsed_Spot(Targets.V, input_channel, ground_channel, base, pulse, width,compliance,measure_range, hold )

    def DC_Spot_I(self, input_channel, ground_channel, input_value,
            compliance, input_range=InputRanges_I.full_auto, power_comp=None,
            measure_range=MeasureRanges_V.full_auto):
        """ Performs a quick Spot Current measurement the specified channels """
        return self._DC_spot(Targets.I, input_channel, ground_channel, input_value,
            compliance, input_range, power_comp,
            measure_range)

    def DC_Spot_V(self, input_channel, ground_channel, input_value,
            compliance, input_range = InputRanges_V.full_auto, power_comp=None,
            measure_range=MeasureRanges_I.full_auto):
        """ Performs a quick Spot Voltage measurement the specified channels """
        return self._DC_spot(Targets.V, input_channel, ground_channel, input_value,
            compliance, input_range, power_comp,
            measure_range)

    def run_test(self, test_tuple, force_wait=False, auto_read=False, default_errcheck=None, force_new_setup=False):
        """ Takes in a test tuple specifying channel setups and global parameters,
        setups up parameters, channels and measurements accordingly and then performs the specified test,
        returning gathered data if auto_read was specified. Allways
        cleans up any opened channels after being run (forces zero and disconnect)"""
        self.open(keep_open=True)
        old_default=self.default_check_err
        if default_errcheck is not None:
            self.default_check_err=default_errcheck
        self.set_format(test_tuple.format, test_tuple.output_mode, force_new_setup)
        self.set_filter_all(test_tuple.filter, force_new_setup)
        self._enable_timestamp(True, force_new_setup)
        self._set_adc_global(
            adc_modes=test_tuple.adc_modes,
            highspeed_adc_number=test_tuple.highspeed_adc_number,
            highspeed_adc_mode=test_tuple.highspeed_adc_mode, force_new_setup=force_new_setup)
        try:
            measurechannels = [c for c in test_tuple.channels if c.measurement]
            measurements = [c.measurement for c in measurechannels]
            if len(set([m.mode for m in measurements]))>1:
                raise ValueError("Only 1 type of measurements allowed per setup, have {}".format(set(measurements)))
            if len(measurements)>1:
                if all([m.mode in (MeasureModes.spot, MeasureModes.staircase_sweep, MeasureModes.CV_sweep_dc_bias,MeasureModes.sampling) for m in measurements]):
                    self.set_parallel_measurements(True)
                    self.set_measure_mode(measurements[0].mode,*[c.number for c in measurechannels])
                else:
                    raise ValueError("Parallel measurement only supported with spot,staircasesweep,sampling and CV-DC Bias sweep. For others, use the dedicated multichannel measurements")
            elif len(measurements)==1 and measurements[0].mode not in (MeasureModes.binary_search, MeasureModes.linear_search):
                self.set_measure_mode(measurements[0].mode, measurechannels[0].number)

            if any([x.spgu for x in test_tuple.channels]):
                if not test_tuple.spgu_selector_setup:
                    raise ValueError("If you want to use the spgu, you need to configure the SMUSPGU selector. seth the Testsetup.selector_setup with a list of (port,state) tuples")
                self.enable_SMUSPGU()
                for p,s in test_tuple.spgu_selector_setup:
                    self.set_SMUSPGU_selector(p, s)
            for channel in test_tuple.channels:
                self.setup_channel(channel, force_new_setup)
                if channel.measurement:
                    self._setup_measurement(channel.number, channel.measurement, force_new_setup)
                # resets timestamp, executes and optionally waits for answer,
                # returns data with elapsed
            ret = self.measure(test_tuple, force_wait,auto_read)
        finally:
            if len(measurements)>1:
                self.set_parallel_measurements(False)
            for channel in test_tuple.channels:
                self._teardown_channel(channel)
            if test_tuple.spgu_selector_setup:
                for p,s in test_tuple.spgu_selector_setup:
                    self.set_SMUSPGU_selector(p, SMU_SPGU_state.open_relay)
            self.default_check_err=old_default
            self.close()
        return ret

    def _Pulsed_Spot(self, target, input_channel, ground_channel, base, pulse, width,compliance,input_range=None,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        if target == Targets.V:
            input = Inputs.I
        else:
            input = Inputs.V
        if input_range is None:
            if input == Inputs.I:
                input_range = self.__channels[input_channel].get_mincover_I(base, pulse)
            else:
                input_range = self.__channels[input_channel].get_mincover_V(base, pulse)
        if measure_range is None:
            if target == Inputs.I:
                measure_range = self.__channels[input_channel].get_mincover_I(compliance)
            else:
                measure_range = self.__channels[input_channel].get_mincover_V(compliance)

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
                input_range = self.__channels[input_channel].get_mincover_I(start,stop)
            else:
                input_range = self.__channels[input_channel].get_mincover_V(start,stop)
        if measure_range is None:
            if target == Inputs.I:
                measure_range = self.__channels[input_channel].get_mincover_I(compliance)
            else:
                measure_range = self.__channels[input_channel].get_mincover_V(compliance)
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
                input_range = self.__channels[input_channel].get_mincover_I(input_value)
            else:
                input_range = self.__channels[input_channel].get_mincover_V(input_value)
        if measure_range is None:
            if target == Inputs.I:
                measure_range = self.__channels[input_channel].get_mincover_I(compliance)
            else:
                measure_range = self.__channels[input_channel].get_mincover_V(compliance)

        measure = MeasureSpot(target=target, range=measure_range)
        measure_channel = Channel(number=input_channel,
                          dcforce=DCForce(input=input,
                                           value=input_value,
                                           compliance=compliance,
                                           input_range=input_range,
                                           ),
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

    def _enable_timestamp(self, state, force_new_setup=False):
        """ Enable Timestamp during measurements"""
        if self.__TSC==state and not force_new_setup:
            exception_logger.info("No change for timestamp, not sending")
        else:
            self.__TSC=state
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
        self.__channels[channel_number].restore(channel_number)

    def check_module_operation(self, explain=False):
        ret = self.query("LOP?")
        if explain:
            raise NotImplementedError("Explanation functionality\
to annotate error codes will come in a future release")
        return ret

    def set_parallel_measurements(self, state):
        if state:
            self.write("PAD 1")
        else:
            self.write("PAD 0")



    def set_SMUSPGU_selector(self, port, status):
        """ After being enabled as explained in __set_DIO_control_mode,
        applys SMU_SPGU_state to the SMU_SPGU_port (see enums.py)"""
        if not self._DIO_control_mode.get(DIO_ControlModes.SMU_PGU_Selector_16440A)==DIO_ControlState.enabled:
            raise ValueError("First execute self.enable_SMUSPGU")
        return self.write("ERSSP {},{}".format(port, status))

    def check_SMUSPGU_selector(self, port):
        """ After being enabled as explained in __set_DIO_control_mode,
        queries the specified SMU_SPGU_port for its state"""
        if not self._DIO_control_mode.get(DIO_ControlModes.SMU_PGU_Selector_16440A):
            raise ValueError("First execute self.enable_SMUSPGU")
        return self.query("ERSSP? {}".format(port))

    def enable_SMUSPGU(self):
        """ Shorthand for activating spgu control"""
        self.__set_DIO_control_mode(DIO_ControlModes.SMU_PGU_Selector_16440A)
        self._DIO_control_mode[DIO_ControlModes.SMU_PGU_Selector_16440A]=True

    def __set_DIO_control_mode(self, mode, state=DIO_ControlState.enabled):
        """ Sets the control mode of the tester. In order to control the SMU/PGU
        Controller via ERSSP or the set_SMU_SPGU_selector first this function needs to
        be executed with mode=DIO_ControlModes.SMU_PGU_Selector_16440A, state=DIO_ControlState.enabled
        There is no need stated in the documentation to ever deactive control modes, so the default is
        "enable"
        """
        if state==DIO_ControlState.enabled:
            state=None
            #HACK the tester complains about "incorrect terminator positi
            #on with the mode argument, default is enabling so use the format_command
        ret = self.write(format_command("ERMOD",mode, state))
        for k,v in DIO_ControlModes.__members__.items():
            if ret==mode:
                self._DIO_control_mode[mode]=state
        return ret

    def _check_DIO_control_mode(self):
        """  Returns the state of  control modes, as a some of the activated value.
        the values are :
            0 General Purpose control mode(always active)
            1 16440A SMUSPGU
            2 N1258A/N1259A
            4 N1265A
            8 N1266A
            16 N1268A
            e.g. 16440A and N1268A active=> output is 17
        """
        ret = int(self.query("ERMOD?").strip())
        for k,v in DIO_ControlModes.__members__.items():
            if ret==v:
                return v
        return ret

    def setup_channel(self, channel, force_new_setup=False):
        """ Configures channel with any parameters which can be set before
        the acutal measurement or without any measurement at all"""
        unit = self.__channels[channel.number]
        unit.connect(channel.number)
        if  not self.__last_channel_setups.get(unit)==channel or force_new_setup:
            self.__last_channel_setups[unit]=channel
            if not channel.spgu:
                unit.set_series_resistance(channel.series_resistance,channel.number)
                unit.set_selected_ADC(channel.number, channel.channel_adc)
            if channel.dcforce is not None:
                unit.setup_dc_force(channel.number, channel.dcforce)
            elif channel.staircase_sweep is not None:
                unit.setup_staircase_sweep(channel.number, channel.staircase_sweep)
            elif channel.pulsed_sweep is not None:
                unit.setup_pulsed_sweep(channel.number, channel.pulsed_sweep)
            elif channel.pulsed_spot is not None:
                unit.setup_pulsed_spot(channel.number, channel.pulsed_spot)
            elif channel.quasipulse is not None:
                raise NotImplementedError("Quasipulse measurements not yet implemented")
            elif channel.highspeed_spot is not None:
                raise NotImplementedError("HighSpeedSpot measurements not yet implemented")
            elif channel.spgu is not None:
                unit.setup_spgu(channel.number, channel.spgu)
            elif channel.binarysearch is not None:
                unit.setup_binarysearch_force(channel.binarysearch,channel=channel.number)
            elif channel.linearsearch is not None:
                unit.setup_linearsearch_force(channel.linearsearch,channel=channel.number)
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
        else:
            exception_logger.warn("Channel configuration for channel {} has not changed, skiping setup".format(channel.number))
    def set_measure_mode(self,mode,*channels):
        """ Defines which measurement to perform on the channel. Not used for all measurements,
        check enums.py  or MeasureModes for a full list of measurements. Not in SMUs because for parallel measurements, need to set all channels at once"""
        self.write(format_command("MM",mode,*channels))

    def _setup_measurement(self,channel_number, measurement, force_new_setup=False):
        """ Sets up all parameters containing to the measurement. This is a
        dispatcher function, since a lot fo measurements have overlapping setup.
        Parameters Concerning the channel setup are handled in the respective
        setup_X functions, this function and its callees are only concerned with
        the measurements themselves."""
        if  not self.__last_channel_measurements.get(channel_number)==measurement or force_new_setup:
            self.__last_channel_measurements[channel_number]=measurement
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
                self.__channels[channel_number]._setup_xe_measure(measurement,channel=channel_number )
            elif measurement.mode in [
                MeasureModes.spot_C,
                MeasureModes.pulsed_spot_C,
                MeasureModes.pulsed_sweep_CV,
                MeasureModes.sweep_Cf,
                MeasureModes.sweep_CV_ac_level,
                MeasureModes.sampling_Ct,
            ]:
                raise NotImplemented("CapacitanceMeasurement not yet implemented")
            elif measurement.mode == MeasureModes.quasi_static_cv:
                raise NotImplemented("QuasistatiCV measurement not yet implemented")
            elif measurement.mode ==MeasureModes.binary_search:
                self.__channels[channel_number].setup_binarysearch_measure(measurement,channel=channel_number )
            elif measurement.mode==MeasureModes.linear_search:
                self.__channels[channel_number].setup_linearsearch_measure(measurement,channel=channel_number )
            else:
                raise ValueError("Unknown Measuremode")

    def clear_buffer(self):
        return self.write("BC")

    def set_filter_all(self, filter_state, force_new_setup=False):
        """ Sets the spike and overshoot filter on the SMU output."""
        if self.__filter_all==filter_state and not force_new_setup:
            exception_logger.info("No change in filter, not sending command")
        else:
            self.__filter_all=filter_state
            return self.write("FL {}".format(filter_state))
    # individual commands (grouped only for input/target types, i.e. V/I


    def _set_adc_global(
        self,
        adc_modes=[], # list of (adctype,admode) tuples, maximum 3, see enums.py
        highspeed_adc_number=None,
     highspeed_adc_mode=None, force_new_setup=False):
        """ Set the configration for the different ADC types, switching between
        manual and auto modes for all ADCs and specifying samples/integration time
        for the highspeed ADC"""
        if adc_modes:
            return [self.set_adc(adctype, adcmode,force_new_setup) for adctype,adcmode in adc_modes]
        else:
            if highspeed_adc_number is None or highspeed_adc_mode is None:
                raise ValueError(
                    "Either give complete adc mapping or specify highspeed ADC")
            self.set_highspeed_ADC(highspeed_adc_number, highspeed_adc_mode,force_new_setup)

    def set_adc(self, adc, mode, force_new_setup=False):
        """ Set the configration for the different ADC types, switching between
        manual and auto modes for all ADC
        """
        if not self.__ADC.get(adc)==mode or force_new_setup:
            self.__ADC[adc]=mode
            self.write(format_command("AIT",adc,mode))
        else:
            exception_logger.info("No change for adc {}, not sending AIT".format(adc))

    def set_highspeed_ADC(self, number, mode, force_new_setup=False):
        if (not (self.__HIGHSPEED_ADC["number"]== number and self.__HIGHSPEED_ADC["mode"]==mode)) or force_new_setup:
            return self.write(
                "AV {}, {}".format(
                    number,
                    mode))
        else:
            exception_logger.info("AV parameters not changed, no write")

    def set_format(self, format, output_mode, force_new_setup=False):
        """ Specifies output mode and format to use for testing. Check
        Formats enum for more details"""
        if not (self.__format == format and self.__outputMode == output_mode) or force_new_setup :
            self.__format = format
            self.__outputMode = output_mode
            self.write("FMT {},{}".format(format, output_mode))
        else:
            exception_logger.info("FMT parameters not changed, no write")

    def _check_modules(self, mainframe=False):
        """ Queries for installed modules and optionally mainframes connected"""
        if mainframe:
            return self.query("UNT? 1")
        else:
            return self.query("UNT? 0")
    def record_program(self,program_name):
        if self._recording:
            raise ValueError("Already recording")
        id = self.programs[self.last_program]["id"]+1 if self.last_program else 1
        self.write("ST {}".format(id))
        self._recording = True
        self.programs[program_name]={}
        self.programs[program_name]["index"]= id
        self.programs[program_name]["steps"]=[]
        self.programs[program_name]["config_nostore"]=[]
        self.last_program=program_name
    def stop_recording(self):
        self._recording = False
        exception_logger.info("Recorded program {} with index {} and the following steps".format(self.last_program,self.programs[self.last_program]["index"]))
        exception_logger.info("\n".join(self.programs[self.last_program]["steps"]))
        exception_logger.info("as well as the following captured steps(check these manually before exeting the program, or execute the self.nostore_execute if you are sure all them are idempotent")
        exception_logger.info("\n".join(self.programs[self.last_program]["config_nostore"]))

    def run_prog(self, program_name):
        if self._recording:
            raise ValueError("still recording")
        self.write("DO {}".format(self.programs[program_name]["index"]))

    def run_progs_by_ids(self, *ids):
        """ Runs the specified programs, in order of the ids given"""
        if self._recording:
            raise ValueError("still recording")
        if any([not i in [x["index"] for x in self.programs]]):
            raise ValueError("One of your specified ids not in the buffer")
        if len(ids)>8:
            raise ValueError("You can only specify 8 programs at once")
        self.write(format_command("DO",*ids))


    def _reset(self):
        """ Reset Tester"""
        query = "*RST"
        return self.write(query)

    def _check_err(self, all=False):
        """ check for single error, or all errors in stack"""
        query = "ERRX?"
        if not self._recording:
            ret = self._device.query(query)
            if all:
                results = []
                while ret[:2]!='+0':
                    exception_logger.warn(ret)
                    results.append(ret)
                    ret = self._device.query(query)
                return results
            if ret[:2]!='+0':
                exception_logger.warn(ret)
            return ret
        else:
            exception.warn("Skipped query \"{}\" since it is not allowed while recording".format(query))

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
        return self.slots_installed[int(str(channel)[0])].slot

    def _teardown_channel(self, channel):
        """ Force Channel to zero and then disconnect """
        if channel.number not in self.sub_channels:
            exception_logger.warn("No channel {} installed, only have \n{}\n, proceeding with teardown but call check_err and verify your setup".format(channel, self.sub_channels))
        self._zero_channel(channel.number)
        self._close_channel(channel.number)

    # methods only used in discovery,intended to be used only by via public calls,
    # not directly

    def __discover_slots(self):
        """ Queries installed modules, then checks their type and their available ranges"""
        slots = {}
        ret = self._check_modules()
        for i,x in enumerate(ret.strip().split(";")):
            if x!="0,0":
                slots[i+1]=self.__getModule(x.split(",")[0], i+1)
        return slots

    def _read_spot(self):
        for i in range(10):  # retry 10 times when failing
            try:
                ret = self.read()
            except Exception:
                continue
            return ret

    def _read_sweep(self, channels):
        self.query("NUB?")
        return self.read()

    def __parse_output(self, test_format, output, num_measurements, timestamp):
        try:
            if test_format in (Format.binary4, Format.binary4_crl):
                return parse_binary4(output)
            elif test_format in (Format.binary8, Format.binary8,):
                return parse_binary8(output)
            else:
                frame,series_dict= parse_ascii_default_dict(test_format, output)
                return (frame,series_dict,output)
                #return parse_ascii(test_format, output ,num_measurements, timestamp, self.__outputMode)
        except Exception as e:
            exception_logger.warn(e)
            return output

    def __getModule(self,model, slot):
        """ Returns tuples of the available OutputRanging used for input_range settings, based on the model. Based on Pages 4-22 and 4-16 of B1500 manual"""
        if model =="B1510A":  # HPSMU High power source/monitor unit
            return HPSMU(self, slot)
        if model in ("B1511A","B1511B"):  # MPSMU Medium power source/monitor unit
            return MPSMU(self, slot)
        if model =="B1512A":  # HCSMU High current source/monitor unit
            return HCSMU(self, slot)
        if model in ("B1513A", "B1513B"):  # HVSMU High voltage source/monitor unit
            return HVSMU(self, slot)
        if model =="B1514A":  # MCSMU Medium current source/monitor unit
            return MCSMU(self, slot)
        if model =="B1517A":  # HRSMU High resolution source/monitor unit
            return HRSMU(self, slot)
        if model =="B1520A":  # MFCMU  CMU Multi frequency capacitance measurement unit
            return MFCFMU(self, slot)
        elif model =="B1525A":  # HVSPGU SPGU High voltage semiconductor pulse generator unit
            return HVSPGU(self, slot)
        else:
            exception_logger.warn("We don't know this model {0} in slot {1}, thus we don't support it".format(model, slot))
