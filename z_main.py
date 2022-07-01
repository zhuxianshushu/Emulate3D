# -*- coding:utf-8 -*-
#导入模块
import time
import re
import RPi.GPIO as GPIO
from rpi_ws281x import Adafruit_NeoPixel, Color
import threading

import z_key as myKey
import z_led as myLed
import z_beep as myBeep
import z_uart as myUart
import z_lirc as myLirc
import z_socket as mySocket
import math
import modbus_tk
import modbus_tk.modbus_tcp as modbus_tcp
import modbus_tk.defines as mdef

# LED 配置:
LED_COUNT      = 6      # 要控制LED的数量.
LED_PIN        = 18      # GPIO接口 (PWM编码).
LED_BRIGHTNESS = 255    # 设置LED亮度 (0-255)
#以下LED配置无需修改
LED_FREQ_HZ    = 800000  # LED信号频率（以赫兹为单位）（通常为800khz）
LED_DMA        = 10       # 用于生成信号的DMA通道（尝试10）
LED_INVERT     = False   # 反转信号（使用NPN晶体管电平移位时）

#红外引脚定义
PIN_lirc = 27

#超声波引脚定义
TRIG = 23
ECHO = 22

#全局变量定义
systick_ms_bak = 0
systick_ms_group_bak = 0
systick_ms_bak_rgb = 0
car_mode = 0
car_mode_bak = 0
pwm_value1 = 1500
pwm_value2 = 1500
dis = 100
lirc_value = 0
#server
#slave1 = 0

#LED灯循坏
def loop_led():
    global systick_ms_bak
    if(int((time.time() * 1000))- systick_ms_bak > 500):
        systick_ms_bak = int((time.time() * 1000))
        myLed.flip()
#按键检测   
def loop_key():
    global key1_flag, key2_flag
    if(myKey.key1() == 0):
        time.sleep(0.02)
        if(myKey.key1() == 0):
            beep_on_once()
            while myKey.key1() == 0:
                pass
            
    if(myKey.key2() == 0):
        time.sleep(0.02)
        if(myKey.key2() == 0):
            beep_on_once()
            while myKey.key2() == 0:
                pass

#串口检测
def loop_uart():
    if myUart.uart_get_ok == 2:
        print(myUart.uart_receive_buf)
        parse_cmd(myUart.uart_receive_buf)
        myUart.uart_receive_buf = ''
        myUart.uart_get_ok = 0
    elif myUart.uart_get_ok == 1 or myUart.uart_get_ok == 3:
        print(myUart.uart_receive_buf)
        myUart.uart_send_str(myUart.uart_receive_buf)
        myUart.uart_receive_buf = ''
        myUart.uart_get_ok = 0
#网络连接服务
def loop_socket():
    if mySocket.socket_get_ok:
       myUart.uart_get_ok =  mySocket.socket_get_ok
       myUart.uart_receive_buf = mySocket.socket_receive_buf
       mySocket.socket_receive_buf = ''
       mySocket.socket_get_ok = 0
