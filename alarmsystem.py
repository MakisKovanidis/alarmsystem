import sys
import time
import smtplib
import os
import glob
import datetime
import schedule
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#set the high and the low temperature for alarm
low_temp_alarm=-29
high_temp_alarm=-5

alarm_set=bool(0)
active_file=" "


#Email account credientials
smtpUser = 'someone@windowslive.com'
smtpPass = 'password'

#Where to sent mails
recipients = ['someone1@hotmail.com', 'someone2@email.com']

def init():
	create_file()
	
def send_email_with_recorded_temperatures():
    subject = "records"
    msg = MIMEMultipart()
    msg['From'] = "Alarm System"
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    body = 'Hi there, sending this email from Python!'
    msg.attach(MIMEText(body, 'plain'))

    previous_day = datetime.datetime.now() - datetime.timedelta(1)
    previous_day_filename = previous_day.strftime("%d%m%Y") + ".txt"
    previous_day_file_if_exist = os.path.isfile(previous_day_filename)
    if previous_day_file_if_exist:
        print(previous_day_filename)
        attachment = open(previous_day_filename, 'rb')
        print(smtpUser)
        print(recipients)
        print(active_file)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)

        part.add_header('Content-Disposition', "attachment; filename= " + previous_day_filename)

        msg.attach(part)
        text = msg.as_string()

        connection_problem = bool(0)
        while (not connection_problem):
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(smtpUser, smtpPass)

                server.sendmail(smtpUser, recipients, text)
                server.quit()
                connection_problem = bool(1)
                print("mail with attach sent")
            except:
                connection_problem = bool(0)
                print("wrong")
                time.sleep(20)
    else:
        print("something wrong")

def alarm_activated():
	temp=read_temp()
	send_Email_Alarm(temp)


def send_Email_Alarm(param):
	global alarm_set
	msg = MIMEMultipart()
	msg['From'] = "Alarm System"
	msg['To'] = ", ".join(recipients)
	msg['Subject'] = "Alarm Activated"
	temper = 20.05
	body = "the temperature is: " + str(param)
	msg.attach(MIMEText(body, 'plain'))
	text = msg.as_string()
	connection_problem = bool(0)
	while (not connection_problem):
		try:
			server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
			server.ehlo()
			server.login(smtpUser, smtpPass)

			server.sendmail(smtpUser, recipients, text)
			server.quit()
			connection_problem = bool(1)
			print("mail alarm activation send")
		except:
			connection_problem = bool(0)
			print("wrong")
			time.sleep(20)
	alarm_set=bool(0)
	print ('Alarm activated sended email')


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def create_file():
    filename = datetime.datetime.now().strftime("%d%m%Y") + ".txt"
    my_file = os.path.isfile(filename)
    global active_file
    if (not my_file):
        print("exist")
        active_file = filename
        file = open(filename, "w")
        file.close()
    else:
        active_file = filename

def record_temperature():
	timestamp_of_record=datetime.datetime.now().strftime("%H:%M:%S")
	temperature_of_record=str(read_temp())
	line=timestamp_of_record + " " + temperature_of_record + "\n"
	global active_file
	print (active_file)
	with open(active_file, "a") as myfile:
		myfile.write(line)
	print (line)
	myfile.close() 
	

#Script begin

init()

schedule.every(5).minutes.do(record_temperature)
schedule.every().day.at("00:00").do(create_file)
schedule.every().day.at("10:00").do(send_email_with_recorded_temperatures)	
print ("begin")
time.sleep(20)
try:
        while True:
		schedule.run_pending()
		temperature = read_temp()
                print (temperature)
               	if (temperature>high_temp_alarm or temperature<low_temp_alarm):
			if (alarm_set==bool(0)):
				alarm_set=bool(1)
				t=threading.Timer(300,alarm_activated)
				t.start()
				print ("alarm activated")
		elif (alarm_set==bool(1)):
			alarm_set=bool(0)
			t.cancel()
			print ("alarm canceled")
                time.sleep(1)

except KeyboardInterrupt:
        sys.exit()
