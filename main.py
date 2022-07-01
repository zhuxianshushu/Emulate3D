import modbus_tk
import modbus_tk.modbus_tcp as modbus_tcp
import modbus_tk.defines as mdef
import math
import time

def computeDegree( xpos, ypos):
    if xpos > 65526:
        xpos = 65536 - xpos
    if ypos > 65526:
        ypos = 65536 - ypos
    angle = 0
    if ypos != 0:
        angle = math.atan(xpos/ypos)*180/math.pi
    return angle

if __name__ == "__main__":

    logger = modbus_tk.utils.create_logger(name='console', record_format='%(message)s')
    logger.info("running...")

    server = modbus_tcp.TcpServer(port=502)
    server.start()

    slave1 = server.add_slave(1)
    # add 2 blocks of holding registers
    slave1.add_block('a', mdef.HOLDING_REGISTERS, 0, 100)  # address 0, length 100
    slave1.add_block('c', mdef.COILS, 0, 100)

    # set the values of registers at address 0
    slave1.set_values('a', 0, 0)
    slave1.set_values('c', 0, 1)

    run = True
    while run:
        time.sleep(2)
        value = slave1.get_values('a', 0, 1)
        value40001 = int(value[0])
        value = slave1.get_values('a', 1, 1)
        value40002 = int(value[0])
        value = slave1.get_values('a', 3, 1)
        value40004 = int(value[0])
        value = slave1.get_values('a', 4, 1)
        value40005 = int(value[0])
        value = slave1.get_values('a', 6, 1)
        value40007 = int(value[0])
        value = slave1.get_values('a', 7, 1)
        value40008 = int(value[0])

        print('40001:', value40001)
        print('40002:', value40002)
        #print('40004:', value40004)
        #print('40005:', value40005)
        #print('40007:', value40007)
        #print('40008:', value40008)
        angle = computeDegree(value40001, value40002)
        print(angle)
        if (value40002 >= 65526 and (angle > 0 and angle < 22.5)):
            print("pan rigth")
        elif ((value40002 > 0 and value40002 <= 10) and (angle > 0 and angle < 22.5)):
            print("pan left")
        elif ((value40001 > 0 and value40001 <= 10) and angle > 67.5):
            print("go straight")
        elif (value40001 >= 65526 and angle > 67.5):
            print("go back")
        elif (value40002 >= 65526 and (angle >=22.5 and angle <= 67.5)):
            print("lean to the up right")
        elif (value40002 >= 65526 and (angle >=22.5 and angle <= 67.5)):
            print("lean to the down right")
        elif ((value40002 >= 0 and value40002 <= 10) and ((angle >=22.5 and angle <= 67.5))):
            print("lean to the up left")
        elif ((value40002 >= 0 and value40002 <= 10) and ((angle >=22.5 and angle <= 67.5))):
            print("lean to the down left")
        else :
            print("stop")

        angle = computeDegree(value40004, value40005)
        if (value40005 >= 65526 and (angle > 0 and angle < 45)):
            print("turn left")
        elif ((value40004 > 0 and value40004 <= 10) and angle > 45 ):
            print("arm extension")
        elif (value40004 >= 65526 and angle > 45):
            print("arm reset")
        elif ((value40004 > 0 and value40004 <= 10) and (angle > 0 and angle < 45)):
            print("turn right")
        else :
            print("")
        # value40001 += 1
        # value40002 += 3
        # slave1.set_values('a', 0, value40001)
        # slave1.set_values('a', 1, value40002)
