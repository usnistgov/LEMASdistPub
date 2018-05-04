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
#       continuously read temperature and humidity from CometSystems T3311, send notification via text/email with graph attached to lab users if temperature or humidity is outside of specified limits
#       log temperature and humidity to <month><YYYY>-all.env.csv
#       log temperature and humidity outages to <month><YYYY>-outage.env.csv
#
#///////////////////////////////////////////////////////////////////////////////
## References
# smtp.nist.gov is at ip: 129.6.16.94
#
#   T3311 manual (T3311manual.pdf)
#   T3311 protocols (T3311protocols.pdf)
#
#   Common cell carrier gateways
#   mostly complete list: https://martinfitzpatrick.name/list-of-email-to-sms-gateways/
#
##///////////////////////////////////////////////////////////////////////////////
## Change log from v1.10 to v1.11
#   April 25, 2018
#
#   ver 1.11    - fixed issues with recording outage type to outage file
#
#///////////////////////////////////////////////////////////////////////////////

## Used libraries
import smtplib, time, os, csv, datetime, copy
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import minimalmodbus
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

## Import lab settings files
program_directory = '/home/pi/LEMASdist'
#program_directory = '/home/braine/BraineCode/LEMASmaster/LEMASdist'
os.chdir(program_directory)
import LabID
import Tcontrols
import RHcontrols
import corrections
import SensorSerial
import LabSettings
import Contacts
import testmsgdate                                                              #import test message date with each loop, in case test message date changes
os.chdir(program_directory+'/tmpimg')

#//////////////////////////Import LabSettings\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
## import settings from LabSettings.py
logemail = 'dmgalert@nist.gov'
labID = LabID.labID
sensorserial = SensorSerial.sensorserial
Tcontrols = Tcontrols.Tcontrols
RHcontrols = RHcontrols.RHcontrols
T3311port = LabSettings.T3311port
pts_per_hr = LabSettings.pts_per_hr
graph_time = LabSettings.graph_time
tick_spacing = LabSettings.tick_spacing
dpi_set = LabSettings.dpi_set
normalstatus_wait = LabSettings.normalstatus_wait
TincSet = LabSettings.TincSet
RHincSet = LabSettings.RHincSet
graphTmax = LabSettings.graphTmax
graphTmin = LabSettings.graphTmin
graphRHmax = LabSettings.graphRHmax
graphRHmin = LabSettings.graphRHmin
FontsizeLabel = LabSettings.FontsizeLabel
FontsizeYticks = LabSettings.FontsizeYticks
FontsizeXticks = LabSettings.FontsizeXticks
GraphLinewidth = LabSettings.GraphLinewidth
rereadT = LabSettings.rereadT
rereadRH = LabSettings.rereadRH
allcontacts = Contacts.allcontacts
labusers = copy.deepcopy(Contacts.labusers[labID])
correction = copy.deepcopy(corrections.correction[sensorserial])                #[temperature, humidity]
TestmsgDate = testmsgdate.TestmsgDate
TestmsgDate = datetime.datetime.strptime(TestmsgDate, "%B %d, %Y %H:%M:%S")

print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Starting NIST Laboratory Environment Monitoring and Alert System (LEMAS), v1.11, October 2017')
print('\n\nMichael Braine, August 2017\nCurator contact: michael.braine@nist.gov')
print('\n\nQuiet Mode')

#///////////////////////////Outage Parameter Setup\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#set up parameters
graph_pts = round(graph_time*pts_per_hr)                                        #maximum number of recent points to plot
sleeptimer = (pts_per_hr / 60 / 60)**-1                                         #amount of time for system to wait until next temperature, seconds
Tmin = Tcontrols[labID][0]                                                      #get lower temperature limit for assigned lab
Tmax = Tcontrols[labID][1]                                                      #get upper temperature limit for assigned lab
RHmin = RHcontrols[labID][0]                                                    #get lower humidity limit for assigned lab
RHmax = RHcontrols[labID][1]                                                    #get upper humidity limit for assigned lab
TincAlert = [Tmin - TincSet, Tmax + TincSet]
RHincAlert = [RHmin - RHincSet, RHmax + RHincSet]

labcontacts = np.array([])
for icontact in range(len(labusers)):
    labcontacts = np.append(labcontacts, allcontacts[labusers[icontact]])

