# vim: set fileencoding: utf-8 -*-
# -*- coding: utf-8 -*-
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
from .helpers import minCover_I, minCover_V
from logging import getLogger
query_logger = getLogger(__name__+":query")
write_logger = getLogger(__name__+":write")
exception_logger = getLogger(__name__+":write")

def availableInputRanges(model):
    """ Returns tuples of the available OutputRanging used for input_range settings, based on the model. Based on Pages 4-22 and 4-16 of B1500 manual"""
    if model =="B1510A":  # HPSMU High power source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,20,200,400,1000,2000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(11,21)))])
    if model in ("B1511A","B1511B"):  # MPSMU Medium power source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,5,50,200,400,1000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(8,20)))])
    if model =="B1512A":  # HCSMU High current source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,2,200,400,)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0,22]+list(range(15,21)))])
    if model in ("B1513A", "B1513B"):  # HVSMU High voltage source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,2000,5000,15000,30000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(11,20)))])
    if model =="B1514A":  # MCSMU Medium current source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,2,200,400,)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(15,21)))])
    if model =="B1517A":  # HRSMU High resolution source/monitor unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in (0,5,50,200,400,1000)]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in tuple([0]+list(range(8,20)))])
    if model =="B1520A":  # MFCMU or CMU Multi frequency capacitance measurement unit
        raise NotImplementedError("This device is not yet supported")
    elif model =="B1525A":  # HVSPGU or SPGU High voltage semiconductor pulse generator unit
        return tuple([InputRanges_V[x] for  x in InputRanges_V.__members__ if InputRanges_V[x].value in ()]+
                     [InputRanges_I[x] for  x in InputRanges_I.__members__ if InputRanges_I[x].value in ()])
    else:
        raise NotImplementedError("This device is not yet supported")

def availableMeasureRanges(model):
    raise NotImplementedError("This device is not yet supported")

