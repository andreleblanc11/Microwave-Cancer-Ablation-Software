"""
AUTOMATION CIRCUIT CONTROL - GENERATOR WITH SWITCH - V1, 2021

Atlantic Cancer Research Institute - ACRI

Code originally formulated by André LeBlanc, Electrical Engineering bachelor student at l'Université de Moncton

March 2021

NOTE 1: USB cable needs to be connected to the host PC AND (generator + fan) must be activated prior to running the code. Otherwise the ablation probe won't emit micro-waves.
"""

import sys
# For file extraction
import pickle
# For code logs (optional)
# import logging
from time import sleep
import PySimpleGUI as sg
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import relay_ft245r
from lucidIo.LucidControlAO4 import LucidControlAO4
from lucidIo.Values import ValueVOS4


"""
GLOBAL OBJECTS
"""

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# logging.basicConfig(format=FORMAT)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

UNIT = 0x01  # Set the generator slave address

# COM varies on which generator your are using.
client = ModbusClient(method='rtu', port='COM14', timeout=4,
                      baudrate=115200, strict=False)

rb = relay_ft245r.FT245R()
dev_list = rb.list_dev()


"""
GENERATOR + SWITCH INIT
"""
def init():

    """
    1. GENERATOR INIT
    """
    client.set_parity = 0
    client.set_bytesize = 8
    client.set_stopbits = 1
    client.connect()
    print("Generator connected \n")

    # ------------------------------------------------------------------------#
    # write all command you want to set here
    # ------------------------------------------------------------------------#

    # RESET FAULT : set bit 7 of register 2 to 1 and then to 0 (see page 19 of Microwave generator documentation --> Cabinet 18, room 455, IARC)
    client.write_register(2, 0x80, unit=UNIT)

    # RESET FAULT: set bit 7 of register 2 back to 0
    # TURN GENERATOR OFF (default state) : set register 2, bit 6 to
    client.write_register(2, 0x00, unit=UNIT)
    print("Faults reseted\n")

    # GENERATOR STARTING MODE TO NORMAL : set registor 3 bit 0 to 0
    client.write_register(3, 0x00, unit=UNIT)

    print("Microwave is turned off for its initial state \n")

    # RESET COMMUNICATION TIMEOUT ( Must be greater than Power_ON_time !!!)
    client.write_register(98, 3000, unit=UNIT)


    """
    2. SWITCH INIT
    NOTE: COMMENT THIS SECTION IF YOU WANT TO RUN CODE WITHOUT SWITCH
    """

    # list of FT245R devices are returned
    if len(dev_list) == 0:
        print('No FT245R devices found')
        sys.exit()

    # Pick the first one for simplicity
    dev = dev_list[0]
    print('Using device with serial number ' + str(dev.serial_number))
    rb.connect(dev)

    # Place switch in state I for its initial state
    rb.switchon(2)
    rb.switchoff(3)


