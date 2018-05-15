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
#   May 10, 2018
#
#   ver 1.12    - moved server information into .py file to easily edit in the public distribution
#               - moved instrument interface into .py file to  easily edit in the public distribution
#
#///////////////////////////////////////////////////////////////////////////////

print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Starting Laboratory Environment Monitoring and Alert System (LEMAS), v1.12, May 2018')
print('\n\nMichael Braine, August 2017\nmichael.braine@nist.gov')
print('\n\nLoud Mode')

## import python libraries
import smtplib, time, os, csv, datetime, copy
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import minimalmodbus
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
from Contacts import labusers

from testmsgdate import TestmsgDate
from testmsgdate import Testmsg

from ServerInfo import SMTPaddress
from ServerInfo import SMTPport
from ServerInfo import logaddress
from ServerInfo import fromaddress
from ServerInfo import username
from ServerInfo import passwd

from LabSettings import instrport
from LabSettings import pts_hr
from LabSettings import graphtime
from LabSettings import tickspacing
from LabSettings import dpi_set
from LabSettings import normalstatus_wait
from LabSettings import TincSet
from LabSettings import RHincSet
from LabSettings import graphTmax
from LabSettings import graphTmin
from LabSettings import graphRHmax
from LabSettings import graphRHmin
from LabSettings import FontsizeLabel
from LabSettings import FontsizeYticks
from LabSettings import FontsizeXticks
from LabSettings import GraphLinewidth
from LabSettings import rereadT
from LabSettings import rereadRH
from LabSettings import figsize_x
from LabSettings import figsize_y

#//////////////////////////Import instrument interface\\\\\\\\\\\\\\\\\\\\\\\\\\
from InstrInterface import ConnectInstr
from InstrInterface import Instr_errfix
from InstrInterface import ReadTemperature
from InstrInterface import ReadHumidity

os.chdir(program_directory+'/tmpimg')

correction = copy.deepcopy(corrections.corrections[sensorserial])               #[temperature, humidity]
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

instr_obj = ConnectInstr()                                                      #connect to instrument

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
    temptemp = ReadTemperature()                                                #read instrument modbus address for temperature
except Exception:                                                               #reestablish connection if failed
    Instr_errfix()
    try:
        temptemp = ReadTemperature()                                            #read instrumnet modbus address for temperature
    except Exception:
        Instr_errfix()
        try:
            temptemp = ReadTemperature()
        except Exception:
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
temperature.append(temptemp)

#initial humidity
try:
    temphumid = ReadHumidity()                                                  #read instrument modbus address for humidity
