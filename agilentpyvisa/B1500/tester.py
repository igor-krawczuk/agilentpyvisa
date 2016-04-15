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
from .SMUs import *


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
        self.__channels={}
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
        self.sub_channels = []
        for s,mod in self.slots_installed.items():
            self.sub_channels.extend(mod.channels)
        self.__channels = {i:self.slots_installed[self.__channel_to_slot(i)] for i in self.sub_channels}
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
        spgu_channels = [x.number for x in channels if x.spgu]
        SPGU =any(spgu_channels)
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
                elif isSpot(channels):
                    data = self.__read_spot()
        # SPGU measurements
        elif SPGU:
            for x in spgu_channels:
                self.__channels[x].start_pulses()
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

    def run_test(self, test_tuple, force_wait=False, auto_read=False):
        """ Takes in a test tuple specifying channel setups and global parameters,
        setups up parameters, channels and measurements accordingly and then performs the specified test,
        returning gathered data if auto_read was specified. Allways
        cleans up any opened channels after being run (forces zero and disconnect)"""
        self.set_format(test_tuple.format, test_tuple.output_mode)
        self.set_filter_all(test_tuple.filter)
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
        self.__channels[channel_number].restore(channel_number)

    def check_module_operation(self, explain=False):
        ret = self.query("LOP?")
        if explain:
            raise NotImplementedError("Explanation functionality\
to annotate error codes will come in a future release")
        return ret

    def _set_DIO_control_mode(self, mode, state):
        """ Sets the control mode of the tester. In order to control the SMU/PGU
        Controller via ERSSP or the set_SMU_SPGU_selector first this function needs to
        be executed with mode=DIO_ControlModes.SMU_PGU_Selector_16440A, state=DIO_ControlState.enabled
        """
        ret = self.write("ERMOD {},{}".format(mode, state))
        return ret
    def _set_SMU_SPGU_selector(self, port, status):
        """ After being enabled as explained in _set_DIO_control_mode,
        applys SMU_SPGU_state to the SMU_SPGU_port (see enums.py)"""
        return self.write("ERSSP {},{}".format(port, status))

    def _check_SMU_SPGU_selector(self, port):
        """ After being enabled as explained in _set_DIO_control_mode,
        queries the specified SMU_SPGU_port for its state"""
        return self.query("ERSSP? {}".format(port))

    def _check_DIO_control_mode(self):
        ret = self.query("ERMOD?")
        return ret

    def setup_channel(self, channel):
        """ Configures channel with any parameters which can be set before
        the acutal measurement or without any measurement at all"""
        unit = self.__channels[channel.number]
        unit.connect(channel.number)
        unit.set_series_resistance(channel.series_resistance,channel.number)
        unit.set_selected_ADC(channel.number, channel.channel_adc)
        if channel.measurement:
            self._setup_measurement(channel.number, channel.measurement)
        if channel.dcforce is not None:
            unit.setup_dc_force(channel.number, channel.dcforce)
        elif channel.staircase_sweep is not None:
            unit.setup_staircase_sweep(channel.number, channel.staircase_sweep)
        elif channel.pulse_sweep is not None:
            unit.setup_pulse_sweep(channel.number, channel.pulse_sweep)
        elif channel.pulsed_spot is not None:
            unit.setup_pulsed_spot(channel.number, channel.pulsed_spot)
        elif channel.quasipulse is not None:
            raise NotImplementedError("Quasipulse measurements not yet implemented")
        elif channel.highspeed_spot is not None:
            raise NotImplementedError("HighSpeedSpot measurements not yet implemented")
        elif channel.spgu is not None:
            unit.setup_spgu(channel.number, channel.spgu)
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
            self.__channels[channel]._setup_xe_measure(channel, measurement)
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

    def set_filter_all(self, filter):
        """ Sets the spike and overshoot filter on the SMU output."""
        return self.write("FL {}".format(filter))
    # individual commands (grouped only for input/target types, i.e. V/I


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

    def set_format(self, format, output_mode):
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

    def __read_spot(self):
        for i in range(10):  # retry 10 times when failing
            try:
                ret = self._device.read()
            except Exception:
                continue
            return ret

    def __read_sweep(self, channels):
        for c in channels:
            if isinstance(c.measurement,StaircaseSweep):
                results = []
                for i in range(test_tuple.measurement.steps):
                    for i in range(10):  # retry 10 times when failing
                        try:
                            ret = self._device.read()
                        except Exception:
                            continue
                        break
                    results.append(ret)
                return results

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
