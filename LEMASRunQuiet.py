#LEMASRun.py
#   Tested with Python 3.6.1 (Anaconda 4.4.0 stack) on Linux Mint 18.2 Sonya Cinnamon, Python 3.4.2, on Raspbian Linux
#
#///////////////////////////////////////////////////////////////////////////////
## LEMASRun.py Notes
#   August, 2017
#   Authored by: Michael Braine, Physical Science Technician, NIST, Gaithersburg, MD
#       PHONE: 301 975 8746
#       EMAIL: michael.braine@nist.gov (use this instead of phone)
#
#   Purpose
#       continuously read temperature and humidity from instrument, send notification via text/email with graph attached to lab users if temperature or humidity is outside of specified limits
#       log temperature and humidity to <month><YYYY>-all.env.csv
#       log temperature and humidity outages to <month><YYYY>-outage.env.csv
#
#///////////////////////////////////////////////////////////////////////////////
## References
#       none
#
##///////////////////////////////////////////////////////////////////////////////
## Change log from v1.11 to v1.12
#   May 30, 2018
#
#   ver 1.12    - moved server information into .py file to easily edit in the public distribution
#               - moved instrument interface into .py file to  easily edit in the public distribution
#               - moved messages into .py file to easily edit in the public distribution
#               - added variable for number of tickmarks on y-axis
#
#///////////////////////////////////////////////////////////////////////////////

import smtplib, time, os, csv, datetime, copy, minimalmodbus
print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Starting Laboratory Environment Monitoring and Alert System (LEMAS)')

with open('/home/pi/LEMASdist/version', 'r') as fin:
    print(fin.read()'\n\nQuietMode')

## import python libraries
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

program_directory = '/home/pi/LEMASdist'
os.chdir(program_directory)

#//////////////////////////Import various configurations\\\\\\\\\\\\\\\\\\\\\\\\
from LabID import labID
from SensorSerial import sensorserial
from Tcontrols import Tcontrols
from RHcontrols import RHcontrols
from corrections import corrections

from Contacts import allcontacts
from Contacts import labusers as labusers_dict

from testmsgdate import TestmsgDate

from ServerInfo import *

from messages import *

from LabSettings import *

#//////////////////////////Import instrument interface\\\\\\\\\\\\\\\\\\\\\\\\\\
from InstrInterface import *

os.chdir(program_directory+'/tmpimg')

correction = copy.deepcopy(corrections[sensorserial])               #[temperature, humidity]
TestmsgDate = datetime.datetime.strptime(TestmsgDate, "%B %d, %Y %H:%M:%S")

#///////////////////////////Outage Parameter Setup\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#set up parameters
graph_pts = round(graphtime*pts_hr)                                             #maximum number of recent points to plot
sleeptimer = (pts_hr / 60 / 60)**-1                                             #amount of time for system to wait until next temperature, seconds
Tmin = Tcontrols[labID][0]                                                      #get lower temperature limit for assigned lab
Tmax = Tcontrols[labID][1]                                                      #get upper temperature limit for assigned lab
RHmin = RHcontrols[labID][0]                                                    #get lower humidity limit for assigned lab
RHmax = RHcontrols[labID][1]                                                    #get upper humidity limit for assigned lab
TincAlert = [Tmin - TincSet, Tmax + TincSet]
RHincAlert = [RHmin - RHincSet, RHmax + RHincSet]

labusers = copy.deepcopy(labusers_dict[labID])
labcontacts = np.array([])
for icontact in range(len(labusers)):
    labcontacts = np.append(labcontacts, allcontacts[labusers[icontact]])

envdata_directory = '/home/pi/Desktop/EnvironmentData'                          #where data is stored in Linux file system, create if doesn't exist, doesn't really ever need changed
TestmsgSent = False                                                             #initialize test message has not been sent
ethoutage = False                                                               #initialize with internet outage status as false
ethoutage_sent = False                                                          #initialize status of messages queued under internet outage as not sent

#///////////////////////////Function Definitions\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#define message sending functions
def SendMessage(toaddress, message):                                            #function for sending regular messages
    msg = MIMEMultipart()                                                       #define msg as having multiple components
    msg['Subject'] = 'DMG Alert: '+labID+' event log'
    msg['From'] = fromaddress
    msg['To'] = toaddress
    text = MIMEText(message)
    msg.attach(text)

    server = smtplib.SMTP(SMTPaddress, SMTPport)
    try:
        server.starttls()
    except Exception:
        print('Looks like your SMTP server may not support TLS. Continuing to send message without it.')
    if len(username) != 0:
        try:
            server.login(username, passwd)
        except Exception:
            print('Either your username and/or password is incorrect, or you do not need to log in to your SMTP server to send messages.')
            print('If a message is received, then no login is needed and you can leave username and password blank.')
    server.sendmail('dmgalert@nist.gov', toaddress, msg.as_string())
    server.quit()

