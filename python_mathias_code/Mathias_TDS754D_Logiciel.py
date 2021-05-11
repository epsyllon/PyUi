# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 10:51:42 2021

@author: henry
"""

import sys, datetime, os, time, shutil
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator


import ui_Mathias_TDS754D_Logiciel
            

class Oscilloscope(QMainWindow, ui_Mathias_TDS754D_Logiciel.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)       
        self.description = ''
        self.fileName = None
        self.configureFileName = None  
        self.cmd_listFileName = None
        self.gpib_init = False 
        self.portserie_initialized = False
        self.configbasefilename = "C:\\Python\\Mathias_TDS754D\\TDS754D_logiciel\\config.txt"
        self.Quit_qpbt.clicked.connect(self.arrete)
        self.InitGPIB_qpbt.clicked.connect(self.initializeGPIB)
        self.Acquire_data_qpbt.clicked.connect(self.Data_query)
        self.Plot_data_qpbt.clicked.connect(self.Plot_data)
        self.FileSaveAs_qpbt.clicked.connect(self.saveAsFileDialog)
        self.FileLoad_qpbt.clicked.connect(self.loadFileDialog)
        #visa.log_to_screen()
        self.rm = visa.ResourceManager()        
        print(self.rm.list_resources())
        self.ressources_nbr = len(self.rm.list_resources())
        print(self.ressources_nbr)
        self.CH1 = False
        self.CH2 = False
        self.CH3 = False
        self.CH4 = False
        self.MEAS1 = False
        self.MEAS2 = False
        self.MEAS3 = False
        self.MEAS4 = False
        self.screen_data_CH1 = list()
        self.screen_data_CH2 = list()
        self.screen_data_CH3 = list()
        self.screen_data_CH4 = list()
        self.data_CH1 = list()
        self.data_CH2 = list()
        self.data_CH3 = list()
        self.data_CH4 = list()
        self.new_data = False
        self.data_saved = False
        self.CURS = 'OFF'
        self.i = 0
        self.initfiles()       
  
      
    def arrete(self):
        #sauvegarde les noms de fichiers
        if os.path.isfile(self.configbasefilename):
            f = open(self.configbasefilename,'w')
            f.write(self.SaveFileName_qledit.text() + '\n')
            gpib_adr = self.TDS754D_ADR_qledit.text()
            f.write('TDS754D\t' + gpib_adr + '\n')
            f.close()

        if self.gpib_init:                 
            self.gpib_init = False

        self.close()
  
      
    def initializeGPIB(self):      
        self.TDS754D_IDN_qledit.setText("")
        gpib_adr = self.TDS754D_ADR_qledit.text()
        #Test tous les nombres de GPIB au moins autant qu'il y ai de ressources
        gpib_nbr = 0
        for gpib_nbr in range(self.ressources_nbr):
            if not self.gpib_init:
                try:
                    self.my_TDS754D = self.rm.open_resource('GPIB' + str(gpib_nbr) + '::' + gpib_adr, read_termination = '\n')
                    self.my_TDS754D.clear()
                    my_TDS754D_IDN = self.my_TDS754D.query('*IDN?')
                    self.TDS754D_IDN_qledit.setText(my_TDS754D_IDN)
                    if (my_TDS754D_IDN):
                        self.gpib_init = True
                except:
                    pass
     
        
    def initfiles(self):
        if os.path.isfile(self.configbasefilename):
            fp = open(self.configbasefilename)
            # supprime les trailings characters '\n' et '\r'
            self.fileName = fp.readline().rstrip('\r\n')
            self.SaveFileName_qledit.setText(self.fileName)
            a = fp.readline().split('\t')
            gpib_adr = a[1].rstrip('\r\n')
            self.TDS754D_ADR_qledit.setText(gpib_adr)
            fp.close()
            #Lis le dernier fichier de mesure sauvgardé
            self.readdata(self.fileName)
            
            
    def Data_query(self):
        if self.gpib_init:
            self.Channel1_Data_qtedit.setText('')
            self.Channel2_Data_qtedit.setText('')
            self.Channel3_Data_qtedit.setText('')
            self.Channel4_Data_qtedit.setText('')
            #Configure la récuperation de données pour obtenir les données des 4 channels
            self.my_TDS754D.write('DATa:SOUrce CH1, CH2, CH3, CH4')
            #Configure la récuperation de données en format ASCII
            self.my_TDS754D.write('DATa:ENCdg ASCII')
            #Configure le nombre d'octet par point :
            #   1 en mode Sample, Envelope ou Peakdetect
            #   Si utilisé en Average ou HiRes le LSB ne sera pas transmis
            #   2 en mode Average ou HiRes
            #   Si utilisé en Sample, Envelope ou Peakdetect le LSB sera égal à 0
            self.my_TDS754D.write('DATa:WIDth 1')
            #Configure le nombre de points que l'on récupère ici 500 000 soit le maximum
            #(l'appareil ne transmettra pas 500 000 points systématiquement)
            #(il renverra uniquement la totalité de ses points)
            self.my_TDS754D.write('DATa:STARt 1')
            self.my_TDS754D.write('DATa:STOP 500000')
            #Demande la configuration du channel et en profite pour detecter les channels présents
            try:
                wvf_CH1 = self.my_TDS754D.query('WFMPre:CH1?')
                self.CH1 = True
            except:
                self.CH1 = False
            try:
                wvf_CH2 = self.my_TDS754D.query('WFMPre:CH2?')
                self.CH2 = True
            except:
                self.CH2 = False
            try:
                wvf_CH3 = self.my_TDS754D.query('WFMPre:CH3?')
                self.CH3 = True
            except:
                self.CH3 = False
            try:
                wvf_CH4 = self.my_TDS754D.query('WFMPre:CH4?')
                self.CH4 = True
            except:
                self.CH4 = False
            #Récupère les points des courbes affichées en coordonnées sur l'écran (127, -128)
            wvf_data = self.my_TDS754D.query('CURVe?')
            self.data = wvf_data.split(',')
            if self.CH1:
                #Formate la configuration du channel
                self.conf_CH1 = self.Conf_processing(wvf_CH1)
                print(self.conf_CH1)
                #Récupère les points du channel
                self.Data_processing(1)
            if self.CH2:
                self.conf_CH2 = self.Conf_processing(wvf_CH2)
                print(self.conf_CH2) 
                self.Data_processing(2)
            if self.CH3:
                self.conf_CH3 = self.Conf_processing(wvf_CH3)
                print(self.conf_CH3)  
                self.Data_processing(3)
            if self.CH4:
                self.conf_CH4 = self.Conf_processing(wvf_CH4)
                print(self.conf_CH4) 
                self.Data_processing(4)
            #Récupération de la date et de la description
            now = datetime.datetime.now()
            mydate = now.strftime('%Y-%m-%d\t%H:%M:%S')
            self.Date_qledit.setText(mydate)
            self.description = self.Description_qledit.text()
            self.my_date = self.Date_qledit.text()
            #Caste les données en float pour affichage et traitement
            self.Data_casting()
            #Convertie les données en V et les affiche
            if self.CH1:
                self.data_CH1.clear()
                self.Data_converting(self.conf_CH1,self.screen_data_CH1,1)
                self.Data_show(self.data_CH1,1)
            if self.CH2:
                self.data_CH2.clear()
                self.Data_converting(self.conf_CH2,self.screen_data_CH2,2)
                self.Data_show(self.data_CH2,2)
            if self.CH3:
                self.data_CH3.clear()
                self.Data_converting(self.conf_CH3,self.screen_data_CH3,3)
                self.Data_show(self.data_CH3,3)
            if self.CH4:
                self.data_CH4.clear()
                self.Data_converting(self.conf_CH4,self.screen_data_CH4,4)
                self.Data_show(self.data_CH4,4)
            
            #Récupération des measurements
            self.MEAS1 = False
            self.MEAS2 = False
            self.MEAS3 = False
            self.MEAS4 = False
            self.Meas()
            
            self.Cursor()
            
            self.new_data = True
            self.data_saved = False
            
            
    def Plot_data(self):
        if self.new_data:
            self.Plot_screen()
                
            
    def Conf_processing(self,wvf_CH):
        ''' Cette fonction récupère de la réponse de l'appareil :
            - le channel
            - l'échelle
            - l'échelle de temps
            - le nombre de points du channel
            - l'offset par rapport au 0 de l'écran'''
        full_conf = wvf_CH.split(', ')
        chan = full_conf[0].lstrip('"')
        scale = full_conf[2]
        time_scale = full_conf[3]
        nb_points = full_conf[4]
        offset_str = full_conf[5]
        offset_list = offset_str.split(';')
        offset = offset_list[9]
        conf = list()
        conf.clear()
        conf.insert(0, chan)
        conf.insert(1, scale)
        conf.insert(2, time_scale)
        conf.insert(3, nb_points)
        conf.insert(4, offset)
        return conf
    
    
    def Data_processing(self,CH):
        '''Comme la list de données est sous format :
            self.data = [CH1(0),CH1(2),...CH1(nb_points),CH2(0),...CH2(nb_points),...]
            Cette fonction récupère les points de chaque channels activés en les effacant
            de self.data au passage'''
        if CH == 1:
            self.screen_data_CH1.clear()
            nb_points = self.conf_CH1[3].rstrip(' points')
            nb_points = int(nb_points)
            for index in range(nb_points):
                self.screen_data_CH1.append(self.data[0])
                self.data.pop(0)
        if CH == 2:
            self.screen_data_CH2.clear()
            nb_points = self.conf_CH2[3].rstrip(' points')
            nb_points = int(nb_points)
            for index in range(nb_points):
                self.screen_data_CH2.append(self.data[0])
                self.data.pop(0)
        if CH == 3:
            self.screen_data_CH3.clear()
            nb_points = self.conf_CH3[3].rstrip(' points')
            nb_points = int(nb_points)
            for index in range(nb_points):
                self.screen_data_CH3.append(self.data[0])
                self.data.pop(0)
        if CH == 4:
            self.screen_data_CH4.clear()
            nb_points = self.conf_CH4[3].rstrip(' points')
            nb_points = int(nb_points)
            for index in range(nb_points):
                self.screen_data_CH4.append(self.data[0])
                self.data.pop(0)
        #Sauvegarde du nombre de points       
        self.points = nb_points
                
                
    def Data_casting(self):
        '''Cette fonction caste les données récupérées sous format 'str' en
            format 'float'''
        if self.CH1:
            #Casting des données de str à float
            index = 0
            for i in self.screen_data_CH1:
                self.screen_data_CH1[index] = float(i)
                index += 1
        if self.CH2:
            index = 0
            for i in self.screen_data_CH2:
                self.screen_data_CH2[index] = float(i)
                index += 1
        if self.CH3:
            index = 0
            for i in self.screen_data_CH3:
                self.screen_data_CH3[index] = float(i)
                index += 1
        if self.CH4:
            index = 0
            for i in self.screen_data_CH4:
                self.screen_data_CH4[index] = float(i)
                index += 1
                
                
    def Plot_screen(self):
        '''Cette fonction affiche les courbes à l'aide des données récupérées
            en coordonnées sur l'écran'''
        self.INIT = False
        Time_scale_show = False
        fig, self.ax = plt.subplots(1,1,figsize=(13, 6))
        self.scales = list()
        scale_label = str()
        self.description = self.Description_qledit.text()
        date = self.my_date.split('\t')

        if self.CH1:            
            #Formatage des données avec numpy
            y_CH1 = np.fromiter(self.screen_data_CH1,np.float)
            x_CH1 = np.fromiter(range(len(self.screen_data_CH1)),np.float)
            #Plot de la courbe
            self.line1, = self.ax.plot(x_CH1, y_CH1,'-', label='CH1')
            #Récupération de l'échelle
            self.scales.append(self.scale_show_CH1)
            #Initialisation du curseur (réalisé seulement une fois si la fonction est call une
            #seconde fois elle initialise uniquement le line du channel)
            self.init(self.line1,1)
            #Appel la fonction 'on_mouse_move' lorsque la souris bouge sur le graph
            self.cursor_CH1 = fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            #Affichage de l'échelle de temps (réalisé une seul fois encore)
            if not Time_scale_show:
                self.ax.text(0.01, 0.95, self.time_scale_CH1, transform=self.ax.transAxes)
                Time_scale_show = True
            #Récupération des données nb_points et offset pour le formatage du graph
            nb_points = self.nb_points_CH1
            offset_CH1 = self.offset_CH1 * 200 / (8 * self.scale_CH1 * self.scale_factor_CH1)
            y_pos_CH1 = (offset_CH1 + 100) / 200
            #Affichage de l'offset sous la forme d'un '1→' sur la gauche des courbes
            if y_pos_CH1 > 0 and y_pos_CH1 < 1:
                self.ax.text(0.11, y_pos_CH1, '1→', transform=self.ax.transAxes)
        if self.CH2:           
            y_CH2 = np.fromiter(self.screen_data_CH2,np.float)
            x_CH2 = np.fromiter(range(len(self.screen_data_CH2)),np.float)
            self.line2, = self.ax.plot(x_CH2, y_CH2,'-', label='CH2')
            self.scales.append(self.scale_show_CH2)
            self.init(self.line2,2)
            self.cursor_CH2 = fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            if not Time_scale_show:
                self.ax.text(0.01, 0.95, self.time_scale_CH2, transform=self.ax.transAxes)
                Time_scale_show = True
            nb_points = self.nb_points_CH2
            offset_CH2 = self.offset_CH2 * 200 / (8 * self.scale_CH2 * self.scale_factor_CH2)
            y_pos_CH2 = (offset_CH2 + 100) / 200
            if y_pos_CH2 > 0 and y_pos_CH2 < 1:
                self.ax.text(0.11, y_pos_CH2, '2→', transform=self.ax.transAxes)
        if self.CH3:           
            y_CH3 = np.fromiter(self.screen_data_CH3,np.float)
            x_CH3 = np.fromiter(range(len(self.screen_data_CH3)),np.float)
            self.line3, = self.ax.plot(x_CH3, y_CH3,'-', label='CH3')
            self.scales.append(self.scale_show_CH3)
            self.init(self.line3,3)
            self.cursor_CH3 = fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            if not Time_scale_show:
                self.ax.text(0.01, 0.95, self.time_scale_CH3, transform=self.ax.transAxes)
                Time_scale_show = True
            nb_points = self.nb_points_CH3
            offset_CH3 = self.offset_CH3 * 200 / (8 * self.scale_CH3 * self.scale_factor_CH3)
            y_pos_CH3 = (offset_CH3 + 100) / 200
            if y_pos_CH3 > 0 and y_pos_CH3 < 1:
                self.ax.text(0.11, y_pos_CH3, '3→', transform=self.ax.transAxes)
        if self.CH4:
            y_CH4 = np.fromiter(self.screen_data_CH4,np.float)
            x_CH4 = np.fromiter(range(len(self.screen_data_CH4)),np.float)
            self.line4, = self.ax.plot(x_CH4, y_CH4,'-', label='CH4')
            self.scales.append(self.scale_show_CH4)
            self.init(self.line4,4)
            self.cursor_CH4 = fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            if not Time_scale_show:
                self.ax.text(0.01, 0.95, self.time_scale_CH4, transform=self.ax.transAxes)
                Time_scale_show = True
            nb_points = self.nb_points_CH4
            offset_CH4 = self.offset_CH4 * 200 / (8 * self.scale_CH4 * self.scale_factor_CH4)
            y_pos_CH4 = (offset_CH4 + 100) / 200
            if y_pos_CH4 > 0 and y_pos_CH4 < 1:
                self.ax.text(0.11, y_pos_CH4, '4→', transform=self.ax.transAxes)
        
        #Effacement des labels des axes
        plt.setp(self.ax.get_xticklabels(), visible=False)
        plt.setp(self.ax.get_yticklabels(), visible=False) 
        #Affichage de la grille
        self.ax.grid(True, linestyle=':')
        #Crée des ticks entre ceux de base de sorte à respecter l'échelle de temps
        self.ax.xaxis.set_minor_locator(MultipleLocator(0.10 * nb_points))
        #Affiche la grille des ticks crée précédemment
        self.ax.grid(True, which='minor', axis='x', linestyle=':')
        #Affiche la légende
        self.ax.legend(loc='lower right', fontsize='small')
        #Affiche la description et la date en titre
        self.ax.set_title(self.description, loc='left')
        self.ax.set_title(date[0] + ' / ' + date[1], loc='right')
        #Ajuste la hauteur de la fenêtre pour coller exactement à l'affichage de l'oscillo
        self.ax.set_ylim(auto=False, ymin=-100, ymax=100)
        #Ajuste la longeur de la fenêtre pour tout afficher avec précision
        self.ax.set_xlim(auto=False, xmin=-0.20 * nb_points, xmax=0.20 * nb_points + nb_points)
        #Fais disparaître les ticks
        self.ax.tick_params(which='both', width=0)
        #Affiche les échelles de chaque channels en xlabel
        for scale in self.scales:
            scale_label += scale + '   '
        self.ax.set_xlabel(scale_label)
        #Affichage des measurments
        if self.MEAS1:
            self.ax.text(0.86, 0.70, self.CH_meas1 + ' ' + self.type_meas1, transform=self.ax.transAxes)
            self.ax.text(0.86, 0.65, self.val_meas1 + self.unit_meas1, transform=self.ax.transAxes)
        if self.MEAS2:
            self.ax.text(0.86, 0.57, self.CH_meas2 + ' ' + self.type_meas2, transform=self.ax.transAxes)
            self.ax.text(0.86, 0.52, self.val_meas2 + self.unit_meas2, transform=self.ax.transAxes)
        if self.MEAS3:
            self.ax.text(0.86, 0.44, self.CH_meas3 + ' ' + self.type_meas3, transform=self.ax.transAxes)
            self.ax.text(0.86, 0.39, self.val_meas3 + self.unit_meas3, transform=self.ax.transAxes)
        if self.MEAS4:
            self.ax.text(0.86, 0.31, self.CH_meas4 + ' ' + self.type_meas4, transform=self.ax.transAxes)
            self.ax.text(0.86, 0.26, self.val_meas4 + self.unit_meas4, transform=self.ax.transAxes)
        #Affichage des lignes de l'écran    
        self.screen_line1 = self.ax.axvline(color='k', lw=0.8, ls='-')
        self.screen_line1.set_xdata(nb_points)
        self.screen_line2 = self.ax.axvline(color='k', lw=0.8, ls='-')
        self.screen_line2.set_xdata(0)
        self.screen_line3 = self.ax.axvline(color='k', lw=0.5, ls='--', alpha=0.5)
        self.screen_line3.set_xdata(nb_points/2)
        self.screen_line4 = self.ax.axhline(color='k', lw=0.5, ls='--', alpha=0.5)
        self.screen_line4.set_ydata(0)
        #Affichage des curseurs
        if self.CURS == 'HBA':
            self.screen_hcursor1 = self.ax.axhline(color='k', lw=0.8, ls=':')
            self.screen_hcursor1.set_ydata(self.hbars_cursor1_pos)
            self.screen_hcursor2 = self.ax.axhline(color='k', lw=0.8, ls=':')
            self.screen_hcursor2.set_ydata(self.hbars_cursor2_pos)
            self.ax.set_ylabel(self.hbars_delta)
        if self.CURS == 'VBA':
            self.screen_vcursor1 = self.ax.axvline(color='k', lw=0.8, ls=':')
            self.screen_vcursor1.set_xdata(self.vbars_cursor1_pos * nb_points)
            self.screen_vcursor2 = self.ax.axvline(color='k', lw=0.8, ls=':')
            self.screen_vcursor2.set_xdata(self.vbars_cursor2_pos * nb_points)
            self.ax.set_ylabel(self.vbars_delta)
        
        plt.show()
        
        #Sauvegarde de la courbe en format png
        if self.data_saved:
            self.fileName = self.SaveFileName_qledit.text()
            filename = self.fileName.split('.')[0] + '.png'
            fig.savefig(filename, dpi = 600)
               
      
    def Data_converting(self,conf,screen_data,CH):
        '''Cette fonction convertie les données de coordonnées sur l'écran en
            V à l'aide de l'échelle du channel et de son offset'''
        #Détermine l'unité de l'échelle
        scale_show = conf[1]
        scale = conf[1].rstrip('olts/div')
        if 'm' in scale:
            scale_factor = 10 ** -3 #Si l'échelle est en mV
        else:
            scale_factor = 1        #Si l'échelle est en V
        #Récupère la valeur de l'échelle
        scale = float(scale.rstrip('mV '))
        #Détermine l'offset et le convertie en V
        offset = float(conf[4])
        offset = offset / 200 * 8 * scale * scale_factor
        #Récupère le time scale
        time_scale = conf[2]
        self.gb_time_scale = time_scale
        #Récupère le nombre de points
        nb_points = int(conf[3].rstrip(' points'))
        #Conversion des données
        for val in screen_data:
            if CH == 1:
                self.data_CH1.append(val / 200 * 8 * scale * scale_factor - offset)
                self.scale_CH1 = scale
                self.scale_factor_CH1 = scale_factor
                self.offset_CH1 = offset
                self.scale_show_CH1 = 'CH1-' + scale_show
                self.time_scale_CH1 = time_scale
                self.nb_points_CH1 = nb_points
            if CH == 2:
                self.data_CH2.append(val / 200 * 8 * scale * scale_factor - offset)
                self.scale_CH2 = scale
                self.scale_factor_CH2 = scale_factor
                self.offset_CH2 = offset
                self.scale_show_CH2 = 'CH2-' + scale_show
                self.time_scale_CH2 = time_scale
                self.nb_points_CH2 = nb_points
            if CH == 3:
                self.data_CH3.append(val / 200 * 8 * scale * scale_factor - offset)
                self.scale_CH3 = scale
                self.scale_factor_CH3 = scale_factor
                self.offset_CH3 = offset
                self.scale_show_CH3 = 'CH3-' + scale_show
                self.time_scale_CH3 = time_scale
                self.nb_points_CH3 = nb_points
            if CH == 4:
                self.data_CH4.append(val / 200 * 8 * scale * scale_factor - offset)
                self.scale_CH4 = scale
                self.scale_factor_CH4 = scale_factor
                self.offset_CH4 = offset
                self.scale_show_CH4 = 'CH4-' + scale_show
                self.time_scale_CH4 = time_scale
                self.nb_points_CH4 = nb_points
                
                
    def Data_show(self,data_CH,CH):
        '''Cette fonction affiche les données sur l'uir'''
        data_CH_show = list()
        #Casting des données de float à str
        index = 0
        for i in data_CH:
            data_CH_show.insert(index, '%.4f' % i)
            index += 1
        #Concaténation des données str
        data_CH_show_string = str()
        for i in data_CH_show:
            data_CH_show_string += i + ',\n'
        #Affichage
        if CH == 1:
            self.Channel1_Data_qtedit.setText(data_CH_show_string)
        if CH == 2:
            self.Channel2_Data_qtedit.setText(data_CH_show_string)
        if CH == 3:
            self.Channel3_Data_qtedit.setText(data_CH_show_string)
        if CH == 4:
            self.Channel4_Data_qtedit.setText(data_CH_show_string)
            
            
    def saveAsFileDialog(self):
        fdialog = MyFileDialog()
        fdialog.send_filename.connect(self.saveFile)
        self.saveFileName = self.SaveFileName_qledit.text()
        fdialog.showDialog(self.saveFileName,'Save')
        
    
    def loadFileDialog(self):
        configdialog = MyFileDialog()
        configdialog.send_filename.connect(self.readdata)
        configdialog.showDialog(self.fileName,'Open')
  
      
    def saveFile(self, val): 
        ''' Cette fonction écrit un fichier de mesure formaté de la sorte :
            Date
            Description
            Channel x -> Channel y -> ...
            Echelle x -> Echelle y -> ...
            Unité de l'échelle x -> Unité de l'échelle y -> ... (1 -> V et 0.001 -> mV)
            Echelle de temps x(str) -> Echelle de temps y(str) -> ...
            Nombre de points x -> Nombre de points y -> ...
            Offset x(V) -> Offset y(V) -> ...
            
            Donnée 1 x(V) -> Donnée 1 y(V) -> ...
            Donnée 2 x(V) -> Donnée 2 y(V) -> ...
            ...'''
        self.my_date = self.Date_qledit.text()
        self.description = self.Description_qledit.text()
        mypath = os.path.dirname(val)
        if os.path.isdir(mypath):
            with open(val,'w') as writer:
                # Ecriture de la date et de la description
                writer.write(self.my_date + '\n' + self.description + '\n')
                # Ecriture des channels
                if self.CH1:
                    writer.write('Channel 1\t')
                if self.CH2:
                    writer.write('Channel 2\t')
                if self.CH3:
                    writer.write('Channel 3\t')
                if self.CH4:
                    writer.write('Channel 4\t')
                writer.write('\n')
                # Ecriture de l'échelle
                if self.CH1:
                    writer.write(str(self.scale_CH1) + '\t')
                if self.CH2:
                    writer.write(str(self.scale_CH2) + '\t')
                if self.CH3:
                    writer.write(str(self.scale_CH3) + '\t')
                if self.CH4:
                    writer.write(str(self.scale_CH4) + '\t')
                writer.write('\n')
                # Ecriture de l'unité de l'échelle (1 -> V et 0.001 -> mV)
                if self.CH1:
                    writer.write(str(self.scale_factor_CH1) + '\t')
                if self.CH2:
                    writer.write(str(self.scale_factor_CH2) + '\t')
                if self.CH3:
                    writer.write(str(self.scale_factor_CH3) + '\t')
                if self.CH4:
                    writer.write(str(self.scale_factor_CH4) + '\t')
                writer.write('\n')
                # Ecriture du time scale (format str)
                if self.CH1:
                    writer.write(self.time_scale_CH1 + '\t')
                if self.CH2:
                    writer.write(self.time_scale_CH2 + '\t')
                if self.CH3:
                    writer.write(self.time_scale_CH3 + '\t')
                if self.CH4:
                    writer.write(self.time_scale_CH4 + '\t')
                writer.write('\n')
                # Ecriture du nombre de points
                if self.CH1:
                    writer.write(str(self.nb_points_CH1) + '\t')
                if self.CH2:
                    writer.write(str(self.nb_points_CH2) + '\t')
                if self.CH3:
                    writer.write(str(self.nb_points_CH3) + '\t')
                if self.CH4:
                    writer.write(str(self.nb_points_CH4) + '\t')
                writer.write('\n')
                # Ecriture de l'offset (V)
                if self.CH1:
                    writer.write(str(self.offset_CH1) + '\t')
                if self.CH2:
                    writer.write(str(self.offset_CH2) + '\t')
                if self.CH3:
                    writer.write(str(self.offset_CH3) + '\t')
                if self.CH4:
                    writer.write(str(self.offset_CH4) + '\t')
                # ligne vide
                writer.write('\n\n')
                # Ecriture des données (V)
                for index in range(self.points):
                    if self.CH1:
                        writer.write(str(self.data_CH1[index]) + ',\t')
                    if self.CH2:
                        writer.write(str(self.data_CH2[index]) + ',\t')
                    if self.CH3:
                        writer.write(str(self.data_CH3[index]) + ',\t')
                    if self.CH4:
                        writer.write(str(self.data_CH4[index]) + ',\t')
                    writer.write('\n')
            self.SaveFileName_qledit.setText(val)  
            self.data_saved = True
            
            
    def readdata(self,filename):
        ''' Cette fonction lis un fichier de mesure formaté de la sorte :
            Date
            Description
            Channel x -> Channel y -> ...
            Echelle x -> Echelle y -> ...
            Unité de l'échelle x -> Unité de l'échelle y -> ... (1 -> V et 0.001 -> mV)
            Echelle de temps x(str) -> Echelle de temps y(str) -> ...
            Nombre de points x -> Nombre de points y -> ...
            Offset x(V) -> Offset y(V) -> ...
            
            Donnée 1 x(V) -> Donnée 1 y(V) -> ...
            Donnée 2 x(V) -> Donnée 2 y(V) -> ...
            ...'''
        if os.path.isfile(filename):
            self.SaveFileName_qledit.setText(filename)
            self.CH1 = False
            self.CH2 = False
            self.CH3 = False
            self.CH4 = False
            self.data_CH1.clear()
            self.data_CH2.clear()
            self.data_CH3.clear()
            self.data_CH4.clear()
            self.Channel1_Data_qtedit.setText('')
            self.Channel2_Data_qtedit.setText('')
            self.Channel3_Data_qtedit.setText('')
            self.Channel4_Data_qtedit.setText('')
            with open(filename) as reader:
                date = reader.readline().rstrip('\r\n')
                self.Date_qledit.setText(date)
                self.my_date = self.Date_qledit.text()
                line = reader.readline().rstrip('\r\n')
                self.Description_qledit.setText(line)
                self.description = self.Description_qledit.text()
                # Détection des channels
                chan = reader.readline().rstrip('\r\n')
                if 'Channel 1' in chan:
                    self.CH1 = True
                if 'Channel 2' in chan:
                    self.CH2 = True
                if 'Channel 3' in chan:
                    self.CH3 = True
                if 'Channel 4' in chan:
                    self.CH4 = True
                # Lecture de la valeur de l'échelle
                scale = reader.readline().rstrip('\r\n').split('\t')
                if self.CH1:
                    self.scale_CH1 = float(scale[0])
                    scale.pop(0)
                if self.CH2:
                    self.scale_CH2 = float(scale[0])
                    scale.pop(0)
                if self.CH3:
                    self.scale_CH3 = float(scale[0])
                    scale.pop(0)
                if self.CH4:
                    self.scale_CH4 = float(scale[0])
                    scale.pop(0)
                # Lecture de l'unité de l'échelle (scale_factor = 1 -> V; " = 10^-3 -> mV)
                scale_factor = reader.readline().rstrip('\r\n').split('\t')
                if self.CH1:
                    self.scale_factor_CH1 = float(scale_factor[0])
                    scale_factor.pop(0)
                if self.CH2:
                    self.scale_factor_CH2 = float(scale_factor[0])
                    scale_factor.pop(0)
                if self.CH3:
                    self.scale_factor_CH3 = float(scale_factor[0])
                    scale_factor.pop(0)
                if self.CH4:
                    self.scale_factor_CH4 = float(scale_factor[0])
                    scale_factor.pop(0)
                # Lecture du time scale (format str)
                time_scale = reader.readline().rstrip('\r\n').split('\t')
                if self.CH1:
                    self.time_scale_CH1 = time_scale[0]
                    time_scale.pop(0)
                if self.CH2:
                    self.time_scale_CH2 = time_scale[0]
                    time_scale.pop(0)
                if self.CH3:
                    self.time_scale_CH3 = time_scale[0]
                    time_scale.pop(0)
                if self.CH4:
                    self.time_scale_CH4 = time_scale[0]
                    time_scale.pop(0)
                # Lecture du nombre de points
                nb_points = reader.readline().rstrip('\r\n').split('\t')
                if self.CH1:
                    self.nb_points_CH1 = int(nb_points[0])
                    nb_points.pop(0)
                if self.CH2:
                    self.nb_points_CH2 = int(nb_points[0])
                    nb_points.pop(0)
                if self.CH3:
                    self.nb_points_CH3 = int(nb_points[0])
                    nb_points.pop(0)
                if self.CH4:
                    self.nb_points_CH4 = int(nb_points[0])
                    nb_points.pop(0)
                # Lecture de l'offset
                offset = reader.readline().rstrip('\r\n').split('\t')
                if self.CH1:
                    self.offset_CH1 = float(offset[0])
                    offset.pop(0)
                if self.CH2:
                    self.offset_CH2 = float(offset[0])
                    offset.pop(0)
                if self.CH3:
                    self.offset_CH3 = float(offset[0])
                    offset.pop(0)
                if self.CH4:
                    self.offset_CH4 = float(offset[0])
                    offset.pop(0)
                # sauter la ligne vide
                values = reader.readline().rstrip('\r\n').split('\t')
                # Lecture des valeurs de gauche à droite
                values = reader.readline().rstrip('\r\n').split('\t')
                while values[0].endswith(','):
                    if self.CH1:
                        val = values[0].rstrip(',\t')
                        self.data_CH1.append(float(val))
                        values.pop(0) 
                    if self.CH2:
                        val = values[0].rstrip(',\t')
                        self.data_CH2.append(float(val))
                        values.pop(0)
                    if self.CH3:
                        val = values[0].rstrip(',\t')
                        self.data_CH3.append(float(val))
                        values.pop(0)
                    if self.CH4:
                        val = values[0].rstrip(',\t')
                        self.data_CH4.append(float(val))
                        values.pop(0)
                    values = reader.readline().rstrip('\r\n').split('\t')
            #Affichage des données et conversion de Volts à coordonnées sur l'écran
            if self.CH1:
                self.Data_show(self.data_CH1,1)
                self.screen_data_CH1.clear()
                self.inv_Data_converting(self.scale_CH1,self.scale_factor_CH1,self.offset_CH1,self.data_CH1,1)
            if self.CH2:
                self.Data_show(self.data_CH2,2)
                self.screen_data_CH2.clear()
                self.inv_Data_converting(self.scale_CH2,self.scale_factor_CH2,self.offset_CH2,self.data_CH2,2)
            if self.CH3:
                self.Data_show(self.data_CH3,3)
                self.screen_data_CH3.clear()
                self.inv_Data_converting(self.scale_CH3,self.scale_factor_CH3,self.offset_CH3,self.data_CH3,3)
            if self.CH4:
                self.Data_show(self.data_CH4,4)
                self.screen_data_CH4.clear()
                self.inv_Data_converting(self.scale_CH4,self.scale_factor_CH4,self.offset_CH4,self.data_CH4,4)
            self.new_data = True 
                
    
    def inv_Data_converting(self,scale,scale_factor,offset,data_CH,CH):
        ''' Cette fonction convertie les données de Volts à coordonnées sur l'écran
        à l'aide de l'échelle et de l'offset lu dans le fichier de sauvegarde'''
        offset = offset * 200 / (8 * scale * scale_factor)
        for val in data_CH:
            if CH == 1:
                self.screen_data_CH1.append(val * 200 / (8 * scale * scale_factor) + offset)
                # Formattage de l'affichage de l'échelle (scale_factor = 1 -> V; " = 10^-3 -> mV)
                if scale_factor == 1:
                    self.scale_show_CH1 = 'CH1-' + str(scale) + ' Volts/div'
                else:
                    self.scale_show_CH1 = 'CH1-' + str(scale) + 'mVolts/div'
            if CH == 2:
                self.screen_data_CH2.append(val * 200 / (8 * scale * scale_factor) + offset)
                if scale_factor == 1:
                    self.scale_show_CH2 = 'CH2-' + str(scale) + ' Volts/div'
                else:
                    self.scale_show_CH2 = 'CH2-' + str(scale) + 'mVolts/div'
            if CH == 3:
                self.screen_data_CH3.append(val * 200 / (8 * scale * scale_factor) + offset)
                if scale_factor == 1:
                    self.scale_show_CH3 = 'CH3-' + str(scale) + ' Volts/div'
                else:
                    self.scale_show_CH3 = 'CH3-' + str(scale) + 'mVolts/div'
            if CH == 4:
                self.screen_data_CH4.append(val * 200 / (8 * scale * scale_factor) + offset)
                if scale_factor == 1:
                    self.scale_show_CH4 = 'CH4-' + str(scale) + ' Volts/div'
                else:
                    self.scale_show_CH4 = 'CH4-' + str(scale) + 'mVolts/div'
                    
                                                      
    def Meas(self):
        state_meas1 = self.my_TDS754D.query('MEASUrement:MEAS1:STATE?')
        if state_meas1 == '1':
            self.MEAS1 = True
            meas1 = self.my_TDS754D.query('MEASUrement:MEAS1?')
            self.val_meas1 = self.my_TDS754D.query('MEASUrement:MEAS1:VALue?')
            self.type_meas1 = (meas1.split(';')[0])
            self.unit_meas1 = (meas1.split(';')[1]).strip('"')
            self.CH_meas1 = (meas1.split(';')[2])
        state_meas2 = self.my_TDS754D.query('MEASUrement:MEAS2:STATE?')
        if state_meas2 == '1':
            self.MEAS2 = True
            meas2 = self.my_TDS754D.query('MEASUrement:MEAS2?')
            self.val_meas2 = self.my_TDS754D.query('MEASUrement:MEAS2:VALue?')
            self.type_meas2 = (meas2.split(';')[0])
            self.unit_meas2 = (meas2.split(';')[1]).strip('"')
            self.CH_meas2 = (meas2.split(';')[2])
        state_meas3 = self.my_TDS754D.query('MEASUrement:MEAS3:STATE?')
        if state_meas3 == '1':
            self.MEAS3 = True
            meas3 = self.my_TDS754D.query('MEASUrement:MEAS3?')
            self.val_meas3 = self.my_TDS754D.query('MEASUrement:MEAS3:VALue?')
            self.type_meas3 = (meas3.split(';')[0])
            self.unit_meas3 = (meas3.split(';')[1]).strip('"')
            self.CH_meas3 = (meas3.split(';')[2])
        state_meas4 = self.my_TDS754D.query('MEASUrement:MEAS4:STATE?')
        if state_meas4 == '1':
            self.MEAS4 = True
            meas4 = self.my_TDS754D.query('MEASUrement:MEAS4?')
            self.val_meas4 = self.my_TDS754D.query('MEASUrement:MEAS4:VALue?')
            self.type_meas4 = (meas4.split(';')[0])
            self.unit_meas4 = (meas4.split(';')[1]).strip('"')
            self.CH_meas4 = (meas4.split(';')[2])
            
            
    def Cursor(self):
        self.CURS = 'OFF'
        cursor_query = self.my_TDS754D.query('CURSor:FUNCtion?')
             
        if 'HBA' in cursor_query:
            self.CURS = 'HBA'
            hbars_cursor1_pos_rtwf = self.my_TDS754D.query('CURSor:HBArs:POSITION1?')
            hbars_cursor2_pos_rtwf = self.my_TDS754D.query('CURSor:HBArs:POSITION2?')
            hbars_delta_val = self.my_TDS754D.query('CURSor:HBArs:DELTa?')
            self.hbars_delta = 'Δ: ' + hbars_delta_val + ' V'
            waveform_query = self.my_TDS754D.query('SELect?')
            if 'CH1' in waveform_query:
                offset = self.offset_CH1 * 200 / (8 * self.scale_CH1 * self.scale_factor_CH1)
                self.hbars_cursor1_pos = (float(hbars_cursor1_pos_rtwf) * 200) / (8 * self.scale_CH1 * self.scale_factor_CH1) + offset
                self.hbars_cursor2_pos = (float(hbars_cursor2_pos_rtwf) * 200) / (8 * self.scale_CH1 * self.scale_factor_CH1) + offset
            if 'CH2' in waveform_query:
                offset = self.offset_CH2 * 200 / (8 * self.scale_CH2 * self.scale_factor_CH2)
                self.hbars_cursor1_pos = (float(hbars_cursor1_pos_rtwf) * 200) / (8 * self.scale_CH2 * self.scale_factor_CH2) + offset
                self.hbars_cursor2_pos = (float(hbars_cursor2_pos_rtwf) * 200) / (8 * self.scale_CH2 * self.scale_factor_CH2) + offset
            if 'CH3' in waveform_query:
                offset = self.offset_CH3 * 200 / (8 * self.scale_CH3 * self.scale_factor_CH3)
                self.hbars_cursor1_pos = (float(hbars_cursor1_pos_rtwf) * 200) / (8 * self.scale_CH3 * self.scale_factor_CH3) + offset
                self.hbars_cursor2_pos = (float(hbars_cursor2_pos_rtwf) * 200) / (8 * self.scale_CH3 * self.scale_factor_CH3) + offset
            if 'CH4' in waveform_query:
                offset = self.offset_CH4 * 200 / (8 * self.scale_CH4 * self.scale_factor_CH4)
                self.hbars_cursor1_pos = (float(hbars_cursor1_pos_rtwf) * 200) / (8 * self.scale_CH4 * self.scale_factor_CH4) + offset
                self.hbars_cursor2_pos = (float(hbars_cursor2_pos_rtwf) * 200) / (8 * self.scale_CH4 * self.scale_factor_CH4) + offset
            
        if 'VBA' in cursor_query:
            self.CURS = 'VBA'
            vbars_cursor1_pos_rtt = self.my_TDS754D.query('CURSor:VBArs:POSITION1?')
            vbars_cursor2_pos_rtt = self.my_TDS754D.query('CURSor:VBArs:POSITION2?')
            vbars_delta_val = self.my_TDS754D.query('CURSor:VBArs:DELTa?')
            vbars_delta_units = self.my_TDS754D.query('CURSor:VBArs:UNIts?')
            self.vbars_delta = 'Δ: ' + vbars_delta_val + ' ' + vbars_delta_units
            time_scale = self.gb_time_scale.rstrip('/div')
            time_scale_factor = 1
            if 'm' in time_scale:
                time_scale_factor = 10**-3
            if 'u' in time_scale:
                time_scale_factor = 10**-6
            if 'n' in time_scale:
                time_scale_factor = 10**-9
            if 'p' in time_scale:
                time_scale_factor = 10**-12
            time_scale = float(time_scale.rstrip('munps'))*time_scale_factor
            self.vbars_cursor1_pos = (float(vbars_cursor1_pos_rtt) + 5*time_scale)/(10*time_scale)
            self.vbars_cursor2_pos = (float(vbars_cursor2_pos_rtt) + 5*time_scale)/(10*time_scale)
            
        if 'PAI' in cursor_query:            
            self.CURS = 'PAI'
            
        
    """
    A cross hair cursor that snaps to the data point of a line, which is
    closest to the *x* position of the cursor.

    For simplicity, this assumes that *x* values of the data are sorted.
    """
    def init(self, line, CH):
        self.x, self.y = line.get_data()
        if CH == 1:
            self.y_CH1 = self.y
            self.y_cursor_CH1 = self.ax.text(0.86, 0.95, '', transform=self.ax.transAxes)
        if CH == 2:
            self.y_CH2 = self.y
            self.y_cursor_CH2 = self.ax.text(0.86, 0.9, '', transform=self.ax.transAxes)
        if CH == 3:
            self.y_CH3 = self.y
            self.y_cursor_CH3 = self.ax.text(0.86, 0.85, '', transform=self.ax.transAxes)
        if CH == 4:
            self.y_CH4 = self.y
            self.y_cursor_CH4 = self.ax.text(0.86, 0.8, '', transform=self.ax.transAxes)
        if not self.INIT:
            self.background = None
            self.vertical_line = self.ax.axvline(color='k', lw=0.8, ls='-.')
            self._last_index = None
            self._creating_background = False
            self.ax.figure.canvas.mpl_connect('draw_event', self.on_draw)
            self.INIT = True

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.vertical_line.get_visible() != visible
        self.vertical_line.set_visible(visible)
        return need_redraw
    
    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            self._last_index = None
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            x = event.xdata
            index = min(np.searchsorted(self.x, x), len(self.x) - 1)
            if index == self._last_index:
                return  # still on the same data point. Nothing to do.
            self._last_index = index
            x = self.x[index]
            # update the line positions
            self.vertical_line.set_xdata(x)
            self.ax.figure.canvas.restore_region(self.background)
            if self.CH1:
                _y_CH1 = self.y_CH1[index]
                _y_CH1 = _y_CH1 / 200 * 8 * self.scale_CH1 * self.scale_factor_CH1 - self.offset_CH1
                self.y_cursor_CH1.set_text('CH1 %.3f V' % _y_CH1)
                self.ax.draw_artist(self.y_cursor_CH1)
            if self.CH2:
                _y_CH2 = self.y_CH2[index]
                _y_CH2 = _y_CH2 / 200 * 8 * self.scale_CH2 * self.scale_factor_CH2 - self.offset_CH2
                self.y_cursor_CH2.set_text('CH2 %.3f V' % _y_CH2)
                self.ax.draw_artist(self.y_cursor_CH2)
            if self.CH3:
                _y_CH3 = self.y_CH3[index]
                _y_CH3 = _y_CH3 / 200 * 8 * self.scale_CH3 * self.scale_factor_CH3 - self.offset_CH3
                self.y_cursor_CH3.set_text('CH3 %.3f V' % _y_CH3)
                self.ax.draw_artist(self.y_cursor_CH3)
            if self.CH4:
                _y_CH4 = self.y_CH4[index]
                _y_CH4 = _y_CH4 / 200 * 8 * self.scale_CH4 * self.scale_factor_CH4 - self.offset_CH4
                self.y_cursor_CH4.set_text('CH4 %.3f V' % _y_CH4)
                self.ax.draw_artist(self.y_cursor_CH4)
            self.ax.draw_artist(self.vertical_line)
            self.ax.figure.canvas.blit(self.ax.bbox)
        
        
class MyFileDialog(QMainWindow):
    send_filename = pyqtSignal("QString")

    def __init__(self):
        super().__init__()

    def showDialog(self,defaultfileName,save_load):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if (save_load == 'Save'):
            fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName_qledit()",defaultfileName,"All Files (*);;Text Files (*.txt)", options=options)
        if (save_load == 'Open'):
            fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName_qledit()",defaultfileName,"All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            self.send_filename.emit(fileName)
        
            
if __name__ == '__main__':    
    app = QApplication(sys.argv)
    prog = Oscilloscope()
    prog.show()
    sys.exit(app.exec_())