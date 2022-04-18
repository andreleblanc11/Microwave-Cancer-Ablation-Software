 #-------------------------------------------------------------------------------------------
""" 
This code has been written to control the Network analyzer E8050A from Keysight technologies
It will take a single measurement on each of its 2 ports. 

# By André LeBlanc, 5th year Electrical Engineering student at Université de Moncton 
August 2021
"""
#-------------------------------------------------------------------------------------------
# Bring in the VISA LIBRARY
import visa
import os
import datetime

"""
NETWORK ANALYZER INIT
"""

# Create a ressource manager
rm = visa.ResourceManager()
rm.list_resources()

# Open the Network analyzer by name
analyzer = rm.open_resource('USB0::0x2A8D::0x0001::MY55201231::0::INSTR')

"""
PARAMETER SELECTION
"""

# Set the time for 10s
analyzer.timeout = 15000
print(analyzer.query('*IDN?'))


# Create one trace on each chanel
analyzer.write(":DISPlay:SPLit 2")


# Create one trace on each chanel and choose the format polar
# channel 1 setting
analyzer.write(":CALCulate1:PARameter:COUNt 1")
analyzer.write("calculate1:measure1:format smith")
analyzer.write("CALCulate1:MEASure1:PARameter 'S11'")


# channel 2 setting
analyzer.write(":CALCulate2:PARameter:COUNt 1")
analyzer.write("calculate2:measure2:format smith")
analyzer.write("CALCulate2:MEASure2:PARameter 'S22'") #utiliser s22 pour le channel 2


# set frequency and number points on each port
numPoints = 101
startFreq = 2.45E9
stopFreq = 2.45E9
numPoints2 = 101
startFreq2 = 2.45E9
stopFreq2 = 2.45E9
analyzer.write("SENS1:SWE:POIN " + str(numPoints))
analyzer.write("SENS1:FREQ:START " + str(startFreq))
analyzer.write("SENS1:FREQ:STOP " + str(stopFreq))
analyzer.write("SENS2:SWE:POIN " + str(numPoints2))
analyzer.write("SENS2:FREQ:START " + str(startFreq2))
analyzer.write("SENS2:FREQ:STOP " + str(stopFreq2))



# Determine, i.e. query, start and stop frequencies, i.e. stimulus begin and end points
analyzer.write("SENS1:FREQ:START?")
startFreqRead = analyzer.read()
analyzer.write("SENS1:FREQ:STOP?")
stopFreqRead = analyzer.read()
print("Analyzer start frequency 1 = " + str(startFreqRead) + " \nStop frequency 1 = " + str(stopFreqRead))

analyzer.write("SENS2:FREQ:START?")
startFreqRead2 = analyzer.read()
analyzer.write("SENS2:FREQ:STOP?")
stopFreqRead2= analyzer.read()
print("Analyzer start frequency 2 = " + str(startFreqRead2) + " \nStop frequency 2 = " + str(stopFreqRead2))


#Set slow sweep so we can see
analyzer.write("SENS1:SWE:TIME 1")
analyzer.write("SENS2:SWE:TIME 1")

# Put both ports in Hold state
analyzer.write("SENS1:SWE:MODE HOLD")
analyzer.write("SENS2:SWE:MODE HOLD")

# Set sweep type to linear for both ports
analyzer.write("SENS1:SWEep:TYPE LIN")
analyzer.write("SENS2:SWEep:TYPE LIN")


#analyzer.assert_trigger()
#analyzer.write ("mmemory:mdirectory 'c:/myFolder2'")  #command to creat a folder in user C: 

x = datetime.datetime.now()
today = x.strftime("%d") + " " + x.strftime("%B") + " " + x.strftime("%Y")
analyzer.write("mmemory:mdirectory 'D:/" + today + "'")


number_of_meas = int(input("How many measurements are you taking ? "))
print("Number of measurements = " + str(number_of_meas))

for x in range(number_of_meas):

  #take 3 set of measurement and save data for channel 1

  analyzer.write("SENS1:SWE:MODE SINGLE")
  analyzer.write("TRIGger:SCOPe CURRent")
  analyzer.write("INITiate1:IMMediate")
  analyzer.write("CALC:MEAS:DATA:SNP:PORTs:Save '1,,', '" + today + "/Port1_Iteration_" + str(x + 1) + ".s1p'")
  analyzer.write("*OPC?")


  analyzer.write("SENS2:SWE:MODE SINGLE")
  analyzer.write("TRIGger:SCOPe CURRent")
  analyzer.write("INITiate1:IMMediate")
  analyzer.write("CALC:MEAS:DATA:SNP:PORTs:Save '1,,', '" + today + "/Port2_Iteration_" + str(x + 1) + ".s1p'")

  
