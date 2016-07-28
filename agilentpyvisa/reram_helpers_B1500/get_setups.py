# define setup functions with sane defaults for Memristor testing.
def get_pulse(base, peak, width,count=1, lead_part=0.8, trail_part=0.8, loadZ=1e6,gate_voltage=1.85,
              ground=SMU2,channel=101,gate=SMU3):
    """
    Defines a SPGU setup based on the given parameters
    The setup assumes we use a transistor with
    smu3->gate, 
    bottom_electrode->drain, 
    source->ground(SMU2 by default.)
    """
    mspgu=SPGU(base, peak,width, loadZ=loadZ, pulse_leading=[lead_part*width], pulse_trailing=[trail_part*width],
               condition=count )
    inp_channel=Channel(number=channel,spgu=mspgu)
    ground_channel=Channel(number=ground,dcforce=DCForce(Inputs.V,0,.1))
    gate_channel = Channel(number=gate,dcforce=DCForce(Inputs.V,gate_voltage,.1))
    spgu_test=TestSetup(channels=[ground_channel, gate_channel, inp_channel,],
                        spgu_selector_setup=[(SMU_SPGU_port.Module_1_Output_2,SMU_SPGU_state.open_relay)])
    return (spgu_test,mspgu, inp_channel, ground_channel, gate_channel)

def get_Vsweep(start, stop, steps, compliance=300e-6,
               measure_range=MeasureRanges_I.full_auto,gate_voltage=1.85, ground=SMU2):
    """
    Defines a Sweep setup based on the given parameters
    The setup assumes we use a transistor with
    smu3->gate, 
    bottom_electrode->drain, 
    source->ground(SMU2 by default. We also measure here.SMU1 if you do not want to use the transistor for current limiting.)
    """
    swep_smu=b15.slots_installed[b15._B1500__channel_to_slot(3)]
    in_range=swep_smu.get_mincover_V(start,stop)
    
    sweep_measure=MeasureStaircaseSweep(Targets.I,range=measure_range, side=MeasureSides.current_side)
    
    sweep = StaircaseSweep(Inputs.V,InputRanges_V.full_auto,start,stop,steps,compliance, auto_abort=AutoAbort.disabled)
    
    inp_channel=Channel(number=SMU4,staircase_sweep=sweep, measurement=sweep_measure)
    
    ground_channel=Channel(number=ground,
                           dcforce=DCForce(Inputs.V,0,compliance),
                          )
    
    gate_channel = Channel(number=SMU3,dcforce=DCForce(Inputs.V,gate_voltage,.1),
                          )
    
    sweep_test=TestSetup(channels=[gate_channel,ground_channel,inp_channel],
                         spgu_selector_setup=[(SMU_SPGU_port.Module_1_Output_2,SMU_SPGU_state.open_relay)],
                        output_mode=OutputMode.with_primarysource,
                        format=Format.ascii13_with_header_crl, filter=Filter.enabled)
    return (sweep_test,sweep, inp_channel, ground_channel, gate_channel)
