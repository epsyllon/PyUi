import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import  QMainWindow
import serial
import time

import data_form


class Soft(QMainWindow, data_form.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)    
        self.ser = None
        #self.initialize_port_serie()  
        self.data_serial = 0
        self.pushButton.clicked.connect(self.Maj_data)
        self.data = open ("test.csv", "w")
        self.step_time.clicked.connect(self.Maj_time)
        self.time = 0
      



    def initialize_port_serie(self):
        self.ser = serial.Serial(port="COM4", baudrate=9600, 
            bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        
        
    def Maj_data (self) :
        print (self.DAC_SELECTOR.currentIndex(), self.VALUE_INPUT.text())
        vara = str(self.DAC_SELECTOR.currentIndex())
        varb = self.VALUE_INPUT.text()
        self.data.write(vara  +',' + varb + '\n')

    def Maj_time (self) :
        print (self.Time_input.text())
        vart = self.time_scale.currentIndex()
        print (vart)
        

if __name__ == '__main__':    
    app = QApplication(sys.argv)
    prog = Soft()
    prog.show()
    sys.exit(app.exec_())
