"""

AUTOMATION CONTROL CODE - NETWORK ANALYZER WITH SWITCH, GENERATOR and PERISTALTIC PUMP - V1 - 2021

Atlantic Cancer Research Institute - ACRI

Code originally written  by André LeBlanc, electrical engineering student at l'Université de Moncton
March 2021

NOTE 1: USB cable needs to be connected to the host PC AND (generator + fan) must be activated prior to running the code. Otherwise the ablation probe won't emit micro-waves.
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
GLOBAL OBJECTS
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

# COM varies on which generator your are using.
client = ModbusClient(method='rtu', port='COM14', timeout=4, baudrate=115200, strict=False)


# RAPPEL POMPE ISOCRATIQUE
# os.system("C:/Windows\Licop\LicopDemo\LicopDemo.exe")


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
def Normal_Test(startFreq, stopFreq, datapoints, BW, num_its, delay, directory, switch1, switch2, freq, power, Peris_ON, RPM):

    print("------------------NORMAL TEST------------------\n")
    time.sleep(2)
    print("The test will begin in 3 seconds\n")
    time.sleep(3)

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
    # Value = 20 Watts (Modify accordingly for test purposes)
    client.write_register(1, 20, unit=UNIT)
    print("Reflected power set to 20 watts \n")

    # TRANSMITTED POWER SET
    client.write_register(0, power, unit=UNIT)
    print("Transmitted power value set \n")

    # TURN GENERATOR OFF (default state)
    client.write_register(2, 0x00, unit=UNIT)
    print("Microwave is turned off for its initial state \n")

    """
    3. Peristaltic pump set
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
    TEST RUN
    """
    print("---------------------START TEST---------------------")

    for i in range(num_its + 1):
        if i == 0:
            # INITIALISE PROGRESS BAR
            sg.OneLineProgressMeter('Measurement progress...', 0, num_its, key='METER1', grab_anywhere=True)
            print("\nInitialising switch. Please wait.\n")

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

            print("\nITERATION " + str(i) + "\n")


            #------------- STATE I - DIELECTRIC MEASUREMENT -------------#

            # MICROWAVES OFF
            client.write_register(2, 0xBF, unit=UNIT)
            print("Microwaves OFF")

            # PLACE SWITCH IN POSITION I (Dielectric measurement)
            rb.switchon(switch1)
            rb.switchoff(switch2)
            print("Switch in position I (Dielectric measurements)")

            # TURN PERISTALTIC PUMP OFF
            if Peris_ON == 1:
                values[1].setVoltage(5.00)
                ao4.setIoGroup(channels, values)
                print("Peristaltic pump turned OFF\n")

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

            #------------- STATE II - MICROWAVE EMISSION -------------#

            # PLACE SWITCH IN POSITION II (50 Ohm terminator)
            rb.switchon(switch2)
            rb.switchoff(switch1)
            print("Switch in position II (Microwave ablation)")

            #IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ablation probe (see switch datasheet for more details)
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


            # WAIT WHILE GENERATOR IS EMITTING MICROWAVES
            time.sleep(delay_with_corr)


            # UPDATE PROGRESS BAR
            sg.OneLineProgressMeter('Measurement progress...', i, num_its, key='METER1', grab_anywhere=True)


    # -------- END OF NORMAL TEST - END STATES ---------- #
    # TURN MICROWAVES OFF FOR ITS DEFAULT END STATE
    client.write_register(2, 0x00, unit=UNIT)

    # PLACE SWITCH IN POSITION I FOR ITS DEFAULT END STATE
    rb.switchon(switch1)
    rb.switchoff(switch2)

    # TURN MOTOR OFF FOR ITS DEFAULT END STATE
    values[1].setVoltage(5.00)
    ao4.setIoGroup(channels, values)

    # Print end of test message
    print("\n------- The test is complete! Select another test or press QUIT from the drop down menu to exit. ------- \n\n")

    client.close()


"""
FREQUENCY SCAN SWEEP FUNCTION
"""
# GENERATOR + SWITCH ONLY
# FREQUENCY SWEEP MODE. SEE GENERATOR USER MANUAL FOR MORE INFO. PAGE 15
# TODO Fix problem with EndOfScan bit.
# TODO Add ENA functions to code
def Freq_sweep(powersweep, sleep_timesweep, micro_timesweep, startfreq, stopfreq, stepfreq, IsManu, switch1, switch2):

    # MANUAL MODE
    if IsManu:
        print("------------------MANUAL SWEEP TEST------------------\n")
        time.sleep(2)
        # Initial delay prior to start of test
        print("The test will begin in 3 seconds\n")
        time.sleep(3)

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
        client.write_register(1, 20, unit=UNIT)
        print("Reflected power set to 20 watts \n")

        # TRANSMITTED POWER SET:
        client.write_register(0, int(powersweep), unit=UNIT)
        print("Forward power set point set \n\n\n")

        currentfreqKHz = startfreqKHz
        print("Start frequency set to" + str(rq1) + "KHz\n")
        while currentfreqKHz <= stopfreqKHz:

            # TURN MICROWAVE ON
            # Place switch in position II (A-D)
            rb.switchon(switch2)
            rb.switchoff(switch1)
            client.write_register(2, 0x50, unit=UNIT)
            print("Microwave turned on for " + str(micro_timesweep) + " seconds \n")


            # wait micro_time seconds
            time.sleep(micro_timesweep)


            # TURN MICROWAVE OFF
            # Place switch in position I (A-B)
            client.write_register(2, 0x00, unit=UNIT)
            print("Microwave turned off for " + str(sleep_timesweep) + " seconds \n\n")
            rb.switchon(switch1)
            rb.switchoff(switch2)


            # Microwave off for time.sleep_time seconds (while ENA is taking measurements)
            time.sleep(sleep_timesweep)


            # INCREMENT FREQUENCY VALUE
            currentfreqKHz += stepfreqKHz
            if currentfreqKHz == 2.5E9 or currentfreqKHz > stopfreqKHz:
                break
            else:
                client.write_register(9, int(currentfreqKHz), unit=UNIT)
                rr1 = client.read_holding_registers(112, 1, unit=UNIT)
                rq1 = rr1.registers
                print("New generator frequency set to :" + str(rq1) + "KHz ")


        # Turn generator OFF for its default end state
        # Place switch in position I (A-B) for its default end state
        client.write_register(2, 0x00, unit=UNIT)
        rb.switchon(switch1)
        rb.switchoff(switch2)
        client.close()

        # Print end of test message
        print("\n------- The test is complete! Select another test or press QUIT from the drop down menu to exit. ------- \n\n")

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
    client.write_register(1, rpower, unit=UNIT)

    # TRANSMITTED POWER SET
    client.write_register(0, power_man, unit=UNIT)

    # GENERATOR ON
    client.write_register(2, 0x50, unit=UNIT)
    print("Generator turned ON\n")


"""
MANUAL GENERATOR OFF FUNCTION
"""
# GENERATOR + SWTICH ONLY
def Manual_Gen_OFF(switch1, switch2):


    # GENERATOR OFF
    client.write_register(2, 0x00, unit=UNIT)
    print("Generator turned OFF\n")

    # Place switch in position I (A-B)
    rb.switchon(switch1)
    rb.switchoff(switch2)


"""
MANUAL ENA TRIGGER FUNCTION
"""
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
    analyzer.write("MMEMory:STORe:DATA '" + filename + "/ENAManTrig_Result" + ".csv', 'CSV formatted Data','Trace','RI', 1")

    time.sleep(delay_with_corr)


"""
FIVE ITERATION TEST FUNCTION
"""
def Five_Iteration_Test(startFreq, stopFreq, datapoints, BW, directory, switch1, switch2, power, delay, freq, rpower, i, Peris_ON, RPM):

    # DELAY WITH CORRECTION (TO ASSURE ALL DATA IS MEASURED IN FREQUENCY SWEEP)
    delay_with_corr = delay + delay / 4

    filename = directory

    """
    Peristaltic pump set
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


    if i == 1:

        print("------------------FIVE ITERATION TEST------------------\n")
        time.sleep(2)
        # INITIAL DELAY
        print("\nThe test will begin in 3 seconds\n")
        time.sleep(3)


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
        analyzer.write("SENS1:SWE:TIME " + str(delay))

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
        rd1 = client.write_register(2, 0x10, unit=UNIT)
        print("Reflected power limitation mode activated \n")

        # REFLECTED POWER SET
        rq1 = client.write_register(1, rpower, unit=UNIT)
        print("Reflected power set to: \n" + str(rpower) + " Watts\n")

        # TURN GENERATOR OFF (default state)
        client.write_register(2, 0x00, unit=UNIT)
        print("Microwave is turned off for its initial state \n")

        print("\n---------------------START TEST---------------------\n")

        print("Initialising switch\n")

        #-------------- DUMP FIRST MEASUREMENT ----------------#

        # DUMP FIRST MEASUREMENT. ALWAYS GIVES UNVALID RESULT EVEN WHEN PROBE CALIBRATED.
        rb.switchon(switch1)
        rb.switchoff(switch2)

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
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
        """
        RUN TEST
        """

        print("\nITERATION " + str(i - 1) + "\n")


        # TRANSMITTED POWER SET
        client.write_register(0, int(power), unit=UNIT)
        print("Microwave output power set to: \n" + str(power) + " Watts\n")

        if Peris_ON == 1:
            voltage = RPM / 40
            # CH0 = SPEED CONTROL
            values[0].setVoltage(voltage)
            # TURN PERISTALTIC PUMP ON
            values[1].setVoltage(0.00)
            ao4.setIoGroup(channels, values)
            print("Peristaltic pump turned ON")

        # MICROWAVES ON
        # Place switch in position II (AD , Microwave ablation)
        rb.switchon(switch2)
        rb.switchoff(switch1)
        client.write_register(2, 0x50, unit=UNIT)
        print("Switch in position II (Microwave ablation)")
        print("Microwaves ON for " + str(delay) + " seconds\n")

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
        time.sleep(0.04)

        # DELAY OF INPUT VALUE SECONDS WITH CORRECTION
        time.sleep(delay_with_corr)

        # MICROWAVES OFF
        # Place switch in position I (AB , Dielectric measurement)
        client.write_register(2, 0x00, unit=UNIT)
        rb.switchon(switch1)
        rb.switchoff(switch2)
        print("Microwaves OFF for " + str(delay) + " seconds")
        print("Switch in position I (Dielectric measurement)")

        if Peris_ON == 1:
            values[0].setVoltage(0.00)
            values[1].setVoltage(5.00)
            ao4.setIoGroup(channels, values)
            print("Peristaltic pump turned OFF\n")

        print("\n")

        # IMPORTANT: WAIT 40 ms for switch to stabilise electrical signal received from ENA (see switch datasheet for more details)
        time.sleep(0.04)

        # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
        analyzer.write("SENS1:SWE:MODE SINGLE")
        analyzer.write("TRIGger:SCOPe CURRent")
        analyzer.write("INITiate1:IMMediate")
        analyzer.write("MMEMory:STORe:DATA '" + filename + "/Iteration" + str(
            i - 1) + ".csv', 'CSV formatted Data','Trace','RI', 1")

        # DELAY OF INPUT VALUE SECONDS WITH CORRECTION
        time.sleep(delay_with_corr)

        if i == 6:

            # MICROWAVES OFF FOR REDUNDENCY PURPOSES
            client.write_register(2, 0x00, unit=UNIT)

            # Place switch in position I for redundency purposes (AB)
            rb.switchon(switch1)
            rb.switchoff(switch2)

            # TURN PERISTALTIC PUMP OFF FOR ITS DEFAULT END STATE
            values[1].setVoltage(5.00)
            ao4.setIoGroup(channels, values)

            # Print end of test message
            print("\n------- The test is complete! Select another test or press QUIT from the drop down menu to exit. ------- \n\n")

            client.close()



