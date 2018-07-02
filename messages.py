"""
Custom messages to be send on various outage conditions.
"""

import time 																	#for getting the current system time within the return strings

#////////////////////////////////Test message\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
def testmsg(labID, temperature, humidity):
	"""
	test message
	"""
	return 'Test: This is a test of '+labID+'. The current system time is '+time.strftime('%a %b %d, %Y, %I.%M %p')+'. The current environment is %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH.'

#////////////////////////////Temperature messages\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
def TOUTmsg(labID, Tmin, Tmax, temperature, humidity):							#initial temperature event message
	"""
	temperature outage message
	"""
	return 'Event: the temperature for '+labID+' is outside its normal range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will be sent should the temperature status change.'

def TinternetOUTmsg(labID, Tmin, Tmax, temperature, humidity):					#initial temperature event during internet outage message
	"""
	temperature outage during ethernet outage
	"""
	return 'Event: the temperature for '+labID+' is outside its normal range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will be sent should the temperature status change.'

def TRETURNmsg(labID, Tmin, Tmax, temperature, humidity):						#message when temperature returns to normal
	"""
	temperature return to normal message
	"""
	return 'Resolved: the temperature for '+labID+' returned to its normal range [%.2f' % Tmin+', %.2f' % Tmax+'] at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'

def TinternetRETURNmsg(labID, Tmin, Tmax, temperature, humidity):				#message when temperature returns to normal during internet outage
	"""
	temperature return to normal during internet outage message
	"""
	return 'Resolved: the temperature for '+labID+' returned to its normal range [%.2f' % Tmin+', %.2f' % Tmax+'] at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'

def Tincmsg(labID, Tmin, Tmax, temperature, humidity):							#message when temperature increases
	"""
	increasing temperature message
	"""
	return 'Update: the temperature for '+labID+' has increased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH.'

def Tdecmsg(labID, Tmin, Tmax, temperature, humidity):							#message when temperature decreases
	"""
	decreasing temperature message
	"""
	return 'Update: the temperature for '+labID+' has decreased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH.'

#//////////////////////////////Humidity messages\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
def RHOUTmsg(labID, RHmin, RHmax, temperature, humidity):						#initial humidity event message
	"""
	humidity outage message
	"""
	return 'Event: the humidity for '+labID+' is outside its normal range [%.2f' % RHmin+', %.2f' % RHmax+'] RH. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will be sent should the humidity status change.'

def RHinternetOUTmsg(labID, RHmin, RHmax, temperature, humidity):				#initial humidity event during internet outage message
	"""
	humidity outage during ethernet outage
	"""
	return 'Event: the humidity for '+labID+' is outside its normal range [%.2f' % RHmin+', %.2f' % RHmax+'] RH. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will be sent should the humidity status change.'

def RHRETURNmsg(labID, RHmin, RHmax, temperature, humidity):					#message when humidity returns to normal
	"""
	humidity return to normal message
	"""
	return 'Resolved: the humidity for '+labID+' returned to its normal range [%.2f' % RHmin+', %.2f' % RHmax+'] at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'

def RHinternetRETURNmsg(labID, RHmin, RHmax, temperature, humidity):			#message when humidity returns to normal
	"""
	humidity return to normal during internet outage message
	"""
	return 'Resolved: the humidity for '+labID+' returned to its normal range [%.2f' % RHmin+', %.2f' % RHmax+'] at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'

def RHincmsg(labID, RHmin, RHmax, temperature, humidity):						#message when humidity increases
	"""
	increasing humidity message
	"""
	return 'Update: the humidity for '+labID+' has increased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH.'

def RHdecmsg(labID, RHmin, RHmax, temperature, humidity):						#message when humidity decreases
	"""
	decreasing humidity message
	"""
	return 'Update: the humidity for '+labID+' has decreased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH.'