"""
GENERATOR + SWITCH TEST FUNCTION
"""
def run_sync_client(power, sleep_time, micro_time, freq, num_its, switch1, switch2, RPM):

    #INITIALISE PROGRESS BAR
    sg.OneLineProgressMeter('Process...', 0, num_its, key='METER1', grab_anywhere=True)

    # Initial delay prior to start of test
    print("\n\nThe test will begin in 3 seconds\n\n")
    sleep(3)

    # RESET COMMUNICATION TIMEOUT ( Must be greater than Power_ON_time !!!)
    # Function : register 98 set to X time before generator is faulted (red light on generator)
    client.write_register(98, 3000, unit=UNIT)

    # SET FREQUENCY
    # See page 31 of microwave generator user manual for more information (Cabinet 18, room 455, IARC)
    freqKHz = freq * 10
    client.write_register(9, freqKHz, unit=UNIT)
    rr = client.read_holding_registers(9, 1, unit=UNIT)
    rr1 = rr.registers
    print("Generator frequency is set to :" + str(rr1) + " Hz \n")

    # REFLECTED POWER LIMITATION MODE - ON
    client.write_register(2, 0x10, unit=UNIT)
    print("Reflected power limitation mode activated \n")

    # REFLECTED POWER SET
    # Value = 20 Watts (Modify accordingly for test purposes)
    client.write_register(1, 20, unit=UNIT)
    rr = client.read_holding_registers(1, 1, unit=UNIT)
    rr1 = rr.registers
    print("Reflected power set to " + str(rr1) + " watts \n")

    # TRANSMITTED POWER SET
    client.write_register(0, power, unit=UNIT)
    rr = client.read_holding_registers(0, 1, unit=UNIT)
    rr1 = rr.registers
    print("Transmitted power value set to " + str(rr1) + " Watts\n")
    print("\nSTART OF TEST\n")


    """
    PERISTALTIC PUMP INIT
    """
    ao4 = LucidControlAO4('COM13')

    # Open AO4 port
    if ao4.open() == False:
        print('Error connecting to port {0} '.format(
            ao4.portName))
        ao4.close()
        exit()

    # Create a tuple of 4 voltage objects
    values = (ValueVOS4(), ValueVOS4(), ValueVOS4(), ValueVOS4())

    # Initialize a boolean tuple for channels to change.
    channels = (True, True, True, True)


    """
    RUN TEST
    """
    for i in range(num_its):

        print("\nITERATION " + str(i + 1) + "\n")

        # Turn peristaltic pump ON
        voltage = RPM / 40
        values[0].setVoltage(voltage)
        values[1].setVoltage(0.00)
        ao4.setIoGroup(channels, values)
        print("Peristaltic pump turned ON\n")

        # TURN MICROWAVES ON
        # Place switch in position II (A-D , 50 ohm termination to slim form probe)
        rb.switchon(switch2)
        rb.switchoff(switch1)

        client.write_register(2, 0x50, unit=UNIT)
        print("Microwave turned on for " + str(micro_time) + " seconds")

        sleep(micro_time)


        # TURN MICROWAVE OFF
        # Place switch in position I (A-B , Power meter to slim form probe)
        client.write_register(2, 0x00, unit=UNIT)
        print("Microwave turned off for " + str(sleep_time) + " seconds \n")

        rb.switchon(switch1)
        rb.switchoff(switch2)

        # Turn peristaltic pump OFF
        values[0].setVoltage(0.00)
        values[1].setVoltage(5.00)
        ao4.setIoGroup(channels, values)
        print("Peristaltic pump turned OFF\n")

        # wait micro_time seconds
        sleep(sleep_time)


        #UPDATE PROGRESS BAR
        sg.OneLineProgressMeter('Process...', i + 1, num_its, key='METER1', grab_anywhere=True)

        connected = client.connect()
        if connected == False:
            print("Generator disconnected. Rerun code to restart.\n")
            break

    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #

    # Turn microwaves OFF again for redundency purposes
    # Place switch in position I again for redundency purposes
    client.write_register(2, 0x00, unit=UNIT)
    rb.switchon(switch1)
    rb.switchoff(switch2)
    values[0].setVoltage(0.00)
    values[1].setVoltage(5.00)
    ao4.setIoGroup(channels, values)

    # Close connection with generator
    client.close()
    print("The test is complete!\n\n")