#指令解析       
def parse_cmd(myStr):
    global car_mode,car_mode_bak,voice_flag,voice_mode
    if myStr.find('$VOICE!') >= 0:
        pass       
    elif myStr.find('$QJ!') >= 0:
        car_mode = 1
        beep_on_once()
    elif myStr.find('$HT!') >= 0:
        car_mode = 2        
        beep_on_once()
    elif myStr.find('$ZZ!') >= 0:
        car_mode = 3
        beep_on_once()
    elif myStr.find('$YZ!') >= 0:
        car_mode = 4
        beep_on_once()
    elif myStr.find('$ZPY!') >= 0:
        car_mode = 5
        beep_on_once()
    elif myStr.find('$YPY!') >= 0:
        car_mode = 6
        beep_on_once()
    elif myStr.find('$ZYBZ!') >= 0:
        car_mode = 7
        beep_on_once()
    elif myStr.find('$WTGS!') >= 0:
        car_mode = 8
        beep_on_once()
    elif myStr.find('$TZ!') >= 0:
        car_mode = 0
        beep_on_once()
    elif myStr.find('$CUP!') >= 0:
        car_mode = 9
        beep_on_once()
    elif myStr.find('$CDOWN') >= 0:
        car_mode = 10
        beep_on_once()
    elif myStr.find('$CLEFT') >= 0:
        car_mode = 11
        beep_on_once()
    elif myStr.find('$CRIGHT') >= 0:
        car_mode = 12
        beep_on_once()
    elif myStr.find('$QJ1') >= 0:
        beep_on_once()
        myUart.uart_send_str("#006P0500T1000!#007P2500T1000!#008P0500T1000!#009P2500T1000!")
    elif myStr.find('$HT1') >= 0:
        beep_on_once()
        myUart.uart_send_str("#006P2500T1000!#007P0500T1000!#008P2500T1000!#009P0500T1000!")
    elif myStr.find('$ZZ1') >= 0:
        beep_on_once()
        myUart.uart_send_str("#006P2500T1000!#007P2500T1000!#008P2500T1000!#009P2500T1000!")
    elif myStr.find('$YZ1') >= 0:
        beep_on_once()
        myUart.uart_send_str("#006P0500T1000!#007P0500T1000!#008P0500T1000!#009P0500T1000!")
#红外检测    
def loop_lirc():
    global lirc_value,car_mode,systick_ms_bak,car_mode_bak
    if lirc_value > 0:
        myBeep.beep(0.1)
        if lirc_value == 1:
            car_mode = 0
        elif lirc_value == 5:
            car_mode = 1
        elif lirc_value == 11:
            car_mode = 2
        elif lirc_value == 7:
            car_mode = 3
        elif lirc_value == 9:
            car_mode = 4
        elif lirc_value == 8:
            car_stop()
        elif lirc_value == 13:
            car_mode = 7
        elif lirc_value == 14:
            car_mode = 8
        lirc_value = 0
#小车状态控制                         
def loop_car_mode():
    global car_mode,car_mode_bak
    if car_mode_bak != car_mode:
        car_mode_bak = car_mode
        if car_mode == 0:
            myUart.uart_send_str("#012P1515T1000!")
            car_stop()
            #rgb_show(0)
        elif car_mode == 1:
            myUart.uart_send_str("#012P1511T1000!")
            car_go_back(800)
        elif car_mode == 2:
            myUart.uart_send_str("#012P1512T1000!")
            car_go_back(-800)
        elif car_mode == 3:
            myUart.uart_send_str("#012P1513T1000!")
            car_left_turn(-800)            
        elif car_mode == 4:
            myUart.uart_send_str("#012P1514T1000!")
            car_right_turn(800)
        elif car_mode == 5:
            car_left_right_run(-800)
        elif car_mode == 6:
            car_left_right_run(800)                      
        
    if car_mode == 7:
        car_zybz()
    elif car_mode == 8:
        car_wtgs()

#红外数据收发
def lircEvent():
    if GPIO.input(PIN_lirc) == 0:
        count = 0
        while GPIO.input(PIN_lirc) == 0 and count < 200:
            count += 1
            time.sleep(0.00006)

        count = 0
        while GPIO.input(PIN_lirc) == 1 and count < 80:
            count += 1
            time.sleep(0.00006)

        idx = 0
        cnt = 0
        data = [0,0,0,0]
        for i in range(0,32):
            count = 0
            while GPIO.input(PIN_lirc) == 0 and count < 15:
                count += 1
                time.sleep(0.00006)

            count = 0
            while GPIO.input(PIN_lirc) == 1 and count < 40:
                count += 1
                time.sleep(0.00006)

            if count > 8:
                data[idx] |= 1<<cnt
            if cnt == 7:
                cnt = 0
                idx += 1
            else:
                cnt += 1
        if data[0]+data[1] == 0xFF and data[2]+data[3] == 0xFF:
             #print("Get the key: 0x%02x" %data[2])
             parse_code(data[2])
