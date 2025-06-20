import pytest
from typhoon.api.schematic_editor import SchematicAPI
import typhoon.api.hil as hil
import typhoon.test.signals as sig
import typhoon.test.reporting.messages as msg
import typhoon.test.reporting.figures as fig
import typhoon.test.capture as cap
from datetime import datetime

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
    v_ref = 480
    
    #Wind_in inputs (Q_mode = 0)
        #v_ref
    hil.set_scada_input_value(scadaInputName='Wind_in.V_ref', 
                               value=v_ref, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in1.V_ref', 
                               value=v_ref, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in2.V_ref', 
                               value=v_ref, 
                               )   
        #Q_ref                       
    hil.set_scada_input_value(scadaInputName='Wind_in.Q_ref', 
                               value=0, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in1.Q_ref', 
                               value=0, 
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in2.Q_ref', 
                               value=0, 
                               )                           
    hil_area = hil.get_scada_input_settings(scadaInputName = 'Wind_in.Q_ref')
    msg.report_message(f"q_ref = {hil_area}")
    
    #Battery Inverter inputs Pref, Qref = 0                           
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
    #wind_speed
    hil.set_scada_input_value(scadaInputName='Wind_in.wind_speed', 
                               value=default, #return to default
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in1.wind_speed', 
                               value=default, #return to default
                               )
    hil.set_scada_input_value(scadaInputName='Wind_in2.wind_speed', 
                               value=default, #return to default
                               )                           
    hil.set_scada_input_value(scadaInputName='Batt_in.On', 
                               value=1, 
                               )
    hil.set_source_sine_waveform(name='Vs1', 
                              rms=65308, 
                              frequency=50, 
                              )

@pytest.mark.parametrize('wind_speed',  [(4), (5), (6)])
#@pytest.mark.parametrize('batt', [(1)])
#@pytest.mark.parametrize('rms', [(63508)])
def test_measurements(wind_speed, return_to_3):
    """
    
    tests wind turbine, power plant, consumption,, battery, and grid measurements as wind speed varies
    
    """
    #capture section
    cap.wait(secs=1) #wait for steady state 
    
    """
    Here, 1 second after simulation starts, capture begins for a variety of sign which 
    can be seen in the start_capture function below.
    
    0 secs after simulation: start sim
    1 sec after sim: start capture for 10 seconds
    1.5 sec after sim: set wind_speed from 3 to wind_speed parameter
    4.5 sec after sim: begin fault by setting source vault to 0 
    7.5 sec after sim: begin fault reperation by setting source vault rms to 65308 
    11 sec after sim: finish capture 
    """
    
    time_before_step = 0.5
    cap.start_capture(duration=10, 
                       rate=fs, 
                       signals=['Battery1.SOC','Wind Turbine 3 measurement.POWER_P', 'Wind Turbine 2 measurement.POWER_P', 'Wind Turbine 1 measurement.POWER_P', 'Grid measurement.POWER_P', 'Wind Power Plant.POWER_P', 'Consumption measurement.POWER_P', 'Battery measurement.POWER_P', 'Money Gain.Money'], 
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
    #fault
    '''
    cap.wait(secs=3)
    
    hil.set_source_sine_waveform(name='Vs1', 
                              rms=0, 
                              frequency=50, 
                              )
    #fault reparation
    #cap.wait(secs=3)
    #
    #hil.set_source_sine_waveform(name='Vs1', 
    #                          rms=65308, 
    #                          frequency=50, 
    #                          )
    #hil.set_scada_input_value("Relay.EnRst",1)
    #cap.wait(secs=0.1)
    #hil.set_scada_input_value("Relay.EnRst",0)
    # 
    '''
    df = cap.get_capture_results(wait_capture=True) #get results and associate it with a data frame
    
    #messages section
    signals = [['Wind Turbine 3 measurement.POWER_P', 'Wind Turbine 2 measurement.POWER_P', 'Wind Turbine 1 measurement.POWER_P'],
               ['Grid measurement.POWER_P', 'Wind Power Plant.POWER_P', 'Consumption measurement.POWER_P', 'Battery measurement.POWER_P']]
    plot(df, signals)
    
    df.index = df.index.total_seconds()
    df['Wind Power Plant.POWER_P'].to_csv(f'wind-power-plant-active-power-wind-speed-{wind_speed}.csv')
    
    #assert section
                           
def plot(df,signals,zoom=None):
    if zoom is None:
        fig.attach_figure([df[sig] for sig in signals], 'Complete') #list comprehension
    else:
        fig.attach_figure([df[sig][zoom[0]:zoom[1]] for sig in signals], f'Zoom ({zoom[0]} to {zoom[1]})')