envdata_directory = '/home/pi/Desktop/EnvironmentData'                          #where data is stored in Linux file system, create if doesn't exist, doesn't really ever need changed
TestmsgSent = False                                                             #initialize test message has not been sent
ethoutage = False                                                               #initialize with internet outage status as false
ethoutage_sent = False                                                          #initialize status of messages queued under internet outage as not sent

## NIST SMTP server credentials and settings
#email = ''
#passwd = ''
#fromaddr = 'NIST Lab Environment Alert'
#SMTPserver = 'smtp.nist.gov'
#SMTPport = 25

## GMail SMTP server settings
#SMTPserver = 'smtp.gmail.com'
#SMTPport = 587

#///////////////////////////Function Definitions\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#define message sending functions
def SendMessage(toaddress, message):                                            #method for sending regular messages
    msg = MIMEMultipart()                                                       #define msg as having multiple components
    msg['Subject'] = 'DMG Alert: '+labID+' event log'
    msg['From'] = 'dmgalert@nist.gov'
    msg['To'] = toaddress
    text = MIMEText(message)
    msg.attach(text)

    server = smtplib.SMTP('129.6.16.94', 25)
    server.sendmail('dmgalert@nist.gov', toaddress, msg.as_string())
    server.quit()

def SendMessageMMS(toaddress, message, img_path):                               #method for sending messages with image attached
    msg = MIMEMultipart()                                                       #define msg as having multiple components
    msg['Subject'] = 'DMG Alert: '+labID+' Environment Event'
    msg['From'] = 'dmgalert@nist.gov'
    msg['To'] = toaddress
    text = MIMEText(message)
    msg.attach(text)
    img_file = open(img_path, 'rb').read()
    image_attach = MIMEImage(img_file)
    msg.attach(image_attach)

    server = smtplib.SMTP('129.6.16.94', 25)
    time.sleep(0.5)
    server.sendmail('dmgalert@nist.gov', toaddress, msg.as_string())
    server.quit()

#external to NIST network testing
# def SendMessage(toaddress, message):                                            #method for sending messages
#     server = smtplib.SMTP('smtp.gmail.com', 587)
#     username = input('Login: ')
#     passwd = input('Password: ')
#     server.ehlo()                                                               #not needed for NIST
#     server.starttls()                                                           #not supported by smtp.nist.gov, required for smtp.gmail.com
#     server.login(username, passwd)                                              #not required by smtp.nist.gov, required for smtp.gmail.com
#     server.sendmail('Test', toaddress, message)
#     server.quit()

#define sensor connection and reading functions
def ConnectT3311():                                                             #Connect to instrument T3311 method, modbus RTU protocol
    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Connecting to T3311...')
    T3311_obj = minimalmodbus.Instrument(T3311port, 1)
    time.sleep(5)
    try:
        T3311_obj.read_register(48,1)
    except Exception:
        pass
    T3311_obj.serial.baudrate = 9600

    return T3311_obj
T3311_obj = ConnectT3311()                                                      #connect to instrument

def T3311_errfix():
    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Error reading from T3311, clearing buffer...')
    T3311_obj.serial.baudrate = 19200
    try:
        T3311_obj.read_register(48,1)
    except Exception:
        pass
    time.sleep(5)
    T3311_obj.serial.baudrate = 9600
    time.sleep(5)

## Definitions for temperature and humidity measurement
def ReadTemperature():                                                          #read T3311 address for temperature
    temptemp = (T3311_obj.read_register(48, 1)-32)*5/9 + correction[0]          #read temperature, convert from deg. F to deg. C
    return round(temptemp, 3)

def ReadHumidity():                                                             #read T3311 address for humidity
    temphumid = T3311_obj.read_register(49, 1) + correction[1]
    return round(temphumid, 3)

#////////////////////////Variable Initialization\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
## Initialize variables and figure setup
currenttime = np.array([])                                                      #initialize empty lists
axestime = np.array([])
temperature = []
humidity = []
tf_alert_T = []
tf_alert_RH = []
plt.ion()                                                                       #activate interactive plotting
fig = plt.figure(num=1, figsize=(4.2,2.2), dpi=dpi_set)                         #get matplotlib figure ID, set figure size
gs = gridspec.GridSpec(2,3)
gs.update(hspace=0.05)
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
    temptemp = ReadTemperature()                                                #read T3311 modbus address for temperature
except Exception:                                                               #reestablish connection if failed
    T3311_errfix()
    try:
        temptemp = ReadTemperature()                                            #read T3311 modbus address for temperature
    except Exception:
        T3311_errfix()
        try:
            temptemp = ReadTemperature()
        except Exception:
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
temperature.append(temptemp)

