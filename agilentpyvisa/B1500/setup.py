from .enums import *
from .force import *
from .measurement import *
from .tester import B1500

class TestSetup(namedtuple('__TestSetup',
                ["channels",    # list of channel setups
                 "highspeed_adc_number",  # AV, default 1, 1-1013 = number or numberx initial in auto
                 "highspeed_adc_mode",          # AV, default ADCMode.auto
                 "adc_modes",  # AIT, [(type,ADCMode.auto for type in ADCTypes as default
                 "multi_setup",
                "format",
                "output_mode",
                "filter"
                ])):
    def __new__(cls, channels, highspeed_adc_number=1, highspeed_adc_mode=ADCMode.auto,adc_modes=[], multi_setup=None, format=Formats.ascii12_with_header_crl,output_mode=OutputModes.dataonly,filter=Filter.disabled):
        # add default values
        return super(TestSetup, cls).__new__(cls, channels, highspeed_adc_number, highspeed_adc_mode, adc_modes, multi_setup, format,output_mode, filter)

