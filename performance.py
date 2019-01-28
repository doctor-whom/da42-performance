import pandas as pd
from numbers import Number
import argparse
import sys
from tabulate import tabulate
import re
import os

clear = lambda: os.system('clear')
#takeoff performance table
takeoff = pd.read_csv('takeoff.csv')


#interpolate first on weight, then pressure altitude, then temperature
#calculate takeoff distance
def takeoffDistance(tow, toPA, toT):
	pass

#calculate landing distance
def landingDistance(lw, lPA, lT):
	pass

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

	return tow, lw, toPA, toT, lPA, lT
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


#Calculate Pressure Altitude
def pressureAlt(elevation,altimeter):
	return int(elevation - (altimeter-29.92)*1000)
#lapse rate 3ºC/1000ft
def lapseRate(refAlt, refT, alt):
	return refT - 3*(alt-refAlt)/1000
#linear interpolator
def interpolate(x1,y1,x2,y2,x):
	return (float(y2)-float(y1))/(float(x2)-float(x1))*(x-x1) + y1

def main():
	tow, lw, toPA, toT, lPA, lT, cruise = getInputs()



main()