def SendMessageMMS(toaddress, message, img_path):                               #function for sending messages with image attached
    msg = MIMEMultipart()                                                       #define msg as having multiple components
    msg['Subject'] = 'DMG Alert: '+labID+' Environment Event'
    msg['From'] = fromaddress
    msg['To'] = toaddress
    text = MIMEText(message)
    msg.attach(text)
    img_file = open(img_path, 'rb').read()
    image_attach = MIMEImage(img_file)
    msg.attach(image_attach)

    server = smtplib.SMTP(SMTPaddress, SMTPport)
    try:
        server.starttls()
    except Exception:
        print('Looks like your SMTP server may not support TLS. Continuing to send message without it.')
    if len(username) != 0:
        try:
            server.login(username, passwd)
        except Exception:
            print('Either your username and/or password is incorrect, or you do not need to log in to your SMTP server to send messages.')
            print('If a message is received, then no login is needed and you can leave username and password blank.')
    time.sleep(0.5)
    server.sendmail(fromaddress, toaddress, msg.as_string())
    server.quit()

instr_obj = ConnectInstr(instrport)                                             #connect to instrument

#////////////////////////Variable Initialization\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
## Initialize variables and figure setup
currenttime = np.array([])                                                      #initialize empty lists
axestime = np.array([])
temperature = []
humidity = []
tf_alert_T = []
tf_alert_RH = []
plt.ion()                                                                       #activate interactive plotting
fig = plt.figure(num=1, figsize=(figsize_x,figsize_y), dpi=dpi_set)             #get matplotlib figure ID, set figure size
gs = gridspec.GridSpec(r_plot, c_plot)
gs.update(hspace=hspace_set)
ax1 = plt.subplot(gs[0,:])
ax2 = plt.subplot(gs[1,:])
fig.subplots_adjust(left=0.06, right=1, top=0.98, bottom=0.14)
fig.canvas.toolbar.pack_forget()
labstatus_T = 'normal'
labstatus_RH = 'normal'

#///////////////////////Initial Environment Data\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
## Initial temperature, humidity, and time values
#used for inside the loop, checking for bad readings
#check requires at least two values, second acquired in the loop
#initial temperature
try:
    temptemp = ReadTemperature(instr_obj)                                                #read instrument modbus address for temperature
except Exception:                                                               #reestablish connection if failed
    instr_obj = Instr_errfix(instr_obj)
    try:
        temptemp = ReadTemperature(instr_obj)                                            #read instrumnet modbus address for temperature
    except Exception:
        instr_obj = Instr_errfix(instr_obj)
        try:
            temptemp = ReadTemperature(instr_obj)
        except Exception:
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
temperature.append(temptemp + correction[0])

#initial humidity
try:
    temphumid = ReadHumidity(instr_obj)                                                  #read instrument modbus address for humidity
except Exception:                                                               #reestablish connection if failed
    instr_obj = Instr_errfix(instr_obj)
    try:
        temphumid = ReadHumidity(instr_obj)                                              #read instrument modbus address for humidity
    except Exception:
        instr_obj = Instr_errfix(instr_obj)
        try:
            temphumid = ReadHumidity(instr_obj)
        except Exception:
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
humidity.append(temphumid + correction[1])

#initial time data
currenttime = np.append(currenttime, time.strftime("%Y-%m-%d %H:%M:%S"))        #get current system time (yyyy mm dd hh mm ss)
axestime = np.append(axestime, time.strftime("%H:%M"))