"""
GU Interface (EN)
Interface UG (FR)
"""
sg.ChangeLookAndFeel('BlueMono')

# ------ Menu Definition ------ #
menu_def = [['OPTIONS', ['TEST', 'QUIT']]]


# INITIAL WINDOW LAYOUTS
Init_layout = [
    [sg.Text('All parameters options (FOR ALL TESTS)', font=("Helvetica", 18), pad=(0, 5))],
    [sg.Submit(key='_ALLPARAMETERS_OK_', button_text='Select', font=("Helvetica", 18), pad=(0, 20))],
    [sg.Text('Test options', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_TEST_OK_', font=("Helvetica", 18), button_text='Select', pad=(0, 20),
               auto_size_button=True)]]

Parameter_layout = [
    [sg.Text('Network Analyzer (FOR NORMAL AND FIVE ITERATION TEST)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_ANA_OK_', button_text='Select', font=("Helvetica", 12), pad=(20, 20))],
    [sg.Text('Switch (FOR ALL TESTS)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_SWITCH_OK_', font=("Helvetica", 12), button_text='Select', pad=(20, 20), auto_size_button=True)],
    [sg.Text('Generator (FOR NORMAL TEST ONLY)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_GEN_OK_', font=("Helvetica", 12), button_text='Select', pad=(20, 20), auto_size_button=True)],
    [sg.Text('Peristaltic pump (FOR NORMAL AND FIVE ITERATION TEST)', font=("Helvetica", 12), pad=(0, 5))],
    [sg.Submit(key='_PERIS_OK_', button_text='Select', font=("Helvetica", 12), pad=(20, 20))],
    [sg.Cancel(key='_ALLPARAMETERS_CANCEL_', font=("Helvetica", 12), button_text='Return', pad=(0, 0), auto_size_button=True)]]

