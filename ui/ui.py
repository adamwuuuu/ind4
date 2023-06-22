#coding:utf-8
import uuid
from PyQt5 import QtWidgets,QtGui,QtCore
from opcua import Client, ua,Server,uamethod
from opcua.ua import ua_binary as uabin
from opcua.common.methods import call_method
from opcua.common.node import Node
import os,sys
import paho.mqtt.client as mqtt
import time,json
import random,datetime

class Indfour(QtWidgets.QWidget):

    def __init__(self):
        super(Indfour,self).__init__()

        #Layouts
        self.main_layout=QtWidgets.QGridLayout()
        self.mqtt_pub_layout=QtWidgets.QGridLayout()
        self.mqtt_sub_layout=QtWidgets.QGridLayout()
        self.opcua_server_layout=QtWidgets.QGridLayout()
        self.opcua_client_layout=QtWidgets.QGridLayout()
        self.ethercat_master_layout=QtWidgets.QGridLayout()
        self.tabs = QtWidgets.QTabWidget()
        self.tab_mqtt_pub=QtWidgets.QTabWidget()
        self.tab_mqtt_sub=QtWidgets.QTabWidget()
        self.tab_opc_server=QtWidgets.QTabWidget()
        self.tab_opc_client=QtWidgets.QTabWidget()
        self.tab_ethercat_master=QtWidgets.QTabWidget()
        self.tabs.addTab(self.tab_mqtt_pub,"MQTT Client")
        # self.tabs.addTab(self.tab_mqtt_sub,"MQTT Broker")
        self.tabs.addTab(self.tab_opc_server,"OPCUA Server")
        self.tabs.addTab(self.tab_opc_client,"OPCUA Client")
        self.tabs.addTab(self.tab_ethercat_master,"EtherCat Master")
        #mqtt pub layout
        self.group_mqtt_client_connection = QtWidgets.QGridLayout()
        self.group_mqtt_client_pub = QtWidgets.QGridLayout()
        self.group_mqtt_client_sub = QtWidgets.QGridLayout()
        self.group_mqtt_client_1=QtWidgets.QGroupBox()
        self.group_mqtt_client_2 = QtWidgets.QGroupBox()
        self.group_mqtt_client_3 = QtWidgets.QGroupBox()
        self.btn_mqtt_pub=QtWidgets.QPushButton('Publish')
        self.btn_mqtt_client_connect=QtWidgets.QPushButton('Connect')
        self.btn_mqtt_client_disconnect = QtWidgets.QPushButton('Disconnect')
        self.btn_mqtt_client_sub = QtWidgets.QPushButton('Subscribe')
        self.edit_pub_username=QtWidgets.QLineEdit()
        self.edit_pub_password=QtWidgets.QLineEdit()
        self.edit_client_sub_topic = QtWidgets.QLineEdit()
        self.edit_client_pub_topic=QtWidgets.QLineEdit()
        self.edit_client_endpoint=QtWidgets.QLineEdit()
        self.edit_client_pub_payload=QtWidgets.QLineEdit()
        self.edit_mqtt_client_rec_msg=QtWidgets.QPlainTextEdit()

        # Group Connect
        self.group_mqtt_client_connection.addWidget(
            QtWidgets.QLabel('EndPoint'),0,0
        )
        self.group_mqtt_client_connection.addWidget(
            self.edit_client_endpoint,0,1
        )
        self.group_mqtt_client_connection.addWidget(
            QtWidgets.QLabel('Username'),1,0
        )
        self.group_mqtt_client_connection.addWidget(
            QtWidgets.QLabel('Password'),1,1
        )
        self.group_mqtt_client_connection.addWidget(
            self.edit_pub_username,2,0
        )
        self.group_mqtt_client_connection.addWidget(
            self.edit_pub_password,2,1
        )
        self.group_mqtt_client_connection.addWidget(
            self.btn_mqtt_client_connect,3,0
        )
        self.group_mqtt_client_connection.addWidget(
            self.btn_mqtt_client_disconnect,3,1
        )
        self.group_mqtt_client_connection.addWidget(
            QtWidgets.QLabel(''),4,0
        )
        #Group Pub
        self.group_mqtt_client_pub.addWidget(
            QtWidgets.QLabel('Topic'), 0, 0
        )
        self.group_mqtt_client_pub.addWidget(
            self.edit_client_pub_topic,1,0
        )
        self.group_mqtt_client_pub.addWidget(
            QtWidgets.QLabel('Message'), 2, 0
        )
        self.group_mqtt_client_pub.addWidget(
            self.edit_client_pub_payload,3,0
        )
        self.group_mqtt_client_pub.addWidget(
            self.btn_mqtt_pub,4,0
        )
        #Group Sub
        self.group_mqtt_client_sub.addWidget(
            QtWidgets.QLabel('Topic'), 0, 0
        )
        self.group_mqtt_client_sub.addWidget(
            self.edit_client_sub_topic, 1, 0
        )
        self.group_mqtt_client_sub.addWidget(
            self.btn_mqtt_client_sub,2,0
        )
        self.group_mqtt_client_sub.addWidget(
            QtWidgets.QLabel(''), 3, 0
        )
        self.group_mqtt_client_sub.addWidget(
            QtWidgets.QLabel(''), 4, 0
        )

        self.group_mqtt_client_1.setLayout(
            self.group_mqtt_client_connection
        )
        self.group_mqtt_client_2.setLayout(
            self.group_mqtt_client_pub
        )
        self.group_mqtt_client_3.setLayout(
            self.group_mqtt_client_sub
        )
        self.mqtt_pub_layout.addWidget(
            QtWidgets.QLabel('Publish'),0,0
        )
        self.mqtt_pub_layout.addWidget(
            self.group_mqtt_client_1,1,0
        )
        self.mqtt_pub_layout.addWidget(
            self.group_mqtt_client_2, 1, 1
        )
        self.mqtt_pub_layout.addWidget(
            self.group_mqtt_client_3,1,2
        )
        self.mqtt_pub_layout.addWidget(
            self.edit_mqtt_client_rec_msg,2,0
        )
        self.tab_mqtt_pub.setLayout(
            self.mqtt_pub_layout
        )

        #mqtt sub layout
        self.mqtt_sub_layout.addWidget(
            QtWidgets.QLabel('Subscribe'),0,0
        )

        self.tab_mqtt_sub.setLayout(
            self.mqtt_sub_layout
        )
        #opcua server layout
        self.opc_server_table = QtWidgets.QTableWidget()
        # self.opc_client_table.setFrameShape(QFrame.NoFrame)
        self.opcua_server_endpoint=QtWidgets.QLineEdit()
        self.opcua_server_name=QtWidgets.QLineEdit()
        self.btn_opc_server_connect=QtWidgets.QPushButton('Conncet')
        self.btn_opc_server_disconnect = QtWidgets.QPushButton('Disconncet')

        self.opcua_server_log=QtWidgets.QPlainTextEdit()

        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel('SERVER'),0,0
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel('Port'),1,0
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel('Server Name'),1,1
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel(' '),1,2
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel(' '),1,3
        )
        self.opcua_server_layout.addWidget(
            self.opcua_server_endpoint,2,0
        )
        self.opcua_server_layout.addWidget(
            self.opcua_server_name,2,1
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel(' '),2,2
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel(' '),2,3
        )
        self.opcua_server_layout.addWidget(
            self.btn_opc_server_connect,3,0
        )
        self.opcua_server_layout.addWidget(
            self.btn_opc_server_disconnect,3,1
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel(' '),3,2
        )
        self.opcua_server_layout.addWidget(
            QtWidgets.QLabel(' '),3,3
        )
        self.opcua_server_layout.addWidget(
            self.opcua_server_log,4,0
        )
        self.opcua_server_layout.addWidget(
            self.opc_server_table,4,1
        )

        self.tab_opc_server.setLayout(
            self.opcua_server_layout
        )
        #opcua client layout
        self.opc_client_table = QtWidgets.QTableWidget()
        self.client_table_view=QtWidgets.QVBoxLayout()
        # self.opc_client_table.setFrameShape(QFrame.NoFrame)
        self.opcua_client_endpoint=QtWidgets.QLineEdit()
        self.btn_opc_client_connect=QtWidgets.QPushButton('Conncet')
        self.btn_opc_client_disconnect = QtWidgets.QPushButton('Disconncet')
        self.opcua_client_log=QtWidgets.QPlainTextEdit()

        self.opcua_client_layout.addWidget(
            QtWidgets.QLabel('Client'),0,0
        )
        self.opcua_client_layout.addWidget(
            QtWidgets.QLabel('EndPoint'),1,0
        )
        self.opcua_client_layout.addWidget(
            self.opcua_client_endpoint,1,1
        )
        self.opcua_client_layout.addWidget(
            QtWidgets.QLabel(''),1,2
        )
        self.opcua_client_layout.addWidget(
            QtWidgets.QLabel(''),1,3
        )
        self.opcua_client_layout.addWidget(
            self.btn_opc_client_connect,2,0
        )
        self.opcua_client_layout.addWidget(
            self.btn_opc_client_disconnect,2,1
        )
        self.opcua_client_layout.addWidget(
            QtWidgets.QLabel(''),2,2
        )
        self.opcua_client_layout.addWidget(
            QtWidgets.QLabel(''),2,3
        )
        self.opcua_client_layout.addWidget(
            self.opcua_client_log,3,0
        )
        self.opcua_client_layout.addWidget(
            self.opc_client_table,3,1
        )


        self.tab_opc_client.setLayout(
            self.opcua_client_layout
        )

        #EtherCat Master


        self.tab_ethercat_master.setLayout(
            self.ethercat_master_layout
        )

        #Main
        self.main_layout.addWidget(
            self.tabs,0,0
        )
        self.setLayout(self.main_layout)
        self.setGeometry(500, 300, 550, 400)

        self.setWindowTitle('IND 4.0')
        self.show()