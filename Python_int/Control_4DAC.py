
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import  QMainWindow
import serial
import time

import ui_DAC


class ui_DAC(QMainWindow, ui_DAC.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)    
        self.ser = None
        self.initialize_port_serie()  
        self.data_serial = 0
        self.pushButton.clicked.connect(self.display)


    def initialize_port_serie(self):
        self.ser = serial.Serial(port="COM4", baudrate=9600, 
            bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        
        
        
        
    def set_bit (self, n):
        self.data_serial = self.data_serial | (1 << n)

    def maj_command (self):
        pass

    def display(self):
        print (self.comboBox.currentIndex(), self.comboBox_2.currentIndex(), self.dial.value())
        self.data_serial = 0
        self.data_serial += self.comboBox.currentIndex() << 14
        self.data_serial += self.comboBox_2.currentIndex() << 12
        self.data_serial += self.dial.value()
        print (hex(self.data_serial))
        
        print(hex((self.data_serial & 0xFF00)>> 8 ), "msb")
        print(hex(self.data_serial & 0x00FF), "lsb")

        msb = ((self.data_serial & 0xFF00)>> 8 ).to_bytes(1,'big')
        lsb = (self.data_serial & 0x00FF).to_bytes(1,'big')
        ack = (6).to_bytes(1,'big')

    

        
        self.ser.write(msb)
        time.sleep(0.01)
        self.ser.write(lsb)
        #print (self.ser.read(1))
        #self.ser.write(ack)
        #self.ser.write(ack)
       
        '''
        time.sleep(1)
        print ("uok?")
        self.ser.write(lsb)

        print (self.ser.read(1))
        
        self.data_serial = 0
        time.sleep(0.01)
        time.sleep(1)
        self.ser.write(ack)
        '''
        self.data_serial = 0
        

        

if __name__ == '__main__':    
    app = QApplication(sys.argv)
    prog = ui_DAC()
    prog.show()
    sys.exit(app.exec_())