"""
FREQUENCY SCAN SWEEP FUNCTION
"""
# FREQUENCY SWEEP MODE. SEE GENERATOR USER MANUAL FOR MORE INFO. PAGE 15
# TODO Fix problem with EndOfScan bit.
def Freq_sweep(powersweep, sleep_timesweep, micro_timesweep, startfreq, stopfreq, stepfreq, IsManu):
    # MANUAL MODE
    if IsManu:
        # Initial delay prior to start of test
        print("The test will begin in 2 seconds\n")
        sleep(2)

        # TIMEOUT ( Must be greater than Power_ON_time !!!)
        client.write_register(98, 3000, unit=UNIT)

        # SET START FREQUENCY
        # (24500 meaning = 24500 x 100 KHz = 2.45 Ghz)
        # See page 31 of microwave generator user manual for more information (Cabinet 18, room 455, IARC)
        startfreqKHz = startfreq * 10
        stopfreqKHz = stopfreq * 10
        stepfreqKHz = stepfreq * 10
        client.write_register(9, int(startfreqKHz), unit=UNIT)

        # REFLECTED POWER LIMITATION MODE - ON
        client.write_register(2, 0x10, unit=UNIT)
        print("Reflected power limitation mode activated \n")

        # REFLECTED POWER SET
        client.write_register(1, 20, unit=UNIT)
        print("Reflected power set to 20 watts \n")

        # TRANSMITTED POWER SET:
        client.write_register(0, int(powersweep), unit=UNIT)
        print("Forward power set point set \n")

        currentfreqKHz = startfreqKHz
        while currentfreqKHz <= stopfreqKHz or currentfreqKHz <= 2.46E9:

            # TURN MICROWAVE ON
            client.write_register(2, 0x50, unit=UNIT)
            print("Microwave turned on for " + str(micro_timesweep) + " seconds \n")

            # wait micro_time seconds
            sleep(micro_timesweep)

            # TURN MICROWAVE OFF
            client.write_register(2, 0xBF, unit=UNIT)
            print("Microwave turned off for " + str(sleep_timesweep) + " seconds \n")

            # Microwave off for sleep_time seconds (while ENA is taking measurements)
            sleep(sleep_timesweep)

            # INCREMENT FREQUENCY VALUE
            currentfreqKHz += stepfreqKHz
            client.write_register(9, int(currentfreqKHz), unit=UNIT)
            rr1 = client.read_holding_registers(112, 0x01, unit=UNIT)
            rq1 = rr1.registers
            print("Generator frequency with increment set to :" + str(rq1) + "KHz \n")

            connected = client.connect()
            if connected == False:
                print("Generator disconnected. Rerun code to restart.\n")
                break
        # ----------------------------------------------------------------------- #
        # close the client
        # ----------------------------------------------------------------------- #
        client.close()
        print("The manual frequency sweep test is complete!\n\n")

    if not IsManu:

        # Initial delay prior to start of test
        print("The test will begin in 2 seconds\n")
        sleep(2)

        # TIMEOUT ( Must be greater than Power_ON_time !!!)
        client.write_register(98, 3000, unit=UNIT)

        startfreqKHz = startfreq * 10
        stopfreqKHz = stopfreq * 10
        stepfreqKHz = stepfreq * 10

        # SET START, STOP and FREQ STEP in 100 KHz format
        client.write_register(11, int(startfreqKHz), unit=UNIT)
        rr1 = client.read_holding_registers(11, 1, unit=UNIT)
        rq1 = rr1.registers
        print("Start frequency set to:\n " + str(rq1) + "KHz\n")

        client.write_register(12, int(stopfreqKHz), unit=UNIT)
        rr2 = client.read_holding_registers(12, 1, unit=UNIT)
        rq2 = rr2.registers
        print("Stop frequency set to:\n " + str(rq2) + "KHz\n")

        client.write_register(16, int(stepfreqKHz), unit=UNIT)
        rr3 = client.read_holding_registers(16, 1, unit=UNIT)
        rq3 = rr3.registers
        print("Frequency step set to:\n" + str(stepfreq) + "MHz\n")

        # ACTIVATE SCAN MODE - SET SCAN MODE BIT TO 1
        client.write_register(17, 0x01, unit=UNIT)
        rr = client.read_holding_registers(17, 1, unit=UNIT)
        rq = rr.registers
        print(rq)


        # REFLECTED POWER LIMITATION MODE - ON
        client.write_register(2, 0x10, unit=UNIT)

        # REFLECTED POWER SET
        client.write_register(1, 20, unit=UNIT)

        # TRANSMITTED POWER SET
        client.write_register(0, int(powersweep), unit=UNIT)

        # GENERATOR ON
        client.write_register(2, 0x50, unit=UNIT)
        # print("Generator turned ON\n")
        """
        """

        while True:
            rr = client.read_holding_registers(105, 0x01, unit=UNIT)
            rq = rr.registers
            print("End of scan response is: " + str(rq))
            sleep(2)

            """
            rr = client.read_holding_registers(113, 1, unit=UNIT)
            rq = rr.registers
            print("Currrent scan frequency is:" + str(rq))         
            """

            if rq[0] == 160 or rq[0] == 32 or rq[0] == 224:
                print("The scan is complete! Processing data\n")
                break

        # ACTIVATE SCAN DATA MODE - SET SCAN DATA BIT TO 1
        client.write_register(17, 0x04, unit=UNIT)

        while True:
            rr = client.read_holding_registers(109, 1, unit=UNIT)
            rq = rr.registers
            print(rq)
            sleep(5)
            if rq[0] == 0:
                rr = client.read_holding_registers(114, 1, unit=UNIT)
                rq = rr.registers
                print("Scanned frequency minimum 1 data:\n " + str(rq) + "\n")

                rr = client.read_holding_registers(115, 1, unit=UNIT)
                rq = rr.registers
                print("Scanned frequency minimum 1 data:\n " + str(rq) + "\n")

                rr = client.read_holding_registers(113, 1, unit=UNIT)
                rq = rr.registers
                print("Scanned frequency register:\n " + str(rq) + "\n")
                sleep(0.1)
                break
        # ----------------------------------------------------------------------- #
        # close the client
        # ----------------------------------------------------------------------- #
        client.close()
        print("The Sairem automatic frequency sweep test is complete!\n\n")