#红外数据解析
def parse_code(key_val):
    global lirc_value
    if(key_val==0x45):
        print("Button POWER")
        lirc_value = 1
    elif(key_val==0x46):
        print("Button MENU")
        lirc_value = 2
    elif(key_val==0x47):
        print("Button VOICE")
        lirc_value = 3
    elif(key_val==0x44):
        print("Button MODE")
        lirc_value = 4
    elif(key_val==0x40):
        print("Button +")
        lirc_value = 5
    elif(key_val==0x43):
        print("Button BACK")
        lirc_value = 6
    elif(key_val==0x07):
        print("Button PREV")
        lirc_value = 7
    elif(key_val==0x15):
        print("Button PLAY/STOP")
        lirc_value = 8
    elif(key_val==0x09):
        print("Button NEXT")
        lirc_value = 9
    elif(key_val==0x16):
        print("Button 0")
        lirc_value = 10
    elif(key_val==0x19):
        print("Button -")
        lirc_value = 11
    elif(key_val==0x0d):
        print("Button OK")
        lirc_value = 12
    elif(key_val==0x0c):
        print("Button 1")
        lirc_value = 13
    elif(key_val==0x18):
        print("Button 2")
        lirc_value = 14
    elif(key_val==0x5e):
        print("Button 3")
        lirc_value = 15
    elif(key_val==0x08):
        print("Button 4")
        lirc_value = 16
    elif(key_val==0x1c):
        print("Button 5")
        lirc_value = 17
    elif(key_val==0x5a):
        print("Button 6")
        lirc_value = 18
    elif(key_val==0x42):
        print("Button 7")
        lirc_value = 19
    elif(key_val==0x52):
        print("Button 8")
        lirc_value = 20
    elif(key_val==0x4a):
        print("Button 9")
        lirc_value = 21
    return lirc_value

#初始化开启示意
def setup_start():
    beep_on_once()
    beep_on_once()
    beep_on_once()

def setup_lirc():
    GPIO.setup(PIN_lirc,GPIO.IN,GPIO.PUD_UP)

#初始化超声波    
def setup_csb():
    GPIO.setup(TRIG, GPIO.OUT,initial = 0)
    GPIO.setup(ECHO, GPIO.IN,pull_up_down = GPIO.PUD_UP)

#RGB彩灯闪烁
def setup_show():    
    rgb_show(1)
    time.sleep(1)
    rgb_show(2)
    time.sleep(1)
    rgb_show(3)
    time.sleep(1)   
    rgb_show(0)
    
#超声波测距    
def distance():
    GPIO.output(TRIG, 0)
    time.sleep(0.000002)

    GPIO.output(TRIG, 1)
    time.sleep(0.00001)
    GPIO.output(TRIG, 0)
   
    while GPIO.input(ECHO) == 0:
        a = 0
    time1 = time.time()
    while GPIO.input(ECHO) == 1:
        a = 1
    time2 = time.time()

    during = time2 - time1
    return during * 340 / 2 * 100

#自由避障
def car_zybz():
    global systick_ms_bak
    if(int((time.time() * 1000))- systick_ms_bak > 50):
        systick_ms_bak = int((time.time() * 1000))
        dis = distance()
        if int(dis) >= 100:
            #rgb_show(3)
            car_go_back(800)
        elif 50 <= int(dis) < 100:
            #rgb_show(1)
            #rgb_show(3)
            car_go_back(600)
        elif 30 <= int(dis) < 50:
            #rgb_show(2)
            car_go_back(400)
        else:
            #rgb_show(1)
            car_right_turn(500)

