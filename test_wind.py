import pytest
from typhoon.api.schematic_editor import SchematicAPI
import typhoon.api.hil as hil
import typhoon.test.signals as sig
import typhoon.test.reporting.messages as msg
import typhoon.test.capture as cap

model = SchematicAPI()
fs = 100e3

@pytest.fixture(scope="module", )
def load_model():
    # Add your fixture setup code here
    
    #model.load(filename='wind farm microgrid.tse')
    #model.set_ns_var(var_name="swept_area", 
    #                  value=6543, 
    #                  )
    #model.compile()

    hil.load_model(file='wind farm microgrid Target files\\wind farm microgrid.cpd',
                    vhil_device=True,
                    )
                    
    #hil_area = hil.get_ns_var("swept_area")
    #msg.report_message(f"Swept Area = {hil_area}")
    
    hil.start_simulation()
    
    #using same values from scada
    #Wind_in inputs
    v_ref = 480
    hil.set_scada_input_value(scadaInputName='Wind_in.V_ref', 
                               value=v_ref, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in.Q_ref', 
                               value=0, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in.Q_mode', 
                               value=1, 
                               )
                               
    #Battery Inverter inputs                           
    hil.set_scada_input_value(scadaInputName='Batt_in.f_ref', 
                               value=50, 
                               )
    hil.set_scada_input_value(scadaInputName='Batt_in.Vref', 
                               value=v_ref, 
                               )                           
    hil.set_scada_input_value(scadaInputName='Batt_in.Pref', 
                               value=0, 
                               ) 
    hil.set_scada_input_value(scadaInputName='Batt_in.Qref', 
                               value=0, 
                               )
                               
    yield
    # Add your fixture teardown code here
    hil.stop_simulation()
    
@pytest.fixture()
def return_to_3(load_model):
    # Add your fixture setup code here
    default = 3
    hil.set_scada_input_value(scadaInputName='Wind_in.wind_speed', 
                               value=default, #return to default
                               )
    hil.set_scada_input_value(scadaInputName='Batt_in.On', 
                               value=1, 
                               )
    hil.set_source_sine_waveform(name='Vs1', 
                              rms=65308, 
                              frequency=50, 
                              )

@pytest.mark.parametrize('wind_speed',  [(4)])
@pytest.mark.parametrize('batt', [(1)])
@pytest.mark.parametrize('rms', [(63508)])
def test_measurements(wind_speed, batt, rms, return_to_3):
    """
    
    tests wind turbine, power plant, consumption,, battery, and grid measurements as wind speed varies
    
    """
    #capture section
    cap.wait(secs=1) #wait for steady state
    
    time_before_step = 0.1
    cap.start_capture(duration=1, 
                       rate=fs, 
                       signals=['Battery measurement.POWER_P', 'Battery measurement.Freq', 'Money Gain.Money', 'Wind Turbine 1 measurement.VAn_RMS', 'Wind Turbine 1 measurement.IA_RMS', 'Wind Turbine 1 measurement.POWER_S', 'Wind Turbine 1 measurement.POWER_Q', 'Wind Turbine 1 measurement.POWER_PF', 'Wind Turbine 1 measurement.Freq','Wind Turbine 3 measurement.POWER_P', 'Wind Turbine 2 measurement.POWER_P', 'Wind Turbine 1 measurement.POWER_P'], 
                       )
                       
    cap.wait(secs=time_before_step)
    
    hil.set_scada_input_value(scadaInputName='Wind_in.wind_speed', 
                               value=wind_speed, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in1.wind_speed', 
                               value=wind_speed, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in2.wind_speed', 
                               value=wind_speed, 
                               )
                               
    hil.set_scada_input_value(scadaInputName='Batt_in.On', 
                               value=batt, 
                               )
    hil.set_source_sine_waveform(name='Vs1', 
                              rms=rms, 
                              frequency=50, 
                              )
    
    df = cap.get_capture_results(wait_capture=True) #get results and associate it with a data frame
    
    #messages section
    
    #assert section
                           
    