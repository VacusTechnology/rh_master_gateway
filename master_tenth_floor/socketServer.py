#! /usr/bin/python3

#
#This script recieves the data from the zone monitors and forwards it to the web
#server after doing all the computations
#
from multiprocessing import Process,Semaphore,Queue
from time import sleep
import logging
import logging.handlers
import socket
import signal,os
import json
import mysql.connector

RECEIVE_BUFFER = 5000
SOCKET_BINDING_ADDR=('127.0.0.1',12310)

DB_USERNAME="vacus"
DB_PASSWORD="vacus321"
DB_NAME="master_db"

def bindSocketAddress(logger):
    try:
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        skt.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
        skt.bind(('',12310))
        skt.listen(10)
    except Exception as err:
        logger.info("Failed to bind the socket due to the exception- " + str(err))
        return None
    else:
        return skt

def Manager(skt,logger):
    while True:
        try:
            # Accepts the connection from the Zone Monitor #
            conn,addrTuple = skt.accept()                  
            logger.info("Accepted the connection from the Reader")
            logger.info("Spawning a worker process for data processing")    

            rcvdBytes = conn.recv(RECEIVE_BUFFER)
            q = Queue()
            q.put(rcvdBytes)
            process = Process(target=worker,args=(q,))
            process.start()

            #Close the connecttion #
            conn.close()

        except Exception as err:
            logger.info("Exception occured in Manager process " + str(err))
            logger.info("Terminating Manager process")
            skt.close()
            os.kill(os.getpid(),signal.SIGKILL)

def worker(q):
    data=q.get()
    q.close()
    print(data)
    jsonList = json.loads(data.decode('utf-8'))
    
    #logger.info("Type of data received is - " + str(type(jsonList)))
    #logger.info("Data received from the Reader is " + str(jsonList))

    try:
        db = mysql.connector.connect(
            host="localhost",
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_NAME
            )

        if len(jsonList)!=0:
            for elem in jsonList:
                sql = """SELECT * FROM tenth_floor WHERE macaddress = %s"""
                val = (elem["macaddress"],)
                cursor = db.cursor() 
                cursor.execute(sql, val)
                result = cursor.fetchone()
            
                if result==None:
                    logger.info("Asset not found in db...storing")
                    sql = """INSERT INTO tenth_floor (macaddress,X,Y,temp,humidity,airflow,iaq,alert,battery,packet,slave) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    tupleData= (elem["macaddress"],elem["X"],elem["Y"],elem["temp"],elem["humidity"],elem["airflow"],elem["iaq"],elem["alert"],elem["battery"],elem["packet"],elem["slaveaddress"])
                    cursor = db.cursor()
                    cursor.execute(sql,tupleData)
                    db.commit()
                else:
                    logger.info("Asset found in db")
                    if elem["packet"]>result[10]:
                        logger.info("Packet number is greater than the stored one, updating the packet")
                        sql="""UPDATE tenth_floor SET X=%s,Y=%s,temp=%s,humidity=%s,airflow=%s,iaq=%s,alert=%s,battery=%s,packet=%s,slave=%s WHERE macaddress = %s"""
                        tupleData= (elem["X"],elem["Y"],elem["temp"],elem["humidity"],elem["airflow"],elem["iaq"],elem["alert"],elem["battery"],elem["packet"],elem["macaddress"],elem["slaveaddress"])
                        cursor=db.cursor()
                        cursor.execute(sql,tupleData)
                        db.commit()

        else:
            logger.info("No data to be stored in db")
    except Exception as err:
        logger.info("ERROR OCCURED - " +str(err))

    os.kill(os.getpid(),signal.SIGKILL)
    
if __name__ == "__main__":
    # Create the logger for the application and bind the output to /sys/log/ #
    logger = logging.getLogger('processing-service')
    logger.setLevel(logging.INFO)
    
    logHandler = logging.handlers.SysLogHandler(address='/dev/log')
    logHandler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(name)s - %(message)s')

    logHandler.setFormatter(formatter)

    logger.addHandler(logHandler)

    skt=bindSocketAddress(logger)

    if (skt!=None):
        Manager(skt,logger)