"""
MANUAL GENERATOR ON/OFF FUNCTIONS
"""

def Manual_Gen_ON(power_man, rpower):

    # Place switch in position II (A-D)
    rb.switchon(3)
    rb.switchoff(2)

    # TIMEOUT (30 seconds)
    client.write_register(98, 3000, unit=UNIT)

    # SET FREQUENCY
    freq = 24500
    client.write_register(9, freq, unit=UNIT)

    # REFLECTED POWER LIMITATION MODE - ON
    client.write_register(2, 0x10, unit=UNIT)

    # REFLECTED POWER SET
    client.write_register(1, rpower, unit=UNIT)

    # TRANSMITTED POWER SET
    client.write_register(0, power_man, unit=UNIT)

    # GENERATOR ON
    client.write_register(2, 0x40, unit=UNIT)
    print("Generator turned ON\n")



def Manual_Gen_OFF():

    # GENERATOR OFF
    client.write_register(2, 0xBF, unit=UNIT)
    print("Generator turned OFF\n")

    # Place switch in position I (A-B)
    rb.switchon(2)
    rb.switchoff(3)

"""
FIVE ITERATION TEST FUNCTION
"""
def Five_Iteration_Test(power, delay, freq, rpower, i):

    if i == 1:
        # INITIAL DELAY
        print("The test will begin in 3 seconds\n")
        sleep(3)

        # FREQUENCY SET
        freq_KHz = freq * 10
        client.write_register(9, freq_KHz, unit=UNIT)
        print("Frequency is set to :\n" + str(freq) + " Hz\n")

        # REFLECTED POWER LIMITATION MODE ON
        rd1 = client.write_register(2, 0x10, unit=UNIT)
        print("Reflected power limitation mode activated \n")

        # REFLECTED POWER SET
        rq1 = client.write_register(1, rpower, unit=UNIT)
        print("Reflected power set to: \n" + str(rpower) + " Watts\n")


    print("\nITERATION " + str(i) + "\n")

    # TRANSMITTED POWER SET
    client.write_register(0, power, unit=UNIT)
    print("Forward power set point set to: \n" + str(power) + " Watts\n")


    # RUN TEST
    # MICROWAVES ON
    client.write_register(2, 0x50, unit=UNIT)
    print("Microwaves ON for " + str(delay) + " seconds \n")

    # DELAY OF INPUT VALUE SECONDS
    sleep(delay)

    # MICROWAVES OFF
    client.write_register(2, 0xBF, unit=UNIT)
    print("Microwaves OFF for " + str(delay) + " seconds \n")

    # DELAY OF INPUT VALUE SECONDS
    sleep(delay)

    if i == 5:
        # ----------------------------------------------------------------------- #
        # close the client
        # ----------------------------------------------------------------------- #
        client.close()



"""
GU Interface (EN)
Interface UG (FR)
"""

sg.ChangeLookAndFeel('BlueMono')


# ------ Menu Definition ------ #
menu_def = [['File', ['Create', 'Open (NOT UPDATED)', 'Save (NOT UPDATED)', 'Quit']]
            ]


