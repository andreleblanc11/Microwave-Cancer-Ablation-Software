"""

AUTOMATION CONTROL CODE - NETWORK ANALYZER WITH SWITCH - V1 - 2021

Atlantic Cancer Research Institute - ACRI

Code originally written  by André LeBlanc, electrical engineering student at l'Université de Moncton
Febuary 2021
"""

# Bring in the VISA LIBRARY
import pyvisa
import PySimpleGUI as sg
import relay_ft245r
import sys
import time

"""
GLOBAL OBJECTS
"""
rb = relay_ft245r.FT245R()
dev_list = rb.list_dev()

# Create a ressource manager
rm = pyvisa.ResourceManager()
rm.list_resources()

# Open the Network analyzer by name
analyzer = rm.open_resource('USB0::0x2A8D::0x0001::MY55201231::0::INSTR')

def init():

    # list of FT245R devices are returned
    if len(dev_list) == 0:
        print('No FT245R devices found')
        sys.exit()

    # Show their serial numbers
    for dev in dev_list:
        print(dev.serial_number)

    # Pick the first one for simplicity
    dev = dev_list[0]
    print('Using device with serial number ' + str(dev.serial_number))
    rb.connect(dev)

    # Place switch in state I for its initial state
    rb.switchon(2)
    rb.switchoff(3)

    # Set the time for 10s
    analyzer.timeout = 15000  # essayer des delay entre les commande

    # Return the Analyzer'ID string to tell us it's connected
    print(analyzer.query('*IDN?'))

    # CHANNEL 1 INITIALISATION
    analyzer.write(":CALCulate1:PARameter:COUNt 1")
    analyzer.write("calculate1:measure1:format smith")

    # Tentative d'acquérir les mesures à travers du port 2
    # analyzer.write("calculate1:measure1:DEFine 'ch1_s11', S11, 2")

    analyzer.write("CALCulate1:MEASure1:PARameter 'S11'")  # Define the parameter for each trace = s11 pour le channel 1



"""
Switch + ENA test function
"""
# NOTE: PROBE NEEDS TO BE CALIBRATED WHEN PYTHON FILE IS RUNNING.
# COULD CAUSE PROBLEMS IN CALIBRATION IF DONE PRIOR.
def test_SWI_ANA(startFreq, stopFreq, datapoints, BW, num_its, delay, directory, switch1, switch2):

    print("The test will begin in 3 seconds\n")
    time.sleep(3)

    """
    1. NETWORK ANALYZER INIT
    """
    # CONVERSION DE FRÉQUENCE DE MHZ À HZ
    startFreqHz = startFreq * 1000000
    stopFreqHz = stopFreq * 1000000
    # Set channel 1 freq and numpoint
    analyzer.write("SENS1:SWE:POIN " + str(datapoints))
    analyzer.write("SENS1:FREQ:START " + str(startFreqHz))
    analyzer.write("SENS1:FREQ:STOP " + str(stopFreqHz))
    analyzer.write("SENS1:BAND " + str(BW))

    # Determine, i.e. query, number of points in trace for ASCII transfer - query
    # Verification of data transfer between host PC and vector analyzer
    analyzer.write("SENS1:SWE:POIN?")
    numPoints = analyzer.read()
    print("Number of trace points (Channel 1)\n" + numPoints)

    # Determine, i.e. query, start and stop frequencies, i.e. stimulus begin and end points
    # Verification of data transfer between host PC and vector analyzer
    analyzer.write("SENS1:FOM:RANG:FREQ:STAR?")
    analyzer.write("SENS1:FREQ:START?")
    startFreq = analyzer.read()
    analyzer.write("SENS1:FREQ:STOP?")
    stopFreq = analyzer.read()
    print("Analyzer start frequency (Channel 1) = \n" + startFreq + "\n" + "Stop frequency (Channel 1) = \n" + stopFreq)

    # SET FREQUENCY SWEEP TIME (MINIMUM DELAY FOR REAL TIME APPLICATION)
    # delay = float(input("Insert frequency sweep duration in seconds: \n"))
    analyzer.write("SENS1:SWE:TIME " + str(delay))

    # DELAY WITH CORRECTION (TO ASSURE ALL DATA IS MEASURED IN FREQUENCY SWEEP)
    delay_with_corr = delay + delay / 4

    # BOTH CHANNELS PUT ON HOLD MODE FOR ITS DEFAULT TRIGGER STATE
    analyzer.write("SENS1:SWE:MODE HOLD")
    # analyzer.write("SENS2:SWE:MODE HOLD")

    filename = directory

    try:
        analyzer.write("mmemory:mdirectory 'D:/" + filename + "'")
        print("D: drive folder created \n")

    except:
        print("D: folders weren't created.\n")

    """
    TEST RUN
    """

    print("\nYour " + str(num_its) + " measurement(s) are being Taken.\n")

    for i in range(num_its + 1):

        if i < 1:
            if i == 0:
                # INITIALISE PROGRESS BAR
                sg.OneLineProgressMeter('Measurement progress...', 0, num_its, key='METER1', grab_anywhere=True)
                print("Initialising switch. Please wait.\n")

            # DUMP FIRST MEASUREMENT. ALWAYS GIVES UNVALID RESULT EVEN WHEN PROBE CALIBRATED.
            rb.switchon(switch1)
            rb.switchoff(switch2)

            #IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
            time.sleep(0.04)

            analyzer.write("SENS1:SWE:MODE SINGLE")
            analyzer.write("TRIGger:SCOPe CURRent")
            analyzer.write("INITiate1:IMMediate")
            time.sleep(delay_with_corr)

            # PLACE SWITCH IN POSITION II (50 Ohm terminator)
            rb.switchon(switch2)
            rb.switchoff(switch1)
            time.sleep(delay_with_corr)


        else:
            print("ITERATION " + str(i) + "\n")
            # PLACE SWITCH IN POSITION I (Dielectric measurement)
            rb.switchon(switch1)
            rb.switchoff(switch2)
            print("Switch in position I (Dielectric measurements)")

            #IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
            time.sleep(0.04)

            # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
            analyzer.write("SENS1:SWE:MODE SINGLE")
            analyzer.write("TRIGger:SCOPe CURRent")
            analyzer.write("INITiate1:IMMediate")
            analyzer.write("MMEMory:STORe:DATA '" + filename + "/Iteration" + str(
                i) + ".csv', 'CSV formatted Data','Trace','RI', 1")

            # WAIT WHILE MEASUREMENTS ARE BEING TAKEN
            time.sleep(delay_with_corr)


            # PLACE SWITCH IN POSITION II (50 Ohm terminator)
            rb.switchon(switch2)
            rb.switchoff(switch1)
            print("Switch in position II (Microwave ablation)\n")

            # WAIT WHILE GENERATOR IS EMITTING MICROWAVES
            time.sleep(delay_with_corr)

            # UPDATE PROGRESS BAR
            sg.OneLineProgressMeter('Measurement progress...', i, num_its, key='METER1', grab_anywhere=True)

        # PLACE SWITCH IN POSITION I FOR ITS DEFAULT END STATE
        rb.switchon(switch1)
        rb.switchoff(switch2)


