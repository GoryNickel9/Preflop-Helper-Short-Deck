from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
from glob import glob
from parser import *
from customButton import DrawScenarioButton, DrawRangeButton
from functools import partial
import numpy as np

class HandTrainer():
    def __init__(self, main, comboMap, font, report=None):
        self.generalTab = QWidget()
        self.mainLayout = QHBoxLayout()
        self.main = main
        self.font = font
        self.comboMap = comboMap
        self.sceneIsClear = True
        self.sceneDict = {}
        self.curSelection = None
        self.report = report
        self.ranges_dir = "ranges"
        
        # Use relative path
        self.ranges_dir = "ranges"
        print(f"Ranges directory: {self.ranges_dir}")

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
        leftLayout = QHBoxLayout()
        leftLayout.setContentsMargins(70, 20, 70, 70)
        leftLayout.setSpacing(0)
       
        self.leftTrainerLayout = QVBoxLayout()
        self.leftTrainerLayout.stretch(0)
        leftLayout.addLayout(self.leftTrainerLayout)
        return leftLayout

    def buildRightLayout(self):
        rightLayout = QVBoxLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightLayout.setSpacing(0)
        
        self.trainingLabel = self.trainingActive()
        rightLayout.addWidget(self.trainingLabel)
        
        self.clearButton = QPushButton("Clear")
        self.clearButton.clicked.connect(self.clearAndSave)
        rightLayout.addWidget(self.clearButton)

        self.treeView = self.createFileTree()
        rightLayout.addWidget(self.treeView)
        
        return rightLayout
    
    def createFileTree(self):
        treeView = QTreeView()
        treeView.setFont(self.font(10))
        
        self.model = QFileSystemModel()
        ranges_path = os.path.join(os.getcwd(), self.ranges_dir)
        self.model.setRootPath(ranges_path)
        
        self.model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Files | QtCore.QDir.AllDirs)
        self.model.setNameFilters(["*.txt"])
        self.model.setNameFilterDisables(False)
        
        treeView.setModel(self.model)
        treeView.setRootIndex(self.model.index(ranges_path))
        treeView.setRootIsDecorated(True)
        
        treeView.setColumnHidden(1, True)
        treeView.setColumnHidden(2, True)
        treeView.setColumnHidden(3, True)
        
        header = treeView.header()
        header.setDefaultAlignment(Qt.AlignLeft)
        header.setStretchLastSection(False)
        self.model.setHeaderData(0, Qt.Horizontal, self.ranges_dir)
        
        treeView.setSelectionMode(QAbstractItemView.SingleSelection)
        
        treeView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        treeView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        treeView.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        treeView.setTextElideMode(Qt.ElideNone)
        treeView.setWordWrap(True)

        treeView.setMinimumWidth(300)

        treeView.clicked.connect(lambda index: self.addScene(os.path.relpath(self.model.filePath(index), os.getcwd())) if os.path.isfile(self.model.filePath(index)) else None)
        
        treeView.expandAll()
        return treeView

    def trainingActive(self):
        self.trainingLabel = QLabel()
        self.trainingLabel.setFont(self.font(15))
        self.updateReportingStatus() 
        return self.trainingLabel

    def updateReportingStatus(self):
        if self.report.isActive():
            self.trainingLabel.setText("Reporting Active")
            self.trainingLabel.setStyleSheet('color: green')
        else:
            self.trainingLabel.setText("Reporting Inactive")
            self.trainingLabel.setStyleSheet('color: red')

    def createAddDeleteClearButtons(self):
        addButton = QPushButton("Add")
        addButton.clicked.connect(self.addScenes)

        deleteButton = QPushButton("Delete")
        deleteButton.clicked.connect(self.deleteScene)

        clearButton = QPushButton("Clear")
        clearButton.clicked.connect(self.clearScene)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(deleteButton)
        buttonLayout.addWidget(clearButton)
        buttonLayout.setContentsMargins(0, 0, 0, 20)
        return buttonLayout

    def createRangeBrowser(self):
        rangeBrowserLayout = QHBoxLayout()
        rangeBrowserLayout.setContentsMargins(0, 0, 40, 0)

        browseButton = QPushButton("Browse")
        browseButton.setFont(self.font(12))
        browseButton.clicked.connect(self.rangeBrowseButtonCallback)

        self.sceneLineEdit = QLineEdit()
        self.sceneLineEdit.setFont(self.font(10))
        self.sceneLineEdit.setText("ranges/")

        rangeBrowserLayout.addWidget(browseButton)
        rangeBrowserLayout.addWidget(self.sceneLineEdit)
        return rangeBrowserLayout

    def formatSpotName(self, filename):
        """Return the full filename without the 'ranges/' prefix"""
        # Remove 'ranges/' or 'ranges\' from the path if present
        if filename.startswith('ranges/') or filename.startswith('ranges\\'):
            return filename[7:]
        return filename

    def rangeBrowseButtonCallback(self):
        fileName, _ = QFileDialog().getOpenFileName(directory=os.getcwd()+"/ranges/")
        if fileName:
            fileName = fileName[len(os.getcwd())+1:]
            self.sceneLineEdit.setText(fileName)
            self.addScene(fileName)

    def addScene(self, path):
        """Add a scene and start training"""
        if self.sceneIsClear:  # Only allow adding new scene if current one is cleared
            if path not in self.sceneDict.keys():
                sceneDict, success = parseLines(path)
                if not success:
                    QMessageBox.about(self.main, "Error", "For scenario \"" + path +"\" " + sceneDict)
                    return
                else:
                    self.sceneDict[path] = sceneDict
                    self.generateFirstTrainingScene()
            else:
                QMessageBox.about(self.main, "Error", "Scenario \""+ path + "\" Already Added")

    def clearAndSave(self):
        """Clear current scene and save report"""
        if not self.sceneIsClear:
            spot_name = os.path.basename(self.problemLabel).replace('.txt', '')
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, False, 0, True)
            self.clearTrainingScenario()
            self.sceneDict = {}

    def selectScenario(self, button):
        if self.curSelection == None:
            button.updateSelected()
            self.curSelection = button
        else:
            self.curSelection.updateSelected()
            self.curSelection = button
            button.updateSelected()

    def deleteScene(self):
        if self.curSelection is not None:
            self.sceneDict.pop(self.curSelection.originalPath)
            if self.curSelection.originalPath == self.problemLabel:
                self.clearTrainingScenario()
                if len(self.sceneDict) != 0:
                    self.generateFirstTrainingScene()
            self.curSelection.deleteLater()
            self.curSelection = None

    def clearScene(self):
        """Clear current scene"""
        self.clearTrainingScenario()
        self.clearLayout(self.dynamicScenarioLayout)
        self.sceneDict = {}
        self.curSelection = None

    def generateFirstTrainingScene(self):
        self.sceneIsClear = False
        sceneLayout = QVBoxLayout()
        sceneLayout.addWidget(self.createSceneProblemTitle())
        sceneLayout.addLayout(self.createMainSceneComponents())
        sceneLayout.addLayout(self.createSceneButtons())
        self.leftTrainerLayout.addLayout(sceneLayout)
        self.generateTrainingScenario()

    def createSceneProblemTitle(self):
        self.curProblemName = QLabel()
        self.curProblemName.setAlignment(QtCore.Qt.AlignCenter)
        self.curProblemName.setFont(self.font(36))
        self.curProblemName.setWordWrap(True)
        self.curProblemName.setMinimumWidth(800)  # Increase minimum width
        self.curProblemName.setMaximumWidth(1200) # Add maximum width to force wrapping
        return self.curProblemName

    def createMainSceneComponents(self):
        mainScene = QHBoxLayout()
        mainScene.stretch(1)
        mainScene.addWidget(self.createSceneRandomizer())
        mainScene.addLayout(self.createSceneCards())
        mainScene.addWidget(self.createSceneScore())
        return mainScene

    def createSceneCards(self):
        cardLayout = QHBoxLayout()
        cardLayout.setContentsMargins(50, 0, 50, 50)
        self.card1 = QLabel()
        self.card2 = QLabel()
        cardLayout.addWidget(self.card1)
        cardLayout.addWidget(self.card2)
        cardLayout.setSpacing(30)
        self.cardHeight = self.card1.height()
        self.cardWidth = self.card1.width()
        return cardLayout

    def createSceneRandomizer(self):
        self.randomLabel = QLabel()
        return self.randomLabel

    def createSceneScore(self):
        self.scoreLabel = QLabel()
        return self.scoreLabel

    def createSceneButtons(self):
        self.sceneButtonLayout = QHBoxLayout()
        callButton = QPushButton("Call")
        raiseButton = QPushButton("Raise")
        foldButton = QPushButton("Fold")

        callButton.clicked.connect(self.scenarioCallButtonCallback)
        raiseButton.clicked.connect(self.scenarioRaiseButtonCallback)
        foldButton.clicked.connect(self.scenarioFoldButtonCallback)
        self.sceneButtonLayout.addWidget(raiseButton)
        self.sceneButtonLayout.addWidget(callButton)
        self.sceneButtonLayout.addWidget(foldButton)
        return self.sceneButtonLayout

    def generateTrainingScenario(self):
        if self.report.isActive():
            self.trainingLabel.setText("Reporting Active")
            self.trainingLabel.setStyleSheet('color: green')
        else:
            self.trainingLabel.setText("Reporting Inactive")
            self.trainingLabel.setStyleSheet('color: red')

        self.clearLayout(self.sceneButtonLayout)
        self.createSceneButtons()
        self.leftTrainerLayout.addLayout(self.sceneButtonLayout)
        self.updateScenarioProblem()
        self.updateScenarioRandomizer()
        self.getHand()
        self.updateHandDrawing(int(self.cardWidth/2.8), int(self.cardHeight/1.55))

    def updateScenarioProblem(self):
        problemVal = np.random.randint(0, len(self.sceneDict))
        self.problemLabel = list(self.sceneDict.keys())[problemVal]
        display_name = os.path.basename(self.problemLabel)
        display_name = os.path.splitext(display_name)[0]
        
        # Add commas after specific words
        for word in ['Call', 'ante', 'Fold', 'AllIn']:
            display_name = display_name.replace(word + '_', word + ', ')
        
        # Replace remaining underscores with spaces
        display_name = display_name.replace('_', ' ')
        
        self.curProblemName.setText(f"Spot:\n{display_name}")

    def updateScenarioRandomizer(self):
        self.randomInt = np.random.randint(0, 100)
        #self.randomLabel.setText("Randomizer:\n    " + str(self.randomInt))

    def clearTrainingScenario(self):
        self.sceneIsClear = True
        self.clearLayout(self.leftTrainerLayout)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clearLayout(child.layout())

    def updateHandDrawing(self, cardWidth, cardHeight):
        # Add error handling and debugging for image loading
        card1_path = f"{self.card1Path}.png"
        card2_path = f"{self.card2Path}.png"
        
        print(f"Loading cards from: {card1_path} and {card2_path}")
        
        pixmap1 = QPixmap(card1_path)
        if pixmap1.isNull():
            print(f"Failed to load first card image: {card1_path}")
            print(f"File exists: {os.path.exists(card1_path)}")
        pixmap1 = pixmap1.scaled(cardWidth, cardHeight, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.card1.setPixmap(pixmap1)

        pixmap2 = QPixmap(card2_path)
        if pixmap2.isNull():
            print(f"Failed to load second card image: {card2_path}")
            print(f"File exists: {os.path.exists(card2_path)}")
        pixmap2 = pixmap2.scaled(cardWidth, cardHeight, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.card2.setPixmap(pixmap2)

    def getHand(self):
        # Use absolute path for card images
        app_path = os.path.dirname(os.path.abspath(__file__))
        cards_path = os.path.join(app_path, "cardimages")
        print(f"Cards directory: {cards_path}")
        
        weightDict = self.sceneDict[self.problemLabel]
        hand = np.random.randint(0, 81)
        comboMap = self.comboMap.reshape(81)
        self.hand = comboMap[hand]
        if "Depends" in weightDict:
            while self.hand not in weightDict["Depends"]:
                hand = np.random.randint(0, 81)
                comboMap = self.comboMap.reshape(81)
                self.hand = comboMap[hand]
        
        print(f"Selected hand: {self.hand}")
        
        if self.hand[-1] != "s":
            suit1 = np.random.randint(0, 4)
            suit2 = np.random.randint(0, 4)
            while suit2 == suit1:
                suit2 = np.random.randint(0, 4)
        else:
            suit1 = np.random.randint(0, 4)
            suit2 = suit1
        suits = ["clubs", "spades", "diamonds", "hearts"]
        
        self.card1Path = os.path.join(cards_path, str(self.hand[0]) + suits[suit1])
        self.card2Path = os.path.join(cards_path, str(self.hand[1]) + suits[suit2])
        
        print(f"Card paths: {self.card1Path} and {self.card2Path}")

    def getWeights(self):
        weightDict = self.sceneDict[self.problemLabel]
        raiseWeight = 0
        callWeight = 0
        for val in weightDict["raise"]:
            if self.hand in val[0]:
                raiseWeight += float(val[1])
        if weightDict["call"] is not None:
            for val in weightDict["call"]:
                if self.hand in val[0]:
                    callWeight += float(val[1])
        return raiseWeight, callWeight, 1-raiseWeight-callWeight

    def scenarioRaiseButtonCallback(self):
        raiseWeight, callWeight, foldWeight = self.getWeights()
        spot_name = os.path.basename(self.problemLabel).replace('.txt', '')
        
        if float(self.randomInt) / 100.0 >= callWeight+foldWeight:
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, True, 1, True)
            if self.scoreLabel.text() == "":
                self.scoreLabel.setText("Score: 1/1")
            else:
                num, dom = self.parseScore()
                self.scoreLabel.setText("Score: " + str(int(num)+1) + "/" + str(int(dom)+1))
            self.generateTrainingScenario()
        else:
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, False, 1, True)
            if self.scoreLabel.text() == "":
                self.scoreLabel.setText("Score: 0/1")
            else:
                num, dom = self.parseScore()
                self.scoreLabel.setText("Score: " + str(int(num)) + "/" + str(int(dom)+1))
            self.clearLayout(self.sceneButtonLayout)
            self.buildDisplayWeights(raiseWeight, callWeight, foldWeight)

    def scenarioCallButtonCallback(self):
        raiseWeight, callWeight, foldWeight = self.getWeights()
        spot_name = os.path.basename(self.problemLabel).replace('.txt', '')
        
        if float(self.randomInt) / 100.0 >= foldWeight and self.randomInt/100 < (callWeight+foldWeight):
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, True, 2, True)
            if self.scoreLabel.text() == "":
                self.scoreLabel.setText("Score: 1/1")
            else:
                num, dom = self.parseScore()
                self.scoreLabel.setText("Score: " + str(int(num)+1) + "/" + str(int(dom)+1))
            self.generateTrainingScenario()
        else:
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, False, 2, True)
            if self.scoreLabel.text() == "":
                self.scoreLabel.setText("Score: 0/1")
            else:
                num, dom = self.parseScore()
                self.scoreLabel.setText("Score: " + str(int(num)) + "/" + str(int(dom)+1))
            self.clearLayout(self.sceneButtonLayout)
            self.buildDisplayWeights(raiseWeight, callWeight, foldWeight)

    def scenarioFoldButtonCallback(self):
        raiseWeight, callWeight, foldWeight = self.getWeights()
        spot_name = os.path.basename(self.problemLabel).replace('.txt', '')
        
        if float(self.randomInt) / 100.0 < foldWeight:
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, True, 3, True)
            if self.scoreLabel.text() == "":
                self.scoreLabel.setText("Score: 1/1")
            else:
                num, dom = self.parseScore()
                self.scoreLabel.setText("Score: " + str(int(num)+1) + "/" + str(int(dom)+1))
            self.generateTrainingScenario()
        else:
            if self.report.isActive():
                self.report.addHandData(spot_name, self.hand, False, 3, True)
            if self.scoreLabel.text() == "":
                self.scoreLabel.setText("Score: 0/1")
            else:
                num, dom = self.parseScore()
                self.scoreLabel.setText("Score: " + str(int(num)) + "/" + str(int(dom)+1))
            self.clearLayout(self.sceneButtonLayout)
            self.buildDisplayWeights(raiseWeight, callWeight, foldWeight)

    def parseScore(self):
        score = self.scoreLabel.text()
        score = score[7:]
        score = score.split("/")
        s1 = float(score[0])
        s2 = float(score[1])
        if s1 > 9 or s2 > 9:
            self.scoreLabel.setFont(self.font(19))
        if s1 > 99 or s2 > 99:
            self.scoreLabel.setFont(self.font(17))
        return s1, s2

    def buildDisplayWeights(self, raiseWeight, callWeight, foldWeight):
        layout = QHBoxLayout()
        layoutLabel = QHBoxLayout()
        layoutLabel.setSpacing(2)
        layoutLabel.setContentsMargins(0, 0, 10, 0)

        incLabel = QLabel("Incorrect  ")
        incLabel.setFont(self.font(15))

        # Convert weights to percentages and round to 1 decimal place
        raisePercent = round(raiseWeight * 100, 1)
        callPercent = round(callWeight * 100, 1)
        foldPercent = round(foldWeight * 100, 1)

        raiseLabel = QLabel(f"Raise: {raisePercent}%  ")
        raiseLabel.setStyleSheet("color: green")
        raiseLabel.setFont(self.font(15))

        callLabel = QLabel(f"Call: {callPercent}%  ")
        callLabel.setStyleSheet("color: blue")
        callLabel.setFont(self.font(15))

        foldLabel = QLabel(f"Fold: {foldPercent}%  ")
        foldLabel.setStyleSheet("color: red")
        foldLabel.setFont(self.font(15))

        layoutLabel.addWidget(incLabel)
        layoutLabel.addWidget(raiseLabel)
        layoutLabel.addWidget(callLabel)
        layoutLabel.addWidget(foldLabel)

        continueButton = QPushButton("Continue")
        continueButton.clicked.connect(self.generateTrainingScenario)
        layout.addLayout(layoutLabel)
        layout.addWidget(continueButton)
        
        if self.sceneButtonLayout is not None:
            self.sceneButtonLayout.addLayout(layout)