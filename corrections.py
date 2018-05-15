# Correction values for each sensor
#If these ever need changed, the format is: corrections['<serial number>'] = [<temperature correction, deg. C>, <humidity correction, %RH>]
#Add new sensors below the last line
corrections = {}                                                                 #initialize empty dictionary

corrections[''] = [0, 0]                                                         #default corrections when no sensor ID exists
#corrections['sensor serial number'] = [<temperature correction>, <humidity correction>]
