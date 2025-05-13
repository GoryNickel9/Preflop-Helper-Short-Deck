from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from datetime import datetime
import os

class TrainingReports:
    def __init__(self, mainWindow, comboMap, comboMapInverse, font, report):
        self.generalTab = QWidget()
        self.mainLayout = QHBoxLayout()
        self.main = mainWindow
        self.comboMap = comboMap
        self.comboMapInverse = comboMapInverse
        self.font = font
        self.report = report
        self.keyArr = []

    def buildMain(self):
        self.leftLayout = self.buildLeftLayout()
        self.rightLayout = self.buildRightLayout()
        self.mainLayout.addLayout(self.leftLayout, 4)
        self.mainLayout.addLayout(self.rightLayout, 1)
        self.generalTab.setLayout(self.mainLayout)

    def getWindow(self):
        self.buildMain()
        return self.generalTab

    def buildLeftLayout(self):
        leftLayout = QVBoxLayout()
        leftLayout.setContentsMargins(70, 20, 70, 10)
        self.rangeLabel = QLabel("Training Report", alignment=Qt.AlignCenter)
        self.rangeLabel.setFont(self.font(36))
        leftLayout.addWidget(self.rangeLabel, 1)
        leftLayout.addLayout(self.buildStatisticsTable(), 3)
        return leftLayout

    def buildRightLayout(self):
        rightLayout = QVBoxLayout()
        rightLayout.addLayout(self.buildRefreshButton())
        rightLayout.addStretch()
        return rightLayout

    def buildRefreshButton(self):
        button = QPushButton("Refresh")
        button.clicked.connect(self.refresh)
        button.setFont(self.font(15))
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(button)
        buttonLayout.setContentsMargins(0, 20, 20, 20)
        return buttonLayout

    def refresh(self):
        if hasattr(self, 'leftLayout'):
            if self.leftLayout.count() >= 2:
                layout = self.leftLayout.takeAt(1)
                if layout is not None:
                    self.leftLayout.removeItem(layout)
                    self.clearLayout(layout)
                
            table_layout = self.buildStatisticsTable()
            if table_layout is not None:
                self.leftLayout.addLayout(table_layout, 3)
            
            self.generalTab.update()

    def buildStatisticsTable(self):
        try:
            self.table = QTableWidget(0, 4)
            self.tableLayout = QHBoxLayout()
            self.tableLayout.setSpacing(0)
            self.tableLayout.setContentsMargins(0, 0, 0, 0)
            self.tableLayout.addWidget(self.table)
            
            self.table.setShowGrid(False)
            self.table.verticalHeader().setDefaultSectionSize(40)
            self.table.horizontalHeader().setDefaultSectionSize(100)
            self.table.setStyleSheet("""
                QTableWidget {
                    gridline-color: transparent;
                    border: none;
                    spacing: 0px;
                }
                QTableWidget::item {
                    padding: 0px;
                    border: none;
                }
                QHeaderView::section {
                    padding: 5px;
                    border: none;
                }
            """)
            
            headers = [
                "Spot",
                "Date",
                "Hands Played",
                "Success Rate"
            ]
            
            for i, header in enumerate(headers):
                header_item = QTableWidgetItem(header)
                header_item.setFont(self.font(12))
                self.table.setHorizontalHeaderItem(i, header_item)

            self.keyArr = []
            
            if not self.report.isEmpty():
                report_data = self.report.getReport()
                
                for idx, key in enumerate(report_data["data"].keys()):
                    self.keyArr.append(key)
                    self.table.insertRow(self.table.rowCount())
                    
                    stats = report_data["data"][key]["statistics"]
                    success_rate = (stats["numberOfHandsCorrect"] / stats["numberOfHands"] * 100) if stats["numberOfHands"] > 0 else 0
                    
                    # Use the filename as spot name without any modification
                    spot_name = key if key == "Total" else os.path.basename(key)
                    
                    items = [
                        spot_name,
                        datetime.now().strftime("%Y-%m-%d") if key != "Total" else "",
                        stats["numberOfHands"],
                        f"{success_rate:.1f}%"
                    ]
                    
                    for col, item in enumerate(items):
                        table_item = self.makeTableItem(item)
                        table_item.setFont(self.font(12))
                        self.table.setItem(idx, col, table_item)

            self.table.horizontalHeader().setStretchLastSection(True)
            for i in range(self.table.columnCount()):
                self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            
            self.table.setMinimumHeight(400)
            
            return self.tableLayout
        except Exception as e:
            print(f"Error building statistics table: {str(e)}")
            return None

    def makeTableItem(self, text):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clearLayout(child.layout())
                    child.layout().deleteLater()