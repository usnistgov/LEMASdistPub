## ////////////////////LABORATORY HUMIDITY CONTROLS\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Lab humidity controls
#If these ever need changed, the format for additional labs and temperature controls using a dictionary is: correction['<building>/<room>'] = [<minimum humidity>, <maximum humidity>]
#Dictionary list of humidity controls. Units are percent relative humidity (0 - 100)
#Add new humidity controls below the last line
correction = {}                                                                 #initialize empty dictionary

correction['0'] = [0, 0]                                                        #default correction when no sensor ID exists
correction['17968243'] = [-0.02, -1.5]
correction['18960415'] = [-0.05, 0.02]
correction['18960416'] = [-0.02, -0.02]
correction['18960417'] = [-0.05, -0.02]
correction['18960418'] = [-0.02, -0.31]
correction['18960419'] = [0.00, -0.48]
correction['18960420'] = [-0.04, -0.04]
correction['18960421'] = [0.04, 0.31]
correction['18960422'] = [-0.04, -0.03]
correction['18960423'] = [0.05, -0.89]
correction['18960424'] = [-0.10, 0.11]
correction['18960425'] = [0.01, 0.04]
correction['18960426'] = [-0.05, 0.36]
correction['18960427'] = [-0.01, 0.16]
correction['18960429'] = [0.00, 0.06]
correction['18960430'] = [-0.11, 0.08]
correction['18960431'] = [0.03, 0.02]
correction['18960432'] = [-0.07, 0.19]
correction['18960433'] = [0.01, 0.26]
correction['18960434'] = [-0.11, -0.30]
correction['18960435'] = [-0.08, -0.21]
correction['18960436'] = [0.04, -0.37]
correction['18960437'] = [-0.09, -0.27]
correction['18960438'] = [-0.04, 0.00]
correction['18960439'] = [-0.04, -0.04]
correction['18960442'] = [-0.12, -0.14]
correction['18960443'] = [-0.02, 0.17]
correction['18960444'] = [0.10, 0.08]
#correction['sensor serial number'] = [<temperature correction>, <humidity correction>]
