"""

AUTOMATION CONTROL CODE - NETWORK ANALYZER WITH SWITCH, GENERATOR and PUMPS (Peristaltic and isocratic) - V3 - 2021

Atlantic Cancer Research Institute - ACRI

Code originally written by André LeBlanc, electrical engineering student at l'Université de Moncton
April 2021

NOTE 1: ALL USB cables need to be connected to the host PC prior to running the code. Otherwise code will show an error.
NOTE 2: Prior to running the code, assure that the switchs' USB driver is in its correct format (lib32).
"""

import pyvisa
from lucidIo.LucidControlAO4 import LucidControlAO4
from lucidIo.Values import ValueVOS4
import PySimpleGUI as sg
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import relay_ft245r
import sys
import os
import time

"""
************************************************
**************** GLOBAL OBJECTS ****************
************************************************
"""

"""
SWITCH
"""
rb = relay_ft245r.FT245R()
dev_list = rb.list_dev()

"""
NETWORK ANALYZER
"""
# Create a ressource manager
rm = pyvisa.ResourceManager()
rm.list_resources()

# Open the Network analyzer by name
analyzer = rm.open_resource('USB0::0x2A8D::0x0001::MY55201231::0::INSTR')

"""
GENERATOR
"""
UNIT = 0x01  # Set the generator slave address

# COM varies from generator to generator
client = ModbusClient(method='rtu', port='COM5', timeout=4, baudrate=115200, strict=False)

"""
*******************************************
**************** FUNCTIONS ****************
*******************************************
"""

"""
INITS
"""
def init():
    print("\n------------------CODE INITIALISATIONS------------------\n\n")
    """
    1. GENERATOR INIT
    """
    client.set_parity = 0
    client.set_bytesize = 8
    client.set_stopbits = 1
    client.connect()
    print("Generator connected \n")

    # TIMEOUT ( Must be greater than Power_ON_time !!!)
    client.write_register(98, 3000, unit=UNIT)

    # RESET FAULT : set bit 7 of register 2 to 1 and then to 0
    # (see page 19 of Microwave generator documentation --> Cabinet 18, room 455, IARC)
    client.write_register(2, 0x80, unit=UNIT)

    # RESET FAULT: set bit 7 of register 2 back to 0
    # TURN GENERATOR OFF (default state) : set register 2, bit 6 to
    client.write_register(2, 0x00, unit=UNIT)
    print("Faults reseted\n")
    print("Microwave is turned off for its initial state \n")

    # GENERATOR STARTING MODE TO NORMAL : set registor 3 bit 0 to 0
    client.write_register(3, 0x00, unit=UNIT)

    """
    2. SWITCH INIT
    """

    switch1 = 2
    switch2 = 3

    # list of FT245R devices are returned
    if len(dev_list) == 0:
        print('No FT245R devices found')
        sys.exit()

    # Show their serial numbers
    for dev in dev_list:
        print(dev.serial_number)

    # Pick the first one for simplicity
    dev = dev_list[0]
    # print('Using device with serial number ' + str(dev.serial_number))
    rb.connect(dev)

    # Place switch in state I for its initial state
    rb.switchon(switch1)
    rb.switchoff(switch2)

    """
    3. NETWORK ANALYZER INIT
    """
    # Set the time for 10s
    analyzer.timeout = 15000  # essayer des delay entre les commande

    # Return the Analyzer'ID string to tell us it's connected
    print(analyzer.query('*IDN?'))

    # CHANNEL 1 INITIALISATION
    analyzer.write(":CALCulate1:PARameter:COUNt 1")
    analyzer.write("calculate1:measure1:format smith")
    analyzer.write("CALCulate1:MEASure1:PARameter 'S11'")  # Define the parameter for each trace = s11 pour le channel 1


"""
NORMAL TEST FUNCTION
"""
def Normal_Test(startFreq, stopFreq, datapoints, BW, num_its, ONdelay, OFFdelay, directory, switch1, switch2, freq,
                power, rpower, Peris_ON, RPM, Iso_ON):
    print("------------------NORMAL TEST------------------\n")
    time.sleep(2)
    print("The test will begin in 3 seconds\n")
    time.sleep(3)

    # Update next step text color on GUI window
    window.find_element('_NORMAL2_').update(text_color='red')
    sg.OneLineProgressMeter('Test progress...', 1, 2 * num_its + 4, key='METER1', grab_anywhere=True)

    """
    1. NETWORK ANALYZER SET
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
    analyzer.write("SENS1:SWE:TIME " + str(OFFdelay))

    # DELAY WITH CORRECTION (TO ASSURE ALL DATA IS MEASURED IN FREQUENCY SWEEP)
    delay_with_corr_OFF = OFFdelay + OFFdelay / 4
    delay_with_corr_ON = ONdelay + ONdelay / 4

    # CHANNEL 1 PUT ON HOLD MODE FOR ITS DEFAULT TRIGGER STATE
    analyzer.write("SENS1:SWE:MODE HOLD")

    filename = directory

    try:
        analyzer.write("mmemory:mdirectory 'D:/" + filename + "'")
        print("D: drive folder created \n")

    except:
        print("D: folders weren't created.\n")

    """
    2. GENERATOR SET
    """
    # RESET COMMUNICATION TIMEOUT ( Must be greater than Power_ON_time !!!)
    # Function : register 98 set to X time before generator is faulted (red light on generator)
    client.write_register(98, 3000, unit=UNIT)

    # SET FREQUENCY
    # See page 31 of microwave generator user manual for more information (Cabinet 18, room 455, IARC)
    freqKHz = freq * 10
    client.write_register(9, freqKHz, unit=UNIT)
    rr = client.read_holding_registers(112, 1, unit=UNIT)
    rr1 = rr.registers
    print("Generator frequency is set to :" + str(rr1) + " Hz \n")

    # REFLECTED POWER LIMITATION MODE - ON
    client.write_register(2, 0x10, unit=UNIT)
    print("Reflected power limitation mode activated \n")

    # REFLECTED POWER SET
    # Value = 30% of transmitted power OR Manual selected value (See generator user manual for more details, cabinet 18, room 455, IARC)
    auto_rpower = 0.25 * power
    if int(rpower) != 0:
        client.write_register(1, int(rpower), unit=UNIT)
        rr = client.read_holding_registers(1, 1, unit=UNIT)
        rr1 = rr.registers
        print("Reflected power set to " + str(rr1) + " W \n")
    else:
        client.write_register(1, int(auto_rpower), unit=UNIT)
        rr = client.read_holding_registers(1, 1, unit=UNIT)
        rr1 = rr.registers
        print("Reflected power set to " + str(rr1) + " W \n")

    # TRANSMITTED POWER SET
    client.write_register(0, power, unit=UNIT)
    print("Transmitted power value set \n")

    # TURN GENERATOR OFF (default state)
    client.write_register(2, 0x00, unit=UNIT)
    print("Microwave is turned off for its initial state \n")

    """
    3. Peristaltic pump set
    """
    if Peris_ON == 1:
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
    4. Isocratic pump set
    """
    if Iso_ON == 1:
        sg.popup("Please wait 40 seconds for isocratic pump to initialise. Once done, enter desired flow speed in command prompt. Press Okay to continue.")
        os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY.exe")
        # window.findElement('_TEST_FRAME_').update(Visible=True)

    """
    TEST RUN
    """
    print("---------------------START TEST---------------------")

    for i in range(num_its + 1):
        if i == 0:

            # ------------- DUMP FIRST MEASUREMENT - SWITCH INIT -------------#
            # Update next step text color on GUI window
            window.find_element('_NORMAL2_').update(text_color='black')
            window.find_element('_NORMAL3_').update(text_color='red')
            sg.OneLineProgressMeter('Test progress...', 2, 2 * num_its + 4, key='METER1', grab_anywhere=True)

            # INITIALISE PROGRESS BAR
            print("\nDumping first measurement. Please wait.\n")

            # DUMP FIRST MEASUREMENT. ALWAYS GIVES UNVALID RESULT EVEN WHEN PROBE CALIBRATED.
            rb.switchon(switch1)
            rb.switchoff(switch2)

            # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
            time.sleep(0.04)

            analyzer.write("SENS1:SWE:MODE SINGLE")
            analyzer.write("TRIGger:SCOPe CURRent")
            analyzer.write("INITiate1:IMMediate")
            time.sleep(delay_with_corr_OFF)

            # PLACE SWITCH IN POSITION II (50 Ohm terminator)
            rb.switchon(switch2)
            rb.switchoff(switch1)
            time.sleep(delay_with_corr_ON)

            # Turn isocratic pump ON for remainder of test (if Iso_ON = 1)
            if Iso_ON == 1:
                window.find_element('_NORMAL8_').update(text_color='red')
                os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")


        else:

            print("\nITERATION " + str(i) + "\n")

            # ------------- STATE I - DIELECTRIC MEASUREMENT -------------#
            # Update next step text color on GUI window
            window.find_element('_NORMAL3_').update(text_color='black')
            window.find_element('_NORMAL5_').update(text_color='red')
            window.find_element('_NORMAL6_').update(text_color='black')
            sg.OneLineProgressMeter('Test progress...', 2 * i + 1, 2 * num_its + 4, key='METER1', grab_anywhere=True)

            # CHECK IF REFLECTED POWER VALUE READ IS GREATER THEN 30% OF TRANSMITTED POWER.
            rr = client.read_holding_registers(103, 1, unit=UNIT)
            rr_rpower = str(rr.registers)
            if int(rr_rpower[1]) > auto_rpower and rpower == 0:
                sg.popup("The reflected power is too high.\n The code will shutdown automatically.\n Rerun the code if you desire retrying the test.")
                sys.exit()

            # MICROWAVES OFF
            client.write_register(2, 0x00, unit=UNIT)
            print("Microwaves OFF")

            # PLACE SWITCH IN POSITION I (Dielectric measurement)
            rb.switchon(switch1)
            rb.switchoff(switch2)
            print("Switch in position I (Dielectric measurements)")

            # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
            time.sleep(0.04)

            # TURN PERISTALTIC PUMP OFF
            if Peris_ON == 1:
                window.find_element('_NORMAL9_').update(text_color='red')
                values[1].setVoltage(5.00)
                ao4.setIoGroup(channels, values)
                print("Peristaltic pump turned OFF\n")

            # PUT ISOCRATIC PUMP ON STANDBY
            # if Iso_ON == 1:
            # os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY1.exe")

            # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
            analyzer.write("SENS1:SWE:MODE SINGLE")
            analyzer.write("TRIGger:SCOPe CURRent")
            analyzer.write("INITiate1:IMMediate")
            analyzer.write("MMEMory:STORe:DATA '" + filename + "/Iteration" + str(
                i) + ".csv', 'CSV formatted Data','Trace','RI', 1")

            # WAIT WHILE MEASUREMENTS ARE BEING TAKEN
            time.sleep(delay_with_corr_OFF)



            # ------------- STATE II - MICROWAVE EMISSION -------------#
            # Update next step text color on GUI window
            window.find_element('_NORMAL5_').update(text_color='black')
            window.find_element('_NORMAL6_').update(text_color='red')
            sg.OneLineProgressMeter('Test progress...', 2 * i + 2, 2 * num_its + 4, key='METER1', grab_anywhere=True)

            # PLACE SWITCH IN POSITION II (50 Ohm terminator)
            rb.switchon(switch2)
            rb.switchoff(switch1)
            print("Switch in position II (Microwave ablation)")

            # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ablation probe (see switch datasheet for more details)
            time.sleep(0.04)

            # MICROWAVES ON
            client.write_register(2, 0x50, unit=UNIT)
            print("Microwaves ON")

            # TURN PERISTALTIC PUMP ON
            if Peris_ON == 1:
                voltage = RPM / 40
                # CH0 = SPEED CONTROL
                values[0].setVoltage(voltage)
                # TURN PERISTALTIC PUMP ON
                values[1].setVoltage(0.00)

                ao4.setIoGroup(channels, values)
                print("Peristaltic pump turned ON\n")
                window.find_element('_NORMAL9_').update(text_color='black')

            # PUT ISOCRATIC PUMP IN ON STATE
            # if Iso_ON == 1:
            # os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")

            # WAIT WHILE GENERATOR IS EMITTING MICROWAVES
            time.sleep(delay_with_corr_ON)


    # -------- END OF NORMAL TEST - END STATES ---------- #
    # Update next step text color on GUI window
    window.find_element('_NORMAL5_').update(text_color='black')
    window.find_element('_NORMAL6_').update(text_color='black')
    window.find_element('_NORMAL7_').update(text_color='red')
    window.find_element('_NORMAL8_').update(text_color='black')
    window.find_element('_NORMAL9_').update(text_color='black')
    sg.OneLineProgressMeter('Test progress...', 2 * num_its + 3, 2 * num_its + 4, key='METER1', grab_anywhere=True)

    # TURN MICROWAVES OFF FOR ITS DEFAULT END STATE
    client.write_register(2, 0x00, unit=UNIT)

    # PLACE SWITCH IN POSITION I FOR ITS DEFAULT END STATE
    rb.switchon(switch1)
    rb.switchoff(switch2)

    # TURN PERISTALTIC MOTOR OFF FOR ITS DEFAULT END STATE
    if Peris_ON == 1:
        values[0].setVoltage(0.00)
        values[1].setVoltage(5.00)
        print("Peristaltic pump turned OFF\n")
        ao4.setIoGroup(channels, values)

    # TURN ISOCRATIC PUMP OFF FOR ITS DEFAULT END STATE
    if Iso_ON == 1:
        os.system("C:/Windows\Licop\LicopDemo\PumpOFF.exe")

    # Print end of test message
    print("\n------- The test is complete! Select another test or press QUIT from the drop down menu to exit. ------- \n\n")

    client.close()

    # Update next step text color on GUI window
    time.sleep(2)
    window.find_element('_NORMAL7_').update(text_color='black')
    sg.OneLineProgressMeter('Test progress...', 2 * num_its + 4, 2 * num_its + 4, key='METER1', grab_anywhere=True)


