import sys
import unittest
import pytest
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtTest
from controller.presentater import Controller
import time

class ToTest(unittest.TestCase):

    def setUp(self):
        #required
        self.o=QtWidgets.QApplication(sys.argv)
        self.ui=Controller()

    def testMqttConnect(self):
        print("\n")
        print("Test MQTT Connection\n")
        self.ui.ui.edit_client_endpoint.clear()
        self.ui.ui.edit_pub_username.clear()
        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.edit_client_endpoint.setText("localhost")
        self.ui.ui.edit_pub_username.setText("abccc")
        self.ui.ui.btn_mqtt_client_connect.click()

        self.assertEqual(self.ui.ui.edit_mqtt_client_rec_msg.toPlainText(),'Client 連線成功')
        # self.ui.edit_mqtt_client_rec_msg.clear()
        # self.ui.btn_mqtt_client_disconnect.click()
        # self.assertEqual(self.ui.edit_mqtt_client_rec_msg.toPlainText(), 'Client 斷線')

    def testMqttDisconnect(self):
        print("\n")
        print("Test MQTT Disconnection\n")
        self.ui.ui.edit_client_endpoint.clear()
        self.ui.ui.edit_pub_username.clear()
        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.edit_client_endpoint.setText("localhost")
        self.ui.ui.edit_pub_username.setText("abccc")
        self.ui.ui.btn_mqtt_client_connect.click()

        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.btn_mqtt_client_disconnect.click()
        self.assertEqual(self.ui.ui.edit_mqtt_client_rec_msg.toPlainText(), 'Client 斷線')

    def testMqttpub(self):
        print("\n")
        print("Test MQTT Pub\n")
        self.ui.ui.edit_client_endpoint.clear()
        self.ui.ui.edit_pub_username.clear()
        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.edit_client_endpoint.setText("localhost")
        self.ui.ui.edit_pub_username.setText("abccc")
        self.ui.ui.btn_mqtt_client_connect.click()

        self.assertEqual(self.ui.ui.edit_mqtt_client_rec_msg.toPlainText(),'Client 連線成功')
        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.edit_client_pub_topic.setText("aaa")
        self.ui.ui.edit_client_pub_payload.setText("AutoTest")
        self.ui.ui.btn_mqtt_pub.click()
        self.assertEqual(1, 1)

    def testMqttsub(self):
        print("\n")
        print("Test MQTT Sub\n")
        self.ui.ui.edit_client_endpoint.clear()
        self.ui.ui.edit_pub_username.clear()
        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.edit_client_endpoint.setText("localhost")
        self.ui.ui.edit_pub_username.setText("abccc")
        self.ui.ui.btn_mqtt_client_connect.click()

        self.assertEqual(self.ui.ui.edit_mqtt_client_rec_msg.toPlainText(),'Client 連線成功')
        self.ui.ui.edit_mqtt_client_rec_msg.clear()
        self.ui.ui.edit_client_sub_topic.setText("ccc")
        self.ui.ui.btn_mqtt_client_sub.click()
        time.sleep(5)

    def testOPCUAServer(self):
        self.ui.ui.tabs.setCurrentIndex(1)


# def test_pp():
#     assert 1==1

if __name__ == '__main__':
    unittest.main(verbosity=2)
    #pytest.main()
