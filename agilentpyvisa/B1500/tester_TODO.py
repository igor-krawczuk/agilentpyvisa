
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

    def quasi_pulse(self, channel_number, quasi_setup):
        self.write("BDT {},{}".format(
            *["{}".format(x) for x in quasi_setup[-2:]]))
        self.write("BDM {},{}".format(
            *["{}".format(x) for x in quasi_setup[0:2]]))
        self.write("BDV {},{}".format(
            channel_number, *["{}".format(x) for x in quasi_setup[2:6]]))
