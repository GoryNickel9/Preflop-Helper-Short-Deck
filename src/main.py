import os
import sys
from glob import glob
from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from customButton import DrawScenarioButton
from trainingReports import TrainingReports
from handTrainer import HandTrainer
from reports import Report
import numpy as np

class simul(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Preflop Helper 6+")
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        
        # Rimuovi i margini
        self.layout = QGridLayout(self.mainWidget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.titleWidget = QLabel("Preflop Helper 6+")
        self.titleWidget.setFont(self.font(30))
        self.layout.addWidget(self.titleWidget, 0, 0, Qt.AlignCenter)

        self.tabWidget = QTabWidget()
        self.tabWidget.setContentsMargins(0, 0, 0, 0)

        self.tabWidget.insertTab(0, self.handTrainerFunc(), "Hand Trainer")
        self.tabWidget.insertTab(1, self.trainingReports(), "Training Reports")
        self.tabWidget.setFont(self.font(25))
        self.tabWidget.setCurrentIndex(0)
        
        self.innerLayout = QGridLayout()
        self.innerLayout.setContentsMargins(0, 0, 0, 0)
        self.innerLayout.setSpacing(0)
        
        self.layout.addLayout(self.innerLayout, 1, 0)
        self.innerLayout.addWidget(self.tabWidget, 1, 0)
        
        # Imposta a schermo intero all'avvio
        self.showMaximized()

    def generateFirstReport(self):
        if not hasattr(self, 'reports'):
            comboMap, comboMapInverse = self.generateMap()
            self.reports = Report(comboMap, comboMapInverse, "True")

    def generateMap(self):
        # Modified to use only cards from 6 to Ace
        cards = ["A", "K", "Q", "J", "T", "9", "8", "7", "6"]
        inverseMap = {}
        combo = []
        for i in range(len(cards)):
            # Goes from 0 to 8 (9 cards)
            # Then from 1 to 8
            for j in range(i+1):
                if i!=j:
                    combo.append(cards[j]+cards[i]+"o")
                    inverseMap[cards[j]+cards[i]+"o"] = [j, i]
            for j in range(i, 9):  # Changed to 9 for 9 cards
                if i!=j:
                    combo.append(cards[i]+cards[j]+"s") 
                    inverseMap[cards[i]+cards[j]+"s"] = [j, i]
                else:
                    combo.append(cards[i]+cards[j]) 
                    inverseMap[cards[i]+cards[j]] = [j, i]
        return np.array(combo).reshape((9, 9)).transpose(), inverseMap  # Changed to 9x9 matrix

    def font(self, size):
        return QFont("courier 10 pitch", size)

    def handTrainerFunc(self):
        comboMap, comboMapInverse = self.generateMap()
        self.generateFirstReport()
        self.handTrainer = HandTrainer(self, comboMap, self.font, self.reports)
        return self.handTrainer.getWindow()

    def trainingReports(self):
        comboMap, comboMapInverse = self.generateMap()
        self.trainingReports = TrainingReports(self, comboMap, comboMapInverse, self.font, self.reports)
        return self.trainingReports.getWindow()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = simul()
    window.show()
    sys.exit(app.exec())