# ------Create Definition ------ #
create_layout = [
    [sg.Text('Test 2.8', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_OPTION_OK_', button_text='OK', font=("Helvetica", 18), pad=(50, 20))],
    [sg.Text('Sweep test (GENERATOR ONLY)', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_OPTION_OK1_', button_text='OK', font=("Helvetica", 18), pad=(50, 20))],
    [sg.Text('Manual inputs', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_OPTION_OK2_', button_text='OK', font=("Helvetica", 18), pad=(40, 20))],
    [sg.Text('Five iteration test (GENERATOR ONLY)', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_OPTION_OK3_', button_text='OK', font=("Helvetica", 18), pad=(40, 20))]]


# Power and time selection layout
# ------Power Definition ------ #
normal_layout = [
    [sg.Text('Microwave power (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_POWER1_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Microwave duration (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DPOWER1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Speed (RPM)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPM_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Number of iterations: ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_NUMITS_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Delay (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DELAY1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2450', do_not_clear=True, key='_FREQ_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Switch 1 (1 to 8) - State AB when ON', font=("Helvetica", 18)),
     sg.Input('2', do_not_clear=True, key='_SWITCH1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Switch 2 (1 to 8 - State AD when ON)', font=("Helvetica", 18)),
     sg.Input('3', do_not_clear=True, key='_SWITCH2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG1_OK_', font=("Helvetica", 18), button_text='Configure', pad=(100, 10),
               auto_size_button=True),
     sg.Submit(key='_TEST1_OK_', font=("Helvetica", 18), button_text='Launch test', pad=(100, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_NORMAL_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# Frequency selection layout
sweep_layout = [
    [sg.Text('Microwave power (W)', font=("Helvetica", 18)),
     sg.Input('1', do_not_clear=True, key='_POWER2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Microwave duration (s): ', font=("Helvetica", 18)),
     sg.Input('5', do_not_clear=True, key='_DPOWER2_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Delay (s): ', font=("Helvetica", 18)),
     sg.Input('5', do_not_clear=True, key='_DELAY2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Step frequency (MHz , min. 100 KHz, max. 10 MHz): ', font=("Helvetica", 18)),
     sg.Input('1', do_not_clear=True, key='_STEPFREQ_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Start frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2400', do_not_clear=True, key='_STARTFREQ_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Stop frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2500', do_not_clear=True, key='_STOPFREQ_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Radio('Manual mode', "RADIO1", default=False, change_submits=True, key="_MANU_MODE_", font=("Helvetica", 18),
              size=(10, 1), pad=(100, 10)),
     sg.Radio('Auto mode', "RADIO1", default=False, change_submits=True, key="_AUTO_MODE_", font=("Helvetica", 18),
              size=(10, 1), pad=(100, 10))],
    [sg.Submit(key='_CONFIG2_OK_', font=("Helvetica", 18), button_text='Configure', pad=(100, 10),
               auto_size_button=True),
     sg.Submit(key='_TEST2_OK_', font=("Helvetica", 18), button_text='Launch test', pad=(100, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_SWEEP_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# Manual input layout
manu_input_layout = [
    [sg.Text('Turn ON generator (freq. = 2.45GHz)', font=("Helvetica", 18)),
     sg.Submit(key='_ONSET_OK_', font=("Helvetica", 18), button_text='GEN ON', pad=(100, 10),
               auto_size_button=True)],
    [sg.Text('Power (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_POWER3_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Ref. power (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPOWER_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('', font=("Helvetica", 18))],
    [sg.Text('Turn OFF generator', font=("Helvetica", 18)),
     sg.Submit(key='_OFFSET_OK_', font=("Helvetica", 18), button_text='GEN OFF', pad=(100, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_MANU_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]

five_it_layout = [
    [sg.Text('Power iteration 1 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER1_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON and OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITDPOWER1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 2 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER2_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON and OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITDPOWER2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 3 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER3_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON and OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITDPOWER3_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 4 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER4_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON and OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITDPOWER4_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 5 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER5_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON and OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITDPOWER5_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_FREQ1_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Reflected power (W): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPOWER1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Cancel(key='_FIVEIT_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True),
     sg.Submit(key='_CONFIG3_OK_', font=("Helvetica", 18), button_text='Configure', pad=(100, 10), auto_size_button=True),
     sg.Submit(key='_TEST3_OK_', font=("Helvetica", 18), button_text='Launch', pad=(100, 10), auto_size_button=True)]]

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
          [sg.Frame('Choose from options', create_layout, font='Any 13', title_color='blue', visible=False,
                    key='_CREATE_FRAME_', size=(800, 400)),
           sg.Frame('Normal test options', normal_layout, font='Any 13', title_color='blue', visible=False,
                    key='_NORMAL_FRAME_', size=(800, 400)),
           sg.Frame('Sweep test options', sweep_layout, font='Any 13', title_color='blue', visible=False,
                    key='_SWEEP_FRAME_', size=(1000, 500)),
           sg.Frame('Manual input options', manu_input_layout, font='Any 13', title_color='blue', visible=False,
                    key='_MANU_FRAME_', size=(800, 400)),
           sg.Frame('Five iteration test options', five_it_layout, font='Any 13', title_color='blue', visible=False,
                    key='_FIVEIT_FRAME_', size=(1000, 500))]]

# Main user interface window popup
window = sg.Window('TEST 2.8 GUI - IARC', layout, default_element_size=(40, 1), grab_anywhere=False,
                   size=(1200, 500))

"""
MAIN CODE
"""


def main():

    value_dict = {"power1": [], "dpower1": [], "freq": [], "numits": [], "delay1": []
                  , "power2": [], "dpower2": [], "startfreq": [], "stopfreq": [], "delay2": []
                  , "stepfreq": [], "power3": [], "rpower": [], "switch1": [], "switch2": []
                  ,"itpower": [], "itdpower": [], "itdpower": [], "rpm": []}
    IsManu = 0

    while True:

        event, values = window.Read()

        # print(event)

        """
        CREATE WINDOW AND RUN APPLICATIONS
        """
        if event == 'Create':
            window.FindElement('_CREATE_FRAME_').Update(visible=True)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)


        if event == '_TEST1_OK_':
            # try:
            sg.popup("Press OK to confirm launch. Press X to exit")
            run_sync_client(value_dict['power1'][0], value_dict['delay1'][0], value_dict['dpower1'][0],
                            value_dict['freq'][0], value_dict['numits'][0], value_dict['switch1'][0],
                            value_dict['switch2'][0], value_dict['rpm'][0])

            window.FindElement('_NORMAL_FRAME_').Update(visible=True)
            sg.popup("Test is complete!")

            # except:
                # sg.popup('Please check the fields')


        """
        OPEN WINDOW
        """
        if event == 'Open':
            name = sg.PopupGetFile('Enter filename : ', 'Open file', keep_on_top=True)

            try:
                with open(name, 'rb') as f:
                    value_dict = pickle.load(f)

                window.FindElement('_POWER_').Update(value=value_dict['power'][0])
                window.FindElement('_DPOWER_').Update(value=value_dict['dpower'][0])

                window.FindElement('_POWER_FRAME_').Update(visible=True)
                window.FindElement('_CREATE_FRAME_').Update(visible=False)

            except:
                print(name)
                if name is not None:
                    sg.popup("Error...")

        """
        SAVE WINDOW
        """
        if event == 'Save':
            name = sg.PopupGetFile('Enter filename : ', 'Save file', save_as=True)

            try:
                value_dict["power"] = []
                value_dict["dpower"] = []

                value_dict["power"].append(int(values['_POWER_']))
                # CODE ABDARAHMANE
                """
                # value_dict["power"].append(int(values['_POWER2_']))
                # value_dict["power"].append(int(values['_POWER3_']))
                # value_dict["power"].append(int(values['_POWER4_']))
                # value_dict["power"].append(int(values['_POWER5_']))                
                """

                value_dict["dpower"].append(int(values['_DPOWER_']))
                # CODE ABDARAHMANE
                """
                # value_dict["dpower"].append(int(values['_DPOWER2_']))
                # value_dict["dpower"].append(int(values['_DPOWER3_']))
                # value_dict["dpower"].append(int(values['_DPOWER4_']))
                # value_dict["dpower"].append(int(values['_DPOWER5_']))
                """

                if ".pkl" in name:
                    name = name.split(".pkl")
                    name = name[0]

                f = open(name + ".pkl", "wb")
                pickle.dump(value_dict, f)
                f.close()
                sg.popup("Saved !")

            except:
                sg.popup('Please check the fields')


        """
        QUIT WINDOW
        """
        if event is None or event == 'Quit':
            break


        """
        NORMAL AND SWEEP TEST WINDOWS
        """
        if event == '_OPTION_OK_':
            window.FindElement('_CREATE_FRAME_').Update(visible=False)
            window.FindElement('_NORMAL_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_OPTION_OK1_':
            window.FindElement('_CREATE_FRAME_').Update(visible=False)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=True)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_OPTION_OK2_':
            window.FindElement('_CREATE_FRAME_').Update(visible=False)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=True)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_OPTION_OK3_':
            window.FindElement('_CREATE_FRAME_').Update(visible=False)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=True)

        if event == '_SWEEP_CANCEL_':
            window.FindElement('_CREATE_FRAME_').Update(visible=True)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_NORMAL_CANCEL_':
            window.FindElement('_CREATE_FRAME_').Update(visible=True)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_MANU_CANCEL_':
            window.FindElement('_CREATE_FRAME_').Update(visible=True)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_FIVEIT_CANCEL_':
            window.FindElement('_CREATE_FRAME_').Update(visible=True)
            window.FindElement('_NORMAL_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANU_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)


        if event == '_CONFIG1_OK_':

            value_dict["power1"] = []
            value_dict["dpower1"] = []
            value_dict["numits"] = []
            value_dict["delay1"] = []
            value_dict["freq"] = []
            value_dict["switch1"] = []
            value_dict["switch2"] = []
            value_dict["rpm"] = []

            try:
                value_dict["power1"].append(int(values['_POWER1_']))
                value_dict["dpower1"].append(int(values['_DPOWER1_']))
                value_dict["numits"].append(int(values['_NUMITS_']))
                value_dict["delay1"].append(int(values['_DELAY1_']))
                value_dict["freq"].append(int(values['_FREQ_']))
                value_dict["switch1"].append(int(values['_SWITCH1_']))
                value_dict["switch2"].append(int(values['_SWITCH2_']))
                value_dict["rpm"].append(int(values['_RPM_']))

                window.FindElement('_NORMAL_FRAME_').Update(visible=True)

                sg.popup("Configured!")

            except:
                sg.popup('Please check the fields')


        if event == '_CONFIG2_OK_':

            value_dict["startfreq"] = []
            value_dict["stopfreq"] = []
            value_dict["stepfreq"] = []
            value_dict["dpower2"] = []
            value_dict["delay2"] = []
            value_dict["power2"] = []

            try:
                value_dict["startfreq"].append(float(values['_STARTFREQ_']))
                value_dict["stopfreq"].append(float(values['_STOPFREQ_']))
                value_dict["stepfreq"].append(float(values['_STEPFREQ_']))
                value_dict["dpower2"].append(float(values['_DPOWER2_']))
                value_dict["delay2"].append(float(values['_DELAY2_']))
                value_dict["power2"].append(float(values['_POWER2_']))

                window.FindElement('_SWEEP_FRAME_').Update(visible=True)

                sg.popup("Configured!")

            except:
                sg.popup('Please check the fields')


        if event == '_MANU_MODE_':
            IsManu = 1

        if event == '_AUTO_MODE_':
            IsManu = 0


        if event == '_CONFIG3_OK_':

            value_dict["itpower"] = []
            value_dict["itdpower"] = []
            value_dict["rpower1"] = []
            value_dict["freq1"] = []

            try:
                value_dict["itpower"].append(int(values['_ITPOWER1_']))
                value_dict["itpower"].append(int(values['_ITPOWER2_']))
                value_dict["itpower"].append(int(values['_ITPOWER3_']))
                value_dict["itpower"].append(int(values['_ITPOWER4_']))
                value_dict["itpower"].append(int(values['_ITPOWER5_']))

                value_dict["itdpower"].append(int(values['_ITDPOWER1_']))
                value_dict["itdpower"].append(int(values['_ITDPOWER2_']))
                value_dict["itdpower"].append(int(values['_ITDPOWER3_']))
                value_dict["itdpower"].append(int(values['_ITDPOWER4_']))
                value_dict["itdpower"].append(int(values['_ITDPOWER5_']))

                value_dict["freq1"].append(int(values['_FREQ1_']))
                value_dict["rpower1"].append(int(values['_RPOWER1_']))

                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)

                sg.popup("Configured!")

            except:
                sg.popup('Please check the fields')



        """
        MANUAL INPUT TEST WINDOWS
        """

        if event == '_ONSET_OK_':

            value_dict["power3"] = []
            value_dict["rpower"] = []

            try:

                value_dict["power3"].append(int(values['_POWER3_']))
                value_dict["rpower"].append(int(values['_RPOWER_']))
                window.FindElement('_MANU_FRAME_').Update(visible=True)
                Manual_Gen_ON(value_dict['power3'][0], value_dict['rpower'][0])

            except:
                sg.popup("Please check the fields!")

        if event == '_OFFSET_OK_':

            try:
                window.FindElement('_MANU_FRAME_').Update(visible=True)
                Manual_Gen_OFF()

            except:
                sg.popup("Please check the fields!")


# try:
init()  # Initialize the generator
main()  # Main generator program

# except:
# sg.popup("Check the generator connection")
