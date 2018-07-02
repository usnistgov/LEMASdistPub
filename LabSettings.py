"""
Various device-specific settings
"""

#where recorded data will be stored in Linux file system, create if doesn't exist, doesn't really ever need changed
#the purpose of getpass.getuser() is to get the current username
import getpass                                                                  #for getting the current username to create save directory string
envdata_directory = '/home/'+getpass.getuser()+'/Desktop/EnvironmentData'

#set communications port. On Raspbian for USB-to-serial it should be /dev/ttyUSB0 (check dmesg immediately after connecting USB), default = /dev/ttyUSB0
#if using GPIO, some modification will be needed to LEMASRun* scripts
instrport = '/dev/ttyUSB0'

## Display and graph settings
#display pixels per inch for 5", 800x480 display, default is 190 px/in^2
dpi_set = 190
#vertical space between figures, % of vertical pixels, default is 0.07
hspace_set = 0.07
#number of rows of subplots, default is 2: one for temperature, one for humidity
r_plot = 2
#number of columns of subplots, default is 1
c_plot = 1
#figure size of the graphs in inches. Default values are for using a 800x480 pixel 5" display.
figsize_x = 4.2
figsize_y = 2.2
#length of time to graph into past, hours, default is 12 hours
graphtime = 12
#amount of space to graph above maximum temperature in graph time range, deg. C. Keep greater than 0.05 deg. C, too small will cause y-axis ticks to appear equal when using a low number of y-ticks
graphTmax = 0.5
#amount of space to graph below minimum temperature in graph time range, deg. C. Keep greater than 0.05 deg. C, too small will cause y-axis ticks to appear equal when using a low number of y-ticks
graphTmin = 0.5
#amount of space to graph above maximum humidity in graph time range, %RH. Keep greater than 0.05 %RH, too small will cause y-axis ticks to appear equal when using a low number of y-ticks
graphRHmax = 1
#amount of space to graph below minimum humidity in graph time range, %RH. Keep greater than 0.05 %RH, too small will cause y-axis ticks to appear equal when using a low number of y-ticks
graphRHmin = 1
#number of points between each x-axis tickmark, default is 20 points per tick
tickspacing_x = 20
#numbter of ticks on the y-axis, default is 3 tickmarks
nticks_y = 3
#fontsize for graph label text, Temperature (deg.C) amd Humidity (RH) text
FontsizeLabel = 16
#fontsize for graph y-axis humidity and temperature values
FontsizeYticks = 5
#fontsize for graph shared x-axis time values
FontsizeXticks = 5
#linewidth of plots of temperature and humidity
GraphLinewidth = 2.0

## Device behavior
#number of minutes to wait before sending message for return to normal status (for ensuring environment is not oscillating around limits), default is 10 minutes
normalstatus_wait = 10
#Increment alert settings
#e.g., upper spec is 25, incremental setting is 5, outage message is sent at 25, incremental message sent at 30, 35, 40, 35, 30, 35, 30, etc.
#temperature incremental alert, for when temperature is constantly changing. deg. C. system sends message every increment of this setting out of spec.
TincSet = 5
#humidity incremental alert, for when humdity is constantly changing. %RH. system sends message every increment of this setting out of spec.
RHincSet = 10
#number of points to record per hour, default is 40 pt/hr (every 90 seconds)
pts_hr = 40
#Conditions for reacquiring data from sensor to prevent graphing bad reads
#if change in temperature from previous is greater than this, reread temperature, deg. C
rereadT = 0.5
#if change in humidity from previous is greater than this, reread humidity, %RH
rereadRH = 1