#物体跟随
def car_wtgs():
    global systick_ms_bak
    if(int((time.time() * 1000))- systick_ms_bak > 50):
        systick_ms_bak = int((time.time() * 1000))
        print(time.time())
        dis = distance()
        if int(dis) > 60 or 20 < int(dis) < 40:
            car_stop()
        elif 40 <= int(dis) <= 60:
            car_go_back(600)
        elif int(dis) <= 20:
            car_go_back(-600)

#控制RGB灯亮起
def rgb_show(x):
    if x == 0:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(0,0,0))
            strip.show()
    elif x == 1:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(255,0,0))
            strip.show()
    elif x == 2:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(0,255,0))
            strip.show()
    elif x == 3:
        for i in range(0,strip.numPixels()):  
            strip.setPixelColor(i, Color(0,0,255))
            strip.show()
  
#蜂鸣器
def beep_on_once():
    myBeep.on()
    time.sleep(0.1)
    myBeep.off()
    time.sleep(0.1)  

'''
函数功能：串口发送指令控制电机转动
范围：-1000～+1000
'''

def car_run(speed_l1,speed_r1,speed_l2,speed_r2):
    #global speed_l1,speed_r1,speed_l2,speed_r2 
    textSrt = '#006P{:0>4d}T0000!#007P{:0>4d}T0000!#008P{:0>4d}T0000!#009P{:0>4d}T0000!'.format(speed_l1,speed_r1,speed_l2,speed_r2)
    print(textSrt)
    myUart.uart_send_str(textSrt)

'''
函数功能：小车前进后退
正值小车前进，负值小车后退
范围：-1000～+1000
'''
def car_go_back(speed):
    car_run(1500+speed,1500-speed,1500+speed,1500-speed)
    
'''
函数功能：小车左转
负值小车左转
范围：-1000～0
'''
def car_left_turn(speed):
    speedl = 1500+speed*2//3
    speedr = 1500+speed
    car_run(speedl,speedr,speedl,speedr)
   

'''
函数功能：小车右转
正值小车右转
范围：0～1000
'''
def car_right_turn(speed):
    speedl = 1500+speed
    speedr = 1500+speed*2//3
    car_run(speedl,speedr,speedl,speedr)

'''
函数功能：小车左右平移
负值小车左转，正值右转
范围：-1000～+1000
'''
def car_left_right_run(speed):
    speed1 = 1500-speed
    speed2 = 1500+speed
    car_run(speed1,speed1,speed2,speed2)
'''
函数功能：小车停止
'''
def car_stop():
    myUart.uart_send_str('#000P1500T1000!#001P2100T1000!#002P2300T1000!#003P1950T1000!#004P1500T1000!#005P1500T1000!#006P1500T1000!#007P1500T1000!#008P1500T1000!#009P1500T1000!')
               
#释放IO资源
def destory():
    myLed.off()
    myBeep.off()
    GPIO.cleanup()

#初始化modbus server
def setupModbus():
    logger = modbus_tk.utils.create_logger(name='console', record_format='%(message)s')
    logger.info("running...")

    global server 
    server = modbus_tcp.TcpServer(port=502)
    server.start()

    global slave1
    slave1 = server.add_slave(1)
    # add 2 blocks of holding registers
    slave1.add_block('a', mdef.HOLDING_REGISTERS, 0, 100)  # address 0, length 100
    slave1.add_block('c', mdef.COILS, 0, 100)

    # set the values of registers at address 0
    slave1.set_values('a', 0, 0)
    slave1.set_values('c', 0, 1)

#计算lever 角度
def computeDegree( xpos, ypos):
    if xpos > 65526:
        xpos = 65536 - xpos
    if ypos > 65526:
        ypos = 65536 - ypos
    angle = 0
    if ypos != 0:
        angle = math.atan(xpos/ypos)*180/math.pi
    return angle

