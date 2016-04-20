from logging import getLogger
exception_logger = getLogger(__name__+":ERRORS")
import visa
from .enums import *
from .force import *
from .helpers import format_command

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
            if channel is None and len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]

        return self.parent.write(format_command("CN", channel))

    def restore(self, channel=None):
        if not channel:
            if channel is None and len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
                return self.parent.write("RZ {}".format(channel))

    def force_zero(self, channel=None):
        if not channel:
            if channel is None and len(self.channels) > 1:
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
            if channel is None and len(self.channels) > 1:
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
        if channel is None and len(self.channels) > 1:
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
        if channel is None and len(self.channels) > 1:
            raise ValueError(
                "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                    self.slot, self.channels))
        else:
            channel = self.channels[0]
            return self.parent.write(
                "SSR {},{}".format(
                    channel,
                    state))  # connects or disconnects 1MOhm series
    def check_search_target(self, target_type, target):
        if target_type==Targets.I:
            if abs(target) >= self._search_min_current and abs(target) <=self._search_max_current:
                return True
            else:
                raise ValueError("Search target current out of range for {} on slot {}, use one between {} and {}".format(self.long_name,self.slot, self._search_min_current, self._search_max_current))
        else:
            if abs(target) >= self._search_min_voltage and abs(target) <=self._search_max_voltage:
                return True
            else:
                raise ValueError("Search target voltage out of range for {} on slot {}, use one between {} and {} ".format(self.long_name,self.slot, self._search_min_current, self._search_max_current))
