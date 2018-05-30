import time, minimalmodbus
#from LabSettings import instrport
#defines sensor functions. Current interfaces use modbus protocols
#set up interface
def ConnectInstr(instrport):                                                             #Connect to instrument with modbus RTU protocol
    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Connecting to instrument...')
    instr_obj = minimalmodbus.Instrument(instrport, 1)                          #modbus protocols
    time.sleep(5)
    try:
        instr_obj.read_register(48,1)
    except Exception:
        pass
    instr_obj.serial.baudrate = 9600

    return instr_obj

#functions for temperature and humidity measurement using modbus protocols
#modbus calls on an address in the hardware where the relevent data is stored, refer to instrument manuals.
def ReadTemperature(instr_obj):                                                 #read instrument address for temperature
    temptemp = (instr_obj.read_register(48, 1)-32)*5/9                          #read temperature, convert from deg. F to deg. C
    return round(temptemp, 4)

def ReadHumidity(instr_obj):                                                    #read instrument address for humidity
    temphumid = instr_obj.read_register(49, 1)
    return round(temphumid, 4)

#this is to clear buffer-related issues when reading from the instrument.
def Instr_errfix(instr_obj):
    print('\n'+time.strftime("%Y-%m-%d %H:%M:%S")+' : Error reading from instrument, clearing buffer...')
    instr_obj.serial.baudrate = 19200
    try:
        instr_obj.read_register(48,1)
    except Exception:
        pass
    time.sleep(5)
    instr_obj.serial.baudrate = 9600
    time.sleep(5)

    return instr_obj