#initial humidity
try:
    temphumid = ReadHumidity()                                                  #read T3311 modbus address for humidity
except Exception:                                                               #reestablish connection if failed
    T3311_errfix()
    try:
        temphumid = ReadHumidity()                                              #read T3311 modbus address for humidity
    except Exception:
        T3311_errfix()
        try:
            temphumid = ReadHumidity()
        except Exception:
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
humidity.append(temphumid)

#initial time data
currenttime = np.append(currenttime, time.strftime("%Y-%m-%d %H:%M:%S"))        #get current system time (yyyy mm dd hh mm ss)
axestime = np.append(axestime, time.strftime("%H:%M"))

#/////////////////////////////Eternal Loop\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
## Measure temperature and humidity for all eternity
while True:
    ti = time.time()                                                            #begin/reset active timer---------------------------------------------------------------------------
    # print('NIST Laboratory Environment Monitoring and Alert System (LEMAS), v1.06, October 2017')
    # print('\n\nMichael Braine, August 2017\nCurator contact: michael.braine@nist.gov\n\nLogging began:'+starttime)

    #//////////////////////////Instrument Communications\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    #read temperature
    try:
        temptemp = ReadTemperature()                                            #read T3311 modbus address for temperature
    except Exception:                                                           #reestablish connection if failed
        T3311_errfix()
        try:
            temptemp = ReadTemperature()                                        #read T3311 modbus address for temperature
        except Exception:
            T3311_errfix()
            try:
                temptemp = ReadTemperature()
            except Exception:
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')

    #if suspected bad sensor read, read temperature again
    if abs(temptemp - temperature[-1]) > rereadT:
        time.sleep(10)
        try:
            temptemp = ReadTemperature()                                        #read T3311 modbus address for temperature
        except Exception:
            T3311_errfix()
            try:
                temptemp = ReadTemperature()                                    #read T3311 modbus address for temperature
            except Exception:
                T3311_errfix()
                try:
                    temptemp = ReadTemperature()
                except Exception:
                    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
    temperature.append(temptemp)

    #read humidity
    try:
        temphumid = ReadHumidity()                                              #read T3311 modbus address for humidity
    except Exception:                                                           #reestablish connection if failed
        T3311_errfix()
        try:
            temphumid = ReadHumidity()                                          #read T3311 modbus address for humidity
        except Exception:
            T3311_errfix()
            try:
                temphumid = ReadHumidity()
            except Exception:
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')

    #if suspected bad sensor read, read humidity again
    if abs(temphumid - humidity[-1]) > rereadRH:
        time.sleep(10)
        try:
            temphumid = ReadHumidity()                                          #read T3311 modbus address for humidity
        except Exception:
            T3311_errfix()
            try:
                temphumid = ReadHumidity()                                      #read T3311 modbus address for humidity
            except Exception:
                T3311_errfix()
                try:
                    temphumid = ReadHumidity()
                except Exception:
                    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
    humidity.append(temphumid)

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
    #plt.ylabel('Temperature (deg. C)', fontsize=4)
    plt.setp(ax1.get_xticklabels(), visible=False)                              #hide tickmarks, will use shared axis
    plt.grid(color='gray', alpha=0.3)
    plt.text(0.05, 0.1, 'Temperature (deg. C)', transform=ax1.transAxes, alpha=0.5, fontsize=FontsizeLabel, color='gray') #add transparent text to bottom left of first axes
    ax1.patch.set_facecolor('black')
    plt.yticks(fontsize=FontsizeYticks)
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
    #plt.ylabel('Humidity (%RH)', fontsize=4)
    plt.grid(color='gray', alpha=0.3)
    plt.text(0.05, 0.1, 'Humidity (%RH) ', transform=ax2.transAxes, alpha=0.5, fontsize=FontsizeLabel, color='gray')
    ax2.patch.set_facecolor('black')
    plt.yticks(fontsize=FontsizeYticks)
    plt.ticklabel_format(useOffset=False)

    #setup xticks
    plt.xticks(np.arange(min(time_vec), max(time_vec), tick_spacing), axestime[np.arange(min(time_vec), max(time_vec), tick_spacing)], rotation='vertical', fontsize=FontsizeXticks)
    #plt.xlabel('Time (YYYY-mm-dd hh:mm:ss)')
    #plt.tight_layout()
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
