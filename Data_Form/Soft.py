import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import  QMainWindow, QFileDialog
import serial
import time
import matplotlib.pyplot as plt
import csv

import data_form2


class Soft(QMainWindow, data_form2.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)    
        self.ser = None 
        self.data_serial = 0
        self.pushButton.clicked.connect(self.Maj_data)
        self.data = open ("init.csv", "w")
        self.file_path = "init.csv"
        self.step_time.clicked.connect(self.Maj_time)
        self.Export.clicked.connect(self.exporter)
        self.current_time = 0
        self.nb_cmd =0
        self.fpga_cmds = []
        self.Flash.clicked.connect(self.data_to_bin)
        self.Open_file.clicked.connect(self.File) 
        self.Wave.clicked.connect(self.plotter)

      



    def initialize_port_serie(self):
        self.ser = serial.Serial(port="COM4", baudrate=9600, 
            bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        
        
    def Maj_data (self) :
        vara = str(self.DAC_SELECTOR.currentIndex())
        varb = self.VALUE_INPUT.text()
        self.data.write("data," +vara  +',' + varb + '\n')

    def Maj_time (self) :
        time_scale = self.time_scale.currentIndex()
        t_temp = int (self.Time_input.text())

        self.data.write("tempo," + str(time_scale)  +',' + str(t_temp) + ",t"+ str(self.current_time) + '\n')

        if (time_scale == 0):
            t_temp =t_temp / 1000
        if (time_scale == 1 ):
            t_temp = t_temp / 100000
        
        self.current_time += t_temp

        self.time.setText( "t= " + str(self.current_time))
        

    def plotter (self): 
        file = open(self.file_path, newline = '') 
        reader = csv.reader(file, 
                        quoting = csv.QUOTE_ALL,
                        delimiter = ',')

        xdat = [[0],[0],[0],[0]]
        ydat = [[0],[0],[0],[0]]
        tdat = 0 

        for rows in reader :
            if rows[0] == 'data' :
                ydat[int(rows[1])].append (int(rows[2]))
                xdat[int(rows[1])].append (tdat)

            if rows[0] == 'tempo' :
                temp = int(rows[2])
                scale = int(rows[1])
                if (scale == 0):
                    temp =temp / 1000
                if (scale == 1 ):
                    temp = temp / 100000

                tdat += temp
        file.close()
        for i in range (4):
            xdat[i].append(tdat)
            ydat[i].append(0)


        plt.step(xdat[0],ydat[0], where= "post")
        plt.step(xdat[1],ydat[1], where= "post")
        plt.step(xdat[2],ydat[2], where= "post")
        plt.step(xdat[3],ydat[3], where= "post")
        plt.show()

    def exporter (self):
        self.data.close()
        self.data_to_bin()
        self.plotter()

    def data_to_bin (self):
        file = open(self.file_path, newline = '') 
        reader = csv.reader(file, 
                        quoting = csv.QUOTE_ALL,
                        delimiter = ',')

        
        
        self.nb_cmd = 0

        for rows in reader:
            commande = 0
            if rows [0] == 'data':
                commande += 8
            
            commande += int (rows[1])

            self.fpga_cmds.append((commande << 12) + round (int (rows[2]) / 0.805860805861))
            print (hex(self.fpga_cmds[self.nb_cmd]))
            self.nb_cmd += 1

        #self.Send_uart()

    def Send_uart (self):
        self.initialize_port_serie() 

        self.ser.write(nb_cmd.to_bytes(1,'big'))
        
        for i in range (self.nb_cmd):
            msb = ((self.fpga_cmds[i] & 0xFF00)>> 8 ).to_bytes(1,'big')
            lsb = (self.fpga_cmds[i] & 0x00FF).to_bytes(1,'big')
            self.ser.write(msb)
            time.sleep(0.01)
            self.ser.write(lsb)

        self.ser.close()

    def File (self):
        file, check = QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()", "", "Data File ( *.csv)")

        if check:
            self.file_path = file
            self.data.close()
            print(file)


if __name__ == '__main__':    
    app = QApplication(sys.argv)
    prog = Soft()
    prog.show()
    sys.exit(app.exec_())