class B1500():
    def __init__(self, tester):
        self.__rm = visa.ResourceManager()
        self._device = self. __rm.open_resource(tester)
        self.tests = OrderedDict()
        self.slots_installed={}
        self.sub_channels = []

    def init(self):
        self.reset()
        self.slots_installed = self._discover_slots()
        self.sub_channels = self._discover_channels()
        self.check_err()

    def _discover_slots(self):
        slots = {}
        ret = self.check_modules()
        for i,x in enumerate(ret.strip().split(";")):
            if x!="0,0":
                slots[i+1]={"type":x.split(",")[0],"revision":x.split(",")[1]}
            else:
                slots[i+1]=None
        for k in slots.keys():
            if slots[k]:
                slots[k]["InputRanges"]=availableInputRanges(slots[k]["type"])
                #slots[k]["MeasureRanges"]=availableMeasureRanges(slots[k]["type"])
        return slots


    def check_modules(self, mainframe=False):
        if mainframe:
            return self.query("UNT? 1")
        else:
            return self.query("UNT? 0")

    def _discover_channels(self):
        channels= []
        for i in range(10):
            try:
                ret = self.check_settings(ParameterSettings.StatusSlot1+i)
            except VisaIOError as e:
                exception_logger.debug("Caught exception\n {} \n as part of discovery prodecure, assuming no module in slot {}".format(e,i))
            channels.extend([int(x.replace("CL","")) for x in ret.strip().split(";")])
        exception_logger.info("Found the folliwing channels\n{}".format(channels))
        return tuple(channels)

    def reset(self):
        query = "*RST"
        return self.write(query)


    def check_err(self):
        query = "ERRX?"
        return self.query(query)

    def query(self, msg, check_error=False):
        query_logger.info(msg)
        retval = self._device.query(msg)
        query_logger.info(str(retval)+"\n")
        if check_error:
            self.check_err()
        return retval

    def write(self, msg, check_error=False):
        write_logger.info(msg)
        retval = self._device.write(msg)
        write_logger.info(str(retval)+"\n")
        if check_error:
            self.check_err()
        return retval

    def check_module_operation(self, explain=False):
        ret = self.query("LOP?")
        if explain:
            raise NotImplementedError("Explanation functionality\
to annotate error codes will come in a future release")
        return ret

    def check_settings(self, parameter):
        ret = self.query("*LRN? {}".format(parameter))
        return ret

    def set_DIO_control(self, mode, state):
        ret = self.write("ERMOD {},{}".format(mode, state))
        return ret

    def check_DIO_control(self):
        ret = self.query("ERMOD?")
        return ret



    def operations_completed(self):
        query = "*OPC?"
        return self.query(query)

    def add_test(name, test_tuple):
        self.tests[name] = test_tuple

    def enable_timestamp(self, state):
        if state:
            return self.write("TSC {}".format(1))
        else:
            return self.write("TSC {}".format(0))


    def zero_channel(self, channel_number):
        return self.write("DZ {}".format(channel_number))

    def restore_channel(self, channel_number):
        return self.write("RZ {}".format(channel_number))

    def SPGU_V(self, input_channel, pulse_base, pulse_peak, pulse_width):
        pulse_channel=Channel(number=input_channel, spgu=SPGU(pulse_base, pulse_peak,pulse_width))
        test = TestSetup(channels=[pulse_channel])
        self.run_test(test)

    def DC_sweep_V(self, input_channel, ground_channel, start,
        stop, step, compliance, input_range=None, sweepmode=SweepMode.linear_up_down,
        power_comp=None, measure_range=MeasureRanges_I.full_auto):
        measure_setup = MeasureStaircaseSweep(target=Targets.I,
            side=MeasureSides.current_side,range=measure_range)
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

    def pulsed_spot_V(self, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_I.full_auto, hold=0 ):
        measure_setup = MeasurePulsedSpot(target=Targets.I, side=MeasureSides.current_side,range=measure_range)
        measure_channel = Channel(number=input_channel,pulsed_spot=PulsedSpot(input=Inputs.V,base=base,pulse=pulse,width=width, compliance=compliance,hold=hold),
                                  measurement=measure_setup)
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[measure_channel, ground],)
        return self.run_test(test)

    def pulsed_spot_I(self, input_channel, ground_channel, base, pulse, width,compliance,measure_range=MeasureRanges_V.full_auto, hold=0 ):
        measure_setup = MeasurePulsedSpot(target=Targets.V,
                        side=MeasureSides.voltage_side,
                        range=measure_range)

        measure_channel = Channel(number=input_channel,
                                  pulsed_spot=PulsedSpot(input=Inputs.I,
                                                         base=base,
                                                         pulse=pulse,
                                                         width=width,
                                                         compliance=compliance,
                                                         hold=hold),
                                    measurement=measure_setup
                                  )
        ground_setup = DCForce(
            input=Inputs.I,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[measure_channel, ground],)
        return self.run_test(test)

    def DC_spot_I(self, input_channel, ground_channel, input_value,
            compliance, input_range=InputRanges_I.full_auto, power_comp=None,
            measure_range=MeasureRanges_V.full_auto):
        measure = MeasureSpot(target=Inputs.V,range=measure_range)
        measure_channel = Channel(number=input_channel,
                          dcforce=DCForce(input=Inputs.I,
                                           value=input_value,
                                           compliance=compliance,
                                           input_range=input_range,
                                           power_comp=power_comp))
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[measure_channel, ground],)
        self.run_test(test)

    def DC_spot_V(self, input_channel, ground_channel, input_value,
            compliance, input_range=InputRanges_V.full_auto, power_comp=None,
            measure_range=MeasureRanges_I.full_auto):
        measure = MeasureSpot(target=Inputs.V,range=measure_range)
        measure_channel = Channel(number=input_channel,
                          dcforce=DCForce(input=Inputs.V,
                                           value=input_value,
                                           compliance=compliance,
                                           input_range=input_range,
                                           power_comp=power_comp))
        ground_setup = DCForce(
            input=Inputs.V,
            value=0,
            compliance=compliance)
        ground = Channel(
            number=ground_channel,
            dcforce=ground_setup)
        test = TestSetup(channels=[measure_channel, ground],)
        self.run_test(test)

    def DC_sweep_I(
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
     measure_range=MeasureRanges_I.full_auto):
        measure_setup = MeasureStaircaseSweep(target=Targets.V,
            side=MeasureSides.current_side,
            range=measure_range)
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
        test = TestSetup(channels=[in_channel, ground],)
        return self.run_test(test)

    def run_test(self, test_tuple):
        self.set_format(test_tuple.format, test_tuple.output_mode)
        self.set_filter(test_tuple.filter)
        self.enable_timestamp(True)
        self.set_adc_global(
            adc_modes=test_tuple.adc_modes,
            highspeed_adc_number=test_tuple.highspeed_adc_number,
            highspeed_adc_mode=test_tuple.highspeed_adc_mode)
        try:
            for channel in test_tuple.channels:
                self.setup_channel(channel)
                # resets timestamp, executes and optionally waits for answer,
                # returns data with elapsed
            ret = self.execute(test_tuple)
        finally:
            for channel in test_tuple.channels:
                self.teardown_channel(channel)
        return ret

    def set_filter(self, filter):
        return self.write("FL {}".format(filter))

    def open_channel(self, number):
        if number not in self.sub_channels:
            raise ValueError("Channel {} not available on device, only \n{}\n are available".format(number,self.sub_channels))
        return self.write("CN {}".format(number))  # connect channel
    def set_series_resistance(self, channel, state):
        return self.write(
            "SSR {},{}".format(
                channel,
                state))  # connects or disconnects 1MOhm series

    def set_channel_ADC_type(self, channel, adc):
        return self.write(
            "AAD {},{}".format(
                channel,
                adc))  # sets channel adc type

    def setup_channel(self, channel):
        # connect channel
        self.open_channel(channel.number)
        self.set_series_resistance(channel.number, channel.series_resistance)
        self.set_channel_ADC_type(channel.number, channel.channel_adc)
        if channel.measurement:
            self.setup_measurement(channel.number, channel.measurement)

        if channel.dcforce is not None:
            self.dc_force(channel.number, channel.dcforce)
        elif channel.staircase_sweep is not None:
            self.staircase_sweep(channel.number, channel.staircase_sweep)
        elif channel.pulse_sweep is not None:
            self.pulse_sweep(channel.number, channel.pulse_sweep)
        elif channel.pulsed_spot is not None:
            self.pulsed_spot(channel.number, channel.pulsed_spot)
        elif channel.quasipulse is not None:
            return self.quasi_pulse(channel.number, channel.quasipulse)
        elif channel.highspeed_spot is not None:
            self.highspeed_spot_setup(
                channel.number, channel.highspeed_spot)
        elif channel.spgu is not None:
            self.spgu(channel.number, channel.spgu)
        else:
            raise ValueError(
                "At least one force should be in the channel, maybe you forgot to force ground to 0?")
        return self.check_err()

    def highspeed_spot_setup(self, channel_number, highspeed_setup):
        if highspeed_setup.target == Targets.C:
            pass  # IMP, FC?

    def highspeed_spot(self, channel_number, highspeed_setup):
        if highspeed_setup.target == Targets.I:
            self.write(
                "TTI {},{}".format(
                    channel_number,
                    highspeed_setup.irange))
        elif highspeed_setup.target == Targets.V:
            self.write(
                "TTV {},{}".format(
                    channel_number,
                    highspeed_setup.vrange))
        elif highspeed_setup.target == Targets.IV:
            self.write(
                "TTIV {},{}".format(
                    channel_number,
                    highspeed_setup.irange,
                    highspeed_setup.vrange))
        elif highspeed_setup.target == Targets.C:
            if highspeed_setup.mode == HighSpeedMode.fixed:
                self.write(
                    "TTC {},{},{}".format(
                        channel_number,
                        highspeed_setup.mode,
                        highspeed_setup.Rrange))
            else:
                self.write(
                    "TTC {},{}".format(
                        channel_number,
                        highspeed_setup.mode))

    def setup_measurement(self,channel, measurement):
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
            self.setup_C_measure(channel, measurement, )
        elif measurement.mode == MeasureModes.quasi_static_cv:
            self.setup_quasi_static_cv(measurement.channel, measurement.config)
        elif measurement.mode in [MeasureModes.linear_search, MeasureModes.binary_search]:
            self.setup_search(channel, measurement)
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
            self.write("BSM {}".format(auto_abort))
        else:
            self.write("LSM {}".format(auto_abort))

    def set_search_output(self, mode, data_output):
        if mode == MeasuringModes.binary_search:
            self.write("BSVM {}".format(data_output))
        else:
            self.write("LSVM {}".format(data_output))

    def set_search_timing(self, mode, hold, delay):
        if mode == MeasuringModes.binary_search:
            self.write("BST {}".format(hold, delay))
        else:
            self.write("LSTM {}".format(hold, delay))

    def set_search_monitor(self, mode, channel, search_mode, condition, measure_range, target_value):
        if mode == MeasuringModes.binary_search:
            self.write("BGI {}".format(channel, search_mode, condition, measure_range, target_value))
        else:
            self.write("LGI {}".format(channel, search_mode, condition, measure_range, target_value))

    def set_search_source(self, target, mode, channel, input_range, start, stop, compliance):
        if target == Targets.V:
            if mode == MeasuringModes.binary_search:
                self.write("BSV {}".format(channel, input_range, start, stop, compliance))
            else:
                self.write("LSV {}".format(channel, input_range, start, stop, compliance))
        else:
            if mode == MeasuringModes.binary_search:
                self.write("BSSI {}".format(channel, input_range, start, stop, compliance))
            else:
                self.write("LSSI {}".format(channel, input_range, start, stop, compliance))

    def set_search_synchronous_source(self, target, mode, channel, polarity,offset, compliance):
        if target == Targets.V:
            if mode == MeasuringModes.binary_search:
                self.write("BSSV {}".format(channel, polarity, offset, compliance))
            else:
                self.write("LSSV {}".format(channel, polarity, offset, compliance))
        else:
            if mode == MeasuringModes.binary_search:
                self.write("BSSI {}".format(channel, polarity, offset, compliance))
            else:
                self.write("LSSI {}".format(channel, polarity, offset, compliance))


    def setup_quasi_static_cv(self, channel, config):
        self.set_measure_mode(config.mode, channel)
        self.set_quasi_static_compatibility()
        self.set_quasi_static_leakage()
        self.set_quasi_static_abort()
        self.set_quasi_static_measure_range()
        self.set_quasi_static_timings()
        self.set_quasi_static_source()

    def set_quasi_static_compatibility(self, compat):
        self.write("QSC {}".format(compat))
    def set_quasi_static_leakage(self, output, compensation):
        self.write("QSL {}".format())
    def set_quasi_static_abort(self, abort):
        self.write("QSM {}".format(abort))
    def set_quasi_static_measure_range(self, range):
        self.write("QSR {}".format(range))
    def set_quasi_static_timings(self, C_integration, L_integration, hold, delay,delay1=0,delay2=0):
        self.write("QST {},{},{},{}".format())
    def set_quasi_static_source(self, channel, mode, vrange, start, stop, capacitive_measure_voltage, step, compliance):
        self.write("QSV {}".format())

    def setup_C_measure(self, channel, config):
        self.adjust_paste_compensation(channel, config.auto_compensation, config.compensation_data)
        self.set_C_ADC_samples(self, config.adc_mode, config.ADC_coeff)

    def set_C_ADC_samples(self, mode, coeff=None):
        self.write("ACT {}".format(",".join(["{}".format(x) for x in [adc_mode, coeff] if x])))

    def adjust_phase_compensation(self, channel, auto_compensation, compensation_data):
        self.write("ADJ {},{}".format(channel, config.auto_compensation))
        self.write("ADJ? {},{}".format(channel, config.compensation_data))

    def set_measure_mode(self, mode, channel):
        self.write(
        "MM {}".format(",".join(["{}".format(x) for x in [mode, channel]])))

    def set_measure_side(self, channel, side):
        self.write("CMM {},{}".format(channel, side))

    def set_measure_range(self, channel, target, range):
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


    def measure_single_setup(self, channel, config):
        self.set_measure_mode(config.mode, channel)
        if config.mode not in set([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_side(channel, config.side)
        if config.mode not in set([MeasureModes.sampling, MeasureModes.quasi_pulsed_spot]):
            self.set_measure_range(channel, config.target, config.range)

    def dc_force(self, channel_number, force_setup):
        if force_setup.input_range not in self.slots_installed.get(channel_number)["InputRanges"]:
            exception_logger.warn("Input range of channel not available for installed slot, might cause errors".format(channel_number))
        force_query = ",".join(["{}".format(x) for x in force_setup[1:] if x is not None])
        if force_setup.input == Inputs.V:
            return self.write(
                "DV {},{}".format(
                    channel_number,
                    force_query))
        if force_setup.input == Inputs.I:
            return self.write(
                "DI {},{}".format(
                    channel_number,
                    force_query))

    def staircase_sweep(self, channel_number, sweep_setup):
        self.write(
            "WT {},{}".format(
                sweep_setup.hold,
                sweep_setup.delay))
        self.write("WM {}".format(sweep_setup.auto_abort))
        if sweep_setup.input == Inputs.V:
            return self.write("WV {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -3]
                                               if isinstance(x, IntEnum)])))
        else:
            return self.write("WI {}".format(
                                          ",".join(
                                              ["{}".format(x)
                                               for x in sweep_setup
                                               [1: -3]
                                               if isinstance(x, IntEnum)])))

    def pulse_sweep(self, channel_number, sweep_setup):
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

    def quasi_pulse(self, channel_number, quasi_setup):
        self.write("BDT {},{}".format(
            *["{}".format(x) for x in quasi_setup[-2:]]))
        self.write("BDM {},{}".format(
            *["{}".format(x) for x in quasi_setup[0:2]]))
        self.write("BDV {},{}".format(
            channel_number, *["{}".format(x) for x in quasi_setup[2:6]]))


    def spgu(self, channel_number, spgu_setup):
        self.set_SPGU_wavemode(spgu_setup.wavemode)
        self.set_SPGU_output_mode(spgu_setup.output_mode, spgu_setup.condition)
        self.set_SPGU_pulse_switch(channel_number, spgu_setup.switch_state, spgu_setup.switch_normal, spgu_setup.switch_delay, spgu_setup.switch_width)   #ODSW
        self.set_SPGU_pulse_period(spgu_setup.pulse_period)  # SPPER
        if spgu_setup.wavemode == SPGUModes.Pulse:
            self.set_SPGU_pulse_levels(channel_number, spgu_setup.pulse_level_sources, spgu_setup.pulse_base, spgu_setup.pulse_peak, spgu_setup.pulse_src)  # SPM, SPV, check if pulse_src==source
        else:
            raise NotImplementedError("Arbitrary Linear Wavemode will be added in a later release")
        self.set_SPGU_pulse_timing(channel_number, spgu_setup.timing_source, spgu_setup.pulse_delay, spgu_setup.pulse_width, spgu_setup.pulse_leading, spgu_setup.pulse_trailing,)  # SPT
        self.set_SPGU_apply(channel_number)  # SPUPD
        if spgu_setup.loadZ == SPGUOutputImpedance.full_auto:
            self.set_SPGU_loadimpedance_auto(channel_number)
        else:
            self.set_SPGU_loadimpedance(channel_number, spgu_setup.loadZ)  # SER

    def set_SPGU_apply(self, channel):
        self.write("SPUPD {}".format(channel))

    def set_SPGU_pulse_timing(self, channel, source, delay, width, leading, trailing):
        self.write("SPT {}".format(",".join(["{}".format(x)  for x in [channel, source, delay, width, leading, trailing]])))

    def set_SPGU_pulse_levels(self, channel, level_sources, base, peak, pulse_src):
        self.write("SPM {},{}".format(channel, level_sources))
        self.write("SPV {},{},{},{}".format(channel, pulse_src, base, peak))


    def set_SPGU_loadimpedance(self, channel, loadZ):
            self.write("SER {},{}".format(channel, loadZ))

    def set_SPGU_loadimpedance_auto(self, channel,update_impedance=1, delay=0, interval=5e-6,count=1 ):
            self.write("CORRSER? {},{},{},{},{}".format(channel, update_impedance, delay, interval, count ))
            # execute a single measurement and set the output load

    def set_SPGU_pulse_period(self, pulse_period):
        self.write("SPPER {}".format(pulse_period))

    def set_SPGU_pulse_switch(self, channel, switch_state, switch_normal, switch_delay, width):
        self.write("ODSW {},{},{},{},{}".format(channel, switch_state, switch_normal, switch_delay, width ))

    def set_SPGU_output_mode(self, output_mode, condition):
        self.write("SPRM {}".format(",".join(["{}".format(x) for x in [output_mode, condition] if x])))

    def set_SPGU_wavemode(self, mode):
        self.write("SIM {}".format(mode))
        pass

    def teardown_channel(self, channel):
        if channel.number not in self.sub_channels:
            exception_logger.warn("No channel {} installed, only have \n{}\n, proceeding with teardown but call check_err and verify your setup".format(channel, self.sub_channels))
        # force voltage to 0
        self.write("DZ {}".format(channel.number))
        # disconnect channel
        self.write("CL {}".format(channel.number))

    def set_format(self, format, output_mode):
        self.write("FMT {},{}".format(format, output_mode))

    def execute(self, test_tuple, force_wait=True, autoread=True):
        channels = test_tuple.channels
        # need to figure out a proper interface on how to kick of and read out
        # measurement data
        # propably implement as genrator, as that will allow the switch betweenstreaming
        # and batch query via OPC?
        exc = None
        data = None
        # look at first measurement only, since we can only measure one type of
        # XE, SPGU, .. at once
        if any([c.measurement and c.measurement.mode in(
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
        ) for c in channels]):
            # triggered by XE=> NUB gets all the data
            exc = self.query("XE")
            if force_wait:
                ready = 0
                while ready == 0:
                    ready = self.query("*OPC?")
            if autoread:
                data = self.query("NUB?")
        elif any([x.spgu for x in channels]):
            exc= self.start_SPGU()
        # elif any([isinstance(x.measurement, ) for x in channels]):
        #     pass
        return (exc,data)

    def start_SPGU(self):
        self.write("SPR")
        busy = 1
        while busy==1:
            busy = self.query("SPST?")

    def set_adc_global(
        self,
        adc_modes=[],
        highspeed_adc_number=None,
     highspeed_adc_mode=None):
        if adc_modes:
            [self.write(
                 "AIT {}".format(",".join(["{}".format(x) for x in setting])))
             for setting in adc_modes]
        else:
            if highspeed_adc_number is None or highspeed_adc_mode is None:
                raise ValueError(
                    "Either give complete adc mapping or specify highspeed ADC")
            self.write(
                "AV {}, {}".format(
                    highspeed_adc_number,
                    highspeed_adc_mode))

    def pulsed_spot(self, channel_number, pulse_setup):
        self.write(
            "PT {}, {}, {}".format(pulse_setup.hold , pulse_setup.width, pulse_setup.period))
        if pulse_setup.input == Inputs.V:
            self.write(
                "PV {},{},{},{},{}".format(channel_number, pulse_setup.input_range, pulse_setup.base, pulse_setup.pulse,pulse_setup.compliance))
        else:
            self.write(
                "PI {},{},{},{},{}".format(channel_number, pulse_setup.input_range, pulse_setup.base, pulse_setup.pulse,pulse_setup.compliance))