#设置carmode
def setCarMode():
    time.sleep(1)
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
    
    running = 1
    angle = computeDegree(value40001, value40002)
    if (value40002 >= 65526 and (angle > 0 and angle < 22.5)):
        #print("pan rigth")
        if value40008 == 0:
            car_run_control('@R4')
        else :
            car_run_control('@R4S')
    elif ((value40002 > 0 and value40002 <= 10) and (angle > 0 and angle < 22.5)):
        #print("pan left")
        if value40008 == 0:
            car_run_control('@R3')
        else:
             car_run_control('@R3S')
    elif ((value40001 > 0 and value40001 <= 10) and angle > 67.5):
        #print("go straight")
        if value40008 == 0:
            car_run_control('@R1')
        else:
            car_run_control('@R1S')
    elif (value40001 >= 65526 and angle > 67.5):
        #print("go back")
        if value40008 == 0:
            car_run_control('@R2')
        else:
            car_run_control('@R2S')
    elif (value40002 >= 65526 and (value40001 > 0 and value40001 <= 10) and (angle >=22.5 and angle <= 67.5)):
        #print("lean to the up right")
        if value40008 == 0:
            car_run_control('@R6')
        else:
            car_run_control('@R6S')
    elif (value40002 >= 65526 and value40001 >= 65526 and (angle >=22.5 and angle <= 67.5)):
        #print("lean to the down right")
        if value40008 == 0:
            car_run_control('@R8')
        else:
            car_run_control('@R8S')
    elif ((value40002 >= 0 and value40002 <= 10) and ((value40002 > 0 and value40002 <= 10)) and ((angle >=22.5 and angle <= 67.5))):
        #print("lean to the up left")
        if value40008 == 0:
            car_run_control('@R5')
        else:
            car_run_control('@R5S')
    elif ((value40002 >= 0 and value40002 <= 10) and value40002 >= 65526 and ((angle >=22.5 and angle <= 67.5))):
        #print("lean to the down left")
        if value40008 == 0:
            car_run_control('@R7')
        else:
            car_run_control('@R7S')
    else :
        #print("stop")
        running = 0
        car_run_control('')

    angle = computeDegree(value40004, value40005)
    if (value40005 >= 65526 and (angle > 0 and angle < 45)):
        #print("turn left")
        car_run_control('@T1')
    elif ((value40004 > 0 and value40004 <= 10) and value40007 != 0 and angle > 45 ):
        print("arm extension")
        car_arm_control('@AF')
    elif (value40004 >= 65526 and angle > 45):
        print("arm reset")
        car_arm_control('')
    elif ((value40004 > 0 and value40004 <= 10) and value40007 != 0 and (angle > 0 and angle < 45)):
        #print("turn right")
        car_run_control('@T4')
    else :
        print("")
    
    if running == 0:
        if value40007 != 0:
            car_arm_control('')
        else :
            car_arm_control('@AReset')