#/////////////////////////////Eternal Loop\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
## Measure temperature and humidity for all eternity
while True:
    ti = time.time()                                                            #begin/reset active timer---------------------------------------------------------------------------
    #//////////////////////////Instrument Communications\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    #read temperature
    try:
        temptemp = ReadTemperature(instr_obj)                                            #read instrument modbus address for temperature
    except Exception:                                                           #reestablish connection if failed
        instr_obj = Instr_errfix(instr_obj)
        try:
            temptemp = ReadTemperature(instr_obj)                                        #read instrument modbus address for temperature
        except Exception:
            instr_obj = Instr_errfix(instr_obj)
            try:
                temptemp = ReadTemperature(instr_obj)
            except Exception:
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')

    #if suspected bad sensor read, read temperature again
    if abs(temptemp - temperature[-1]) > rereadT:
        time.sleep(10)
        try:
            temptemp = ReadTemperature(instr_obj)                                        #read instrument modbus address for temperature
        except Exception:
            instr_obj = Instr_errfix(instr_obj)
            try:
                temptemp = ReadTemperature(instr_obj)                                    #read instrument modbus address for temperature
            except Exception:
                instr_obj = Instr_errfix(instr_obj)
                try:
                    temptemp = ReadTemperature(instr_obj)
                except Exception:
                    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
    temperature.append(temptemp + correction[0])

    #read humidity
    try:
        temphumid = ReadHumidity(instr_obj)                                              #read instrument modbus address for humidity
    except Exception:                                                           #reestablish connection if failed
        instr_obj = Instr_errfix(instr_obj)
        try:
            temphumid = ReadHumidity(instr_obj)                                          #read instrument modbus address for humidity
        except Exception:
            instr_obj = Instr_errfix(instr_obj)
            try:
                temphumid = ReadHumidity(instr_obj)
            except Exception:
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')

    #if suspected bad sensor read, read humidity again
    if abs(temphumid - humidity[-1]) > rereadRH:
        time.sleep(10)
        try:
            temphumid = ReadHumidity(instr_obj)                                          #read instrument modbus address for humidity
        except Exception:
            instr_obj = Instr_errfix(instr_obj)
            try:
                temphumid = ReadHumidity(instr_obj)                                      #read instrument modbus address for humidity
            except Exception:
                instr_obj = Instr_errfix(instr_obj)
                try:
                    temphumid = ReadHumidity(instr_obj)
                except Exception:
                    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
    humidity.append(temphumid + correction[1])

    #get and format time
    currenttime = np.append(currenttime, time.strftime("%Y-%m-%d %H:%M:%S"))    #get current system time (yyyy mm dd hh mm ss)
    axestime = np.append(axestime, time.strftime("%H:%M"))

    #remove oldest data points from memory that no longer need graphed
    if len(temperature) >= graph_pts:
        del temperature[0]
        del humidity[0]
        currenttime = np.delete(currenttime, 0)
        axestime = np.delete(axestime, 0)

    #///////////////////////////////Update Graphs\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    time_vec = range(len(axestime))

    #plot temperature
    ax1 = plt.subplot(gs[0,:])
    plt.cla()
    plt.plot(time_vec, temperature, 'r-', linewidth=GraphLinewidth)
    plt.plot(time_vec, np.zeros([len(time_vec),])+Tmin, 'b-', linewidth=0.25)
    plt.plot(time_vec, np.zeros([len(time_vec),])+Tmax, 'b-', linewidth=0.25)
    plt.fill_between(np.array(time_vec), np.zeros([len(time_vec),])+Tmin, np.zeros([len(time_vec),])-1000, alpha=0.2, color='lightblue')
    plt.fill_between(np.array(time_vec), np.zeros([len(time_vec),])+Tmax, np.zeros([len(time_vec),])+1000, alpha=0.2, color='lightblue')
    ax1.set_ylim([min(temperature)-graphTmin, max(temperature)+graphTmax])      #y-axis limits
    ax1.ticklabel_format(style='plain')                                         #disable scientific notation on y-axis
    plt.setp(ax1.get_xticklabels(), visible=False)                              #hide tickmarks, will use shared axis
    plt.grid(color='gray', alpha=0.3)
    plt.text(0.05, 0.1, 'Temperature (deg. C)', transform=ax1.transAxes, alpha=0.5, fontsize=FontsizeLabel, color='gray') #add transparent text to bottom left of first axes
    ax1.patch.set_facecolor('black')
    plt.yticks(np.round(np.linspace(min(temperature)-graphTmin, max(temperature)+graphTmax, nticks_y), 1), fontsize=FontsizeYticks)
    plt.ticklabel_format(useOffset=False)

    #plot humidity with temperature's x-axis
    ax2 = plt.subplot(gs[1,:], sharex=ax1)
    plt.cla()
    plt.plot(time_vec, humidity, 'g-', linewidth=GraphLinewidth)
    plt.plot(time_vec, np.zeros([len(time_vec),])+RHmin, 'b-', linewidth=0.25)
    plt.plot(time_vec, np.zeros([len(time_vec),])+RHmax, 'b-', linewidth=0.25)
    plt.fill_between(np.array(time_vec), np.zeros([len(time_vec),])+RHmin, np.zeros([len(time_vec),])-1000, alpha=0.2, color='lightblue')
    plt.fill_between(np.array(time_vec), np.zeros([len(time_vec),])+RHmax, np.zeros([len(time_vec),])+1000, alpha=0.2, color='lightblue')
    ax2.set_ylim([min(humidity)-graphRHmin, max(humidity)+graphRHmax])
    ax2.ticklabel_format(style='plain')
    plt.grid(color='gray', alpha=0.3)
    plt.text(0.05, 0.1, 'Humidity (%RH) ', transform=ax2.transAxes, alpha=0.5, fontsize=FontsizeLabel, color='gray')
    ax2.patch.set_facecolor('black')
    plt.yticks(np.round(np.linspace(min(humidity)-graphRHmin, max(humidity)+graphRHmax, nticks_y), 1), fontsize=FontsizeYticks)
    plt.ticklabel_format(useOffset=False)

    #setup xticks
    plt.xticks(np.arange(min(time_vec), max(time_vec), tickspacing_x), axestime[np.arange(min(time_vec), max(time_vec), tickspacing_x)], rotation='vertical', fontsize=FontsizeXticks)
    plt.pause(0.001)

    #///////////////////////////////Environment Logs\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    ## Data file management
    #Create EnvironmentData directory if it does not exist
    if not(os.path.isdir(envdata_directory)):
        os.makedirs(envdata_directory)

    ## Read csv and append to end of file
    #files get stored with month and year as filename in .csv format with .env.csv extension in envdata_directory
    monthYYYY = time.strftime("%B%Y")                                           #get month and year for title of file
    if os.path.isfile(envdata_directory+'/'+monthYYYY+'-all.env.csv'):          #use existing monthYYYY.env.csv file
        envfile = open(envdata_directory+'/'+monthYYYY+'-all.env.csv', 'a')     #open file with append properties
        envfile.write(str(currenttime[-1]))                                     #add time of measurement
        envfile.write(','+str(temperature[-1]))                                 #add latest temperature
        envfile.write(','+str(humidity[-1]))                                    #add latest humidity
        envfile.write('\n')
        envfile.close()                                                         #close file
    else:                                                                       #otherwise create new monthYYYY.env.csv
        envfile = open(envdata_directory+'/'+monthYYYY+'-all.env.csv', 'w')     #create file with write properties
        envfile.write('time,Temperature (deg. C),Humidity (%RH)\n')             #write header
        envfile.write(str(currenttime[-1]))                                     #add time of measurement
        envfile.write(','+str(temperature[-1]))                                 #add latest temperature
        envfile.write(','+str(humidity[-1]))                                    #add latest humidity
        envfile.write('\n')
        envfile.close()                                                         #close file

        envfile = open(envdata_directory+'/'+monthYYYY+'-outages.env.csv', 'w') #create file with write properties
        envfile.write('time,Temperature (deg. C),Humidity (%RH),Temperature Outage?,Humidity Outage?\n') #write header
        envfile.close()                                                         #close file

    ## Log outages to a -outage.env.csv file
    if (temperature[-1] > Tmax) or (temperature[-1] < Tmin) or (humidity[-1] > RHmax) or (humidity[-1] < RHmin): #if either T or RH out
        #existing outage file
        if os.path.isfile(envdata_directory+'/'+monthYYYY+'-outages.env.csv'):  #use existing monthYYYY.env.csv file
            envfile = open(envdata_directory+'/'+monthYYYY+'-outages.env.csv', 'a') #open file with append properties
            envfile.write(str(currenttime[-1]))                                 #add time of measurement
            envfile.write(','+str(temperature[-1]))                             #add latest temperature
            envfile.write(','+str(humidity[-1]))                                #add latest humidity
        #new outage file
        else:                                                                   #otherwise create new monthYYYY.env.csv
            envfile = open(envdata_directory+'/'+monthYYYY+'-outages.env.csv', 'w') #create file with write properties
            envfile.write('time,Temperature (deg. C),Humidity (%RH),Temperature Outage?,Humidity Outage?\n') #write header
            envfile.write(str(currenttime[-1]))                                 #add time of measurement
            envfile.write(','+str(temperature[-1]))                             #add latest temperature
            envfile.write(','+str(humidity[-1]))                                #add latest humidity
        #Record outage type
        if (temperature[-1] > Tmax) or (temperature[-1] < Tmin):
                envfile.write(',TEMPERATURE OUTAGE,')
        if (humidity[-1] > RHmax) or (humidity[-1] < RHmin):
                envfile.write(', ,HUMIDITY OUTAGE')
        envfile.write('\n')
        envfile.close()
    tf = time.time()                                                            #stop timer---------------------------------------------------------------------------
    if sleeptimer-(tf-ti) > 0:
        time.sleep(sleeptimer-(tf-ti))                                          #sleep for sleeptimer less time taken for the above lines
#end of while
