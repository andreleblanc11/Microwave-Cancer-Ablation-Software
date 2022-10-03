# Automated Microwave Ablation test software for Cancer Research
***
- This repository holds the embedded software for the Automated Microwave Ablation tests conducted on beef liver by the ACRI (Atlantic Cancer Research Institute). The tests are configured via GUI to improve the operator user experience.
- It also consists of my work realised in the summer of 2021 for my last coop internship.
   Five machines were combined together (Network Analyzer : ENA5080A, Microwave Generator: KMS200, Switch: BN754098, Peristaltic Pump: VWR-PP4400, Isocratic Pump: Agilent 1200).
  - Through the network analyzer, accompanied by an automatic load calibrater (Ecal), accurate dielectric measurements were taken to track its evolution through time.
  - The microwave generator can be timed in different instances (will need to modify code) or by using one of the two functions available in the GUI menu page.
  - The test procedure utilized for our measurements is found in the **TestProcedure_French_ACRI2022** folder.
  	- It gives a detailed explanation of the test hardware, the test software as well as all of the steps followed.
- The final version of the code is available in the directory *src/CircuitAutomatisation_V5_2021*.
- The **2ports_Measurements.py** is able to control two ports simultaneously on the network analyzer.

- All code can be used by all. Unfortunately, the tests had to be stopped due to a budget shortage. I am hoping this can be utilized by another group of researchers to help improve cancer ablation technologies.
