import pandas as pd
from numbers import Number
import argparse
import sys
from tabulate import tabulate
import re
import os
import math
import numpy as np
from scipy import stats

clear = lambda: os.system('clear')

takeoff = pd.read_csv('takeoff.csv')
climbRate = pd.read_csv('climb.csv')
landing = pd.read_csv('landing.csv')

#interpolate first on temp, then pressure altitude, then mass
#calculate takeoff distance
def takeoffDistance(tow, toPA, toT):
	tuplePA = multipleRound(toPA,1000)
	tupleT = tuple(np.add(multipleRound(toT,10),(5,5)))
	tupleWeight = ((3935,3500),(3500,3000))
	gR = []; gR50 = []; out = []
	#ground roll, ground roll + 50
	if 3935 >= tow >= 3500 and toPA >= 0:
		for weight in tupleWeight[0]:
			for alt in tuplePA:
				for temp in tupleT:
					gR.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll'].iloc[0])
					gR50.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll + 50ft'].iloc[0])
	elif 3500 > tow >= 3000 and toPA >= 0:
		for weight in tupleWeight[1]:
			for alt in tuplePA:
				for temp in tupleT:
					gR.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll'].iloc[0])
					gR50.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll + 50ft'].iloc[0])
	#in case negative pressure altitude, just use 0 and 1000 PA to linear extrapolate
	elif 3935 >= tow >= 3500 and toPA < 0:
		tuplePA = (0,1000)
		for weight in tupleWeight[0]:
			for alt in tuplePA:
				for temp in tupleT:
					gR.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll'].iloc[0])
					gR50.append(takeoff.loc[(takeoff.Weight == weight) & (takeoff.PA == alt) & (takeoff.Temp == temp)]['Ground Roll + 50ft'].iloc[0])
	elif 3500 > tow >= 3000 and toPA < 0:
		tuplePA = (0,1000)
		for weight in tupleWeight[1]:
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
def landingDistance(lPA, lT):
	tuplePA = multipleRound(lPA,1000)
	if lPA < 0:
		tuplePA = (0,1000)
	tupleT = tuple(np.add(multipleRound(lT,10),(5,5)))
	lR = []; lR50 = []; out = []

	for alt in tuplePA:
		for temp in tupleT:
			lR.append(landing.loc[(landing.Temp == temp) & (landing.PA == alt)]['Ground Roll'].iloc[0])
			lR50.append(landing.loc[(landing.Temp == temp) & (landing.PA == alt)]['Ground Roll + 50ft'].iloc[0])
	#Interpolate on temp then PA
	for takeoffType in [lR,lR50]:
		tempInterpol = []
		for index, pair in enumerate(np.array_split(takeoffType,2)):
			tempInterpol.append(interpolate(tuplePA[0],pair[0],tuplePA[1],pair[1],lPA))
		out.append(interpolate(tupleT[0],tempInterpol[0],tupleT[1],tempInterpol[1],lT))

	return out[0],out[1]
#calculate climb rates (up to 1000 AGL then to specified cruise altitude) and assuming adiabatic lapse rate
def climb(tow, toPA, toT, cruise):
	tupleWeight = ((3935,3500),(3500,3000))
	tempAloft = ((toPA, toT),(toPA + 1000, lapseRate(toPA, toT, toPA + 1000)),(cruise, lapseRate(toPA, toT, cruise)))
	out = [[],[],[]]

	for point in tempAloft:
		tupleAlt = multipleRound(point[0],1000); tupleTemp = multipleRound(point[1],5);
		tupleWeightMax = (3935,3500); tupleWeightMin = (3500,3000); tupleWeight = (0,0)
		cR = []; cRMCP = []; cROEI = [];
		if 3935 >= tow >= 3500:
			tupleWeight = tupleWeightMax
		elif 3500 > tow >= 3000 and toPA >= 0:
			tupleWeight = tupleWeightMin
		if toPA < 0:
			tupleAlt = (0,1000)

		for weight in tupleWeight:
			for alt in tupleAlt:
				for temp in tupleTemp:
					cR.append(climbRate.loc[(climbRate.Weight == weight) & (climbRate.PA == alt) & (climbRate.Temp == temp)]['TO Climb Rate'].iloc[0])
					cRMCP.append(climbRate.loc[(climbRate.Weight == weight) & (climbRate.PA == alt) & (climbRate.Temp == temp)]['MCP Climb Rate'].iloc[0])
					cROEI.append(climbRate.loc[(climbRate.Weight == weight) & (climbRate.PA == alt) & (climbRate.Temp == temp)]['OEI Climb Rate'].iloc[0])

		for idx, climbType in enumerate([cR, cRMCP, cROEI]):
			# Interpolate on Temp interpolate(T1,C1,T2,C2,T)
			tempInterpol = []
			for index, pair in enumerate(np.array_split(climbType,4)):
				tempInterpol.append(interpolate(tupleTemp[0],pair[0], tupleTemp[1], pair[1], point[1]))
			# Interpolate on PA
			PAInterpol = []
			for index, pair in enumerate(np.array_split(tempInterpol,2)):
				PAInterpol.append(interpolate(tupleAlt[0],pair[0], tupleAlt[1], pair[1], point[0]))
			# Interpolate on Mass
			out[idx].append(interpolate(tupleWeight[0],PAInterpol[0],tupleWeight[1],PAInterpol[1],tow))
	# out: [airport, airport + 1000, cruise][T/O, MCP, OEI]
	# T/O climb average to 1000 AGL, MCP climb between 1000 AGL and cruise,  OEI climb to 1000 AGL
	return np.mean(out[0][0:2]), np.mean(out[1][1:3]), np.mean(out[2][0:2])

