from logging import getLogger
from .helpers import format_command
from .loggers import exception_logger,write_logger, query_logger
from .enums import *
class SearchUnit(object):
    def set_search_measure(self, mode):
        self.parent.write("MM {}".format(mode))

    def _validateSearchInput(self, inp, start, stop):
        for x in (start,stop):
            if inp == Inputs.V:
                if abs(x) >self._search_max_voltage:
                    raise ValueError("Invalid Search input, ensure both start and stop are smaller than +- {}".format(self._search_max_voltage))
            else:
                if abs(x) >self._search_max_current:
                    raise ValueError("Invalid Search input, ensure both start and stop are smaller than +- {}".format(self._search_max_current))
    def _validateCompliance(self, inp, compliance, start, stop):
        m = max([abs(start),abs(stop)])
        if inp == Inputs.V:
            check=[(m <= k,k) for k in self._search_compliance_current.keys()]
            if not any([x[0] for x in check]):
                raise ValueError("Invalid Search compliance, check page 4-24 in the manual for valid Icomp")
            if not any([ compliance <y for y in [ self._search_compliance_current[x[1]] for x in check if x[0]]]):
                raise ValueError("For your current start and stop, please choose one of the following Compliance values {}".format([self._search_compliance_current[x[1]] for x in check if x[0]]))
        else:
            check=[(m < k,k) for k in self._search_compliance_voltage.keys()]
            if not any([x[0] for x in check]):
                raise ValueError("Invalid Search compliance, check page 4-24 in the manual for valid Icomp")
            if not any([ compliance <y for y in [ self._search_compliance_voltage[x[1]] for x in check if x[0]]]):
                raise ValueError("For your voltage start and stop, please choose one of the following Compliance values {}".format([self._search_compliance_voltage[x[1]] for x in check if x[0]]))

