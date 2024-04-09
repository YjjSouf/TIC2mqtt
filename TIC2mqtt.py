

####-----
#	Soufian YJJOU, 2024. Under MIT LICENSE
#	All is in english here, but 99% of users mights be French so... Bonjour à vous !
#	This script reads a serial input and retrieves the TIC data if any. Only adapted to TEMPO contracts with EDF as a supplier.
#	To read the tic data, the reference documentation is from ENEDIS: Enedis-NOI-CPT_54E, 06/2018 https://www.enedis.fr/media/2035/download
#	Once data is recovered, the script updates a few mqqt topics. Computes Power based on energy consumption as a bonus.
#	Feel free to use this code as per the license file on github: https://github.com/YjjSouf/TIC2mqtt
#	Disclamer! This code is provided free of charge for you to use. However, errors, bugs or issues might araise.
#	Please, take your responsabilities. I cannot be held responsible for any loss that might be induced from the use of this script.
###-----




import serial
from time import sleep
import paho.mqtt.publish as publish
import sys
import numpy as np
import time



# Checks if the data fields match the chksum. If not, return false
#Checksum = (S1 & 0x3F) + 0x20
def checksum(s_input):
	char = (sum(bytearray((s_input[0]+" "+s_input[1]).encode())) & 0x3F) + 0x20
	return (chr(char) == s_input[2])



Pwr_update_interval_s = 5 	#Time period between apparent power updates
E_update_interval_p = 4 	#number of Pwr updates before energy update

#Main variable init. Naming: E{B, W, R} = Energy Blue, White, Red. H{C,P} = Heure Cruse/Pleine
Tempo_Color="----"
EB_HC_Wh=0
EB_HP_Wh=0
EW_HC_Wh=0
EW_HP_Wh=0
ER_HC_Wh=0
ER_HP_Wh=0

#Aux variables, to store previous measurement for power calculation (auxp). not to get confused with (aux) which is used to check sanity of measurements.
EB_HC_Wh_auxp=0
EB_HP_Wh_auxp=0
EW_HC_Wh_auxp=0
EW_HP_Wh_auxp=0
ER_HC_Wh_auxp=0
ER_HP_Wh_auxp=0

AppPwr_VA=0 	#Apparent power (VA) straight from the TIC data.
EffPwr_W=0	#Effective power (W) derived from comsuption.
timer=0
ts = time.time()
ts_aux = ts	#Aux variable to store last measurement time stamp


# build a table mapping all non-printable characters to None to avoid weird prints
NOPRINT_TRANS_TABLE = {
    i: None for i in range(0, sys.maxunicode + 1) if not chr(i).isprintable()
}


# init serial com. Very very important to keep timeout to None. otherwise, the flush operation fails and you get "lagged" values.
# Pay attention to the baud rate byte size etc. This is not the default 9600 you might be used to.
ser = serial.Serial ("/dev/ttyUSB0", 1200, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=None)    #Open port with baud rate

