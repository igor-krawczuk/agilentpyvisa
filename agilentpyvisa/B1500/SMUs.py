from logging import getLogger
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *
from .force import *
from .helpers import format_command
import visa
from .SMU_capabilities import *


class SMU(object):

    def __init__(self, parent_device, slot):
        self.parent = parent_device
        self.slot = slot
        self.channels = self.__discover_channels()
        self.connected = False
        self.source_output_filter = False
        self.channel_setups = {}  # dict with channel number as id
        self.measurements = {}  # dict with channel number as id
        self.name = self.__class__.__name__

    def set_selected_ADC(self, channel, adc):
        """ Selects which ADC to use for the specified channe. Available are
        highspeed = 0
        highresolution = 1
        highspeed_pulse =2
        Default is highspeed
        """
        return self.parent.write(
            "AAD {},{}".format(
                channel,
                adc))  # sets channel adc type

    def get_mincover_V(self,  val1, val2=None, fixed=False):
        """ This returns the smallest voltage range covering the largest given
        values. Only returns auto or limited, in order to be used both for measure and input ranges.
        Takes into account the slots which will be used"""
        val = val1
        if val2:
            val = max(abs(val), abs(val2))
            if not fixed:
                cov = [(k, v) for k, v in MeasureRanges_V.__members__.items(
                    ) if v >= 10*val and MeasureRanges_V[k] in self.input_ranges]
            else:
                cov = [
                    (k, v) for k, v in MeasureRanges_V.__members__.items()
                    if -1 * v >= 10 * val and
                    MeasureRanges_V[k] in self.input_ranges]
                if cov:
                    if fixed:
                        mincov = max(cov, key=lambda x: x.__getitem__(1))
                        return range_map[maxcov]
                    else:
                        mincov = min(cov, key=lambda x: x.__getitem__(1))
                        return MeasureRanges_V[mincov[0]]
                else:
                    return MeasureRanges_V.full_auto

    def get_mincover_I(self,  val1, val2=None, fixed=False):
        """ This returns the smallest voltage range covering the largest given
        values. Only returns auto or limited, in order to be used both for measure and input ranges.
        Takes into account the slots which will be used"""
        val = val1
        if val2:
            val = max(abs(val), abs(val2))

            def valid(y):
                covered = MeasureRanges_I[y].value <= 20
                if fixed:
                    covered = covered and MeasureRanges_I[y].value < 0
                else:
                    covered = covered and MeasureRanges_I[y].value > 0
                    return covered and MeasureRanges_I[y] in self.input_ranges
        range_map = {round(1e-12*pow(10, i), 12): x for i, x in enumerate(
            (y for y in MeasureRanges_I.__members__ if valid(y)))
        }
        range_map[
            2] = MeasureRanges_I.A2_limited if not fixed else MeasureRanges_I.A2_fixed
        range_map[
            20] = MeasureRanges_I.A20_limited if not fixed else MeasureRanges_I.A20_fixed
        range_map[
            40] = MeasureRanges_I.A40_limited if not fixed else MeasureRanges_I.A40_fixed
        cov = [x for x in range_map.keys() if x >= val]
        if cov:
            if fixed:
                maxcov = max(cov)
                return range_map[maxcov]
            else:
                mincov = min(cov)
                return range_map[mincov]
        else:
            return MeasureRanges_I.full_auto

    def __discover_channels(self):
        channels = []
        try:
            ret = self.parent.check_settings(self.slot)
            channels.extend([int(x.replace("CL", ""))
                             for x in ret.strip().split(";") if x])
        except visa.VisaIOError as e:
            self._check_err()
            exception_logger.warn(
                "Caught exception\n {} \n as part of discovery prodecure, assuming no module in slot {}".format(
                    e, i))
            exception_logger.info(
                "Found the folliwing channels\n{} in slot {}".format(channels),
                self.slot)
        return channels


    def disconnect(self, channel=None):
        if channel is None and len(self.channels) > 1:
            raise ValueError(
                "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                    self.slot, self.channels))
        return self.parent.write(format_command("CL", self.channels[0]))

    def connect(self, channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]

        return self.parent.write(format_command("CN", channel))

    def restore(self, channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
                return self.parent.write("RZ {}".format(channel))

    def force_zero(self, channel=None):
        if not channel:
            if len(self.channels) > 1:
                exception_logger.warn("Multiple channels founds on Slot {}, please\
                                      specifiy one of {}. ONLY for DZ and CL  we apply the command to ALL channels \
                                      since it might be critical to shut of all channels".format(self.slot, self.channels)
                                      )
                return self.parent.write("DZ")
            else:
                channel = self.channels[0]
        else:
            return self.parent.write("DZ {}".format(channel))

    def teardown(self, channel=None):
        self.force_zero(channel)
        self.disconnect(channel)

    def set_connection_state(self, state, channel):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
                if state:
                    return self.parent.write(format_command("CN", channel))
                else:
                    return self.parent.write(format_command("CL", channel))

    def set_filter(self, state, channel=None):
        if len(self.channels) > 1:
            raise ValueError(
                "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                    self.slot, self.channels))
        else:
            channel = self.channels[0]
            return self.parent.write(format_command("FL", state, channel))

    def set_series_resistance(self, state, channel=None):
        """Enables or disables the ~1MOhm SMU series resistor"""
        if state and not self.series_resistance:
            raise ValueError(
                "The module {}  on slot {} does not support the 1MOhm series resistance".format(
                    self.name, self.slot))
        if len(self.channels) > 1:
            raise ValueError(
                "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                    self.slot, self.channels))
        else:
            channel = self.channels[0]
            return self.parent.write(
                "SSR {},{}".format(
                    channel,
                    state))  # connects or disconnects 1MOhm series

class PulsedSweep(PulseUnit, SweepUnit):

    def set_pulse_sweep_voltage(
        self,
        channel,
        input_range,
        base,
        start,
        stop,
        step,
        compliance,
        sweepmode=SweepMode.linear_up_down,
      power_comp=None):
        return self.parent.write(format_command("PWV",
                                                channel,
                                                mode,
                                                input_range,
                                                base,
                                                start,
                                                stop,
                                                step,
                                                compliance,
                                                power_comp
                                                ))

        def set_pulse_sweep_current(
                self,
                channel,
                input_range,
                base,
                start,
                stop,
                step,
                compliance,
                sweepmode=SweepMode.linear_up_down,
                power_comp=None):
            return self.parent.write(format_command("PWI",
                                                    channel,
                                                    mode,
                                                    input_range,
                                                    base,
                                                    start,
                                                    stop,
                                                    step,
                                                    compliance,
                                                    power_comp
                                                    )
                                     )

    def setup_pulse_sweep(self, channel, sweep_setup):
        self.set_pulse_timing(
            sweep_setup.hold,
            sweep_setup.width,
            sweep_setup.period)
        self.set_sweep_auto_abort(sweep_setup.auto_abort)
        if sweep_setup.input == Inputs.V:
            self.set_pulse_sweep_voltage(
                channel,
                sweep_setup.sweepmode,
                sweep_setup.input_range,
                sweep_setup.base,
                sweep_setup.start,
                sweep_setup.stop,
                sweep_setup.step,
                sweep_setup.compliance,
                sweep_setup.power_comp
            )
        else:
            self.set_pulse_sweep_current(
                channel,
                sweep_setup.sweepmode,
                sweep_setup.input_range,
                sweep_setup.base,
                sweep_setup.start,
                sweep_setup.stop,
                sweep_setup.step,
                sweep_setup.compliance,
                sweep_setup.power_comp
            )




class PulsedSpotUnit(PulseUnit):

    def set_pulse_spot_voltage(
        self,
        channel,
        input_range,
        base,
        pulse,
     compliance):
        return self.parent.write(
            format_command(
                "PV",
                channel,
                input_range,
                base,
                pulse,
                compliance))

    def set_pulse_spot_current(
        self,
        channel,
        input_range,
        base,
        pulse,
     compliance):
        return self.parent.write(
            format_command(
                "PI",
                channel,
                input_range,
                base,
                pulse,
                compliance))

    def setup_pulsed_spot(self, channel, pulse_setup):
        if pulse_setup.input == Inputs.V:
            return self.set_pulse_spot_voltage(
                channel,
                pulse_setup.input_range,
                pulse_setup.base,
                pulse_setup.pulse,
                pulse_setup.compliance)
        else:
            return self.set_pulse_spot_current(
                channel,
                pulse_setup.input_range,
                pulse_setup.base,
                pulse_setup.pulse,
                pulse_setup.compliance)


# bundling up all the different Measuring Types possible with almost every SMU
class GeneralSMU(SMU,DCForceUnit, PulsedSpotUnit, SingleMeasure, StaircaseSweepUnit):# SpotUnit, PulsedSweep, StaircaseSweep):
    pass
class HPSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High power source/monitor unit"
        self.models = ["B1510A"]
        self.input_ranges = tuple([InputRanges_V[x] for x in
                                   InputRanges_V.__members__
                                   if InputRanges_V[x].value
                                   in (0, 20, 200, 400, 1000, 2000)] +
                                  [InputRanges_I[x] for x in
                                   InputRanges_I.__members__
                                   if InputRanges_I[x].value
                                   in tuple([0] + list(range(11, 21)))])
        self.measure_ranges = tuple([0,20, 200, 400, 1000,
                                    2000, -20, -200,-400,-1000,-2000]+
                                   list(range(11,21))+list(range(-11,-21,-1))
                                    )
        super().__init__(parent_device, slot)


class MPSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "Medium power source/monitor unit"
        self.models = ("B1511A", "B1511B")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 5, 50, 200, 400, 1000)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(8, 20)))]
        self.measure_ranges = tuple([0,5,20,50, 200, 400, 1000,
                                    -5, -20,-50, -200,-400,-1000,]+
                                   list(range(8,20))+list(range(-8,-20,-1))
                                     )
        super().__init__(parent_device, slot)


class HCSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High current source/monitor unit"
        self.models = ("B1512A")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 20, 200, 400, 1000, 2000)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(11, 21)))]
        self.measure_ranges = tuple([0,2,20, 200, 400,
                                    -5, -20,-200, -400,]+
                                    list(range(15,20))+list(range(-15,-20))+[22,-22]
                                    )
        super().__init__(parent_device, slot)


class HVSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High voltage source/Monitor unit"
        self.models = ("B1513A", "B1513B")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 2000, 5000, 15000, 30000)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(11, 19)))]
        self.measure_ranges = tuple([0,2000,5000, 15000, 30000,
                                    -2000, -5000, -15000, -30000,]+
                                    list(range(11,19))+list(range(-11,-19,-1))
                                    )
        super().__init__(parent_device, slot)

class MCSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "Medium current source/monitor unit"
        self.models = ("B1514A")
        self.input_ranges = [
            InputRanges_V[x] for x in InputRanges_V.__members__
            if InputRanges_V[x].value in (0, 2, 200, 400,)] + [
            InputRanges_I[x] for x in InputRanges_I.__members__
            if InputRanges_I[x].value in tuple([0] + list(range(15, 21)))]
        self.measure_ranges = tuple([0, 2,20,200,400,
                                    -2,-20,-200,-400]+
                                    list(range(15,20))+list(range(-15,-20))
                                    )

        super().__init__(parent_device, slot)