except Exception:                                                               #reestablish connection if failed
    Instr_errfix()
    try:
        temphumid = ReadHumidity()                                              #read instrument modbus address for humidity
    except Exception:
        Instr_errfix()
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
    #//////////////////////////Instrument Communications\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    #read temperature
    try:
        temptemp = ReadTemperature()                                            #read instrument modbus address for temperature
    except Exception:                                                           #reestablish connection if failed
        Instr_errfix()
        try:
            temptemp = ReadTemperature()                                        #read instrument modbus address for temperature
        except Exception:
            Instr_errfix()
            try:
                temptemp = ReadTemperature()
            except Exception:
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')

    #if suspected bad sensor read, read temperature again
    if abs(temptemp - temperature[-1]) > rereadT:
        time.sleep(10)
        try:
            temptemp = ReadTemperature()                                        #read instrument modbus address for temperature
        except Exception:
            Instr_errfix()
            try:
                temptemp = ReadTemperature()                                    #read instrument modbus address for temperature
            except Exception:
                Instr_errfix()
                try:
                    temptemp = ReadTemperature()
                except Exception:
                    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')
    temperature.append(temptemp)

    #read humidity
    try:
        temphumid = ReadHumidity()                                              #read instrument modbus address for humidity
    except Exception:                                                           #reestablish connection if failed
        Instr_errfix()
        try:
            temphumid = ReadHumidity()                                          #read instrument modbus address for humidity
        except Exception:
            Instr_errfix()
            try:
                temphumid = ReadHumidity()
            except Exception:
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Communications with instrument failed')

    #if suspected bad sensor read, read humidity again
    if abs(temphumid - humidity[-1]) > rereadRH:
        time.sleep(10)
        try:
            temphumid = ReadHumidity()                                          #read instrument modbus address for humidity
        except Exception:
            Instr_errfix()
            try:
                temphumid = ReadHumidity()                                      #read instrument modbus address for humidity
            except Exception:
                Instr_errfix()
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

    #//////////////////////Communications with outside world\\\\\\\\\\\\\\\\\\\\\\\\
    ## Update NoContact list
    NoContact = []                                                              #reinitialize No Contact list
    labusers = copy.deepcopy(Contacts.labusers[labID])                          #reinitialize labusers
    with open(program_directory+'/NoContact.list') as openedfile:
        reader = csv.reader(openedfile, delimiter=',')
        filedata = list(zip(*reader))

    #sort through list, remove NoContact entries from labusers list
    r, nNoContact = np.shape(filedata)
    for i in range(nNoContact):
        NoContact.append(filedata[0][i])
        if len(NoContact) > 0:
            if NoContact[-1] in labusers:
                del labusers[labusers.index[NoContact[-1]]]

    ## Send scheduled test message to all users
    comparetime = datetime.datetime.strptime(time.strftime("%B %d, %Y %H:%M:%S"), "%B %d, %Y %H:%M:%S")
    if (TestmsgDate-comparetime) < datetime.timedelta(0,30*60) and (TestmsgDate-comparetime) > datetime.timedelta(0,0): #if 30 minutes prior to sending test message
        if not(TestmsgSent):                                                    #if test message has not been sent
            message = Testmsg+labID+'. The current system time is '+time.strftime('%a %b %d, %Y, %I.%M %p')+'. The current environment is %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH.'
            plt.savefig(program_directory+'/tmpimg/outage.jpg')                 #save current figure
            for naddress in range(len(labcontacts)):
                SendMessageMMS(labcontacts, message, program_directory+'/tmpimg/outage.jpg') #send test message with attached graph
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Sending scheduled test message to users...')
            TestmsgSent = True
    else:                                                                       #if not 30 minutes before sending test message
        TestmsgSent = False                                                     #set test message to has not been sent

    ## Temperature alerts
    #initial temperature outage
    if (temperature[-1] > Tmax) or (temperature[-1] < Tmin):                    #if outside of temperature range
        if (temperature[-2] > Tmax) or (temperature[-2] < Tmin):                #if previous temperature was also out of range
            if (labstatus_T == 'normal'):                                       #if lab status was previously normal, or there was an ethernet outage
                plt.savefig(program_directory+'/tmpimg/outage.jpg')             #save current figure
                message = 'DMG alert: the temperature for '+labID+' is outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will be sent should the temperature status change.'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:                                           #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                        if not(ethoutage): #if this is
                            ethoutage_Toutmessage = 'DMG alert: An internet outage prevented the sending of a recent temperature event. The temperature for '+labID+' was outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will follow should the temperature status have changed during the internet outage.'
                            msglog = msglog+'\n'+ethoutage_Toutmessage
                        ethoutage = True
                        pass
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Temperature outage detected...messages sent/queued for users and temperature status elevated')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
                labstatus_T = 'warning'                                         #elevate status
            elif labstatus_T == 'warning':                                      #if temperature was already out
                tf_alert_T = [time.time()]                                      #reset temperature alert timer

    #incremental tmeperature alerts
    if (temperature[-1] > TincAlert[1]) or (temperature[-1] < TincAlert[0]):    #if temperature has changed passed the allowed increment
        if (temperature[-2] > TincAlert[1]) or (temperature[-2] < TincAlert[0]): #if previous temperature was also passed the allowed increment
            if (temperature[-1] > Tmin) and (temperature[-1] < Tmax):           #if temperature is within spec
                TincAlert = [Tmin - TincSet, Tmax + TincSet]                    #reset TincAlert
            elif (temperature[-1] > TincAlert[1]):                              #if temperature increased
                plt.savefig(program_directory+'/tmpimg/outage.jpg')
                message = 'DMG alert update: the temperature for '+labID+' has increased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                TincAlert[1] = TincAlert[1] + TincSet                           #set new incremental alert parameters
                TincAlert[0] = TincAlert[1] - 2*TincSet
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:                                           #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                        if not(ethoutage): #if this is
                            ethoutage_Toutmessage = 'DMG alert: An internet outage prevented the sending of a recent temperature event. The temperature for '+labID+' was outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 xxxx. A message will follow should the temperature status have changed during the internet outage.'
                            msglog = msglog+'\n'+ethoutage_Toutmessage
                        ethoutage = True
                        pass
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Temperature status changed...messages sent/queued for users and temperature status elevated')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
            elif (temperature[-1] < TincAlert[0]):                              #if temperature decreased
                plt.savefig(program_directory+'/tmpimg/outage.jpg')
                message = 'DMG alert update: the temperature for '+labID+' has decreased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                TincAlert[0] = TincAlert[0] - TincSet                           #set new incremental alert parameters
                TincAlert[1] = TincAlert[0] + 2*TincSet
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:                                           #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                        if not(ethoutage): #if this is
                            ethoutage_Toutmessage = 'DMG alert: An internet outage prevented the sending of a recent temperature event. The temperature for '+labID+' was outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will follow should the temperature status have changed during the internet outage.'
                            msglog = msglog+'\n'+ethoutage_Toutmessage
                        ethoutage = True
                        pass
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Temperature status changed...messages sent/queued for users and temperature status elevated')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
    #temperature outage under an internet outage
    if ethoutage:                                                               #if under internet outage, try to send queued messages
        for naddress in range(len(labcontacts)):
            try:
                SendMessageMMS(labcontacts[naddress], ethout_Toutmessage, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                ethoutage_sent = True                                           #set status of messages queued under ethernet outage
            except Exception:                                                   #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                pass
        try:
            SendMessage(logaddress, msglog)
        except Exception:
            pass

    #temperature return to normal
    if (temperature[-1] < Tmax) and (temperature[-1] > Tmin):                   #if temperature is inside temperature range
        if labstatus_T == 'warning':                                            #if lab status was previously under warning
            if len(tf_alert_T) == 0:                                            #if temperature alert timer has not been set
                tf_alert_T = [time.time()]                                      #set the start of the temperature alert timer
            elif (time.time() - tf_alert_T[0]) > normalstatus_wait*60:          #if normalstatus_wait has passed since temperature alert timer has start/reset
                plt.savefig(program_directory+'/tmpimg/outage.jpg')             #save current figure
                message = 'DMG alert update: the temperature for '+labID+' returned to normal at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:
                        if not(ethoutage):
                            ethoutage_Tinmessage = 'DMG alert update: the temperature for '+labID+' returned to normal at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'
                            msglog = msglog+'\n'+ethoutage_Tinmessage
                        ethoutage = True
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Temperature returned to normal...messages sent/queued to users and temperature status reduced')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
                labstatus_T = 'normal'                                          #reduce status
                tf_alert_T = []                                                 #remove temperature alert timer

    #temperature outage under an internet outage
    if ethoutage:                                                               #if under internet outage, try to send queued messages
        for naddress in range(len(labcontacts)):
            try:
                SendMessageMMS(labcontacts[naddress], ethout_Tinmessage, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                ethoutage_sent = True                                           #set status of messages queued under ethernet outage
            except Exception:                                                   #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                pass
        try:
            SendMessage(logaddress, msglog)
        except Exception:
            pass

    ## Humidity alerts
    #initial humidity outage
    if (humidity[-1] > RHmax) or (humidity[-1] < RHmin):                        #if outside of humidity range
        if (humidity[-2] > RHmax) or (humidity[-2] < RHmin):                    #if previous humidity was also out of range
            if labstatus_RH == 'normal':                                        #if lab status was previously normal
                plt.savefig(program_directory+'/tmpimg/outage.jpg')             #save current figure
                message = 'DMG alert: the humidity for '+labID+' is outside the allowable range: [%.2f' % RHmin+', %.2f' % RHmax+'] RH. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will be sent should the humidity status change.'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:
                        if not(ethoutage):
                            ethoutage_RHoutmessage = 'DMG alert: An internet outage prevented the sending of a recent humidity event. The humidity for '+labID+' was outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. A message will follow should the humidity status have changed during the internet outage'
                            msglog = msglog+'\n'+ethoutage_RHoutmessage
                        ethoutage = True
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Humidity outage detected...messages sent/queued to users and humidity status elevated')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
                labstatus_RH = 'warning'                                        #elevate status
            elif labstatus_RH == 'warning':                                     #if humidity was already out
                tf_alert_RH = [time.time()]                                     #reset humidity alert timer
    #incremental humidity alerts
    if (humidity[-1] > RHincAlert[1]) or (humidity[-1] < RHincAlert[0]):        #if humidity has changed passed the allowed increment
        if (humidity[-2] > RHincAlert[1]) or (humidity[-2] < RHincAlert[0]):    #if previous humidity was also passed the allowed increment
            if (humidity[-1] > RHmin) and (humidity[-1] < RHmax):               #if humidity is within spec
                RHincAlert = [RHmin - RHincSet, RHmax + RHincSet]               #reset TincAlert
            elif (humidity[-1] > RHincAlert[1]):                                #if humidity increased
                plt.savefig(program_directory+'/tmpimg/outage.jpg')
                message = 'DMG alert update: the humidity for '+labID+' has increased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                RHincAlert[1] = RHincAlert[1] + RHincSet                        #set new incremental alert parameters
                RHincAlert[0] = RHincAlert[1] - 2*RHincSet
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:                                           #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                        if not(ethoutage): #if this is
                            ethoutage_RHoutmessage = 'DMG alert: An internet outage prevented the sending of a recent humidity event. The humidity for '+labID+' was outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. A message will follow should the humidity status have changed during the internet outage.'
                            msglog = msglog+'\n'+ethoutage_RHoutmessage
                        ethoutage = True
                        pass
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Humidity status changed...messages sent/queued for users and temperature status elevated')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
            elif (humidity[-1] < RHincAlert[0]):                                #if humidity decreased
                plt.savefig(program_directory+'/tmpimg/outage.jpg')
                message = 'DMG alert update: the humidity for '+labID+' has decreased. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                RHincAlert[0] = RHincAlert[0] - RHincSet                        #set new incremental alert parameters
                RHincAlert[1] = RHincAlert[0] + 2*RHincSet
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:                                           #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                        if not(ethoutage): #if this is
                            ethoutage_RHoutmessage = 'DMG alert: An internet outage prevented the sending of a recent humidity event. The temperature for '+labID+' was outside the allowable range [%.2f' % Tmin+', %.2f' % Tmax+'] deg. C. At '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST the environment was %.2f' % temperature[-1]+' deg. C and %.2f' % humidity[-1]+' RH. The number for plant is 301 975 6928. A message will follow should the humidity status have changed during the internet outage.'
                            msglog = msglog+'\n'+ethoutage_RHoutmessage
                        ethoutage = True
                        pass
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Humidity status changed...messages sent/queued for users and temperature status elevated')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
    if ethoutage:                                                               #if under internet outage, try to send queued messages
        for naddress in range(len(labcontacts)):
            try:
                SendMessageMMS(labcontacts[naddress], ethout_RHoutmessage, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                ethoutage_sent = True                                           #set status of messages queued under ethernet outage
            except Exception:                                                   #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                pass
        try:
            SendMessage(logaddress, msglog)
        except Exception:
            pass

    #humidity return to normal
    if (humidity[-1] < RHmax) and (humidity[-1] > RHmin):                       #if humidity is inside humidity range
        if labstatus_RH == 'warning':                                           #if lab status was previously under humidity warning
            if len(tf_alert_RH) == 0:                                           #if humidity alert timer has not been set
                tf_alert_RH = [time.time()]                                     #set the start of the humidity alert timer
            elif (time.time() - tf_alert_RH[0]) > normalstatus_wait*60:         #if normalstatus_wait has passed since humidity alert timer has start/reset
                message = 'DMG alert update: the humidity for '+labID+' returned to normal at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'
                msglog = 'Start log for'+labID+'\n\n'+message+'\n'
                plt.savefig(program_directory+'/tmpimg/outage.jpg')             #save current figure
                for naddress in range(len(labcontacts)):
                    try:
                        SendMessageMMS(labcontacts[naddress], message, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                        msglog = msglog+'\n'+labcontacts[naddress]
                    except Exception:
                        if not(ethoutage):
                            ethoutage_RHinmessage = 'DMG alert update: the humidity for '+labID+' returned to normal at '+time.strftime('%a %b %d, %Y, %I.%M %p')+' EST.'
                            msglog = msglog+'\n'+ethoutage_RHinmessage
                        ethoutage = True
                print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Humidity returned to normal...messages sent/queued to users and humidity status reduced')
                try:
                    SendMessage(logaddress, msglog)
                except Exception:
                    pass
                labstatus_RH = 'normal'                                         #reduce status
                tf_alert_RH = []                                                #remove humidity alert timer
    if ethoutage:                                                               #if under internet outage, try to send queued messages
        for naddress in range(len(labcontacts)):
            try:
                SendMessageMMS(labcontacts[naddress], ethout_RHinmessage, program_directory+'/tmpimg/outage.jpg') #connect to SMTP server and send outage message with graph attached
                ethoutage_sent = True                                           #set status of messages queued under ethernet outage
            except Exception:                                                   #if cannot reach internet to send messages, continue logging and send outage alert when internet connection resumes
                pass
        try:
            SendMessage(logaddress, msglog)
        except Exception:
            pass

    #reset ethoutage and ethoutage_sent statuses if queued messages were successfully sent
    if ethoutage:
        if ethoutage_sent:
            print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Internet connection reestablished')
            ethoutage = False
            ethoutage_sent = False

    tf = time.time()                                                            #stop timer---------------------------------------------------------------------------
    if sleeptimer-(tf-ti) > 0:
        time.sleep(sleeptimer-(tf-ti))                                          #sleep for sleeptimer less time taken for the above lines
#end of while