Test_layout = [
    [sg.Text('Launch normal test (w. selected number of iterations)', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_LAUNCH_OK_', button_text='Launch', font=("Helvetica", 18), pad=(40, 10))],
    [sg.Text('Sweep test - GENERATOR/SWITCH ONLY', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_TEST_OK1_', button_text='OK', font=("Helvetica", 18), pad=(40, 10))],
    [sg.Text('Manual generator', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_TEST_OK2_', button_text='OK', font=("Helvetica", 18), pad=(40, 10)),
     sg.Text('Manual ENA', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_TEST_OK4_', button_text='OK', font=("Helvetica", 18), pad=(40, 10))],
    [sg.Text('Five iteration test', font=("Helvetica", 18), pad=(0, 5)),
     sg.Submit(key='_TEST_OK3_', button_text='OK', font=("Helvetica", 18), pad=(40, 10))],
    [sg.Cancel(key='_TEST_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# GENERATOR SETTINGS LAYOUT
gen_layout = [
    [sg.Text('Microwave power (W)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_POWER1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Delay duration (s)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_DELAY1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Frequency (MHz)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_FREQ1_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Submit(key='_SET_GEN_', font=("Helvetica", 18), button_text='Set values', pad=(170, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_GEN_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# NETWORK ANALYZER SETTINGS LAYOUT
Analyzer_layout = [
    [sg.Text('Frequency', font=("Helvetica", 18), pad=(0, 5)), ],
    [sg.Submit(key='_FREQ_OK_', button_text='Select', font=("Helvetica", 18), pad=(300, 20))],
    [sg.Text('Parameters', font=("Helvetica", 18), pad=(0, 5)), ],
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
    [sg.Text('Number of test iterations', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_NUMITS_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Text('Desired filename (must not leave blank)', font=("Helvetica", 18)),
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
    [sg.Text('Flow speed (RPM)', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPM_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Radio('PERIS ON', "RADIO2", default=False, change_submits=True, key="_PERIS_ON_", font=("Helvetica", 18),
              size=(10, 1), pad=(100, 10)),
     sg.Radio('PERIS OFF', "RADIO2", default=False, change_submits=True, key="_PERIS_OFF_",
              font=("Helvetica", 18), size=(10, 1), pad=(100, 10))],
    [sg.Submit(key='_CONFIG7_OK_', font=("Helvetica", 18), button_text='Set values', pad=(300, 10),
               auto_size_button=True)],
    [sg.Cancel(key='_PERIS_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]



# TEST - Frequency sweep scan selection layout
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
    [sg.Cancel(key='_SWEEP_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# TEST - Manual generator layout
manu_gen_layout = [
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
    [sg.Cancel(key='_MANUGEN_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


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
    [sg.Cancel(key='_MANUENA_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True)]]


# TEST - Five iteration test layout
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
    [sg.Text('Reflected power (W): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_RPOWER1_', size=(10, 10), font=("Helvetica", 18)),
     sg.Text('Frequency (MHz): ', font=("Helvetica", 18)),
     sg.Input('', do_not_clear=True, key='_FREQ2_', size=(10, 10), font=("Helvetica", 18))],
    [sg.Cancel(key='_FIVEIT_CANCEL_', font=("Helvetica", 18), button_text='Return', pad=(0, 0), auto_size_button=True),
     sg.Submit(key='_CONFIG5_OK_', font=("Helvetica", 18), button_text='Configure', pad=(100, 10), auto_size_button=True),
     sg.Submit(key='_TEST5IT_OK_', font=("Helvetica", 18), button_text='Launch', pad=(100, 10), auto_size_button=True)]]


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
          [sg.Frame('Select parameters or test options', Init_layout, font='Any 13', title_color='blue', visible=False,
                    key='_INIT_FRAME_', size=(800, 400)),
           sg.Frame('All parameters options', Parameter_layout, font='Any 13', title_color='blue', visible=False,
                    key='_ALLPARAMETERS_FRAME_', size=(1200, 600)),
           sg.Frame('Generator options', gen_layout, font='Any 13', title_color='blue', visible=False,
                    key='_GEN_FRAME_', size=(1200, 600)),
           sg.Frame('Analyzer options', Analyzer_layout, font='Any 13', title_color='blue', visible=False,
                    key='_ANA_FRAME_', size=(800, 400)),
           sg.Frame('Frequency options', Freq_layout, font='Any 13', title_color='blue', visible=False,
                    key='_FREQ_FRAME_', size=(800, 400)),
           sg.Frame('Parameter options', Params1_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PARAMS1_FRAME_', size=(800, 400)),
           sg.Frame('Switch options', Switch_layout, font='Any 13', title_color='blue', visible=False,
                    key='_SWITCH_FRAME_', size=(800, 400)),
           sg.Frame('Parameter options', Params2_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PARAMS2_FRAME_', size=(800, 400)),
           sg.Frame('Cooling options', Peristaltic_layout, font='Any 13', title_color='blue', visible=False,
                    key='_PERIS_FRAME_', size=(800, 400)),
           sg.Frame('Test options', Test_layout, font='Any 13', title_color='blue', visible=False,
                    key='_TEST_FRAME_', size=(800, 400)),
           sg.Frame('Sweep test options', sweep_layout, font='Any 13', title_color='blue', visible=False,
                    key='_SWEEP_FRAME_', size=(1000, 500)),
           sg.Frame('Manual generator options', manu_gen_layout, font='Any 13', title_color='blue', visible=False,
                    key='_MANUGEN_FRAME_', size=(800, 400)),
           sg.Frame('Manual ENA options', manu_ENA_layout, font='Any 13', title_color='blue', visible=False,
                    key='_MANUENA_FRAME_', size=(800, 400)),
           sg.Frame('Five iteration test options', five_it_layout, font='Any 13', title_color='blue', visible=False,
                    key='_FIVEIT_FRAME_', size=(1200, 600))]]

# Main user interface window popup
window = sg.Window('ANALYZER + GENERATOR + SWITCH + COOLING TEST - IARC - V1', layout, default_element_size=(40, 1), grab_anywhere=False,
                   size=(1200, 600))


# Print introductory message
print("\n\n------------------WELCOME TO THE TEST 2.5 UI! Select OPTIONS -> TEST to get started.------------------\n")

def main():
    value_dict = {"startfreq": [], "stopfreq": [], "datapoints": [], "bw": [], "num_its": [], "delay1": [],
                  "directory": [], "switch1": [], "switch2": [], "power1": [], "freq1": [], "power2": [], "dpower2": [],
                  "startfreq2": [], "stopfreq2": [], "delay2": [], "stepfreq": [], "power3": [], "rpower": [], "itpower": [],
                  "itdpower": [], "freq2": [], "startfreqmanu": [], "stopfreqmanu": [], "datapointsmanu": [], "bwmanu": [],
                  "delayENAmanu": [], "directorymanu": [], "RPM": []}
    IsManu = 1
    Peris_ON = 0

    while True:
        event, values = window.Read()

        # For debugging purposes
        # print(event)

        """
        INIT WINDOW
        """
        if event == 'TEST':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)


        """
        TEST RUN FUNCTIONS
        """
        if event == '_ONSET_OK_':

            value_dict["power3"] = []
            value_dict["rpower"] = []

            try:

                value_dict["power3"].append(int(values['_POWER3_']))
                value_dict["rpower"].append(int(values['_RPOWER_']))
                window.FindElement('_MANUGEN_FRAME_').Update(visible=True)
                Manual_Gen_ON(value_dict['power3'][0], value_dict['rpower'][0], value_dict['switch1'][0], value_dict['switch2'][0])

            except:
                sg.popup("Please check the fields!")



        if event == '_OFFSET_OK_':

            try:
                window.FindElement('_MANUGEN_FRAME_').Update(visible=True)
                Manual_Gen_OFF(value_dict['switch1'][0], value_dict['switch2'][0])

            except:
                sg.popup("Please check the fields!")



        if event == '_TEST2_OK_':
            try:
                sg.popup("Press OK to confirm launch. Press X to exit")
                Freq_sweep(value_dict['power2'][0], value_dict['delay2'][0], value_dict['dpower2'][0],
                           value_dict['startfreq1'][0], value_dict['stopfreq1'][0], value_dict['stepfreq'][0], IsManu,
                           value_dict['switch1'][0], value_dict['switch2'][0])

                window.FindElement('_SWEEP_FRAME_').Update(visible=True)
                sg.popup("Test is complete!")

            except:
                sg.popup('Please check the fields')
                window.FindElement('_SWEEP_FRAME_').Update(visible=True)


        if event == '_TEST3_OK_':
            try:
                sg.popup("Press OK to confirm launch. Press X to exit")
                Manual_ENA_Trigger(value_dict['startfreqmanu'][0], value_dict['stopfreqmanu'][0], value_dict['datapointsmanu'][0],
                                   value_dict['bwmanu'][0], value_dict['delayENAmanu'][0], value_dict['directorymanu'][0], value_dict['switch1'][0],
                                   value_dict['switch2'][0])

                window.FindElement('_MANUENA_FRAME_').Update(visible=True)
                sg.popup("Test is complete!")

            except:
                 sg.popup('Please check the fields')
                 window.FindElement('_MANUENA_FRAME_').Update(visible=True)


        if event == '_TEST5IT_OK_':
            try:
                # window.disappear()
                sg.popup("Press OK to confirm launch. Press X to exit")

                # INITIALISE PROGRESS BAR
                sg.OneLineProgressMeter('Process...', 0, 5, key='METER1', grab_anywhere=True)

                for i in range(6):
                    Five_Iteration_Test(value_dict['startfreq'][0], value_dict['stopfreq'][0], value_dict['datapoints'][0],
                                        value_dict['bw'][0], value_dict['directory'][0], value_dict['switch1'][0],
                                        value_dict['switch2'][0], value_dict['itpower'][i - 1], value_dict['itdpower'][i - 1], value_dict['freq2'][0],
                                        value_dict['rpower1'][0], i + 1, Peris_ON, value_dict['RPM'][0])
                    if i >= 1:
                        sg.OneLineProgressMeter('Process...', i, 5, key='METER1', grab_anywhere=True)

                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)
                sg.popup("Test is complete!")
                # window.reappear()

            except:
                sg.popup('Please check the fields')
                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)


        if event == '_LAUNCH_OK_':
            try:
                # window.disappear()
                sg.popup("Press OK to confirm launch. Press X to exit")
                Normal_Test(value_dict['startfreq'][0], value_dict['stopfreq'][0], value_dict['datapoints'][0],
                            value_dict['bw'][0], value_dict['num_its'][0], value_dict['delay1'][0],
                            value_dict['directory'][0], value_dict['switch1'][0], value_dict['switch2'][0],
                            value_dict['freq1'][0], value_dict['power1'][0], Peris_ON, value_dict['RPM'][0])
                sg.popup("Test is complete!")
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=True)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_SET_GEN_':

            value_dict["power1"] = []
            value_dict["delay1"] = []
            value_dict["freq1"] = []
            try:
                value_dict["power1"].append(int(values['_POWER1_']))
                value_dict["delay1"].append(float(values['_DELAY1_']))
                value_dict["freq1"].append(int(values['_FREQ1_']))

                window.FindElement('_GEN_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')


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
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_CONFIG7_OK_':

            value_dict["RPM"] = []

            try:
                value_dict["RPM"].append(int(values['_RPM_']))

                window.FindElement('_PERIS_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')

        if event == '_PERIS_ON_':
            Peris_ON = 1

        if event == '_PERIS_OFF_':
            Peris_ON = 0



        """
        TEST WINDOW
        """
        if event == '_TEST_OK1_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=True)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_TEST_OK2_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=True)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

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
            window.FindElement('_FIVEIT_FRAME_').Update(visible=True)

        if event == '_TEST_OK4_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=True)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_TEST_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=True)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=False)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        """
        MANUALS, SCAN SWEEP AND FIVE ITERATION TEST WINDOWS
        """
        if event == '_SWEEP_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_MANUGEN_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_MANUENA_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_MANUENA_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)

        if event == '_FIVEIT_CANCEL_':
            window.FindElement('_INIT_FRAME_').Update(visible=False)
            window.FindElement('_ALLPARAMETERS_FRAME_').Update(visible=False)
            window.FindElement('_GEN_FRAME_').Update(visible=False)
            window.FindElement('_ANA_FRAME_').Update(visible=False)
            window.FindElement('_FREQ_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS1_FRAME_').Update(visible=False)
            window.FindElement('_SWITCH_FRAME_').Update(visible=False)
            window.FindElement('_PARAMS2_FRAME_').Update(visible=False)
            window.FindElement('_PERIS_FRAME_').Update(visible=False)
            window.FindElement('_TEST_FRAME_').Update(visible=True)
            window.FindElement('_SWEEP_FRAME_').Update(visible=False)
            window.FindElement('_MANUGEN_FRAME_').Update(visible=False)
            window.FindElement('_FIVEIT_FRAME_').Update(visible=False)


        if event == '_CONFIG4_OK_':

            value_dict["startfreq1"] = []
            value_dict["stopfreq1"] = []
            value_dict["stepfreq"] = []
            value_dict["dpower2"] = []
            value_dict["delay2"] = []
            value_dict["power2"] = []

            try:
                value_dict["startfreq1"].append(int(values['_STARTFREQ1_']))
                value_dict["stopfreq1"].append(int(values['_STOPFREQ1_']))
                value_dict["stepfreq"].append(int(values['_STEPFREQ_']))
                value_dict["dpower2"].append(float(values['_DPOWER2_']))
                value_dict["delay2"].append(float(values['_DELAY2_']))
                value_dict["power2"].append(int(values['_POWER2_']))

                window.FindElement('_SWEEP_FRAME_').Update(visible=True)

                sg.popup("Values are set!")

            except:
                sg.popup('Please check the fields')


        if event == '_MANU_MODE_':
            IsManu = 1


        if event == '_AUTO_MODE_':
            IsManu = 0


        if event == '_CONFIG5_OK_':

            value_dict["itpower"] = []
            value_dict["itdpower"] = []
            value_dict["rpower1"] = []
            value_dict["freq2"] = []

            try:
                value_dict["itpower"].append(float(values['_ITPOWER1_']))
                value_dict["itpower"].append(float(values['_ITPOWER2_']))
                value_dict["itpower"].append(float(values['_ITPOWER3_']))
                value_dict["itpower"].append(float(values['_ITPOWER4_']))
                value_dict["itpower"].append(float(values['_ITPOWER5_']))

                value_dict["itdpower"].append(float(values['_ITDPOWER1_']))
                value_dict["itdpower"].append(float(values['_ITDPOWER2_']))
                value_dict["itdpower"].append(float(values['_ITDPOWER3_']))
                value_dict["itdpower"].append(float(values['_ITDPOWER4_']))
                value_dict["itdpower"].append(float(values['_ITDPOWER5_']))

                value_dict["freq2"].append(int(values['_FREQ2_']))
                value_dict["rpower1"].append(int(values['_RPOWER1_']))

                window.FindElement('_FIVEIT_FRAME_').Update(visible=True)

                sg.popup("Configured!")

            except:
                sg.popup('Please check the fields')


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
