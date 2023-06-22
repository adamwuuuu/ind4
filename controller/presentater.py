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
import pysoem
import threading
from collections import namedtuple
import struct
from ui.ui import Indfour

class Controller:

    def __init__(self):

        self.ui=Indfour()
        # Variable
        self.mqtt_pub = None
        self.mqtt_client = None
        self.mqtt_sub = None
        self.opcua_client_var = None
        self.opcua_client_nodeid = []
        self.opcua_client_nodevaluee = []
        self.opcua_server_nodes = []
        self.opcua_server_node_values = []
        self.opcua_server_var = None
        self.opcua_server_obj_node = None
        self.mqtt_broker = "test.mosquitto.org"
        self.opcua_root = None
        self.opcua_object = None
        self.table_font = QtGui.QFont('微软雅黑', 10)
        self.table_font.setBold(True)
        self.ethercat_master_adapter_list = []
        self.ethercat_master_adapter_name_list = []
        self.ethercat_master = None
        self.pd_thread_stop_event = threading.Event()
        self.ch_thread_stop_event = threading.Event()
        self.actual_wkc = 0
        self.slave_set = namedtuple('SlaveSet', 'name product_code config_func')
        self.expected_slave_layout = None

        self.ui.btn_mqtt_client_connect.clicked.connect(lambda :self.mqtt_client_connect(
            self.ui.edit_pub_username.text(),self.ui.edit_pub_password.text(),self.ui.edit_client_endpoint.text(),
            60,False
        ))
        self.ui.btn_mqtt_client_disconnect.clicked.connect(self.mqtt_client_disconnect)
        self.ui.btn_mqtt_client_sub.clicked.connect(lambda :self.mqtt_subscribe(self.ui.edit_client_sub_topic.text()))
        self.ui.btn_mqtt_pub.clicked.connect(lambda: self.mqtt_publish(self.ui.edit_client_pub_topic.text(),
                                                                    self.ui.edit_client_pub_payload.text(),False))

        self.ui.btn_mqtt_client_disconnect.setEnabled(False)
        self.ui.btn_mqtt_client_sub.setEnabled(False)
        self.ui.btn_mqtt_pub.setEnabled(False)

        self.ui.opc_server_table.horizontalHeader().setFixedHeight(40)
        self.ui.opc_server_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)  # 设置只可以单选，可以使用ExtendedSelection进行多选
        self.ui.opc_server_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # 设置 不可选择单个单元格，只可选择一行。
        self.ui.opc_server_table.horizontalHeader().resizeSection(0, 200)
        self.ui.opc_server_table.setColumnCount(3)
        self.ui.opc_server_table.setHorizontalHeaderLabels(['Node ID','Data Type','Value'])
        self.ui.opc_server_table.horizontalHeader().setFont(self.table_font)
        self.ui.btn_opc_server_connect.clicked.connect(lambda :self.opcua_server(self.ui.opcua_server_endpoint.text(),
                                                                              self.ui.opcua_server_name.text()))
        self.ui.btn_opc_server_disconnect.clicked.connect(self.opcua_server_disconnect)
        self.ui.btn_opc_server_disconnect.setEnabled(False)

        #opcua client layout
        self.ui.opc_client_table.horizontalHeader().setFixedHeight(40)
        # self.opc_client_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)  #第五列宽度自动调整，充满屏幕
        # self.opc_client_table.horizontalHeader().setStretchLastSection(True)  ##设置最后一列拉伸至最大
        self.ui.opc_client_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)  # 设置只可以单选，可以使用ExtendedSelection进行多选
        self.ui.opc_client_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # 设置 不可选择单个单元格，只可选择一行。
        self.ui.opc_client_table.horizontalHeader().resizeSection(0, 200)
        self.ui.opc_client_table.setColumnCount(3)
        self.ui.opc_client_table.setHorizontalHeaderLabels(['Node ID','Data Type','Value'])
        self.ui.opc_client_table.horizontalHeader().setFont(self.table_font)
        self.ui.opc_client_table.cellChanged.connect(self.cellchange)
        self.ui.opc_client_table.itemDoubleClicked.connect(self.editItem)

        self.ui.btn_opc_client_connect.clicked.connect(lambda :self.opcua_client(self.ui.opcua_client_endpoint.text()))
        self.ui.btn_opc_client_disconnect.clicked.connect(self.opcua_client_disconnect)
        self.ui.btn_opc_client_disconnect.setEnabled(False)


    def opcua_server(self,endpoint,name="Object"):
      try:
        self.opcua_server_var=Server()
        self.opcua_server_var.set_endpoint("opc.tcp://0.0.0.0:"+endpoint)
        self.opcua_server_var.set_server_name(name)
        self.opcua_server_var.set_security_policy([ua.SecurityPolicyType.NoSecurity])

        addspace = self.opcua_server_var.register_namespace(name)
        self.opcua_server_obj_node=self.opcua_server_var.get_objects_node()

        Param = self.opcua_server_obj_node.add_object(addspace, "Parameters")

        Temp = self.opcua_server_obj_node.add_variable(addspace, "Temperature", 0)
        Humid = self.opcua_server_obj_node.add_variable(addspace, "Humidity", 0)
        Time = Param.add_variable(addspace, "Time", 0)

        self.opcua_server_var.start()
        self.opcua_server_nodes=self.opcua_server_var.get_objects_node().get_variables()
        self.opcua_server_node_values=[0,0,0]
        self.ui.opc_server_table.setRowCount(len(self.opcua_server_var.get_objects_node().get_children()))
        i=0
        for childId in self.opcua_server_var.get_objects_node().get_children():
            if i > 0:
                nodes = str(childId.nodeid)
                node_id = nodes.split("i=")[1].replace("))", "").split(")")[0]
                data_type = nodes.split("(")[0]
                nodeitem = QtWidgets.QTableWidgetItem(node_id)
                nodeitem.setFlags(QtCore.Qt.ItemIsEnabled)
                dataitem = QtWidgets.QTableWidgetItem(data_type)
                dataitem.setFlags(QtCore.Qt.ItemIsEnabled)
                value = QtWidgets.QTableWidgetItem(str(self.opcua_server_node_values[i - 1]))
                value.setFlags(QtCore.Qt.ItemIsEnabled)
                self.ui.opc_server_table.setItem(i - 1, 0, nodeitem)
                self.ui.opc_server_table.setItem(i - 1, 1, dataitem)
                self.ui.opc_server_table.setItem(i - 1, 2, value)
            i += 1
        self.ui.opcua_server_log.appendPlainText("OPCUA Server建立成功")
        self.ui.btn_opc_server_disconnect.setEnabled(True)
        self.ui.btn_opc_server_connect.setEnabled(False)

      except Exception as e:
        self.ui.opcua_server_var.stop()
        self.ui.opcua_server_log.appendPlainText(str(e))
        self.ui.btn_opc_server_disconnect.setEnabled(False)
        self.ui.btn_opc_server_connect.setEnabled(True)
    def opcua_server_disconnect(self):
        self.opcua_server_var.stop()
        self.ui.opcua_server_log.appendPlainText("OPCUA Server離線")
        self.ui.btn_opc_server_disconnect.setEnabled(False)
        self.ui.btn_opc_server_connect.setEnabled(True)
    def opcua_client(self,endpoint):
        try:
         if endpoint.find("opc.tcp://")==-1:
             endpoint="opc.tcp://"+endpoint
         self.opcua_client_var=Client(endpoint)
         self.opcua_client_var.connect()
         self.ui.opcua_client_log.appendPlainText("Client 連線成功")

         nodd=self.opcua_client_var.get_node("ns=2;g=7249f318-d1ce-46cc-fc8a-cf80c2634e5d")
         g = ua.ByteStringNodeId(nodd,2)

         self.opcua_root=self.opcua_client_var.get_root_node()
         self.opcua_object=self.opcua_client_var.get_objects_node()

         i=0
         self.opcua_client_nodeid=self.opcua_object.get_variables()
         # self.opcua_client_nodevaluee=self.opcua_client_var.get_values(self.opcua_object.get_variables())
         self.ui.opc_client_table.setRowCount(len(self.opcua_object.get_children())-1)
         print(self.opcua_object.get_children())
         for childId in self.opcua_object.get_children():
            if i>0:
             nodename=str(childId.get_browse_name()).split("(")[1].replace(")","")
             nodes=str(childId.nodeid)
             node_id=nodes.split("i=")[1].replace("))","").split(")")[0]
             data_type=nodes.split("(")[0]
             #nodeitem=QtWidgets.QTableWidgetItem(node_id)
             nodeitem = QtWidgets.QTableWidgetItem(nodename)
             nodeitem.setFlags(QtCore.Qt.ItemIsEnabled)
             dataitem=QtWidgets.QTableWidgetItem(data_type)
             dataitem.setFlags(QtCore.Qt.ItemIsEnabled)
             value=QtWidgets.QTableWidgetItem(str(self.opcua_client_nodevaluee[i-1]))
             value.setFlags(QtCore.Qt.ItemIsEnabled)
             self.ui.opc_client_table.setItem(i-1,0,nodeitem)
             self.ui.opc_client_table.setItem(i-1,1,dataitem)
             self.ui.opc_client_table.setItem(i-1, 2,value)
            i+=1
         self.ui.btn_opc_client_disconnect.setEnabled(True)
         self.ui.btn_opc_client_connect.setEnabled(False)
        except Exception as e:
            self.ui.opcua_client_log.appendPlainText(str(e))
    def cellchange(self,row,col):
        item = self.ui.opc_client_table.item(row,col)
        txt = item.text()
        print(txt)
    def editItem(self, clicked):
       try:
        global okPressed,d
        self.dialogs = QtWidgets.QMessageBox()
        self.dialogs.setWindowTitle("修改")
        self.dialogs.setText("是否修改數值?")
        self.dialogs.setIcon(QtWidgets.QMessageBox.Icon.Information)
        self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Close)
        self.dialogs.setDefaultButton(QtWidgets.QMessageBox.Ok)
        oringal_val=self.opcua_client_nodevaluee[clicked.row()]
        reply=self.dialogs.exec()
        if reply==QtWidgets.QMessageBox.Ok:
                if  type(oringal_val)==bool:
                  d, okPressed = QtWidgets.QInputDialog.getInt(self, "修改數值","數值範圍:", bool(oringal_val), 0, 1, 1)
                elif type(oringal_val)==float:
                  d, okPressed = QtWidgets.QInputDialog.getInt(self, "修改數值", "數值範圍:", int(oringal_val), 0, 100,
                                                                 1)
                elif type(oringal_val)==int:
                  d, okPressed = QtWidgets.QInputDialog.getInt(self, "修改數值", "數值範圍:", int(oringal_val), 0.00,
                                                                 100.00,1)
                if okPressed:
                 self.opcua_client_nodevaluee[clicked.row()]=d
                 self.opcua_client_var.get_node(self.opcua_client_nodeid[clicked.row()]).set_value(d)
                 #self.opcua_client_var.set_values(self.opcua_client_nodeid, self.opcua_client_nodevaluee)
                 self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok )
                 self.dialogs.setText("修改成功\n"+"原本: "+oringal_val+"\n"+
                                     "新的數值: "+ d)
                self.dialogs.exec_()
        else:
                self.dialogs.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok )
                self.dialogs.setText("修改失敗")
                self.dialogs.exec_()
       except Exception as e:
           self.dialogs.setIcon(QtWidgets.QMessageBox.Icon.Warning)
           self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok)
           self.dialogs.setText("修改失敗")
           self.dialogs.exec_()
           self.opcua_client_log.appendPlainText(str(e))
    def opcua_client_disconnect(self):
        try:
            self.opcua_client_var.disconnect()
            self.ui.opcua_client_log.appendPlainText("Client 斷線!")
            self.ui.btn_opc_client_disconnect.setEnabled(False)
            self.ui.btn_opc_client_connect.setEnabled(True)
        except Exception as e:
            self.ui.opcua_client_log.appendPlainText(str(e))

    def mqtt_client_connect(self,id,pwd,host,timeout=60,crpto=False):
        try:
         self.mqtt_client=mqtt.Client()
         self.mqtt_client.username_pw_set(id, pwd)
         self.mqtt_client.on_message = self.on_message
         self.mqtt_client.on_connect = self.on_connect
         if crpto:
            self.mqtt_client.connect(host,8883,timeout)
         else:
            self.mqtt_client.connect(host,1883,timeout)
        except Exception as e:
            self.edit_mqtt_client_rec_msg.appendPlainText(str(e))

            self.ui.btn_mqtt_client_disconnect.setEnabled(False)
            self.ui.btn_mqtt_client_sub.setEnabled(False)
            self.ui.btn_mqtt_pub.setEnabled(False)
            self.ui.btn_mqtt_client_connect.setEnabled(True)
        finally:
            self.ui.edit_mqtt_client_rec_msg.appendPlainText("Client 連線成功")
            self.ui.btn_mqtt_client_disconnect.setEnabled(True)
            self.ui.btn_mqtt_client_sub.setEnabled(True)
            self.ui.btn_mqtt_pub.setEnabled(True)
            self.ui.btn_mqtt_client_connect.setEnabled(False)
    def mqtt_client_disconnect(self):
       try:
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()
        self.ui.edit_mqtt_client_rec_msg.appendPlainText("Client 斷線")
        self.ui.btn_mqtt_client_disconnect.setEnabled(False)
        self.ui.btn_mqtt_client_sub.setEnabled(False)
        self.ui.btn_mqtt_pub.setEnabled(False)
        self.ui.btn_mqtt_client_connect.setEnabled(True)
       except Exception as e:
           self.ui.edit_mqtt_client_rec_msg.appendPlainText(str(e))
           self.ui.btn_mqtt_client_disconnect.setEnabled(False)
           self.ui.btn_mqtt_client_sub.setEnabled(False)
           self.ui.btn_mqtt_pub.setEnabled(False)
           self.ui.btn_mqtt_client_connect.setEnabled(True)
    def mqtt_publish(self,topic,payload,keepalive):
       try:
        while True:
            t0 = random.randint(0, 30)
            t = datetime.datetime.now().strftime('%m/%d %H:%M:%S')
            #payload = {'Temperature': t0, 'Time': t}
            print(json.dumps(payload))
            # 要發布的主題和內容
            self.mqtt_client.publish(topic, json.dumps(payload))
            self.ui.edit_mqtt_client_rec_msg.appendPlainText("Client Publish:\n"+
                                                          "Topic: "+topic+"\n"
                                                          "Payload: "+payload)
            time.sleep(5)
            if not keepalive:
                break
       except Exception as e:
           self.ui.edit_mqtt_client_rec_msg.appendPlainText(str(e))
    def mqtt_subscribe(self,topic):

        self.mqtt_client.subscribe(topic)
        self.ui.edit_mqtt_client_rec_msg.appendPlainText("Client Subscribe:\n" +
                                                      "Topic: " + topic)
        self.mqtt_client.loop_start()
    def on_connect(self,client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # 將訂閱主題寫在on_connet中
        # 如果我們失去連線或重新連線時
        # 程式將會重新訂閱
        # client.subscribe(topic)
        self.ui.edit_mqtt_client_rec_msg.appendPlainText(str(rc))

    # 當接收到從伺服器發送的訊息時要進行的動作
    def on_message(self,client, userdata, msg):
        # 轉換編碼utf-8才看得懂中文
        print(msg.topic + " " + msg.payload.decode('utf-8'))
        self.ui.edit_mqtt_client_rec_msg.appendPlainText(
            "Client 接收訊息:\n"+"Topic: "+msg.topic + "\n" +"Message: "
            + msg.payload.decode('utf-8'))
    def ethercat_master_find_adapter(self):
        adapters = pysoem.find_adapters()

        for i, adapter in enumerate(adapters):
            #print('Adapter {}'.format(i))
            #print('  {}'.format(adapter.name))
            #print('  {}'.format(adapter.desc))
            self.ethercat_master_adapter_list.append(adapter.name)
            self.ethercat_master_adapter_name_list.append(adapter.desc)

    def ethercat_master_connect(self,ifname):
        #For Ex
        BECKHOFF_VENDOR_ID = 0x0002
        EK1100_PRODUCT_CODE = 0x044c2c52
        EL3002_PRODUCT_CODE = 0x0bba3052
        EL1259_PRODUCT_CODE = 0x04eb3052

        if ifname=="":
            return
        self.ethercat_master=None
        self.ethercat_master= pysoem.Master()
        self.ethercat_master.in_op = False
        self.ethercat_master.do_check_state = False
        self.expected_slave_layout = {0: self.slave_set('EK1100', EK1100_PRODUCT_CODE, None),
                                       1: self.slave_set('EL3002', EL3002_PRODUCT_CODE, None),
                                       2: self.slave_set('EL1259', EL1259_PRODUCT_CODE, self.el1259_setup)}

    def el1259_setup(self, slave_pos):
        slave = self.ethercat_master.slaves[slave_pos]

        slave.sdo_write(0x8001, 2, struct.pack('B', 1))

        rx_map_obj = [0x1603,
                      0x1607,
                      0x160B,
                      0x160F,
                      0x1611,
                      0x1617,
                      0x161B,
                      0x161F,
                      0x1620,
                      0x1621,
                      0x1622,
                      0x1623,
                      0x1624,
                      0x1625,
                      0x1626,
                      0x1627]
        rx_map_obj_bytes = struct.pack(
            'Bx' + ''.join(['H' for i in range(len(rx_map_obj))]), len(rx_map_obj), *rx_map_obj)
        slave.sdo_write(0x1c12, 0, rx_map_obj_bytes, True)

        slave.dc_sync(1, 10000000)

    def processdata_thread(self):
        while not self.pd_thread_stop_event.is_set():
            self.ethercat_master.send_processdata()
            self._actual_wkc = self.ethercat_master.receive_processdata(10000)
            if not self._actual_wkc == self.ethercat_master.expected_wkc:
                print('incorrect wkc')
            time.sleep(0.01)

    def pdo_update_loop(self):

        self.ethercat_master.in_op = True

        output_len = len(self.ethercat_master.slaves[2].output)

        tmp = bytearray([0 for i in range(output_len)])

        toggle = True
        try:
            while 1:
                if toggle:
                    tmp[0] = 0x00
                else:
                    tmp[0] = 0x02
                self.ethercat_master.slaves[2].output = bytes(tmp)

                toggle ^= True

                time.sleep(1)

        except KeyboardInterrupt:
            # ctrl-C abort handling
            print('stopped')

    def ethercat_run(self,ifname):

        self.ethercat_master.open(ifname)

        if not self.ethercat_master.config_init() > 0:
            self.ethercat_master.close()
            raise BasicExampleError('no slave found')

        for i, slave in enumerate(self.ethercat_master.slaves):
            if not ((slave.man == self.BECKHOFF_VENDOR_ID) and
                    (slave.id == self.expected_slave_layout[i].product_code)):
                self.ethercat_master.close()
                raise BasicExampleError('unexpected slave layout')
            slave.config_func = self.expected_slave_layout[i].config_func
            slave.is_lost = False

        self.ethercat_master.config_map()

        if self.ethercat_master.state_check(pysoem.SAFEOP_STATE, 50000) != pysoem.SAFEOP_STATE:
            self.ethercat_master.close()
            raise BasicExampleError('not all slaves reached SAFEOP state')

        self.ethercat_master.state = pysoem.OP_STATE

        check_thread = threading.Thread(target=self.check_thread)
        check_thread.start()
        proc_thread = threading.Thread(target=self.processdata_thread)
        proc_thread.start()

        # send one valid process data to make outputs in slaves happy
        self.ethercat_master.send_processdata()
        self.ethercat_master.receive_processdata(2000)
        # request OP state for all slaves

        self.ethercat_master.write_state()

        all_slaves_reached_op_state = False
        for i in range(40):
            self.ethercat_master.state_check(pysoem.OP_STATE, 50000)
            if self.ethercat_master.state == pysoem.OP_STATE:
                all_slaves_reached_op_state = True
                break

        if all_slaves_reached_op_state:
            self.pdo_update_loop()

        self.pd_thread_stop_event.set()
        self.ch_thread_stop_event.set()
        proc_thread.join()
        check_thread.join()
        self.ethercat_master.state = pysoem.INIT_STATE
        # request INIT state for all slaves
        self.ethercat_master.write_state()
        self.ethercat_master.close()

        if not all_slaves_reached_op_state:
            raise BasicExampleError('not all slaves reached OP state')

    @staticmethod
    def check_slave(slave, pos):
        if slave.state == (pysoem.SAFEOP_STATE + pysoem.STATE_ERROR):
            print(
                'ERROR : slave {} is in SAFE_OP + ERROR, attempting ack.'.format(pos))
            slave.state = pysoem.SAFEOP_STATE + pysoem.STATE_ACK
            slave.write_state()
        elif slave.state == pysoem.SAFEOP_STATE:
            print(
                'WARNING : slave {} is in SAFE_OP, try change to OPERATIONAL.'.format(pos))
            slave.state = pysoem.OP_STATE
            slave.write_state()
        elif slave.state > pysoem.NONE_STATE:
            if slave.reconfig():
                slave.is_lost = False
                print('MESSAGE : slave {} reconfigured'.format(pos))
        elif not slave.is_lost:
            slave.state_check(pysoem.OP_STATE)
            if slave.state == pysoem.NONE_STATE:
                slave.is_lost = True
                print('ERROR : slave {} lost'.format(pos))
        if slave.is_lost:
            if slave.state == pysoem.NONE_STATE:
                if slave.recover():
                    slave.is_lost = False
                    print(
                        'MESSAGE : slave {} recovered'.format(pos))
            else:
                slave.is_lost = False
                print('MESSAGE : slave {} found'.format(pos))

    def check_thread(self):

        while not self.ch_thread_stop_event.is_set():
            if self.ethercat_master.in_op and ((self._actual_wkc < self.ethercat_master.expected_wkc) or self.ethercat_master.do_check_state):
                self.ethercat_master.do_check_state = False
                self.ethercat_master.read_state()
                for i, slave in enumerate(self.ethercat_master.slaves):
                    if slave.state != pysoem.OP_STATE:
                        self.ethercat_master.do_check_state = True
                        Indfour.check_slave(slave, i)
                if not self.ethercat_master.do_check_state:
                    print('OK : all slaves resumed OPERATIONAL.')
            time.sleep(0.01)
    def msg_deliver(self,title:str,text:str,yesno:bool):
        self.dialogs = QtWidgets.QMessageBox()
        self.dialogs.setWindowTitle(title)
        self.dialogs.setText(text)
        self.dialogs.setIcon(QtWidgets.QMessageBox.Icon.Information)
        if yesno:
            self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Close)
            self.dialogs.setDefaultButton(QtWidgets.QMessageBox.Ok)
            reply=self.dialogs.exec()
            if reply==QtWidgets.QMessageBox.Ok:
                self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok )
                self.dialogs.setText(text+"成功")
                self.dialogs.exec_()
            else:
                self.dialogs.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok )
                self.dialogs.setText(text+"取消")
                self.dialogs.exec_()
        else:
            self.dialogs.setStandardButtons(QtWidgets.QMessageBox.Ok )
            self.dialogs.exec_()

class BasicExampleError(Exception):
    def __init__(self, message):
        super(BasicExampleError, self).__init__(message)
        self.message = message















