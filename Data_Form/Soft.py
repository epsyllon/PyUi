import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import  QMainWindow
import serial
import time
import matplotlib

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
        self.Export.clicked.connect(self.exporter)
        self.current_time = 0
      



    def initialize_port_serie(self):
        self.ser = serial.Serial(port="COM4", baudrate=9600, 
            bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        
        
    def Maj_data (self) :
        print (self.DAC_SELECTOR.currentIndex(), self.VALUE_INPUT.text())
        vara = str(self.DAC_SELECTOR.currentIndex())
        varb = self.VALUE_INPUT.text()
        self.data.write("data," +vara  +',' + varb + '\n')

    def Maj_time (self) :
        print (self.Time_input.text())
        time_scale = self.time_scale.currentIndex()
        t_temp = int (self.Time_input.text())

        self.data.write("tempo," + str(time_scale)  +',' + str(t_temp) + '\n')

        if (time_scale == 0):
            t_temp =t_temp / 1000
        if (time_scale == 1 ):
            t_temp = t_temp / 100000
        
        self.current_time += t_temp

        self.time.setText( "t= " + str(self.current_time))
        

    def plotter (self, x, y): 
        print (x , y)

    def exporter (self):
        self.data.close()
        self.data = open ("test.csv", "r")

        for rows in self.data :
            self.plotter( rows[1] , rows [2])



if __name__ == '__main__':    
    app = QApplication(sys.argv)
    prog = Soft()
    prog.show()
    sys.exit(app.exec_())
