from logging import getLogger
exception_logger = getLogger(__name__+":ERRORS")
from .enums import *
from .force import *
from .helpers import format_command

class SPGUSMU(object):
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
        """ Sets up the timing parameters for the given signal and channel.
        Only Pulse parameters, the switch parameters(if enabled) are set separately,
        (self.set_pulse_switch) as is the period (self.set_pulse_period)"""
        return [self.parent.write(
            format_command("SPT",channel,s,d,w,l,t)) for
            s,d,w,l,t in zip(source,delay,width,leading,trailing)]

    def set_num_levels(self, channel, level_sources):
        """ Selects number of levels and signals used for the levels . Available:
            - 0 DC mode
            - 2 level pulse, using Signal 1 only
            - 2 level pulse, using Signal 2 only
            - 3 level pulse, using Signal 1 and 2
        If you set 3 level pulses, you need to explicitly set the timing and voltage seutps as len-2 tuples or lists
        """
        self.parent.write(format_command("SPM", channel, level_sources))

    def set_pulse_levels(self, channel,  base, peak, pulse_src):
        """ Sets the base and peak value for the pulse source in the specified channel"""
        if any([abs(v) > self.maxV for v in base+peak]):
            raise ValueError("SPGU output must be in range -40V to 40V")
        return [self.parent.write(format_command("SPV", channel, src, b, p)) for src,b,p in zip(pulse_src,base,peak)]

    def set_loadimpedance(self, channel, loadZ):
        """ Sets the load impedance to a value between 0.1 Ohm to 1MOhm, default 50 O
        Setting the output resistance correctly ensures that the output voltage
        is as close as possible to the SPV value. Execute set_loadimpedance_auto to
        automatically set an estimated impedance"""
        if not(loadZ==SPGUOutputImpedance.full_auto or (loadZ<1e6 and loadZ>0.1)):
            raise ValueError("loadZ must be SPGUOutputImpedance.full_auto or between 0.1 - 1e6 Ohm")
        self.load_impedance[channel] = loadZ
        return self.parent.write(format_command("SER", channel, loadZ))

    def set_loadimpedance_auto(
        self,
        channel,
        update_impedance=1,
        delay=0,
        interval=5e-6,
     count=1):
        """ Executes a voltage measurement on the SPGU terminal and sets the
        load impedance to the calulated voltage.
        """
        self.load_impedance[channel] = "autoset"
        return self.parent.write(
            format_command(
                "CORRSER?",
                channel,
                update_impedance,
                delay,
                interval,
                count))


    def set_pulse_period(self, pulse_period):
        """ Sets the pulse period to all installed SPGU modules
        """
        return self.parent.write(format_command("SPPER", pulse_period))

    def set_pulse_switch(
        self,
        channel,
        switch_state,
        switch_normal,
        switch_delay,
     width):
        """ Enables or disables the pulse switch (which I presume is a
        semiconductor switch) and sets the state, delay and "normal" state of the switch
        (normally open/closed). the manual states it is "more durable than mechanical relays and
        better suited for frequent switching applications", so if you want to use high
        frequency patterns, enable this. By default enabled"""
        return self.parent.write(
            format_command(
                "ODSW",
                channel,
                switch_state,
                switch_normal,
                switch_delay,
                width))

    def set_output_mode(self, output_mode, condition):
        """ Selects between different completion conditions:
        1. Free run (run until SPP is executed, ignores condition)
        2. Count, run until *condition* pulses have been send
        3. Duration, run until *conditions* seconds have elapsed
        """
        return self.parent.write(format_command("SPRM", output_mode, condition))

    def set_wavemode(self, mode):
        """ Changes betwee pulsed and arbitrary linear wave mode"""
        return self.parent.write("SIM {}".format(mode))

    def start_pulses(self):
        """Starts SPGU output"""
        return self.parent.write("SPR")
    def stop_pulses(self):
        """Stops SPGU output"""
        return self.parent.write("SPP")

    def wait_spgu(self):
        """ Queries SPGU and blocks until it has finished pulsing"""
        self.busy = 1
        while busy == 1:
            self.busy = self.parent.query("SPST?")
        return busy

    def setup_spgu(self, channel, spgu_setup):
        """ Creates the specified spgu setup for the given channel. For more detials about the setup look at the SPGU IntEnum"""
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
            self.set_num_levels(channel, spgu_setup.levels)
            self.set_pulse_levels(
                channel,
                spgu_setup.pulse_base,
                spgu_setup.pulse_peak,
                spgu_setup.sources)  # SPM, SPV, check if pulse_src==source
        else:
            raise NotImplementedError(
                "Arbitrary Linear Wavemode will be added in a later release")
        self.set_pulse_timing(
            channel,
            spgu_setup.sources,
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