"""
GU Interface (EN)
Interface UG (FR)
"""
sg.ChangeLookAndFeel('BlueMono')

# ------ Menu Definition ------ #
menu_def = [['OPTIONS', ['TEST', 'QUIT']]]

# Initial window layout
Init_layout = [
    [sg.Text('Network Analyzer', font=("Helvetica", 18), pad=(0, 5))],
    [sg.Submit(key='_ANA_OK_', button_text='Select', font=("Helvetica", 18), pad=(0, 20))],
    [sg.Text('Switch', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_SWITCH_OK_', font=("Helvetica", 18), button_text='Select', pad=(0, 20),
               auto_size_button=True)],
    [sg.Submit(key='_LAUNCH_OK_', font=("Helvetica", 18), button_text='Launch test', pad=(300, 10),
               auto_size_button=True)]
]

# Analyzer main window layout
Analyzer_layout = [
    [sg.Text('Frequency', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_FREQ_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Text('Parameters', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_PARAMS1_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Cancel(key='_ANA_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]
]

# Frequency configuration window layout
Freq_layout = [
    [sg.Text('Start frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2440', do_not_clear=True, key='_STARTFREQ_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Stop frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2460', do_not_clear=True, key='_STOPFREQ_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Number data points ', font=("Helvetica", 18)),
     sg.Input('101', do_not_clear=True, key='_NUMDATA_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Bandwidth (Hz)', font=("Helvetica", 18)),
     sg.Input('300', do_not_clear=True, key='_BW_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG1_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_FREQ_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]

# Frequency configuration window layout
Params1_layout = [
    [sg.Text('Number of test iterations', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_NUMITS_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Delay between measurements (s)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DELAY_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Desired filename (must not leave blank)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DIRECTORY_', size=(20, 30), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG2_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_PARAMS1_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]

# Switch main layout
Switch_layout = [
    [sg.Text('Switch configurations', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_PARAMS2_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Cancel(key='_SWITCH_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]
]

# Test configuration selection window layout
Params2_layout = [
    [sg.Text('Switch 1 (1 to 8) - State AB when ON', font=("Helvetica", 18)),
     sg.Input('2', do_not_clear=True, key='_SWITCH1_', size=(10, 10), font=("Helvetica", 18))],
     [sg.Text('Switch 2 (1 to 8) - State AD when ON: ', font=("Helvetica", 18)),
     sg.Input('3', do_not_clear=True, key='_SWITCH2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG3_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_PARAMS2_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]

#PROGRESS BAR LAYOUT
progress_bar_layout = [[sg.Text('A custom progress meter')],
                       [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='METER1')],
                       [sg.Cancel()]]

'''
Main user layout (EN)
Fenêtre principal (FR)
'''

# Frame creation (For main window)
layout = [[sg.Menu(menu_def, tearoff=True)],
          [sg.Frame('Select analyzer or switch options', Init_layout, font='Any 13', title_color='blue', visible=False,
                    key='_INIT_FRAME_', size=(800, 400)),
           sg.Frame('Analyzer options', Analyzer_layout, font='Any 13', title_color='blue', visible=False,
                    key='_ANA_FRAME_', size=(800, 400)),
           sg.Frame('Frequency options', Freq_layout, font='Any 13', title_color='blue', visible=False,
                    key='_FREQ_FRAME_', size=(800, 400)),
           sg.Frame('Parameter options', Params1_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PARAMS1_FRAME_', size=(800, 400)),
           sg.Frame('Switch options', Switch_layout, font='Any 13', title_color='blue', visible=False,
                    key='_SWITCH_FRAME_', size=(800, 400)),
           sg.Frame('Parameter options', Params2_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PARAMS2_FRAME_', size=(800, 400))
           ]]

# Main user interface window popup
window = sg.Window('ANALYZER + SWITCH TEST - IARC - V1', layout, default_element_size=(40, 1), grab_anywhere=False,
                   size=(800, 400))


def main():
    value_dict = {"startfreq": [], "stopfreq": [], "datapoints": [], "bw": [], "num_its": [], "delay": [],
                  "directory": [], "switch1": [], "switch2": []}

    while True:
        event, values = window.Read()

        """
        INIT WINDOW
        """
        if event == 'TEST':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_ANA_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=True)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_SWITCH_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=True)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_LAUNCH_OK_':
            try:
                # window.disappear()
                sg.popup("Press OK to confirm launch. Press X to exit")
                test_SWI_ANA(value_dict['startfreq'][0], value_dict['stopfreq'][0], value_dict['datapoints'][0],
                             value_dict['bw'][0], value_dict['num_its'][0], value_dict['delay'][0],
                             value_dict['directory'][0], value_dict['switch1'][0], value_dict['switch2'][0])
                sg.popup("Test is complete!")
                # window.reappear()

            except:
                window.reappear()
                sg.popup('Please check the fields')

        """
        ANALYZER WINDOW
        """
        if event == '_ANA_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_FREQ_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=True)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_PARAMS1_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=True)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        """
        PARAMS1 WINDOW
        """
        if event == '_PARAMS1_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=True)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_CONFIG2_OK_':

            value_dict["num_its"] = []
            value_dict["delay"] = []
            value_dict["directory"] = []
            try:
                value_dict["num_its"].append(int(values['_NUMITS_']))
                value_dict["delay"].append(float(values['_DELAY_']))
                value_dict["directory"].append(str(values['_DIRECTORY_']))

                window.FindElement('_PARAMS1_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        """
        FREQ WINDOW
        """
        if event == '_FREQ_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=True)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_CONFIG1_OK_':

            value_dict["startfreq"] = []
            value_dict["stopfreq"] = []
            value_dict["datapoints"] = []
            value_dict["bw"] = []

            try:
                value_dict["startfreq"].append(float(values['_STARTFREQ_']))
                value_dict["stopfreq"].append(float(values['_STOPFREQ_']))
                value_dict["datapoints"].append(int(values['_NUMDATA_']))
                value_dict["bw"].append(int(values['_BW_']))

                window.FindElement('_FREQ_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        """
        SWITCH WINDOW
        """
        if event == '_SWITCH_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_PARAMS2_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=True)

        """
        PARAMS2 WINDOW
        """
        if event == '_PARAMS2_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=True)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)

        if event == '_CONFIG3_OK_':

            value_dict["switch1"] = []
            value_dict["switch2"] = []
            try:
                value_dict["switch1"].append(int(values['_SWITCH1_']))
                value_dict["switch2"].append(int(values['_SWITCH2_']))

                window.FindElement('_PARAMS2_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        if event is None or event == 'QUIT':
            break


try:
    init()
    main()  # Main program

except:
    sg.popup("Verify the connections")