class LinearSearchUnit(SearchUnit):
    def setup_linearsearch_measure(self,measure_setup,channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        self.set_search_measure(measure_setup.mode)
        self.set_linear_search_output_mode(measure_setup.output_mode)
        self.set_linearsearch_controlmode( measure_setup.auto_abort, measure_setup.post)
        self.set_linearsearch_timing(measure_setup.hold,measure_setup.delay)
        if measure_setup.target==Targets.I:
            self.set_linearsearch_condition_current(channel,measure_setup.searchmode,measure_setup.condition, measure_setup.measure_range, measure_setup.target_value)
        else:
            self.set_linearsearch_condition_voltage(channel,measure_setup.searchmode,measure_setup.condition, measure_setup.measure_range, measure_setup.target_value)

    def setup_linearsearch_force(self, search_setup, channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        if search_setup.start is not None:
            self._validateSearchInput(search_setup.input,search_setup.start,search_setup.stop,)
            self._validateCompliance(search_setup.input, search_setup.compliance,search_setup.start,search_setup.stop)
            if search_setup.input==Inputs.I:
                self.set_linearsearch_current(channel,search_setup.start, search_setup.stop, search_setup.input_range, search_setup.compliance)
            else:
                self.set_linearsearch_voltage(channel,search_setup.start, search_setup.stop, search_setup.input_range, search_setup.compliance)
        elif search_setup.sync_polarity is not None:
            if search_setup.input==Inputs.I:
                self.set_linearsearch_synchrous_current(channel,search_setup.sync_polarity, search_setup.sync_offset, search_setup.sync_compliance)
            else:
                self.set_linearsearch_synchrous_voltage(channel,search_setup.sync_polarity, search_setup.sync_offset, search_setup.sync_compliance)

    def set_linearsearch_controlmode(self, auto_abort, post):
        self.parent.write(format_command("LSM",auto_abort, post))

    def set_linearsearch_condition_current(self,channel,searchmode,condition,measure_range,target_value):
        self.check_search_target(Targets.I,target_value)
        self.parent.write(format_command("LGI",channel, searchmode, condition,measure_range,target_value))

    def set_linearsearch_condition_voltage(self,channel,searchmode,condition,measure_range,target_value):
        self.check_search_target(Targets.V,target_value)
        self.parent.write(format_command("LGV",channel, searchmode, condition,measure_range,target_value))

    def set_linearsearch_synchrous_voltage(self, channel,polarity,offset,compliance):
        self.parent.write(format_command("LSSV",channel,polarity,offset,compliance))

    def set_linearsearch_synchrous_current(self, channel,polarity,offset,compliance):
        self.parent.write(format_command("LSSI",channek,polarity,offset,compliance))

    def set_linearsearch_voltage(self, channel,start,stop,input_range,compliance):
        self.parent.write(format_command("LSV",channel,input_range,start,stop,compliance))

    def set_linearsearch_current(self, channel,start,stop,input_range,compliance):
        self.parent.write(format_command("LSI",channel,input_range,start,stop,compliance))

    def set_linearsearch_timing(self, hold, delay):
        self.parent.write(format_command("LSTM",hold, delay))

    def set_linear_search_output_mode(self, output):
        self.parent.write("LSVM {}".format(output))

class BinarySearchUnit(SearchUnit):
    def setup_binarysearch_measure(self,measure_setup,channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        self.set_search_measure(measure_setup.mode)
        self.set_binary_search_output_mode(measure_setup.output_mode)
        self.set_binarysearch_controlmode(measure_setup.control_mode, measure_setup.auto_abort,measure_setup.post)
        self.set_binarysearch_timing(measure_setup.hold,measure_setup.delay)
        if measure_setup.target==Targets.I:
            self.set_binarysearch_condition_current(channel,measure_setup.searchmode,measure_setup.condition, measure_setup.measure_range, measure_setup.target_value)
        else:
            self.set_binarysearch_condition_voltage(channel,measure_setup.searchmode,measure_setup.condition, measure_setup.measure_range, measure_setup.target_value)

    def setup_binarysearch_force(self, search_setup, channel=None):
        if not channel:
            if len(self.channels) > 1:
                raise ValueError(
                    "Multiple channels founds on Slot {}, please specifiy one of {}".format(
                        self.slot, self.channels))
            else:
                channel = self.channels[0]
        if search_setup.start is not None:
            self._validateSearchInput(search_setup.input,search_setup.start,search_setup.stop,)
            self._validateCompliance(search_setup.input, search_setup.compliance,search_setup.start,search_setup.stop)
            if search_setup.input==Inputs.I:
                self.set_binarysearch_current(channel,search_setup.start, search_setup.stop, search_setup.input_range, search_setup.compliance)
            else:
                self.set_binarysearch_voltage(channel,search_setup.start, search_setup.stop, search_setup.input_range, search_setup.compliance)
        elif search_setup.sync_polarity is not None:
            if search_setup.input==Inputs.I:
                self.set_binarysearch_synchrous_current(channel,search_setup.sync_polarity, search_setup.sync_offset, search_setup.sync_compliance)
            else:
                self.set_binarysearch_synchrous_voltage(channel,search_setup.sync_polarity, search_setup.sync_offset, search_setup.sync_compliance)

    def set_binarysearch_controlmode(self, controlmode, auto_abort,post):
        self.parent.write(format_command("BSM",controlmode,auto_abort,post))

    def set_binarysearch_condition_current(self,channel,searchmode,condition,measure_range,target_value):
        self.check_search_target(Targets.I,target_value)
        self.parent.write(format_command("BGI",channel, searchmode, condition,measure_range,target_value))

    def set_binarysearch_condition_voltage(self,channel,searchmode,condition,measure_range,target_value):
        self.check_search_target(Targets.V,target_value)
        self.parent.write(format_command("BGV",channel, searchmode, condition,measure_range,target_value))

    def set_binarysearch_synchrous_voltage(self, channel,polarity,offset,compliance):
        self.parent.write(format_command("BSSV",channel,polarity,offset,compliance))

    def set_binarysearch_synchrous_current(self, channel,polarity,offset,compliance):
        self.parent.write(format_command("BSSI",channek,polarity,offset,compliance))

    def set_binarysearch_voltage(self, channel,start,stop,input_range,compliance):
        self.parent.write(format_command("BSV",channel,input_range,start,stop,compliance))

    def set_binarysearch_current(self, channel,start,stop,input_range,compliance):
        self.parent.write(format_command("BSI",channel,input_range,start,stop,compliance))

    def set_binarysearch_timing(self, hold, delay):
        self.parent.write(format_command("BST",hold, delay))

    def set_binary_search_output_mode(self, output):
        self.parent.write("BSVM {}".format(output))