#calculate single engine ceiling assuming adiabatic lapse rate
def ceiling(mass,PA,T):
	tupleWeight = ((3935,3500),(3500,3000))
	seedAltitude = np.arange(0,18000,step=100)
	tupleWeightMax = (3935,3500); tupleWeightMin = (3500,3000); tupleWeight = (0,0)

	if 3935 >= mass >= 3500:
			tupleWeight = tupleWeightMax
	elif 3500 > mass >= 3000:
			tupleWeight = tupleWeightMin

	while(True):
		for altitude in seedAltitude:
			tempAloft = lapseRate(PA, T, altitude)
			tupleAlt = multipleRound(altitude,1000)
			tupleT = multipleRound(tempAloft,5)

			altOut = []

			for alt in tupleAlt:
				for weight in tupleWeight:
					x = climbRate.loc[(climbRate.PA == alt)&(climbRate.Weight == weight)]['Temp'].values
					y = climbRate.loc[(climbRate.PA == alt)&(climbRate.Weight == weight)]['OEI Climb Rate'].values

					slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)

					altOut.append(slope*tempAloft + intercept)

			upperMass = interpolate(tupleAlt[0],altOut[0],tupleAlt[1],altOut[2],altitude)
			lowerMass = interpolate(tupleAlt[0],altOut[1],tupleAlt[1],altOut[3],altitude)

			seedClimb = interpolate(tupleWeight[0],upperMass,tupleWeight[1],lowerMass,mass)

			if seedClimb < 50:
				return seedClimb, altitude
				break
		break
	
#various helper input functions
def getInputs():
	tow = takeoff_weight()
	lw = landing_weight(tow)[0]
	toPA, toT = airport('takeoff')
	lPA, lT = airport('landing')
	cruiseAlt = cruise()
	clear()

	print ('| TO Weight: ' + str(tow) + '\t LDG Weight:' + str(lw) + ' \t|\n| TO PA: ' + str(toPA) + '\t\t LDG PA: ' \
		+ str(lPA) + ' \t\t|\n| TO Temp: ' + str(toT) + '\t\t LDG Temp: ' + str(lT) + ' \t|\n| Selected Cruise Altitude: ' + str(cruiseAlt) \
		+ '\t\t|\n')

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
			if 25 <= altimeter <= 35 and -35 <= temp <= 45 and pressureAlt(elev,altimeter) <= 10000:
				return pressureAlt(elev,altimeter), temp
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

#to nearest multiples
def multipleRound(x,n):
	if x%n != 0:
		return x-(x%n), x + (-x%n)
	elif x == 0:
		return x,n
	else:
		return x-n,x
#Calculate Pressure Altitude
def pressureAlt(elevation,altimeter):
	return int(elevation - (altimeter-29.92)*1000)
#lapse rate 3C/1000ft
def lapseRate(refAlt, refT, alt):
	return float(float(refT) - 3.0*(float(alt)-float(refAlt))/1000.0)
#linear interpolator
def interpolate(x1,y1,x2,y2,x):
	return (float(y2)-float(y1))/(float(x2)-float(x1))*(x-x1) + y1

def main():
	tow, lw, toPA, toT, lPA, lT, cruise = getInputs()
	TOgroundRoll, TOgroundRoll50 = takeoffDistance(tow, toPA, toT)
	tOClimb, cruiseClimb, OEIClimb = climb(tow,toPA, toT, cruise)
	LDGgroundRoll, LDGgroundRoll50 = landingDistance(lPA,lT)
	climbRateCeilingTO, OEICeilingTO = ceiling(tow,toPA,toT)
	climbRateCeilingLDG, OEICeilingLDG = ceiling(lw,lPA,lT)

	print ('T/O Ground Roll: ' + str(int(TOgroundRoll)) +'\t\t Landing Ground Roll: ' \
		+ str(int(LDGgroundRoll)) + '\nT/O Ground Roll + 50\': ' + str(int(TOgroundRoll50))+'\t Landing Ground Roll + 50\': ' \
		+ str(int(LDGgroundRoll50)) +'\nAccelerate Stop Distance: ' + str(int(TOgroundRoll50)+int(LDGgroundRoll50)) )
	
	print ('\nT/O Climb: ' + str(int(tOClimb)) +' ft/min \t\t\t' + str(int(tOClimb*0.66)) +' ft/nmi\n' + \
		'Cruise Climb: ' + str(int(cruiseClimb)) + ' ft/min\nOEI Climb to 1000 AGL: ' + str(int(OEIClimb))+ \
		' ft/min\t' + str(int(OEIClimb*0.66))+ ' ft/nmi\n')

	print ('At T/O:\n Single Engine Ceiling: ' + str(int(OEICeilingTO)) + '\t Single Engine Ceiling Climb Rate: ' \
		+ str(int(climbRateCeilingTO)))

	print ('At LDG:\n Single Engine Ceiling: ' + str(int(OEICeilingLDG)) + '\t Single Engine Ceiling Climb Rate: ' \
		+ str(int(climbRateCeilingLDG)))


main()