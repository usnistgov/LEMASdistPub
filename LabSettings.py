#set communications port. On Raspbian for USB-to-serial it should be /dev/ttyUSB0 (check dmesg immediately after connecting USB), default = /dev/ttyUSB0
instrport = '/dev/ttyUSB0'

## ///////////////////////////USER PREFERENCES\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#display pixels per inch for 5", 800x480 display, default is 186 px/in^2
dpi_set = 186
#number of minutes before sending message for return to normal status (for ensuring environment is not oscillating around limits), default is 10 minutes
normalstatus_wait = 10
#temperature incremental alert, for when temperature is constantly changing. deg. C. system sends message every increment of this setting out of spec.
#e.g., upper spec is 25, setting is 5, outage message sent at 25, incremental message sent at 30, 35, 40, 35, 30, 35, 30, etc.
TincSet = 5
#humidity incremental alert, for when humdity is constantly changing. %RH. system sends message every increment of this setting out of spec.
RHincSet = 10

## Graphing settings
#figure size of the graphs in inches. Default values are for using a 800x480 pixel 5" display.
figsize_x = 4.2
figsize_y = 2.2
#number of points to record per hour, default is 40 pt/hr (every 90 seconds)
pts_hr = 40
#length of time to graph into past, hours, default is 12 hours
graphtime = 12
#number of points between each x-axis tickmark, default is 20 points per tick
tickspacing = 20
#amount of space to graph above maximum temperature in graph time range, deg. C
graphTmax = 0.5
#amount of space to graph below minimum temperature in graph time range, deg. C
graphTmin = 0.5
#amount of space to graph above maximum humidity in graph time range, %RH. 100 sets maximum displays humidity to 100 %RH with no autoscaling
graphRHmax = 1
#amount of space to graph below minimum humidity in graph time range, %RH. 100 sets minimum displays humidity to 0 %RH with no autoscaling
graphRHmin = 1
#fontsize for graph label text, Temperature (deg.C) amd Humidity (RH) text
FontsizeLabel = 16
#fontsize for graph y-axis humidity and temperature values
FontsizeYticks = 5
#fontsize for graph shared x-axis time values
FontsizeXticks = 5
#linewidth of plots of temperature and humidity
GraphLinewidth = 2.0

## Conditions for reacquiring data from sensor to prevent graphing bad reads
#if change in temperature from previous is greater than this, reread temperature, deg. C
rereadT = 0.5
#if change in humidity from previous is greater than this, reread humidity, %RH
rereadRH = 1
