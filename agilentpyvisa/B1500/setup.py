from .enums import (ADCMode, Format, Filter, OutputMode, SeriesResistance, ADCTypes,)
from collections import namedtuple

class TestSetup(namedtuple('__TestSetup',
                           ["channels",    # list of channel setups
                            "highspeed_adc_number",
                            # AV, default 1, 1-1013 = number or numberx initial
                            # in auto
                            "highspeed_adc_mode",          # AV, default ADCMode.auto
                            "adc_modes",
                            # AIT, [(type,ADCMode.auto for type in ADCTypes as
                            # default
                            "format",
                            "output_mode",
                            "filter"
                            ])):

    def __new__(cls, channels=[], highspeed_adc_number=1, highspeed_adc_mode=ADCMode.auto,
        adc_modes=[], format=Format.ascii12_with_header_crl,
        output_mode=OutputMode.dataonly, filter=Filter.disabled):
        # add default values
        return super(TestSetup, cls).__new__(cls, channels, highspeed_adc_number,
            highspeed_adc_mode, adc_modes, format, output_mode, filter)



class TestSetup(namedtuple('__TestSetup',
                           ["channels",    # list of channel setups
                            "highspeed_adc_number",
                            # AV, default 1, 1-1013 = number or numberx initial
                            # in auto
                            "highspeed_adc_mode",          # AV, default ADCMode.auto
                            "adc_modes",
                            # AIT, [(type,ADCMode.auto for type in ADCTypes as
                            # default
                            "format",
                            "output_mode",
                            "filter"
                            ])):

    def __new__(cls, channels=[], highspeed_adc_number=1, highspeed_adc_mode=ADCMode.auto,
        adc_modes=[], format=Format.ascii12_with_header_crl,
        output_mode=OutputMode.dataonly, filter=Filter.disabled):
        # add default values
        num_mes= len(set([c.measurement for c in channels if c.measurement]))
        if num_mes>1:
                raise ValueError("Only 1 type of measurements allowed per setup, have {}".format(num_mes))
        return super(TestSetup, cls).__new__(cls, channels, highspeed_adc_number,
            highspeed_adc_mode, adc_modes, format, output_mode, filter)

class Channel(
              namedtuple(
                  '__Channel',
                  ["number",    # channel number
                     "series_resistance",  # connect series yes or no? default no
                     "channel_adc",  # AAD, default ADCTypes.highspeed
                   "dcforce",
                    "staircase_sweep",
                   "pulsed_sweep",
                    "pulsed_spot",
                    "quasipulse",
                   "spgu",
                   "highspeed_spot",
                   "measurement",
                   "binarysearch",
                   "linearsearch",
                   ])):
    def __new__(cls,number,  series_resistance=SeriesResistance.disabled, channel_adc=ADCTypes.highspeed,
                   dcforce=None, staircase_sweep=None, pulsed_sweep=None, pulsed_spot=None, spgu=None, quasipulse=None,
                   highspeed_spot=None, measurement=None,binarysearch=None,linearsearch=None ):
        # add default values
        # adc_type = AAD
        #
        if [x is not None for x in [dcforce, staircase_sweep, pulsed_sweep,  quasipulse, pulsed_spot, spgu, highspeed_spot]].count(True)>1:
            raise ValueError("At most one force setup can be use per channel")
        return super(Channel, cls).__new__(cls, number, series_resistance, channel_adc,
                   dcforce, staircase_sweep, pulsed_sweep,  pulsed_spot, quasipulse, spgu, highspeed_spot, measurement,binarysearch,linearsearch )