#Let's start processing...
while True:

	corrupted_data=False	#Flag is set but unused at the moment due to a bug when the checksum char is a " "...
	EB_HC_Wh_aux=EB_HC_Wh
	EB_HP_Wh_aux=EB_HP_Wh
	EW_HC_Wh_aux=EW_HC_Wh
	EW_HP_Wh_aux=EW_HP_Wh
	ER_HC_Wh_aux=ER_HC_Wh
	ER_HP_Wh_aux=ER_HP_Wh
	EB_HC_Wh=0
	EB_HP_Wh=0
	EW_HC_Wh=0
	EW_HP_Wh=0
	ER_HC_Wh=0
	ER_HP_Wh=0
	AppPwr_VA=-1
	EffPwr_W=-1
	received_data = "flush" #Random string.
	
	ser.flushInput() #Flush whatever is in the buffer (partial data, accumulated packets...)
	ser.flushOutput()
	received_data = ser.read_until(b"ADCO xxxxxxxxxxxx =") #force the fush till the end of the data packet. Fill with your ADCO number.
	

	received_data = ser.read_until(b"ADCO xxxxxxxxxxxx =").decode() # reads a full data packet. Fill with your ADCO number.

	#Makes sure there is something in the received data.
	if(len(received_data) > 120):
		data = received_data.split("\r\n")
		
		#Makes sure there is something in the received data.
		if(data[2].find("ISOUSC") != -1):
			#print(data)
			try:
				if(data[13].split(" ")[0].find("PAPP") != -1 and checksum(data[13].split(" "))):	
					AppPwr_VA = int(data[13].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					AppPwr_VA = -1
					print("e")
				if(data[3].split(" ")[0].find("BBRHCJB") != -1 and checksum(data[3].split(" "))):
					EB_HC_Wh = int(data[3].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					EB_HC_Wh=-1
					print("f")
				if(data[4].split(" ")[0].find("BBRHPJB") != -1 and checksum(data[4].split(" "))):
					EB_HP_Wh = int(data[4].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					EB_HP_Wh =-1
					print("g")
				if(data[5].split(" ")[0].find("BBRHCJW") != -1 and checksum(data[5].split(" "))):				
					EW_HC_Wh = int(data[5].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					print("h")
					EW_HC_Wh=-1
				if(data[6].split(" ")[0].find("BBRHPJW") != -1 and checksum(data[6].split(" "))):								
					EW_HP_Wh = int(data[6].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					print("i")
					EW_HP_Wh=-1
				if(data[7].split(" ")[0].find("BBRHCJR") != -1 and checksum(data[7].split(" "))):								
					ER_HC_Wh = int(data[7].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					print("j")
					ER_HC_Wh=-1
				if(data[8].split(" ")[0].find("BBRHPJR") != -1 and checksum(data[8].split(" "))):												
					ER_HP_Wh = int(data[8].split(" ")[1].translate(NOPRINT_TRANS_TABLE))
				else:
					corrupted_data = True
					print("k")
					ER_HP_Wh=-1
				if(data[10].split(" ")[0].find("DEMAIN") != -1 and checksum(data[10].split(" "))):												
					Tempo_Color = data[10].split(" ")[1].translate(NOPRINT_TRANS_TABLE)
				else:
					corrupted_data = True
					print("l")
					Tempo_Color="----"
			except:
				print("failed to turn into int some inputs.")
				corrupted_data=True
				
	#Flag disabled until the " " char is accepted by the checksum function as valid. This happens once in a while but a true issue..			
	if(not corrupted_data or True):

		timer+=1 # start counting. will only update Energy (E) once periodiciy is reached
		if(timer >= E_update_interval_p):
			ts = time.time()
			#Sanity check...
			if(EB_HC_Wh >= EB_HC_Wh_aux and EB_HC_Wh>0):
				if(EB_HC_Wh_auxp ==0): #First loop? init then
					EB_HC_Wh_auxp = EB_HC_Wh
				publish.single("Maison/Energie/EB_HC_Wh", EB_HC_Wh, hostname="localhost") #Feel free to update the mqqt structure to suite your needs.
				#computing Effective power...
				EffPwr_W = float(EB_HC_Wh - EB_HC_Wh_auxp)/(ts - ts_aux)*3600.0
				if(EB_HC_Wh - EB_HC_Wh_auxp > 0): #Maybe the periodiciy is not enough for you to consume 1Wh. If not, do not update ts_aux and auxp.
					EB_HC_Wh_auxp = EB_HC_Wh
					ts_aux = ts
					
			if(EB_HP_Wh >= EB_HP_Wh_aux and EB_HP_Wh>0):
				if(EB_HP_Wh_auxp ==0):
					EB_HP_Wh_auxp = EB_HP_Wh
				publish.single("Maison/Energie/EB_HP_Wh", EB_HP_Wh, hostname="localhost")
				if(EffPwr_W <=0):
					EffPwr_W = float(EB_HP_Wh - EB_HP_Wh_auxp)*3600.0/(ts - ts_aux)
					if(EB_HP_Wh - EB_HP_Wh_auxp > 0):
						EB_HP_Wh_auxp = EB_HP_Wh
						ts_aux = ts

			if(EW_HC_Wh >= EW_HC_Wh_aux and EW_HC_Wh>0):
				if(EW_HC_Wh_auxp ==0):
					EW_HC_Wh_auxp = EW_HC_Wh	
				publish.single("Maison/Energie/EW_HC_Wh", EW_HC_Wh, hostname="localhost")
				if(EffPwr_W <=0):
					EffPwr_W = float(EW_HC_Wh - EW_HC_Wh_auxp)/(ts - ts_aux)*3600.0
					if(EffPwr_W > 0):
						EW_HC_Wh_auxp = EW_HC_Wh
						ts_aux = ts

			if(EW_HP_Wh >= EW_HP_Wh_aux and EW_HP_Wh>0):
				if(EW_HP_Wh_auxp ==0):
					EW_HP_Wh_auxp = EW_HP_Wh
				publish.single("Maison/Energie/EW_HP_Wh", EW_HP_Wh, hostname="localhost")
				if(EffPwr_W <=0):
					EffPwr_W = float(EW_HP_Wh - EW_HP_Wh_auxp)/(ts - ts_aux)*3600.0
					if(EffPwr_W > 0):
						EW_HP_Wh_auxp = EW_HP_Wh
						ts_aux = ts

			if(ER_HC_Wh >= ER_HC_Wh_aux and ER_HC_Wh>0):
				if(ER_HC_Wh_auxp ==0):
					ER_HC_Wh_auxp = ER_HC_Wh
				publish.single("Maison/Energie/ER_HC_Wh", ER_HC_Wh, hostname="localhost")
				if(EffPwr_W <=0):
					EffPwr_W = float(ER_HC_Wh - ER_HC_Wh_auxp)/(ts - ts_aux)*3600.0
					if(EffPwr_W > 0):
						ER_HC_Wh_auxp = ER_HC_Wh
						ts_aux = ts

			if(ER_HP_Wh >= ER_HP_Wh_aux and ER_HP_Wh>0):
				if(ER_HP_Wh_auxp ==0):
					ER_HP_Wh_auxp = ER_HP_Wh
				publish.single("Maison/Energie/ER_HP_Wh", ER_HP_Wh, hostname="localhost")
				if(EffPwr_W <=0):
					EffPwr_W = float(ER_HP_Wh - ER_HP_Wh_auxp)/(ts - ts_aux)*3600.0
					if(EffPwr_W > 0):
						ER_HP_Wh_auxp = ER_HP_Wh
						ts_aux = ts

			if(Tempo_Color != "----"):
				publish.single("Maison/Energie/Tempo_Color", Tempo_Color, hostname="localhost")
			timer=0
		if(AppPwr_VA > -1):
			publish.single("Maison/Energie/AppPwr_VA", AppPwr_VA, hostname="localhost")
		
		#At this point, if EffPwr is 0W	we provide the highest possible power that would fly under the radar based on the time base. Next loop might catch it.
		if(EffPwr_W == 0):
			EffPwr_W = 3600.0/(ts - ts_aux)
		#Never pubish if 0 or -1. Lowest I could get is 4W in my particular case and I'm fine with this.
		if(EffPwr_W > 0):
			publish.single("Maison/Energie/EffPwr_W", EffPwr_W, hostname="localhost")		
		sleep(Pwr_update_interval_s)
	else:
		#print("Apparent Pwr (VA):\t"+str(AppPwr_VA))
		#print("Total energy (kWh):\t"+str(float(E_Wh)/1000.0))
		print("TIC2mqtt: data discarded")

			