#! /usr/bin/python3

import mysql.connector
import logging
import logging.handlers
import time
import paho.mqtt.client as mqtt
import json

CLOUD_BROKER_ENDPOINT="localhost"
PORT=1883

DB_USERNAME="vacus"
DB_PASSWORD="vacus321"
DB_NAME="master_db"

# def fetchMacId():
#     with open("/home/pi/configuration/macid.conf","r") as fd:
#         lines = fd.read().splitlines()
#         macid = lines[0]
#     return macid
masterMacId ="5a-c2-15-08-00-03" #first floor

def on_connect(client, user_data, flags, rc):
    logger.info("Connected with result code " + str(rc))

def systemcon():
    st = 0
    try:
        st = client.connect(CLOUD_BROKER_ENDPOINT, PORT, keepalive=60)  # establishing connection
    
    except Exception as err:
        st = 1;

    finally:    
        if (st != 0):
            logger.info("not able to connect to broker...trying to connect again")
            time.sleep(5)
            systemcon();
        else:
            logger.info("Connected to the broker")

def uploadData(logger):
    try:
        db = mysql.connector.connect(
            host="localhost",
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = db.cursor()
        sql = """select * from first_floor"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        logger.info("Data processed is - ")
        logger.info(rows)

        if len(rows)!=0:
            payload = []
            for elem in rows:
                payload.append({"macaddress":elem[1] , "X":elem[2] , "Y":elem[3] , "temp":elem[4] , "humidity":elem[5] , "airflow":elem[6] ,"iaq":elem[7] , "alert":elem[8] , "battery":elem[9] , "slaveaddress":elem[11]})                
        else:
            logger.info("No Assets data to be sent to the server")
            return

    except Exception as err:
        logger.info("Error occured while uploading data to server - " + str(err) + " exiting now")
    else:
        ret = client.publish("tracking", payload=json.dumps({"master":masterMacId,"assets":payload}), qos=0)
        if ret[0]==0:
            logger.info("Data posted successfully to the server")
        else:
            logger.info("Failed to post data to the server with return code - " + str(ret))

        cursor = db.cursor()
        sql = """delete from first_floor"""
        cursor.execute(sql)
        db.commit()

        logger.info("Cleared tracking data in database")

if __name__ == "__main__":
    # Create the logger for the application and bind the output to /sys/log/ #
    logger = logging.getLogger('data-upload-service')
    logger.setLevel(logging.INFO)
    logHandler = logging.handlers.SysLogHandler(address='/dev/log')
    logHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    client = mqtt.Client()
    client.on_connect = on_connect
    systemcon()
    client.loop_start()

    while True:
        uploadData(logger)
        time.sleep(15)