"""
FREQUENCY SCAN SWEEP FUNCTION
"""
# AUTOMATIC FREQUENCY SWEEP MODE. SEE GENERATOR USER MANUAL FOR MORE INFO. PAGE 15. CABINET 17/18.
# TODO Fix problem with EndOfScan bit for automatic mode
def Freq_sweep(startFreqAna, stopFreqAna, datapoints, BW, directory, powersweep, rpower, ONdelay, OFFdelay, startfreq, stopfreq,
               stepfreq, IsManu, switch1, switch2, Peris_ON, RPM, Iso_ON):
    # MANUAL MODE
    if IsManu:
        print("------------------MANUAL SWEEP TEST------------------\n")
        time.sleep(2)
        # Initial delay prior to start of test
        print("The test will begin in 3 seconds\n")
        time.sleep(3)

        count = 0

        num_its = int(((stopfreq - startfreq) / stepfreq) + 1)

        # Update next step text color on GUI window
        window.find_element('_SWEEP2_').update(text_color='red')
        sg.OneLineProgressMeter('Test progress...', 1, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        """
        1. NETWORK ANALYZER INIT
        """
        # CONVERSION DE FRÉQUENCE DE MHZ À HZ
        startFreqAnaHz = startFreqAna * 1000000
        stopFreqAnaHz = stopFreqAna * 1000000
        # Set channel 1 freq and numpoint
        analyzer.write("SENS1:SWE:POIN " + str(datapoints))
        analyzer.write("SENS1:FREQ:START " + str(startFreqAnaHz))
        analyzer.write("SENS1:FREQ:STOP " + str(stopFreqAnaHz))
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
        startFreqRead = analyzer.read()
        analyzer.write("SENS1:FREQ:STOP?")
        stopFreqRead = analyzer.read()
        print("Analyzer start frequency (Channel 1) = \n" + startFreqRead + "\n" + "Stop frequency (Channel 1) = \n" + stopFreqRead)

        # SET FREQUENCY SWEEP TIME (MINIMUM DELAY FOR REAL TIME APPLICATION)
        analyzer.write("SENS1:SWE:TIME " + str(OFFdelay))

        # DELAY WITH CORRECTION (TO ASSURE ALL DATA IS MEASURED IN FREQUENCY SWEEP)
        delay_with_corr_OFF = OFFdelay + OFFdelay / 4
        delay_with_corr_ON = ONdelay + ONdelay / 4

        # CHANNEL 1 PUT ON HOLD MODE FOR ITS DEFAULT TRIGGER STATE
        analyzer.write("SENS1:SWE:MODE HOLD")

        filename = directory

        try:
            analyzer.write("mmemory:mdirectory 'D:/" + filename + "'")
            print("D: drive folder created \n")

        except:
            print("D: folders weren't created.\n")

        """
        2. GENERATOR INIT
        """
        # TIMEOUT ( Must be greater than Power_ON_time !!!)
        client.write_register(98, 3000, unit=UNIT)

        # SET START FREQUENCY
        # (24500 meaning = 24500 x 100 KHz = 2.45 Ghz)
        # See page 31 of microwave generator user manual for more information (Cabinet 18, room 455, IARC)
        startfreqKHz = startfreq * 10
        stopfreqKHz = stopfreq * 10
        stepfreqKHz = stepfreq * 10
        client.write_register(9, int(startfreqKHz), unit=UNIT)
        rr1 = client.read_holding_registers(9, 1, unit=UNIT)
        rq1 = rr1.registers

        # REFLECTED POWER LIMITATION MODE - ON
        client.write_register(2, 0x10, unit=UNIT)
        print("Reflected power limitation mode activated \n")

        # REFLECTED POWER SET
        # Value = 30% of transmitted power OR Manual selected value (See generator user manual for more details, cabinet 18, room 455, IARC)
        auto_rpower = 0.25 * powersweep
        if int(rpower) != 0:
            client.write_register(1, int(rpower), unit=UNIT)
            rr = client.read_holding_registers(1, 1, unit=UNIT)
            rr1 = rr.registers
            print("Reflected power set to " + str(rr1) + " W \n")
        else:
            client.write_register(1, int(auto_rpower), unit=UNIT)
            rr = client.read_holding_registers(1, 1, unit=UNIT)
            rr1 = rr.registers
            print("Reflected power set to " + str(rr1) + " W \n")

        # TRANSMITTED POWER SET:
        client.write_register(0, int(powersweep), unit=UNIT)
        print("Forward power set point set \n\n\n")

        """
        3. Peristaltic pump set
        """
        if Peris_ON == 1:
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
        4. Isocratic pump set
        """
        if Iso_ON == 1:
            sg.popup("Please wait 40 seconds for isocratic pump to initialise. Once done, enter desired flow speed in command prompt. Press Okay to continue")
            os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY.exe")
            # window.findElement('_SWEEP_FRAME_').update(Visible=True)



        currentfreqKHz = startfreqKHz
        print("\n-------------START TEST-------------\n")
        print("Start frequency set to" + str(rq1) + "KHz\n")


        # ------------- DUMP FIRST MEASUREMENT - SWITCH INIT -------------#
        # Update next step text color on GUI window
        window.find_element('_SWEEP2_').update(text_color='black')
        window.find_element('_SWEEP3_').update(text_color='red')
        sg.OneLineProgressMeter('Test progress...', 2, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        # INITIALISE PROGRESS BAR
        print("\nDumping first measurement. Please wait.\n")

        # DUMP FIRST MEASUREMENT. ALWAYS GIVES UNVALID RESULT EVEN WHEN PROBE CALIBRATED.
        rb.switchon(switch1)
        rb.switchoff(switch2)

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
        time.sleep(0.04)

        analyzer.write("SENS1:SWE:MODE SINGLE")
        analyzer.write("TRIGger:SCOPe CURRent")
        analyzer.write("INITiate1:IMMediate")
        time.sleep(delay_with_corr_OFF)

        # PLACE SWITCH IN POSITION II (50 Ohm terminator)
        rb.switchon(switch2)
        rb.switchoff(switch1)
        time.sleep(delay_with_corr_ON)


        # Turn isocratic pump ON (if Iso_ON = 1)
        if Iso_ON == 1:
            window.find_element('_SWEEP8_').update(text_color='red')
            os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")


        while currentfreqKHz <= stopfreqKHz:

            # ------------- STATE II - MICROWAVE EMISSION -------------#
            # Update next step text color on GUI window
            window.find_element('_SWEEP3_').update(text_color='black')
            window.find_element('_SWEEP5_').update(text_color='red')
            window.find_element('_SWEEP6_').update(text_color='black')
            sg.OneLineProgressMeter('Test progress...', 2 * (count + 1) + 1, 2 * num_its + 4, key='METER1',
                                    grab_anywhere=True)

            # TURN MICROWAVE ON
            # Place switch in position II (A-D)
            rb.switchon(switch2)
            rb.switchoff(switch1)

            # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
            time.sleep(0.04)

            # MICROWAVES ON
            client.write_register(2, 0x50, unit=UNIT)
            print("Microwaves ON for " + str(ONdelay) + " seconds")

            # TURN PERISTALTIC PUMP ON
            if Peris_ON == 1:
                window.find_element('_SWEEP9_').update(text_color='black')

                voltage = RPM / 40
                # CH0 = SPEED CONTROL
                values[0].setVoltage(voltage)
                # TURN PERISTALTIC PUMP ON
                values[1].setVoltage(0.00)

                ao4.setIoGroup(channels, values)
                print("Peristaltic pump turned ON\n")

            # PUT ISOCRATIC PUMP IN ON STATE
            # if Iso_ON == 1:
            # os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")

            # wait micro_time seconds
            time.sleep(delay_with_corr_ON)

            # ------------- STATE I - DIELECTRIC MEASUREMENT -------------#
            # Update next step text color on GUI
            window.find_element('_SWEEP5_').update(text_color='black')
            window.find_element('_SWEEP6_').update(text_color='red')
            sg.OneLineProgressMeter('Test progress...', 2 * (count + 1) + 2, 2 * num_its + 4, key='METER1',
                                    grab_anywhere=True)

            # CHECK IF REFLECTED POWER VALUE READ IS GREATER THEN 30% OF TRANSMITTED POWER.
            rr = client.read_holding_registers(103, 1, unit=UNIT)
            rr_rpower = str(rr.registers)
            if int(rr_rpower[1]) > auto_rpower and rpower == 0:
                sg.popup("The reflected power is too high.\n The code will shutdown automatically.\n Rerun the code if you desire retrying the test.")
                sys.exit()

            # TURN MICROWAVE OFF
            # Place switch in position I (A-B)
            client.write_register(2, 0x00, unit=UNIT)
            print("Microwave turned off for " + str(OFFdelay) + " seconds")

            rb.switchon(switch1)
            rb.switchoff(switch2)

            # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
            time.sleep(0.04)

            # TURN PERISTALTIC PUMP OFF
            if Peris_ON == 1:
                window.find_element('_SWEEP9_').update(text_color='red')

                values[1].setVoltage(5.00)
                ao4.setIoGroup(channels, values)
                print("Peristaltic pump turned OFF\n")

            # PUT ISOCRATIC PUMP ON STANDBY
            # if Iso_ON == 1:
            # os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY1.exe")

            # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
            analyzer.write("SENS1:SWE:MODE SINGLE")
            analyzer.write("TRIGger:SCOPe CURRent")
            analyzer.write("INITiate1:IMMediate")
            analyzer.write("MMEMory:STORe:DATA '" + filename + "/Iteration" + str(
                count + 1) + ".csv', 'CSV formatted Data','Trace','RI', 1")

            # Microwave off for input value seconds (while ENA is taking measurements)
            time.sleep(delay_with_corr_OFF)

            # ------------- INCREMENT FREQUENCY -------------#

            currentfreqKHz += stepfreqKHz
            if currentfreqKHz == 2.5E9 or currentfreqKHz > stopfreqKHz:
                break
            else:
                client.write_register(9, int(currentfreqKHz), unit=UNIT)
                rr1 = client.read_holding_registers(112, 1, unit=UNIT)
                rq1 = rr1.registers
                print("New generator frequency set to :" + str(rq1) + "KHz ")
                count += 1


        # -------- END OF SWEEP MANUAL TEST - END STATES ---------- #
        # Update next step text color on GUI window
        window.find_element('_SWEEP5_').update(text_color='black')
        window.find_element('_SWEEP6_').update(text_color='black')
        window.find_element('_SWEEP7_').update(text_color='red')
        window.find_element('_SWEEP8_').update(text_color='black')
        window.find_element('_SWEEP9_').update(text_color='black')
        sg.OneLineProgressMeter('Test progress...', 2 * num_its + 3, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        # TURN MICROWAVES OFF FOR ITS DEFAULT END STATE
        client.write_register(2, 0x00, unit=UNIT)

        # PLACE SWITCH IN POSITION I FOR ITS DEFAULT END STATE
        rb.switchon(switch1)
        rb.switchoff(switch2)

        # TURN PERISTALTIC MOTOR OFF FOR ITS DEFAULT END STATE
        if Peris_ON == 1:
            values[0].setVoltage(0.00)
            values[1].setVoltage(5.00)
            ao4.setIoGroup(channels, values)

        # TURN ISOCRATIC PUMP OFF FOR ITS DEFAULT END STATE
        if Iso_ON == 1:
            os.system("C:/Windows\Licop\LicopDemo\PumpOFF.exe")

        # Update next step text color on GUI window
        time.sleep(2)
        window.find_element('_SWEEP7_').update(text_color='black')
        sg.OneLineProgressMeter('Test progress...', 2 * num_its + 4, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        # Print end of test message
        print(
            "\n------- The test is complete! Select another test or press QUIT from the drop down menu to exit. ------- \n\n")

    # AUTOMATIC MODE
    if not IsManu:
        print("------------------AUTOMATIC SWEEP TEST------------------\n")
        time.sleep(2)
        # Initial delay prior to start of test
        print("The test will begin in 3 seconds\n")
        time.sleep(3)

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
        print("Frequency step set to:\n" + str(rq3) + "MHz\n")

        # ACTIVATE SCAN MODE - SET SCAN MODE BIT TO 1
        client.write_register(17, 1, unit=UNIT)
        # rr = client.read_holding_registers(17, 1, unit=UNIT)
        # rq = rr.registers
        # print(rq)

        # REFLECTED POWER LIMITATION MODE - ON
        client.write_register(2, 0x10, unit=UNIT)

        # REFLECTED POWER SET
        client.write_register(1, 20, unit=UNIT)

        # TRANSMITTED POWER SET
        client.write_register(0, int(powersweep), unit=UNIT)

        # GENERATOR ON
        # Switch position II
        rb.switchon(switch2)
        rb.switchoff(switch1)

        client.write_register(2, 0x50, unit=UNIT)
        print("Generator turned ON\n")
        """
        """

        while True:
            rr = client.read_holding_registers(105, 1, unit=UNIT)
            rq = rr.registers
            print("End of scan response is: " + str(rq))
            time.sleep(2)

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
            time.sleep(5)
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
                time.sleep(0.1)
                break

        # Turn generator OFF for its default end state
        # Place switch in position I (A-B) for its default end state
        client.write_register(2, 0x00, unit=UNIT)
        rb.switchon(switch1)
        rb.switchoff(switch2)

        client.close()
        print("The Sairem automatic frequency sweep test is complete!\n\n")


"""
MANUAL GENERATOR ON FUNCTION
"""
# GENERATOR + SWITCH ONLY
def Manual_Gen_ON(power_man, rpower, switch1, switch2):
    # Place switch in position II (A-D)
    rb.switchon(switch2)
    rb.switchoff(switch1)

    # TIMEOUT (30 seconds)
    client.write_register(98, 3000, unit=UNIT)

    # SET FREQUENCY
    freq = 24500
    client.write_register(9, freq, unit=UNIT)

    # REFLECTED POWER LIMITATION MODE - ON
    client.write_register(2, 0x10, unit=UNIT)

    # REFLECTED POWER SET
    # Value = 30% of transmitted power OR Manual selected value (See generator user manual for more details, cabinet 18, room 455, IARC)
    auto_rpower = 0.25 * power_man
    if int(rpower) != 0:
        client.write_register(1, int(rpower), unit=UNIT)
        rr = client.read_holding_registers(1, 1, unit=UNIT)
        rr1 = rr.registers
        print("Reflected power set to " + str(rr1) + " W \n")
    else:
        client.write_register(1, int(auto_rpower), unit=UNIT)
        rr = client.read_holding_registers(1, 1, unit=UNIT)
        rr1 = rr.registers
        print("Reflected power set to " + str(rr1) + " W \n")

    # TRANSMITTED POWER SET
    client.write_register(0, power_man, unit=UNIT)

    # GENERATOR ON
    client.write_register(2, 0x50, unit=UNIT)
    print("Generator turned ON\n")

    # Update dynamic text display
    window.find_element('OFFSETTEXT').update(text_color='black')
    window.find_element('ONSETTEXT').update(text_color='red')


"""
MANUAL GENERATOR OFF FUNCTION
"""
# GENERATOR + SWTICH ONLY
def Manual_Gen_OFF(switch1, switch2):
    # GENERATOR OFF
    client.write_register(2, 0x00, unit=UNIT)
    print("Generator turned OFF\n")

    # Update dynamic text display
    window.find_element('OFFSETTEXT').update(text_color='red')
    window.find_element('ONSETTEXT').update(text_color='black')

    # Place switch in position I (A-B)
    rb.switchon(switch1)
    rb.switchoff(switch2)


"""
MANUAL ENA TRIGGER FUNCTION
"""
# ENA + SWITCH ONLY
def Manual_ENA_Trigger(startFreq, stopFreq, datapoints, BW, delay, directory, switch1, switch2):
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
    analyzer.write("SENS1:SWE:TIME " + str(delay))

    # DELAY WITH CORRECTION (TO ASSURE ALL DATA IS MEASURED IN FREQUENCY SWEEP)
    delay_with_corr = delay + delay / 4

    # CHANNEL 1 PUT ON HOLD MODE FOR ITS DEFAULT TRIGGER STATE
    analyzer.write("SENS1:SWE:MODE HOLD")

    filename = directory

    try:
        analyzer.write("mmemory:mdirectory 'D:/" + filename + "'")
        print("D: drive folder created \n")

    except:
        print("D: folders weren't created.\n")

    # Place switch in position I (A-B)
    rb.switchon(switch1)
    rb.switchoff(switch2)

    # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from dielectric probe (see switch datasheet for more details)
    time.sleep(0.04)

    # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
    analyzer.write("SENS1:SWE:MODE SINGLE")
    analyzer.write("TRIGger:SCOPe CURRent")
    analyzer.write("INITiate1:IMMediate")
    analyzer.write(
        "MMEMory:STORe:DATA '" + filename + "/ENAManTrig_Result" + ".csv', 'CSV formatted Data','Trace','RI', 1")

    time.sleep(delay_with_corr)


"""
MANUAL PERISTALTIC AND ISOCRATIC PUMP CONTROL
"""
# PUMPS ONLY
def Manual_Pumps(Manu_Pumps_State, RPM, Manu_Iso_ON, Manu_Peris_ON):
    if Manu_Pumps_State == 1:
        sg.popup("Please wait 40 seconds for isocratic pump to initialise. Once done, enter desired flow speed in command prompt. Press Okay to continue")
        os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY.exe")
        os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")
        if Manu_Peris_ON == 1:
            window.find_element('_ALCOHOLON_').update(text_color='red')
            window.find_element('_ALCOHOLOFF_').update(text_color='black')
            window.find_element('_COOLINGON_').update(text_color='red')
            window.find_element('_COOLINGOFF_').update(text_color='black')
        else:
            window.find_element('_ALCOHOLON_').update(text_color='red')
            window.find_element('_ALCOHOLOFF_').update(text_color='black')
            window.find_element('_COOLINGON_').update(text_color='black')
            window.find_element('_COOLINGOFF_').update(text_color='red')

    if Manu_Pumps_State == 3:
        # PUMP INIT
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

        # SET RPM SPEED AND TURN ON PUMP
        voltage = RPM / 40
        # CH0 = SPEED CONTROL
        values[0].setVoltage(voltage)
        # TURN PERISTALTIC PUMP ON
        values[1].setVoltage(0.00)
        ao4.setIoGroup(channels, values)

        if Manu_Iso_ON == 1:
            window.find_element('_ALCOHOLON_').update(text_color='red')
            window.find_element('_ALCOHOLOFF_').update(text_color='black')
            window.find_element('_COOLINGON_').update(text_color='red')
            window.find_element('_COOLINGOFF_').update(text_color='black')
        else:
            window.find_element('_ALCOHOLON_').update(text_color='black')
            window.find_element('_ALCOHOLOFF_').update(text_color='red')
            window.find_element('_COOLINGON_').update(text_color='red')
            window.find_element('_COOLINGOFF_').update(text_color='black')

    if Manu_Pumps_State == 2:
        os.system("C:/Windows\Licop\LicopDemo\PumpOFF.exe")
        if Manu_Peris_ON == 1:
            window.find_element('_ALCOHOLON_').update(text_color='black')
            window.find_element('_ALCOHOLOFF_').update(text_color='red')
            window.find_element('_COOLINGON_').update(text_color='red')
            window.find_element('_COOLINGOFF_').update(text_color='black')
        else:
            window.find_element('_ALCOHOLON_').update(text_color='black')
            window.find_element('_ALCOHOLOFF_').update(text_color='red')
            window.find_element('_COOLINGON_').update(text_color='black')
            window.find_element('_COOLINGOFF_').update(text_color='red')

    if Manu_Pumps_State == 4:
        # PUMP INIT
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

        # TURN PUMP OFF
        # CH0 = SPEED CONTROL
        values[0].setVoltage(0.00)
        # TURN PERISTALTIC PUMP OFF
        values[1].setVoltage(5.00)
        ao4.setIoGroup(channels, values)

        if Manu_Iso_ON == 1:
            window.find_element('_ALCOHOLON_').update(text_color='red')
            window.find_element('_ALCOHOLOFF_').update(text_color='black')
            window.find_element('_COOLINGON_').update(text_color='black')
            window.find_element('_COOLINGOFF_').update(text_color='red')
        else:
            window.find_element('_ALCOHOLON_').update(text_color='black')
            window.find_element('_ALCOHOLOFF_').update(text_color='red')
            window.find_element('_COOLINGON_').update(text_color='black')
            window.find_element('_COOLINGOFF_').update(text_color='red')


"""
RESET GENERATOR FAULTS FUNCTION
"""
def Reset_Faults():
    # RESET FAULT : set bit 7 of register 2 to 1 and then to 0
    # (see page 19 of Microwave generator documentation --> Cabinet 18, room 455, IARC)
    client.write_register(2, 0x80, unit=UNIT)

    # RESET FAULT: set bit 7 of register 2 back to 0
    # TURN GENERATOR OFF (default state) : set register 2, bit 6 to
    client.write_register(2, 0x00, unit=UNIT)
    print("\nFaults Reseted\n")
    sg.popup("Fault reseted")


"""
FIVE ITERATION TEST FUNCTION
"""
def Five_Iteration_Test(startFreq, stopFreq, datapoints, BW, directory, switch1, switch2, power, ONdelay, OFFdelay,
                        freq, rpower, i, Peris_ON, RPM, Iso_ON):
    # DELAY WITH CORRECTION (TO ASSURE ALL DATA IS MEASURED IN FREQUENCY SWEEP)
    delay_with_corr_ON = ONdelay + ONdelay / 4
    delay_with_corr_OFF = OFFdelay + OFFdelay / 4

    filename = directory

    num_its = 5

    auto_rpower = 0.25 * power

    """
    Peristaltic pump set
    """
    if Peris_ON == 1:
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

    if i == 1:

        print("------------------FIVE ITERATION TEST------------------\n")
        time.sleep(2)
        # INITIAL DELAY
        print("\nThe test will begin in 3 seconds\n")
        time.sleep(3)

        # Update next step text color on GUI window
        window.find_element('_FIVEIT2_').update(text_color='red')
        sg.OneLineProgressMeter('Test progress...', 1, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        """
        1. NETWORK ANALYZER SET
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
        analyzer.write("SENS1:SWE:TIME " + str(OFFdelay))

        # CHANNEL 1 PUT ON HOLD MODE FOR ITS DEFAULT TRIGGER STATE
        analyzer.write("SENS1:SWE:MODE HOLD")

        try:
            analyzer.write("mmemory:mdirectory 'D:/" + filename + "'")
            print("D: drive folder created \n")

        except:
            print("D: folders weren't created.\n")

        """
        2. GENERATOR SET
        """
        # TIMEOUT ( Must be greater than Power_ON_time !!!)
        client.write_register(98, 3000, unit=UNIT)

        # FREQUENCY SET
        freq_KHz = freq * 10
        client.write_register(9, freq_KHz, unit=UNIT)
        print("Generator frequency is set to :\n" + str(freq) + " MHz\n")

        # REFLECTED POWER LIMITATION MODE ON
        client.write_register(2, 0x10, unit=UNIT)
        print("Reflected power limitation mode activated \n")

        # TURN GENERATOR OFF (default state)
        client.write_register(2, 0x00, unit=UNIT)
        print("Microwave is turned off for its initial state \n")

        """
        3. Isocratic pump set
        """
        if Iso_ON == 1:
            sg.popup("Please wait 40 seconds for isocratic pump to initialise. Once done, enter desired flow speed in command prompt. Press Okay to continue")
            os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY.exe")
            # window.findElement('_FIVEIT_FRAME_').update(Visible=True)


        print("\n---------------------START TEST---------------------\n")
        print("Initialising switch\n")


        # -------------- DUMP FIRST MEASUREMENT - SWITCH INIT ----------------#
        # Update next step text color on GUI window
        window.find_element('_FIVEIT2_').update(text_color='black')
        window.find_element('_FIVEIT3_').update(text_color='red')
        sg.OneLineProgressMeter('Test progress...', 2, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        print("\nDumping first measurement. Please wait.\n")

        # DUMP FIRST MEASUREMENT. ALWAYS GIVES UNVALID RESULT EVEN WHEN PROBE CALIBRATED.
        rb.switchon(switch1)
        rb.switchoff(switch2)

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
        time.sleep(0.04)

        analyzer.write("SENS1:SWE:MODE SINGLE")
        analyzer.write("TRIGger:SCOPe CURRent")
        analyzer.write("INITiate1:IMMediate")
        time.sleep(delay_with_corr_OFF)

        # PLACE SWITCH IN POSITION II (50 Ohm terminator)
        rb.switchon(switch2)
        rb.switchoff(switch1)
        time.sleep(delay_with_corr_ON)

        # Turn isocratic pump ON for remainder of test (if Iso_ON = 1)
        if Iso_ON == 1:
            window.find_element('_FIVEIT8_').update(text_color='red')
            os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")


    else:
        """
        RUN TEST
        """

        print("\nITERATION " + str(i - 1) + "\n")


        # ------------- STATE II - MICROWAVE ABLATION -------------#
        # Update next step text color on GUI window
        window.find_element('_FIVEIT3_').update(text_color='black')
        window.find_element('_FIVEIT5_').update(text_color='red')
        window.find_element('_FIVEIT6_').update(text_color='black')
        sg.OneLineProgressMeter('Test progress...', 2 * (i - 1) + 1, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        # TRANSMITTED POWER SET
        client.write_register(0, int(power), unit=UNIT)
        print("Microwave output power set to: \n" + str(power) + " Watts\n")

        # REFLECTED POWER SET
        # Value = 30% of transmitted power OR Manual selected value (See generator user manual for more details, cabinet 18, room 455, IARC)
        if int(rpower) != 0:
            client.write_register(1, int(rpower), unit=UNIT)
            rr = client.read_holding_registers(1, 1, unit=UNIT)
            rr1 = rr.registers
            print("Reflected power set to " + str(rr1) + " W \n")

        else:
            client.write_register(1, int(auto_rpower), unit=UNIT)
            rr = client.read_holding_registers(1, 1, unit=UNIT)
            rr1 = rr.registers
            print("Reflected power set to " + str(rr1) + " W \n")

        # TURN PERISTALTIC PUMP ON
        if Peris_ON == 1:
            window.find_element('_FIVEIT9_').update(text_color='black')
            voltage = RPM / 40
            # CH0 = SPEED CONTROL
            values[0].setVoltage(voltage)
            # TURN PERISTALTIC PUMP ON
            values[1].setVoltage(0.00)
            ao4.setIoGroup(channels, values)
            print("Peristaltic pump turned ON")

        # PUT ISOCRATIC PUMP IN ON STATE
        # if Iso_ON == 1:
            # os.system("C:/Windows\Licop\LicopDemo\PumpON.exe")

        # MICROWAVES ON
        # Place switch in position II (AD , Microwave ablation)
        rb.switchon(switch2)
        rb.switchoff(switch1)

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
        time.sleep(0.04)

        client.write_register(2, 0x50, unit=UNIT)
        print("Switch in position II (Microwave ablation)")
        print("Microwaves ON for " + str(ONdelay) + " seconds\n")

        # DELAY OF INPUT VALUE SECONDS WITH CORRECTION
        time.sleep(delay_with_corr_ON)



        # ------------- STATE I - DIELECTRIC MEASUREMENT -------------#
        # Update next step text color on GUI window
        window.find_element('_FIVEIT5_').update(text_color='black')
        window.find_element('_FIVEIT6_').update(text_color='red')
        sg.OneLineProgressMeter('Test progress...', 2 * (i - 1) + 2, 2 * num_its + 4, key='METER1', grab_anywhere=True)

        # CHECK IF REFLECTED POWER VALUE READ IS GREATER THEN 30% OF TRANSMITTED POWER.
        rr = client.read_holding_registers(103, 1, unit=UNIT)
        rr_rpower = str(rr.registers)
        if int(rr_rpower[1]) > auto_rpower and rpower == 0:
            sg.popup("The reflected power is too high.\n The code will shutdown automatically.\n Rerun the code if you desire retrying the test.")
            sys.exit()

        # MICROWAVES OFF
        # Place switch in position I (AB , Dielectric measurement)
        client.write_register(2, 0x00, unit=UNIT)
        rb.switchon(switch1)
        rb.switchoff(switch2)

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
        time.sleep(0.04)

        print("Microwaves OFF for " + str(OFFdelay) + " seconds")
        print("Switch in position I (Dielectric measurement)")

        if Peris_ON == 1:
            window.find_element('_FIVEIT9_').update(text_color='red')
            values[0].setVoltage(0.00)
            values[1].setVoltage(5.00)
            ao4.setIoGroup(channels, values)
            print("Peristaltic pump turned OFF\n")

        # PUT ISOCRATIC PUMP IN STANDBY STATE
        # if Iso_ON == 1:
            # os.system("C:/Windows\Licop\LicopDemo\PumpSTANDBY1.exe")

        print("\n")

        # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
        analyzer.write("SENS1:SWE:MODE SINGLE")
        analyzer.write("TRIGger:SCOPe CURRent")
        analyzer.write("INITiate1:IMMediate")
        analyzer.write("MMEMory:STORe:DATA '" + filename + "/Iteration" + str(
            i - 1) + ".csv', 'CSV formatted Data','Trace','RI', 1")

        # DELAY OF INPUT VALUE SECONDS WITH CORRECTION
        time.sleep(delay_with_corr_OFF)


        # ------------------------- END OF TEST, DEFAULT END STATES--------------------------------
        if i == 6:

            # Update next step text color on GUI window
            window.find_element('_FIVEIT5_').update(text_color='black')
            window.find_element('_FIVEIT6_').update(text_color='black')
            window.find_element('_FIVEIT7_').update(text_color='red')
            window.find_element('_FIVEIT8_').update(text_color='black')
            window.find_element('_FIVEIT9_').update(text_color='black')
            sg.OneLineProgressMeter('Test progress...', 2 * num_its + 3, 2 * num_its + 4, key='METER1',grab_anywhere=True)

            # MICROWAVES OFF FOR REDUNDENCY PURPOSES
            client.write_register(2, 0x00, unit=UNIT)

            # Place switch in position I for redundency purposes (AB)
            rb.switchon(switch1)
            rb.switchoff(switch2)

            # TURN PERISTALTIC PUMP OFF FOR ITS DEFAULT END STATE
            if Peris_ON == 1:
                values[0].setVoltage(0.00)
                values[1].setVoltage(5.00)
                print("Peristaltic pump turned OFF\n")
                ao4.setIoGroup(channels, values)

            # PUT ISOCRATIC PUMP IN OFF STATE FOR ITS DEFAULT END STATE
            if Iso_ON == 1:
                os.system("C:/Windows\Licop\LicopDemo\PumpOFF.exe")

            # Update next step text color on GUI window
            time.sleep(2)
            window.find_element('_FIVEIT7_').update(text_color='black')
            sg.OneLineProgressMeter('Test progress...', 2 * num_its + 4, 2 * num_its + 4, key='METER1',
                                    grab_anywhere=True)

            # Print end of test message
            print("\n------- The test is complete! Select another test or press QUIT from the drop down menu to exit. ------- \n\n")

            client.close()


"""
**********************************************
**************** UI INTERFACE ****************
**********************************************
"""

sg.ChangeLookAndFeel('BlueMono')

# MENU DEFINITION
menu_def = [['OPTIONS', ['CREATE', 'QUIT']]]

# INITIAL WINDOWS LAYOUTS
Init_layout = [
    [sg.Text('Parameter configuration', font=("Helvetica", 18), pad=(0, 5))],
    [sg.Submit(key='_ALLPARAMETERS_OK_', button_text='Select', font=("Helvetica", 18), pad=(0, 20))],
    [sg.Text('Tests and manual component control', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_TEST_OK_', font=("Helvetica", 18), button_text='Select', pad=(0, 20),
               auto_size_button=True)]]

Parameter_layout = [
    [sg.Text('Network Analyzer and # of iterations (ALL TESTS)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_ANA_OK_', button_text='Select', font=("Helvetica", 12), pad=(20, 20))],
    [sg.Text('Switch (ALL TESTS AND MANUAL COMPONENTS)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_SWITCH_OK_', font=("Helvetica", 12), button_text='Select', pad=(20, 20), auto_size_button=True)],
    [sg.Text('Generator and Delays (ALL TESTS)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_GEN_OK_', font=("Helvetica", 12), button_text='Select', pad=(20, 20), auto_size_button=True)],
    [sg.Text('Pumps (ALL TESTS)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_PERIS_OK_', button_text='Select', font=("Helvetica", 12), pad=(20, 20))],
    [sg.Cancel(key='_ALLPARAMETERS_CANCEL_', font=("Helvetica", 12), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]

Test_layout = [
    [sg.Text('TESTS', font=("Helvetica", 16), pad=(0, 5))],
    [sg.Text('Normal test', font=("Helvetica", 14), pad=(0, 5)),
     sg.Submit(key='_LAUNCH_OK_', button_text='Launch', font=("Helvetica", 14), pad=(40, 5))],
    [sg.Text('Five iteration test', font=("Helvetica", 14), pad=(0, 5)),
     sg.Submit(key='_TEST_OK3_', button_text='Select', font=("Helvetica", 14), pad=(40, 5))],
    [sg.Text('Sweep test', font=("Helvetica", 14), pad=(0, 5)),
     sg.Submit(key='_TEST_OK1_', button_text='Select', font=("Helvetica", 14), pad=(40, 5))],
    [sg.Text('MANUAL COMPONENT CONTROL', font=("Helvetica", 16), pad=(0, 5))],
    [sg.Text('Generator', font=("Helvetica", 14), pad=(0, 5)),
     sg.Submit(key='_TEST_OK2_', button_text='Select', font=("Helvetica", 14), pad=(40, 5)),
     sg.Text('Network Analyzer', font=("Helvetica", 14), pad=(0, 5)),
     sg.Submit(key='_TEST_OK4_', button_text='Select', font=("Helvetica", 14), pad=(40, 5))],
    [sg.Text('Pumps', font=("Helvetica", 14), pad=(0, 5)),
     sg.Submit(key='_TEST_OK5_', button_text='Select', font=("Helvetica", 14), pad=(40, 5))],
    [sg.Cancel(key='_TEST_CANCEL_', font=("Helvetica", 14), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# GENERATOR SETTINGS LAYOUT
gen_layout = [
    [sg.Text('Microwave power (W, must not leave blank for five it. test)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_POWER1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('ON delay duration (s, must not leave blank for five it. test)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ONDELAY1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('OFF delay duration (s, must not leave blank for five it. test)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_OFFDELAY1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_FREQ1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Reflected power (W, set to 0 if not configuring)', font=("Helvetica", 18), text_color='red', background_color='yellow'),
     sg.Input('', do_not_clear=True, key='_REFPOWER_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_SET_GEN_', font=("Helvetica", 18), button_text='Set other values', pad=(170, 10),
               auto_size_button=True),
     sg.Submit(key='_SET_RPOWER_', font=("Helvetica", 18), button_text='Set reflected power', pad=(170, 10),
               auto_size_button=True)
     ],
    [sg.Cancel(key='_GEN_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# NETWORK ANALYZER SETTINGS LAYOUT
Analyzer_layout = [
    [sg.Text('Frequencies, # of datapoints, bandwidth', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_FREQ_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Text('# of iterations & filename', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_PARAMS1_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Cancel(key='_ANA_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]

Freq_layout = [
    [sg.Text('Start frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2440', do_not_clear=True, key='_STARTFREQ_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Stop frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2460', do_not_clear=True, key='_STOPFREQ_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Number data points ', font=("Helvetica", 18)),
     sg.Input('101', do_not_clear=True, key='_NUMDATA_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Bandwidth (Hz)', font=("Helvetica", 18)),
     sg.Input('300', do_not_clear=True, key='_BW_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG2_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_FREQ_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]

Params1_layout = [
    [sg.Text('Number of test iterations (must not leave blank for five it. and sweep test)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_NUMITS_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Desired filename', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DIRECTORY_', size=(20, 30), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG1_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_PARAMS1_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]


# SWITCH SETTINGS LAYOUT
Switch_layout = [
    [sg.Text('Switch configurations', font=("Helvetica", 18), pad=(0, 5))],
    [sg.Submit(key='_PARAMS2_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Cancel(key='_SWITCH_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]

Params2_layout = [
    [sg.Text('Switch 1 (1 to 8) - State AB when ON', font=("Helvetica", 18)),
     sg.Input('2', do_not_clear=True, key='_SWITCH1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Switch 2 (1 to 8) - State AD when ON: ', font=("Helvetica", 18)),
     sg.Input('3', do_not_clear=True, key='_SWITCH2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG3_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_PARAMS2_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]


# PERISTALTIC PUMP LAYOUT
Peristaltic_layout = [
    [sg.Text('Cooling flow speed (RPM - set to 0 if not using)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPM_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Radio('COOLING ON', "RADIO2", default=False, change_submits=True, key="_PERIS_ON_", font=("Helvetica", 18),
              size=(15, 1), pad=(50, 10)),
     sg.Radio('COOLING OFF', "RADIO2", default=False, change_submits=True, key="_PERIS_OFF_",
              font=("Helvetica", 18), size=(15, 1), pad=(50, 10))],
    [sg.Radio('ALCOHOL ON', "RADIO3", default=False, change_submits=True, key="_ISO_ON_", font=("Helvetica", 18),
              size=(15, 1), pad=(50, 10)),
     sg.Radio('ALCOHOL OFF', "RADIO3", default=False, change_submits=True, key="_ISO_OFF_",
              font=("Helvetica", 18), size=(15, 1), pad=(50, 10))],
    [sg.Submit(key='_CONFIG7_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_PERIS_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# TEST - Frequency sweep scan selection layout
sweep_layout = [
    [sg.Text('Step frequency (MHz , min. 100 KHz, max. 10 MHz): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_STEPFREQ_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Start frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2400', do_not_clear=True, key='_STARTFREQ1_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Stop frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2500', do_not_clear=True, key='_STOPFREQ1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Radio('Manual mode', "RADIO1", default=False, change_submits=True, key="_MANU_MODE_", font=("Helvetica", 18),
              size=(10, 1), pad=(100, 10)),
     sg.Radio('Auto mode', "RADIO1", default=False, change_submits=True, key="_AUTO_MODE_", font=("Helvetica", 18),
              size=(10, 1), pad=(100, 10))],
    [sg.Submit(key='_CONFIG4_OK_', font=("Helvetica", 18), button_text='Configure', pad=(100, 10),
               auto_size_button=True),
     sg.Submit(key='_TEST2_OK_', font=("Helvetica", 18), button_text='Launch test', pad=(100, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_SWEEP_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)],
    [sg.Text('TEST EXECUTIONS', font=("Helvetica", 18), text_color='green', key='_SWEEP1_', pad=(10, 10))],
    [sg.Text('Initialisations', font=("Helvetica", 18), key='_SWEEP2_', pad=(10, 0))],
    [sg.Text('Dump first measurement', font=("Helvetica", 18), key='_SWEEP3_', pad=(10, 0))],
    [sg.Text('FOR LOOP', font=("Helvetica", 18), key='_SWEEP4_', pad=(10, 0))],
    [sg.Text('   Microwaves ON', font=("Helvetica", 18), key='_SWEEP5_', pad=(10, 0))],
    [sg.Text('   Microwaves OFF / Dielectric measurement', font=("Helvetica", 18), key='_SWEEP6_', pad=(10, 0))],
    [sg.Text('Test complete', font=("Helvetica", 18), key='_SWEEP7_', pad=(10, 0))],
    [sg.Text('', font=("Helvetica", 14), pad=(0, 0))],
    [sg.Text('PUMPS', font=("Helvetica", 14), text_color='green', pad=(0, 0))],
    [sg.Text('Alcohol/Isocratic pump ON', font=("Helvetica", 14), key='_SWEEP8_', pad=(0, 0))],
    [sg.Text('Cooling/Peristaltic pump ON', font=("Helvetica", 14), key='_SWEEP9_', pad=(0, 0))]]

# TEST - Normal text layout
normal_text_layout = [
    [sg.Text('NORMAL TEST EXECUTIONS', font=("Helvetica", 14), text_color='green', key='_NORMAL1_', pad=(0, 10))],
    [sg.Text('Initialisations', font=("Helvetica", 14), key='_NORMAL2_', pad=(0, 0))],
    [sg.Text('Dump first measurement', font=("Helvetica", 14), key='_NORMAL3_', pad=(0, 0))],
    [sg.Text('FOR LOOP', font=("Helvetica", 14), key='_NORMAL4_', pad=(0, 0))],
    [sg.Text('   Microwaves OFF / Dielectric measurement', font=("Helvetica", 14), key='_NORMAL5_', pad=(0, 0))],
    [sg.Text('   Microwaves ON', font=("Helvetica", 14), key='_NORMAL6_', pad=(0, 0))],
    [sg.Text('Test complete', font=("Helvetica", 14), key='_NORMAL7_', pad=(0, 0))],
    [sg.Text('', font=("Helvetica", 14), pad=(0, 0))],
    [sg.Text('PUMPS', font=("Helvetica", 14), text_color='green', pad=(0, 0))],
    [sg.Text('Alcohol/Isocratic pump ON', font=("Helvetica", 14),key='_NORMAL8_', pad=(0, 0))],
    [sg.Text('Cooling/Peristaltic pump ON', font=("Helvetica", 14), key='_NORMAL9_', pad=(0, 0))]]

# TEST - Manual generator layout
manu_gen_layout = [
    [sg.Text('Turn ON generator (freq. = 2.45GHz)', font=("Helvetica", 18)),
     sg.Submit(key='_ONSET_OK_', font=("Helvetica", 18), button_text='GEN ON', pad=(100, 10),
               auto_size_button=True)],
    [sg.Text('Power (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_POWER3_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Reflected power (W, set to 0 if not configuring)', font=("Helvetica", 18), text_color='red', background_color='yellow'),
     sg.Input('', do_not_clear=True, key='_RPOWER_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('', font=("Helvetica", 18))],
    [sg.Text('STATUS', text_color='green', font=("Helvetica", 18))],
    [sg.Text('Generator OFF', font=("Helvetica", 18), text_color='red', key='OFFSETTEXT')],
    [sg.Text('Generator ON', font=("Helvetica", 18), text_color='black', key='ONSETTEXT')],
    [sg.Text('', font=("Helvetica", 18))],
    [sg.Submit(key='_OFFSET_OK_', font=("Helvetica", 18), button_text='GEN OFF', pad=(100, 10),
               auto_size_button=True)],
    [sg.Submit(key='_RESET_FAULTS_', font=("Helvetica", 18), button_text='RESET FAULTS', pad=(200, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_MANUGEN_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]

# TEST - Manual ENA layout
manu_ENA_layout = [
    [sg.Text('Start Frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('2440', do_not_clear=True, key='_STARTFREQMANU_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Stop Frequency (GHz)', font=("Helvetica", 18)),
     sg.Input('2460', do_not_clear=True, key='_STOPFREQMANU_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('# of datapoints', font=("Helvetica", 18)),
     sg.Input('101', do_not_clear=True, key='_DATAPOINTSMANU_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Bandwidth (Hz)', font=("Helvetica", 18)),
     sg.Input('300', do_not_clear=True, key='_BWMANU_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('File directory', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DIRECTORYMANU_', size=(30, 10), font=("Helvetica", 18))],
    [sg.Text('Measurement delay', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DELAYENAMANU_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_CONFIG6_OK_', font=("Helvetica", 18), button_text='Set values', pad=(100, 10),
               auto_size_button=True),
     sg.Submit(key='_TEST3_OK_', font=("Helvetica", 18), button_text='Trigger ENA', pad=(100, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_MANUENA_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]

# TEST - Manual Pumps layout
manu_pumps_layout = [
    [sg.Text('Cooling flow speed (RPM, must not leave blank)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPM1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Radio('COOLING ON', "RADIO4", default=False, change_submits=True, key="_MANU_PERIS_ON_", font=("Helvetica", 18),
              size=(15, 1), pad=(50, 10)),
     sg.Radio('COOLING OFF', "RADIO4", default=False, change_submits=True, key="_MANU_PERIS_OFF_",
              font=("Helvetica", 18), size=(15, 1), pad=(50, 10))],
    [sg.Radio('ALCOHOL ON', "RADIO4", default=False, change_submits=True, key="_MANU_ISO_ON_", font=("Helvetica", 18),
              size=(15, 1), pad=(50, 10)),
     sg.Radio('ALCOHOL OFF', "RADIO4", default=False, change_submits=True, key="_MANU_ISO_OFF_",
              font=("Helvetica", 18), size=(15, 1), pad=(50, 10))],
    [sg.Text('', font=("Helvetica", 18))],
    [sg.Text('STATUS', text_color='green', font=("Helvetica", 18))],
    [sg.Text('Cooling OFF', font=("Helvetica", 18), text_color='red', key='_COOLINGOFF_')],
    [sg.Text('Cooling ON', font=("Helvetica", 18), text_color='black', key='_COOLINGON_')],
    [sg.Text('Alcohol OFF', font=("Helvetica", 18), text_color='red', key='_ALCOHOLOFF_')],
    [sg.Text('Alcohol ON', font=("Helvetica", 18), text_color='black', key='_ALCOHOLON_')],
    [sg.Text('', font=("Helvetica", 18))],
    [sg.Submit(key='_TEST4_OK_', font=("Helvetica", 18), button_text='Launch', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_MANUPUMPS_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0),
               auto_size_button=True)]]

# TEST - Five iteration test layout
five_it_layout = [
    [sg.Text('Power iteration 1 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER1_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ONDELAY31_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_OFFDELAY31_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 2 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER2_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ONDELAY32_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_OFFDELAY32_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 3 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER3_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ONDELAY33_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_OFFDELAY33_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 4 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER4_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ONDELAY34_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_OFFDELAY34_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Power iteration 5 (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ITPOWER5_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration ON (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_ONDELAY35_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Duration OFF (s): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_OFFDELAY35_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Cancel(key='_FIVEIT_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True),
     sg.Submit(key='_CONFIG5_OK_', font=("Helvetica", 18), button_text='Configure', pad=(100, 0),
               auto_size_button=True),
     sg.Submit(key='_TEST5IT_OK_', font=("Helvetica", 18), button_text='Launch', pad=(100, 0), auto_size_button=True)],
    [sg.Text('TEST EXECUTIONS', font=("Helvetica", 18), text_color='green', key='_FIVEIT1_', pad=(10, 10))],
    [sg.Text('Initialisations', font=("Helvetica", 18), key='_FIVEIT2_', pad=(10, 0))],
    [sg.Text('Dump first measurement', font=("Helvetica", 18), key='_FIVEIT3_', pad=(10, 0))],
    [sg.Text('FOR LOOP', font=("Helvetica", 18), key='_FIVEIT4_', pad=(10, 0))],
    [sg.Text('   Microwaves ON', font=("Helvetica", 18), key='_FIVEIT5_', pad=(10, 0))],
    [sg.Text('   Microwaves OFF / Dielectric measurement', font=("Helvetica", 18), key='_FIVEIT6_', pad=(10, 0))],
    [sg.Text('Test complete', font=("Helvetica", 18), key='_FIVEIT7_', pad=(10, 0))],
    [sg.Text('', font=("Helvetica", 14), pad=(0, 0))],
    [sg.Text('PUMPS', font=("Helvetica", 14), text_color='green', pad=(0, 0))],
    [sg.Text('Alcohol/Isocratic pump ON', font=("Helvetica", 14), key='_FIVEIT8_', pad=(0, 0))],
    [sg.Text('Cooling/Peristaltic pump ON', font=("Helvetica", 14), key='_FIVEIT9_', pad=(0, 0))]]

# PROGRESS BAR LAYOUT
progress_bar_layout = [[sg.Text('Test progress meter')],
                       [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='METER1')],
                       [sg.Cancel()]]

'''
MAIN USER LAYOUT
'''
# Frame creation (For main window)
layout = [[sg.Menu(menu_def, tearoff=True)],
          [sg.Frame('', Init_layout, font='Any 13', title_color='blue', visible=False,
                    key='_INIT_FRAME_', size=(800, 400)),
           sg.Frame('Parameters options', Parameter_layout, font='Any 13', title_color='blue', visible=False,
                    key='_ALLPARAMETERS_FRAME_', size=(1200, 600)),
           sg.Frame('Generator parameters options', gen_layout, font='Any 13', title_color='blue', visible=False,
                    key='_GEN_FRAME_', size=(800, 300)),
           sg.Frame('ENA parameters', Analyzer_layout, font='Any 13', title_color='blue', visible=False,
                    key='_ANA_FRAME_', size=(800, 400)),
           sg.Frame('ENA parameters option 1', Freq_layout, font='Any 13', title_color='blue', visible=False,
                    key='_FREQ_FRAME_', size=(800, 400)),
           sg.Frame('ENA parameters option 2', Params1_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PARAMS1_FRAME_', size=(800, 400)),
           sg.Frame('Switch parameters', Switch_layout, font='Any 13', title_color='blue', visible=False,
                    key='_SWITCH_FRAME_', size=(800, 400)),
           sg.Frame('Switch parameters options', Params2_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PARAMS2_FRAME_', size=(800, 400)),
           sg.Frame('Pumps parameters options', Peristaltic_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PUMPS_FRAME_', size=(800, 400)),
           sg.Frame('Tests and manual component control options', Test_layout, font='Any 13', title_color='blue', visible=False,
                    key='_TEST_FRAME_', size=(800, 400)),
           sg.Frame('Sweep test options (SELECT MANUAL MODE ONLY)', sweep_layout, font='Any 13', title_color='blue', visible=False,
                    key='_SWEEP_FRAME_', size=(1200, 600)),
           sg.Frame('Manual generator control options', manu_gen_layout, font='Any 13', title_color='blue',
                    visible=False, key='_MANUGEN_FRAME_', size=(800, 400)),
           sg.Frame('Manual ENA control options', manu_ENA_layout, font='Any 13', title_color='blue', visible=False,
                    key='_MANUENA_FRAME_', size=(800, 400)),
           sg.Frame('Manual pumps control options', manu_pumps_layout, font='Any 13', title_color='blue', visible=False,
                    key='_MANUPUMPS_FRAME_', size=(800, 400)),
           sg.Frame('Five iteration test options', five_it_layout, font='Any 13', title_color='blue', visible=False,
                    key='_FIVEIT_FRAME_', size=(1200, 600)),
           sg.Frame('', normal_text_layout, font='Any 13', visible=False,
                    key='_NORMALTEXT_FRAME_', size=(400, 300))
           ]]

# Main user interface window popup
window = sg.Window('AUTOMATION CIRCUIT - V2', layout, default_element_size=(40, 1), grab_anywhere=False,
                   size=(1200, 700))

"""
***********************************************
**************** MAIN FUNCTION ****************
***********************************************
"""


def main():
    value_dict = {"startfreq": [], "stopfreq": [], "datapoints": [], "bw": [], "num_its": [], "ondelay1": [],
                  "offdelay1": [],
                  "directory": [], "switch1": [], "switch2": [], "power1": [], "freq1": [], "dpower2": [],
                  "startfreq2": [], "stopfreq2": [], "stepfreq": [], "power3": [],
                  "rpower": [], "rpower1": [], "itpower": [],
                  "ondelay3": [], "offdelay3": [], "startfreqmanu": [], "stopfreqmanu": [],
                  "datapointsmanu": [], "bwmanu": [],
                  "delayENAmanu": [], "directorymanu": [], "RPM": [], "RPM1": []}

    # Initialise bit trigger values
    IsManu = 1
    Peris_ON = 0
    Iso_ON = 0
    Manu_Pumps_State = 0
    Manu_Iso_ON = 0
    Manu_Peris_ON = 0

    # Print introductory message
    print("\n\n------------------WELCOME TO THE AUTOMATION CIRCUIT V2 UI! Select OPTIONS -> CREATE to get started.------------------\n")

    while True:
        event, values = window.Read()

        # For debugging purposes
        # print(event)

        """
        INIT WINDOW
        """
        if event == 'CREATE':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_ALLPARAMETERS_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=True)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_TEST_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)
            


        """
        TEST RUN FUNCTIONS
        """
        # Turn generator on manually
        if event == '_ONSET_OK_':

            value_dict["power3"] = []
            value_dict["rpower"] = []

            try:

                value_dict["power3"].append(int(values['_POWER3_']))
                value_dict["rpower"].append(int(values['_RPOWER_']))

                if int(value_dict["rpower"][0]) != 0:
                    sg.popup("Are you sure you want to manually configure the reflected power?\nIts value should not exceed 30% of the transmitted powers' value.\nPress OK to continue.")

                window.FindElement('_MANUGEN_FRAME_').Update(visible=True)
                Manual_Gen_ON(value_dict['power3'][0], value_dict['rpower'][0], value_dict['switch1'][0],
                              value_dict['switch2'][0])

            except:
                sg.popup("Please check the fields!")

        # Turn generator off manually
        if event == '_OFFSET_OK_':

            try:
                window.FindElement('_MANUGEN_FRAME_').Update(visible=True)
                Manual_Gen_OFF(value_dict['switch1'][0], value_dict['switch2'][0])

            except:
                sg.popup("Please check the fields!")

        # Frequency sweep test
        if event == '_TEST2_OK_':
            try:
                # sg.popup("Press OK to confirm launch. Press X to exit")
                Freq_sweep(value_dict['startfreq'][0], value_dict['stopfreq'][0], value_dict['datapoints'][0],
                           value_dict['bw'][0], value_dict['directory'][0], value_dict['power1'][0], value_dict['rpower1'][0],
                           value_dict['ondelay1'][0], value_dict['offdelay1'][0],
                           value_dict['startfreq1'][0], value_dict['stopfreq1'][0], value_dict['stepfreq'][0], IsManu,
                           value_dict['switch1'][0], value_dict['switch2'][0], Peris_ON, value_dict['RPM'][0], Iso_ON)

                window.FindElement('_SWEEP_FRAME_').Update(visible=True)
                sg.popup("Test is complete!")

            except:
                sg.popup('Please check the fields')
                window.FindElement('_SWEEP_FRAME_').Update(visible=True)

        #Manual ENA trigger
        if event == '_TEST3_OK_':
            try:
                # sg.popup("Press OK to confirm launch. Press X to exit")
                Manual_ENA_Trigger(value_dict['startfreqmanu'][0], value_dict['stopfreqmanu'][0],
                                   value_dict['datapointsmanu'][0],
                                   value_dict['bwmanu'][0], value_dict['delayENAmanu'][0],
                                   value_dict['directorymanu'][0], value_dict['switch1'][0],
                                   value_dict['switch2'][0])

                window.FindElement('_MANUENA_FRAME_').Update(visible=True)
                sg.popup("Trigger complete!")

            except:
                sg.popup('Please check the fields')
                window.FindElement('_MANUENA_FRAME_').Update(visible=True)

        #Manual pumps trigger
        if event == '_TEST4_OK_':

            value_dict["RPM1"] = []

            try:
                value_dict["RPM1"].append(int(values['_RPM1_']))

                # window.disappear()
                # sg.popup("Press OK to confirm launch. Press X to exit")

                Manual_Pumps(Manu_Pumps_State, value_dict['RPM1'][0], Manu_Iso_ON, Manu_Peris_ON)

                window.FindElement('_MANUPUMPS_FRAME_').Update(visible=True)
                # window.reappear()

            except:
                sg.popup('Please check the fields')
                window.FindElement('_MANUPUMPS_FRAME_').Update(visible=True)

        # 5 iteration test
        if event == '_TEST5IT_OK_':
            try:
                # window.disappear()
                # sg.popup("Press OK to confirm launch. Press X to exit")

                for i in range(6):
                    Five_Iteration_Test(value_dict['startfreq'][0], value_dict['stopfreq'][0],
                                        value_dict['datapoints'][0],
                                        value_dict['bw'][0], value_dict['directory'][0], value_dict['switch1'][0],
                                        value_dict['switch2'][0], value_dict['itpower'][i - 1],
                                        value_dict['ondelay3'][i - 1], value_dict['offdelay3'][i - 1],
                                        value_dict['freq1'][0], value_dict['rpower1'][0], i + 1, Peris_ON,
                                        value_dict['RPM'][0], Iso_ON)

                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)
                sg.popup("Test is complete!")
                # window.reappear()

            except:
                sg.popup('Please check the fields')
                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)

        # Normal test
        if event == '_LAUNCH_OK_':
            try:
                # window.disappear()
                # sg.popup("Press OK to confirm launch. Press X to exit")
                Normal_Test(value_dict['startfreq'][0], value_dict['stopfreq'][0], value_dict['datapoints'][0],
                            value_dict['bw'][0], value_dict['num_its'][0], value_dict['ondelay1'][0],
                            value_dict['offdelay1'][0],
                            value_dict['directory'][0], value_dict['switch1'][0], value_dict['switch2'][0],
                            value_dict['freq1'][0], value_dict['power1'][0], value_dict['rpower1'][0],
                            Peris_ON, value_dict['RPM'][0], Iso_ON)
                sg.popup("Test is complete!")
                window.FindElement('_TEST_FRAME_').Update(visible=True)
                window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)
                # window.reappear()

            except:
                # window.reappear()
                sg.popup('Please check the fields')


        """
        ALL PARAMETERS WINDOW
        """
        if event == '_ANA_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=True)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_SWITCH_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=True)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_GEN_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=True)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_PERIS_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=True)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_ALLPARAMETERS_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)


        """
        ANALYZER WINDOW
        """
        if event == '_ANA_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=True)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_FREQ_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=True)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_PARAMS1_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=True)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        """
        PARAMS1 WINDOW
        """
        if event == '_PARAMS1_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=True)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_CONFIG1_OK_':

            value_dict["num_its"] = []
            value_dict["directory"] = []
            try:
                value_dict["num_its"].append(int(values['_NUMITS_']))
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
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=True)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_CONFIG2_OK_':

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
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=True)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_PARAMS2_OK_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=True)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        """
        PARAMS2 WINDOW
        """
        if event == '_PARAMS2_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=True)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

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


        """
        GENERATOR WINDOW
        """
        if event == '_GEN_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=True)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_SET_GEN_':

            value_dict["power1"] = []
            value_dict["ondelay1"] = []
            value_dict["offdelay1"] = []
            value_dict["freq1"] = []

            try:
                value_dict["power1"].append(int(values['_POWER1_']))
                value_dict["ondelay1"].append(float(values['_ONDELAY1_']))
                value_dict["offdelay1"].append(float(values['_OFFDELAY1_']))
                value_dict["freq1"].append(int(values['_FREQ1_']))

                window.FindElement('_GEN_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        if event == '_SET_RPOWER_':

            value_dict["rpower1"] = []

            try:
                value_dict["rpower1"].append(float(values['_REFPOWER_']))

                if int(value_dict["rpower1"][0]) != 0:
                    sg.popup("Are you sure you want to manually configure the reflected power?\nIts value should not exceed 30% of the transmitted powers' value.\nPress OK to continue.")

                window.FindElement('_GEN_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                Rpower_Manu = 0
                sg.popup('Please check the fields')

        if event == '_RESET_FAULTS_':
            # Reset generator faults function
            Reset_Faults()


        """
        PERISTALTIC PUMP WINDOW
        """
        if event == '_PERIS_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=True)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_CONFIG7_OK_':

            value_dict["RPM"] = []

            try:
                value_dict["RPM"].append(int(values['_RPM_']))

                window.FindElement('_PUMPS_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        if event == '_PERIS_ON_':
            Peris_ON = 1

        if event == '_PERIS_OFF_':
            Peris_ON = 0

        if event == '_ISO_ON_':
            Iso_ON = 1

        if event == '_ISO_OFF_':
            Iso_ON = 0


        """
        TEST WINDOW
        """
        # Select button executions
        if event == '_TEST_OK1_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=True)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=False)

        if event == '_TEST_OK2_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=True)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=False)

        if event == '_TEST_OK3_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=True)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=False)

        if event == '_TEST_OK4_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=True)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=False)

        if event == '_TEST_OK5_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=True)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=False)

        # Cancel button execution
        if event == '_TEST_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=False)


        """
        MANUALS, SCAN SWEEP AND FIVE ITERATION TEST WINDOWS
        """
        # Cancel buttons executions
        if event == '_SWEEP_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)

        if event == '_MANUGEN_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)

        if event == '_MANUENA_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)

        if event == '_MANUPUMPS_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)

        if event == '_FIVEIT_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PUMPS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUPUMPS_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)
            window.FindElement('_NORMALTEXT_FRAME_').Update(visible=True)
            


        # Sweep scan test configuration
        if event == '_CONFIG4_OK_':

            value_dict["startfreq1"] = []
            value_dict["stopfreq1"] = []
            value_dict["stepfreq"] = []

            try:
                value_dict["startfreq1"].append(int(values['_STARTFREQ1_']))
                value_dict["stopfreq1"].append(int(values['_STOPFREQ1_']))
                value_dict["stepfreq"].append(int(values['_STEPFREQ_']))

                window.FindElement('_SWEEP_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        if event == '_MANU_MODE_':
            IsManu = 1

        if event == '_AUTO_MODE_':
            IsManu = 0


        # Five iteration test configuration
        if event == '_CONFIG5_OK_':

            value_dict["itpower"] = []
            value_dict["ondelay3"] = []
            value_dict["offdelay3"] = []

            try:
                value_dict["itpower"].append(float(values['_ITPOWER1_']))
                value_dict["itpower"].append(float(values['_ITPOWER2_']))
                value_dict["itpower"].append(float(values['_ITPOWER3_']))
                value_dict["itpower"].append(float(values['_ITPOWER4_']))
                value_dict["itpower"].append(float(values['_ITPOWER5_']))

                value_dict["ondelay3"].append(float(values['_ONDELAY31_']))
                value_dict["ondelay3"].append(float(values['_ONDELAY32_']))
                value_dict["ondelay3"].append(float(values['_ONDELAY33_']))
                value_dict["ondelay3"].append(float(values['_ONDELAY34_']))
                value_dict["ondelay3"].append(float(values['_ONDELAY35_']))

                value_dict["offdelay3"].append(float(values['_OFFDELAY31_']))
                value_dict["offdelay3"].append(float(values['_OFFDELAY32_']))
                value_dict["offdelay3"].append(float(values['_OFFDELAY33_']))
                value_dict["offdelay3"].append(float(values['_OFFDELAY34_']))
                value_dict["offdelay3"].append(float(values['_OFFDELAY35_']))

                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)

                sg.popup("Configured!")

            except:
                sg.popup('Please check the fields')


        # Manual ENA trigger configuration
        if event == '_CONFIG6_OK_':

            value_dict["startfreqmanu"] = []
            value_dict["stopfreqmanu"] = []
            value_dict["datapointsmanu"] = []
            value_dict["bwmanu"] = []
            value_dict["delayENAmanu"] = []
            value_dict["directorymanu"] = []

            try:
                value_dict["startfreqmanu"].append(int(values['_STARTFREQMANU_']))
                value_dict["stopfreqmanu"].append(int(values['_STOPFREQMANU_']))
                value_dict["datapointsmanu"].append(int(values['_DATAPOINTSMANU_']))
                value_dict["bwmanu"].append(int(values['_BWMANU_']))
                value_dict["delayENAmanu"].append(float(values['_DELAYENAMANU_']))
                value_dict["directorymanu"].append(str(values['_DIRECTORYMANU_']))

                window.FindElement('_MANUENA_FRAME_').Update(visible=True)

                sg.popup("Values Set!")

            except:
                sg.popup('Please check the fields')


        # Manual pumps control
        if event == '_MANU_ISO_ON_':
            Manu_Pumps_State = 1
            Manu_Iso_ON = 1

        if event == '_MANU_ISO_OFF_':
            Manu_Pumps_State = 2
            Manu_Iso_ON = 0

        if event == '_MANU_PERIS_ON_':
            Manu_Pumps_State = 3
            Manu_Peris_ON = 1

        if event == '_MANU_PERIS_OFF_':
            Manu_Pumps_State = 4
            Manu_Peris_ON = 0

        """
        QUIT WINDOW
        """
        if event is None or event == 'QUIT':
            break


try:
    init()
    main()  # Main program

except:
    sg.popup("Verify the connections")
    sys.exit()
