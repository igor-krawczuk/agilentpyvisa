from .enums import ADCMode, Format, Filter, OutputMode
from collections import namedtuple


class TestSetup(namedtuple('__TestSetup',
                           ["channels",    # list of channel setups
                           "measurements",    # list of measurement setups
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

    def __new__(cls, channels=[],measurements=[], highspeed_adc_number=1, highspeed_adc_mode=ADCMode.auto,
        adc_modes=[], format=Format.ascii12_with_header_crl,
        output_mode=OutputMode.dataonly, filter=Filter.disabled):
        # add default values
        if len(channels) <  2:
            raise InputError("You need so specify at least two channels, input and ground")
        return super(TestSetup, cls).__new__(cls, channels,measurements, highspeed_adc_number,
            highspeed_adc_mode, adc_modes, format, output_mode, filter)