class HRSMU(GeneralSMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High resolution source/monitor unit"
        self.models = ["B1517A"]
        self.input_ranges = tuple([InputRanges_V[x]
                                   for x in InputRanges_V.__members__
                                   if InputRanges_V[x].value
                                   in (0, 5, 50, 200, 400, 1000)] +
                                  [InputRanges_I[x]
                                   for x in InputRanges_I.__members__
                                   if InputRanges_I[x].value in tuple(
                                       [0] + list(range(8, 20)))])
        self.measure_ranges = tuple([0, 5,20, 50,200,400,1000,
                                    -5, -20, -50, -200, -400, -1000,]+
                                   list(range(8,20))+list(range(-8,-20,-1))
                                    )
        super().__init__(parent_device, slot)


class HVSPGU(SMU):

    def __init__(self, parent_device, slot):
        self.long_name = "High Voltage SPGU (Semiconductor pulse generator unit)"
        self.models = ["B1525A"]
        self.load_impedance = {}
        self.busy = 0
        self.minV = -40
        self.maxV = 40
        super().__init__(parent_device, slot)

    def set_apply(self, channel):
        """ Applys the recently set configuration to SPGU, immediately staring to force
        base voltage"""
        self.parent.write("SPUPD {}".format(channel))

    def set_pulse_timing(
        self,
        channel,
        source,
        delay,
        width,
        leading,
     trailing):
        self.parent.write(
            format_command(
                "SPT",
                channel,
                source,
                delay,
                width,
                leading,
                trailing))

    def set_num_levels(self, channel, level_sources):
        self.parent.write(format_command("SPM", channel, level_sources))
    def set_pulse_levels(self, channel,  base, peak, pulse_src):
        self.parent.write(format_command("SPV", channel, pulse_src, base, peak))

    def set_loadimpedance(self, channel, loadZ):
        self.parent.write(format_command("SER", channel, loadZ))
        self.load_impedance[channel] = loadZ

    def set_loadimpedance_auto(
        self,
        channel,
        update_impedance=1,
        delay=0,
        interval=5e-6,
     count=1):
        self.parent.write(
            format_command(
                "CORRSER?",
                channel,
                update_impedance,
                delay,
                interval,
                count))
        self.load_impedance[channel] = "autoset"
        # execute a single measurement and set the output load

    def set_pulse_period(self, pulse_period):
        self.parent.write(format_command("SPPER", pulse_period))

    def set_pulse_switch(
        self,
        channel,
        switch_state,
        switch_normal,
        switch_delay,
     width):
        self.parent.write(
            format_command(
                "ODSW",
                channel,
                switch_state,
                switch_normal,
                switch_delay,
                width))

    def set_output_mode(self, output_mode, condition):
        self.parent.write(format_command("SPRM", output_mode, condition))

    def set_wavemode(self, mode):
        """ Changes betwee pulsed and arbitrary linear wave mode"""
        self.parent.write("SIM {}".format(mode))

    def start_pulses(self):
        """Starts SPGU output"""
        self.parent.write("SPR")

    def wait(self):
        """ Queries SPGU and blocks until it has finished pulsing"""
        self.busy = 1
        while busy == 1:
            self.busy = self.parent.query("SPST?")

    def setup_spgu(self, channel, spgu_setup):
        self.set_wavemode(spgu_setup.wavemode)
        self.set_output_mode(spgu_setup.output_mode, spgu_setup.condition)
        self.set_pulse_switch(
            channel,
            spgu_setup.switch_state,
            spgu_setup.switch_normal,
            spgu_setup.switch_delay,
            spgu_setup.switch_width)  # ODSW
        self.set_pulse_period(spgu_setup.pulse_period)  # SPPER
        if spgu_setup.wavemode == SPGUModes.Pulse:
            self.set_num_levels(channel, spgu_setup.pulse_level_sources)
            self.set_pulse_levels(
                channel,
                spgu_setup.pulse_base,
                spgu_setup.pulse_peak,
                spgu_setup.pulse_src)  # SPM, SPV, check if pulse_src==source
        else:
            raise NotImplementedError(
                "Arbitrary Linear Wavemode will be added in a later release")
        self.set_pulse_timing(
            channel,
            spgu_setup.timing_source,
            spgu_setup.pulse_delay,
            spgu_setup.pulse_width,
            spgu_setup.pulse_leading,
            spgu_setup.pulse_trailing,
            )  # SPT
        self.set_apply(channel)  # SPUPD
        if spgu_setup.loadZ == SPGUOutputImpedance.full_auto:
            self.set_loadimpedance_auto(channel)
        else:
            self.set_loadimpedance(channel, spgu_setup.loadZ)  # SER



class MFCFMU(SMU):

    def __init__(self, parent_device, slot):
        self.long_name = "Multiple frequency capacitive frequency measuring unit"
        self.models = ["B1520A"]
        # TODO special treatment
        super().__init__(parent_device, slot)