'''
Add by Leah
'''
def car_run_control(sMode):
#fast mode
    if sMode.find('@R1') >= 0:#向前
        myUart.uart_send_str('#008P2500T1000!#009P0500T1000!#006P2500T1000!#007P0500T1000!')
    elif sMode.find('@R2') >= 0:#向后
        myUart.uart_send_str('#008P0500T1000!#009P2500T1000!#006P0500T1000!#007P2500T1000!')
    elif sMode.find('@R3') >= 0:#左 平移
        myUart.uart_send_str('#006P0500T1000!#007P0500T1000!#008P2500T1000!#009P2500T1000!')
    elif sMode.find('@R4') >= 0:#右 平移 
        myUart.uart_send_str('#006P2500T1000!#007P2500T1000!#008P0500T1000!#009P0500T1000!')

    elif sMode.find('@R5') >= 0:#左前 
        myUart.uart_send_str('#007P0500T1000!#008P2500T1000!')
    elif sMode.find('@R6') >= 0:#右前
        myUart.uart_send_str('#006P2500T1000!#009P0500T1000!')
    elif sMode.find('@R7') >= 0:#左后
        myUart.uart_send_str('#006P0500T1000!#009P2500T1000!')
    elif sMode.find('@R8') >= 0:#右后
        myUart.uart_send_str('#007P2500T1000!#008P0500T1000!')

    elif sMode.find('@T1') >= 0:#Turning Left 左转 90
        myUart.uart_send_str('#006P0500T1000!#007P0500T1000!#008P0500T1000!#009P0500T1000!')
    elif sMode.find('@T2') >= 0:#Turning Right 右转 90
        myUart.uart_send_str('#006P2500T1000!#007P2500T1000!#008P2500T1000!#009P2500T1000!')
    elif sMode.find('@T3') >= 0:#Curved left 左转 30~45
        myUart.uart_send_str('#006P1700T1000!#007P0800T1000!#008P1700T1000!#009P0800T1000!')
    elif sMode.find('@T4') >= 0:#Curved right 右转 30~45
        myUart.uart_send_str('#006P2200T1000!#007P1300T1000!#008P2200T1000!#009P1300T1000!')
        
 #slow mode *new
    elif sMode.find('@R1S') >= 0:#向前 T0800
        myUart.uart_send_str('#008P2200T1000!#009P0800T1000!#006P2200T1000!#007P0800T1000!')
    elif sMode.find('@R2S') >= 0:#向后
        myUart.uart_send_str('#008P0800T1000!#009P2200T1000!#006P0800T1000!#007P2200T1000!')
    elif sMode.find('@R3S') >= 0:#左 平移
        myUart.uart_send_str('#006P0800T1000!#007P0800T1000!#008P2200T1000!#009P2200T1000!')
    elif sMode.find('@R4S') >= 0:#右 平移
        myUart.uart_send_str('#006P2200T1000!#007P2200T1000!#008P0800T1000!#009P0800T1000!')

    elif sMode.find('@R5S') >= 0:#左前
        myUart.uart_send_str('#007P0800T1000!#008P2200T1000!')
    elif sMode.find('@R6S') >= 0:#右前
        myUart.uart_send_str('#006P2200T1000!#009P0800T1000!')
    elif sMode.find('@R7S') >= 0:#左后
        myUart.uart_send_str('#006P0800T1000!#009P2200T1000!')
    elif sMode.find('@R8S') >= 0:#右后
        myUart.uart_send_str('#007P2200T1000!#008P0800T1000!')
        
#Stop mode        
    else:#Stop 停止
        myUart.uart_send_str('#006P1500T1000!#007P1500T1000!#008P1500T1000!#009P1500T1000!')

