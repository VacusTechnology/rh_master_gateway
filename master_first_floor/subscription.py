#! /usr/bin/python3
import paho.mqtt.client as paho
import logging 
import logging.handlers
import time
import ast
import json
from subprocess import PIPE,Popen
import socket

# This script sucbscribes to the local broker to receive the data from the slave gateway
BROKER_ENDPOINT= "localhost"
PORT_NUMBER = 12301
PORT=1883
subTopic = "first_floor"

def systemcon():
    global client
    st=0
    try :
        st=client.connect(BROKER_ENDPOINT,PORT) #establishing connection
    except Exception as err:
        st=1;
    finally:
        if(st!=0):
            logger.info("Failed to connect to the broker...will try again after five seconds")
            time.sleep(5)
            systemcon();


def on_publish(client,userdata,result): #create function for callback
    logger.info("Message published")

def on_message(client, userdata, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if ( s.connect_ex(("127.0.0.1",PORT_NUMBER)) == 0 ):
            logger.info("Connected to the tcp socket server process, sending data via socket.")
            s.sendall(message.payload)
            s.close()
        else:
            logger.info("Failed to connect to the tcp socket server process, not sending any data.")

    except Exception as err:
        print(err)
        logger.info("Failed to connect to the tcp socket server process, not sending any data.")
    


def on_connect(client, userdata, flags, rc):
    logger.info("Connected to broker successfully(CALLBACK FUNCTION)")
    print("connected successfully")
    client.subscribe(subTopic)#subscribe topic test

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.info("Unexpected disconnection.")
        systemcon()
        client.subscribe(subTopic) #subscribe topic test

if __name__ == "__main__":
    # Create the logger for the application and bind the output to /sys/log/ #
    logger = logging.getLogger('subscription-service')
    logger.setLevel(logging.INFO)
    logHandler = logging.handlers.SysLogHandler(address='/dev/log')
    logHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    client= paho.Client() #create client object
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message=on_message
    client.on_disconnect = on_disconnect
    
    systemcon()
    client.subscribe(subTopic)#subscribe topic test
    client.loop_forever()
