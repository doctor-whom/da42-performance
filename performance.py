import pandas as pd
from numbers import Number
import argparse
import sys
from tabulate import tabulate
import re
import os
import math
import numpy as np

clear = lambda: os.system('clear')
takeoff = pd.read_csv('takeoff.csv')
landing = pd.read_csv('landing.csv')

#interpolate first on weight, then pressure altitude, then temperature
#calculate takeoff distance
def takeoffDistance(tow, toPA, toT):
	tuplePA = round(toPA,3)
	tupleT = tuple(np.subtract(round(toT,1),(5,5)))
	tupleWeight = ((3935,3500),(3500,3000))
	gR = []; gR50 = []; out = []
	#ground roll, ground roll + 50
	if 3935 >= tow >= 3500:
		for weight in tupleWeight[0]:
			for alt in tuplePA:
				for temp in tupleT:
					gR.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll'].iloc[0])
					gR50.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll + 50ft'].iloc[0])
	elif 3500 > tow >= 3000:
		tupleWeight = (3500,3000)
		for weight in tupleWeight:
			for alt in tuplePA:
				for temp in tupleT:
					gR.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll'].iloc[0])
					gR50.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll + 50ft'].iloc[0])
	for takeoffType in [gR,gR50]:
		#Interpolate on Temp
		tempInterpol = []
		for index, pair in enumerate(np.array_split(takeoffType,4)):
			tempInterpol.append(interpolate(tupleT[0],pair[0], tupleT[1],pair[1],toT))
		#Interpolate on PA
		PAInterpol = []
		for index, pair in enumerate(np.array_split(tempInterpol,2)):
			PAInterpol.append(interpolate(tuplePA[0],pair[0], tuplePA[1],pair[1],toPA))
		#Interpolate on Mass
		if 3935 >= tow >= 3500: 
			out.append(interpolate(tupleWeight[0][0],PAInterpol[0],tupleWeight[0][1],PAInterpol[1],tow))
		elif 3500 > tow >= 3000:
			out.append(interpolate(tupleWeight[1][0],PAInterpol[0],tupleWeight[1][1],PAInterpol[1],tow))
	return out
#calculate landing distance
def landingDistance(lw, lPA, lT):
	tuplePA = round(toPA,3)
	tupleT = tuple(np.subtract(round(toT,1),(5,5)))

#calculate climb rates (up to 1000 AGL then to specified cruise altitude) and assuming adiabatic lapse rate
def climb(tow, toPA, toT, cruise):
	pass

#calculate single engine ceiling assuming adiabatic lapse rate
def ceiling(tow,toPA,toT):
	pass


#various helper input functions
def getInputs():
	tow = takeoff_weight()
	lw = landing_weight(tow)[0]
	toPA, toT = airport('takeoff')
	lPA, lT = airport('landing')
	cruiseAlt = cruise()
	clear()

	print ('TO Weight: ' + str(tow) + '\t LDG Weight:' + str(lw) + '\nTO PA: ' + str(toPA) + '\t\t LDG PA: ' \
		+ str(lPA) + '\nTO Temp: ' + str(toT) + '\t\t LDG Temp: ' + str(lT) + '\n Selected Cruise Altitude: ' + str(cruiseAlt))

	return tow, lw, toPA, toT, lPA, lT, cruiseAlt
def takeoff_weight():
	prompt = 'Enter takeoff weight:'
	max_tow = 3935
	min_tow = 3009
	#Check validity
	while (True):
		response = raw_input(prompt)
		try:
			if isinstance(float(response),Number):
				if max_tow >= float(response) >= min_tow:
					return float(response)
				elif float(response) > max_tow:
					print('Entered weight exceeds MTOW')
					continue
				elif float(response) < min_tow:
					print('Entered weight less than Minimum Flight Mass')
					continue
		except:
			print('Invalid numerical input')		
def landing_weight(tow):
	prompt = 'Enter landing weight OR fuel burn in gallons:'
	max_ldg = 3748
	min_flight = 3009
	max_fuel = 454
	#Check validity
	while (True):
		response = raw_input(prompt)
		try:
			if isinstance(float(response),Number):
				if max_ldg >= float(response) >= min_flight:
					return float(response), (tow-float(response))/6
				if max_fuel >= float(response) > 0:
					lw = tow - float(response)*6
					if max_ldg >= lw >= min_flight:
						print('Calculated Landing Weight:' + str(lw))
						return lw, float(response)
					elif lw > max_ldg:
						print('Landing Weight greater than Maximum Landing Weight')
					elif min_flight > lw:
						print('Landing Weight less than Minimum Flight Mass')
				else:
					print('Invalid takeoff weight or fuel burn')
					continue
		except:
			print('Invalid numerical input')
def airport(phase):
	if phase == 'takeoff':
		prompt= 'Enter takeoff field elevation, field altimeter and temperature in celcius. Example: 1000, 29.98, 10 \n'
	else:
		prompt= 'Enter landing field elevation, field altimeter and temperature in celcius. Example: 1000, 29.98, 10 \n'
	while (True):
		response = raw_input(prompt)
		try:
			elev = float(re.split(',',response)[0])
			altimeter = float(re.split(',',response)[1])
			temp = float(re.split(',',response)[2])
			if 25 <= altimeter <= 35 and -35 <= temp <= 45:
				return pressureAlt(elev,altimeter),temp
			else:
				print('Invalid altimeter setting or temperature out of limits')
				continue
		except:
			print('Invalid input, example: 1000, 29.98, 10')
def cruise():
	prompt = 'Enter cruise altitude'
	while (True):
		response = raw_input(prompt)
		try:
			if isinstance(float(response),Number):
				return float(response)
		except:
			print('Invalid numerical input')

#to the nearest nth place
def round(toRound, n):
	return math.ceil(toRound/10**n)*10**n, math.ceil((toRound+10**n)/10**n)*10**n
#Calculate Pressure Altitude
def pressureAlt(elevation,altimeter):
	return int(elevation - (altimeter-29.92)*1000)
#lapse rate 3C/1000ft
def lapseRate(refAlt, refT, alt):
	return refT - 3*(alt-refAlt)/1000
#linear interpolator
def interpolate(x1,y1,x2,y2,x):
	return (float(y2)-float(y1))/(float(x2)-float(x1))*(x-x1) + y1

def main():
	tow, lw, toPA, toT, lPA, lT, cruise = getInputs()
	print takeoffDistance(tow, toPA, toT)



main()