#         # CONVERSION DE FRÉQUENCE DE MHZ À HZ
 #         startFreqHz = startFreq * 1000000
 #         stopFreqHz = stopFreq * 1000000
 #         # Set channel 1 freq and numpoint
 #         analyzer.write("SENS1:SWE:POIN " + str(datapoints))
 #         analyzer.write("SENS1:FREQ:START " + str(startFreqHz))
 #         analyzer.write("SENS1:FREQ:STOP " + str(stopFreqHz))
 #         analyzer.write("SENS1:BAND " + str(BW))
 #
 #         # Determine, i.e. query, number of points in trace for ASCII transfer - query
 #         # Verification of data transfer between host PC and vector analyzer
 #         analyzer.write("SENS1:SWE:POIN?")
 #         numPoints = analyzer.read()
 #
 #         print("Number of trace points (Channel 1)\n" + numPoints)
 #         TextFile.write("\n\n----------NETWORK ANALYZER INIT------------\n\n")
 #         TextFile.write("Number of trace points (Channel 1)\n" + str(numPoints) + "\n")
 #
 #
 #         # Determine, i.e. query, start and stop frequencies, i.e. stimulus begin and end points
 #         # Verification of data transfer between host PC and vector analyzer
 #         analyzer.write("SENS1:FOM:RANG:FREQ:STAR?")
 #         analyzer.write("SENS1:FREQ:START?")
 #         startFreq = analyzer.read()
 #         analyzer.write("SENS1:FREQ:STOP?")
 #         stopFreq = analyzer.read()
 #
 #         print("Analyzer start frequency (Channel 1) = \n" + startFreq + "\n" + "Stop frequency (Channel 1) = \n" + stopFreq)
 #         TextFile.write("Analyzer start frequency (Channel 1) = \n" + str(startFreq) + "\n" + "Stop frequency (Channel 1) = \n" + str(stopFreq) + "\n")
 #
 #         # SET FREQUENCY SWEEP TIME (MINIMUM DELAY FOR REAL TIME APPLICATION)
 #         analyzer.write("SENS1:SWE:TIME " + str(delaimesure))
 #         TextFile.write("Measurement sweep set to " + str(delaimesure) + " seconds\n\n")
 #
 #         # CHANNEL 1 PUT ON HOLD MODE FOR ITS DEFAULT TRIGGER STATE
 #         analyzer.write("SENS1:SWE:MODE HOLD")
 #         TextFile.write("Sweep mode set to HOLD\n\n")
 #
 #         # Saved format specification (RI is selected)
 #         analyzer.write("MMEMory:STOR:TRAC:FORM:SNP RI")
 #
 #         # Selection of sweep type (linear or logarithmic)
 #         if IsLog == 0:
 #             analyzer.write("SENS1:SWEep:TYPE LIN")
 #             print("Linear frequency sweep selected\n")
 #             TextFile.write("Linear frequency sweep selected\n\n")
 #
 #         if IsLog == 1:
 #             analyzer.write("SENS1:SWEep:TYPE LOG")
 #             print("Logarithmic frequency sweep selected\n")
 #             TextFile.write("Logarithmic frequency sweep selected\n\n")
 #
 #
 #         analyzer.write("mmemory:mdirectory 'D:/" + filename + "'")
 #         print("D: drive folder created \n")
 #         TextFile.write("D: drive folder created under the name " + str(filename) + "\n\n")




 #                 # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .CSV (REAL IMAGINARY DATA FORMAT)
 #                 analyzer.write("SENS1:SWE:MODE SINGLE")
 #                 analyzer.write("TRIGger:SCOPe CURRent")
 #                 analyzer.write("INITiate1:IMMediate")
 #                 # analyzer.write("MMEMory:STORe:DATA '" + filename + "/Iteration" + str(i - 1) + "_" + str(j) + ".csv', 'CSV formatted Data','Trace','RI', 1")
 #
 #                 # DELAY OF INPUT GUI VALUE SECONDS
 #                 time.sleep(delaimesure)
 #
 #                 # TAKE MEASUREMENT AND SAVE FILE OF PORT 1 AS A .S1P (REAL IMAGINARY DATA FORMAT)
 #                 analyzer.write("CALC:MEAS:DATA:SNP:PORTs:Save '1,,', '" + filename + "/Iteration_" + str(len(DonneesTemps)) + ".s1p'")
 #                 analyzer.write("*OPC?")
 #                 print("     Measure triggered and saved\n")
 #                 TextFile.write("\n      Measure triggered and saved\n")