def car_arm_control(sMode):
    if sMode.find('@A0L') >= 0:#0号舵机 左转 60
        myUart.uart_send_str('#000P2000T1000!')
    elif sMode.find('@A0R') >= 0:#0号舵机 右转 60
        myUart.uart_send_str('#000P1000T1000!')
    elif sMode.find('@A0M') >= 0:#0号舵机 恢复中间位置
        myUart.uart_send_str('#000P1500T1000!')                
        
    elif sMode.find('@A1F') >= 0:#1号舵机 向前
        myUart.uart_send_str('#001P1300T1000!')
    elif sMode.find('@A1B') >= 0:#1号舵机 向后
        myUart.uart_send_str('#001P1700T1000!')
    elif sMode.find('@A1M') >= 0:#1号舵机 恢复中间位置
        myUart.uart_send_str('#001P1500T1000!')

    elif sMode.find('@A2F45') >= 0:#2号舵机 向前 45
        myUart.uart_send_str('#002P1800T1000!')
    elif sMode.find('@A2F90') >= 0:#2号舵机 向前 90
        myUart.uart_send_str('#002P2000T1000!')
    elif sMode.find('@A2B45') >= 0:#2号舵机 向后 45
        myUart.uart_send_str('#002P1200T1000!')
    elif sMode.find('@A2B90') >= 0:#2号舵机 向后 90
        myUart.uart_send_str('#002P1000T1000!')
    elif sMode.find('@A2M') >= 0:#2号舵机 恢复中间位置
        myUart.uart_send_str('#002P1500T1000!')

    elif sMode.find('@A3F45') >= 0:#3号舵机 向前 45
        myUart.uart_send_str('#003P1900T1000!')
    elif sMode.find('@A3F90') >= 0:#3号舵机 向前 90
        myUart.uart_send_str('#003P2200T1000!')
    elif sMode.find('@A3B45') >= 0:#3号舵机 向后 45
        myUart.uart_send_str('#003P1200T1000!')
    elif sMode.find('@A3B90') >= 0:#3号舵机 向后 90
        myUart.uart_send_str('#003P1000T1000!')
    elif sMode.find('@A3M') >= 0:#3号舵机 恢复中间位置
        myUart.uart_send_str('#003P1500T1000!')

    elif sMode.find('@A4L45') >= 0:#4号舵机 左转 45
        myUart.uart_send_str('#004P1900T1000!')
    elif sMode.find('@A4L90') >= 0:#4号舵机 左转 90
        myUart.uart_send_str('#004P2200T1000!')
    elif sMode.find('@A4R45') >= 0:#4号舵机 右转 45
        myUart.uart_send_str('#004P1200T1000!')
    elif sMode.find('@A4R90') >= 0:#4号舵机 右转 90
        myUart.uart_send_str('#004P1000T1000!')
    elif sMode.find('@A4M') >= 0:#4号舵机 恢复中间位置    
        myUart.uart_send_str('#004P1500T1000!')

    elif sMode.find('@A5O') >= 0:#5号舵机 开open
        myUart.uart_send_str('#005P0500T1000!')
    elif sMode.find('@A5C') >= 0:#5号舵机 闭合
        myUart.uart_send_str('#005P2300T1000!')
    elif sMode.find('@A5M') >= 0:#5号舵机 恢复
        myUart.uart_send_str('#005P1500T1000!')

    elif sMode.find('@AALL') >= 0:#机械臂全部垂直 最高 
        myUart.uart_send_str('#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!#004P1500T1000!#005P1500T1000!')
    elif sMode.find('@AReset') >= 0:#机械臂蜷缩
        myUart.uart_send_str('#000P1500T1000!#001P2200T1000!#002P2300T1000!#003P1950T1000!#004P1500T1000!#005P1500T1000!')
    elif sMode.find('@A7') >= 0:#机械臂7字形
        myUart.uart_send_str('#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P2200T1000!#004P1500T1000!#005P1500T1000!')
    elif sMode.find('@AF') >= 0:#
        myUart.uart_send_str('#001P1200T1000!#002P1100T1000!')
    else:#Reset 机械臂7字形
        myUart.uart_send_str('#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P2200T1000!#004P1500T1000!#005P1500T1000!')

#大循环
if __name__ == '__main__':
    time.sleep(5)
    myLed.setup_led()        #led初始化
    myBeep.setup_beep()      #蜂鸣器初始化
    setup_csb()              #初始化超声波
    setup_lirc()             #初始化红外
    myKey.setup_key()        #按键初始化
    setupModbus()
    myUart.setup_uart(115200) #设置串口
    
    mySocket.setup_socket(1314)
    #创建NeoPixel对象
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    #初始化库
    strip.begin()
    #RGB彩灯开机闪烁
    setup_show()
    #机械臂蜷缩
    myUart.uart_send_str('#000P1500T1000!#001P2200T1000!#002P2300T1000!#003P1950T1000!#004P1500T1000!#005P1500T1000!')
    setup_start()            #启动示意滴滴滴三声
    try:
        while True:            
            loop_led()
            loop_key()
            loop_uart()
            loop_socket()
            lircEvent()
            loop_lirc()
            setCarMode()
            #loop_car_mode()
    except KeyboardInterrupt:
        destory()
        