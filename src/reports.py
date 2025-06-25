from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from customButton import DrawReportButton
from functools import partial
from colorPicker import ColorButton
from parser import *
import os
import numpy as np
import sys
from datetime import datetime

class Report():
    def __init__(self, comboMap, comboMapInverse, active):
        """
        Initialize the Report class
        Args:
            comboMap: Map of card combinations
            comboMapInverse: Inverse map of card combinations
            active: Boolean indicating if reporting is active
        """
        # Store the card combination maps
        self.comboMap = comboMap
        self.comboMapInverse = comboMapInverse
        self.active = active
        
        # Initialize empty report dictionary
        self.report = {}
        
        # Get application base directory for report storage
        try:
            if getattr(sys, 'frozen', False):
                # If running as exe
                self.base_dir = os.path.dirname(sys.executable)
            else:
                # If running from source
                self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except Exception as e:
            print(f"Error getting base directory: {str(e)}")
            self.base_dir = os.getcwd()  # Fallback to current directory
        
        # Set and create reports directory
        self.reports_dir = os.path.join(self.base_dir, "reports")
        try:
            os.makedirs(self.reports_dir, exist_ok=True)
            print(f"Reports will be saved to: {self.reports_dir}")
        except Exception as e:
            print(f"Error creating reports directory: {str(e)}")
        
        # Initialize report
        try:
            # Generate initial report
            self.generateReport("report1")
            
            # Load today's existing reports
            print("Loading existing reports for today...")
            self.loadTodaysReports()
        except Exception as e:
            print(f"Error during report initialization: {str(e)}")

    
    def isActive(self):
        return getattr(self, 'active', False)

    def setActive(self):
        self.active = True

    def setInactive(self):
        self.active = False

    def getReport(self):
        return self.report

    def generateReport(self, name):
        self.report = {}
        self.report["name"] = name
        self.report["data"] = {}
        self.generateSpot("Total")
        self.setActive()

    def generateSpot(self, spotName):
        spot = {}
        spot["handTotalArrAttempt"] = np.zeros((9, 9), dtype=np.int32)
        spot["handTotalArrCorrect"] = np.zeros((9, 9), dtype=np.int32)
        spot["statistics"] = {
            "numberOfHands": 0,
            "numberOfHandsCorrect": 0
        }
        self.report["data"][spotName] = spot

    def addHandData(self, spot, hand, correct, mode, addTotals):
        if addTotals:
            self.addHandData("Total", hand, correct, mode, False)
            
        if spot not in self.report["data"].keys():
            self.generateSpot(spot)
            
        handIdx = self.comboMapInverse[hand]
        data = self.report["data"][spot]
        
        # Update statistics
        data["statistics"]["numberOfHands"] += 1
        data["handTotalArrAttempt"][handIdx[0]][handIdx[1]] += 1
        
        if correct:
            data["statistics"]["numberOfHandsCorrect"] += 1
            data["handTotalArrCorrect"][handIdx[0]][handIdx[1]] += 1
        
        # Auto-save after each hand
        self.autoSaveReport(spot)

    def saveReport(self, filename):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, "w") as f:
                f.write(self.report["name"] + "\n")
                for spot in self.report["data"].keys():
                    f.write(spot + "\n")
                    spot_data = self.report["data"][spot]
                    
                    # Write statistics
                    stats = spot_data["statistics"]
                    f.write(str(stats["numberOfHands"]) + "\n")
                    f.write(str(stats["numberOfHandsCorrect"]) + "\n")
                    
                    # Write arrays
                    arr = spot_data["handTotalArrAttempt"].flatten()
                    f.write(",".join(map(str, arr)) + "\n")
                    arr = spot_data["handTotalArrCorrect"].flatten()
                    f.write(",".join(map(str, arr)) + "\n")
                        
            return True
            
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            return False

    def loadTodaysReports(self):
        """Load all reports for today's date"""
        try:
            # Clear existing data before loading today's reports
            self.report["data"] = {}
            self.generateSpot("Total")
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            # Get all report files for today
            for filename in os.listdir(self.reports_dir):
                if filename.endswith(f"_{current_date}.txt"):
                    filepath = os.path.join(self.reports_dir, filename)
                    self.loadReport(filepath)
                    
        except Exception as e:
            print(f"Error loading today's reports: {str(e)}")
            
    def loadReport(self, filename):
        """Load a report and merge it with existing data"""
        try:
            if not os.path.exists(filename):
                print(f"Report file not found: {filename}")
                return False
                
            print(f"Loading report from: {filename}")
            with open(filename, "r") as f:
                report_name = f.readline().strip()
                
                while True:
                    spot_name = f.readline().strip()
                    if not spot_name:
                        break
                    
                    # Extract just the spot name without path
                    if spot_name != "Total":
                        spot_name = os.path.basename(spot_name)
                        spot_name = spot_name.replace('.txt', '')
                        
                    # Read statistics
                    num_hands = int(f.readline().strip())
                    num_correct = int(f.readline().strip())
                    
                    # Read arrays
                    attempts_line = f.readline().strip()
                    attempts_values = list(map(int, attempts_line.split(",")))
                    attempts_array = np.array(attempts_values).reshape((9, 9))
                    
                    correct_line = f.readline().strip()
                    correct_values = list(map(int, correct_line.split(",")))
                    correct_array = np.array(correct_values).reshape((9, 9))
                    
                    # Create spot if it doesn't exist
                    if spot_name not in self.report["data"]:
                        self.generateSpot(spot_name)
                    
                    # Accumulate the data instead of overwriting
                    spot_data = self.report["data"][spot_name]
                    if "accumulated_hands" not in spot_data:
                        spot_data["accumulated_hands"] = 0
                        spot_data["accumulated_correct"] = 0
                    
                    # Update accumulation
                    new_hands = num_hands - spot_data["accumulated_hands"]
                    new_correct = num_correct - spot_data["accumulated_correct"]
                    
                    if new_hands > 0:
                        spot_data["statistics"]["numberOfHands"] += new_hands
                        spot_data["statistics"]["numberOfHandsCorrect"] += new_correct
                        spot_data["handTotalArrAttempt"] += attempts_array
                        spot_data["handTotalArrCorrect"] += correct_array
                        
                        # Update accumulated totals
                        spot_data["accumulated_hands"] = num_hands
                        spot_data["accumulated_correct"] = num_correct
                    
            print(f"Successfully loaded report: {filename}")
            return True
            
        except Exception as e:
            print(f"Error loading report: {str(e)}")
            return False
            
    def autoSaveReport(self, spot):
        try:
            # Get current date when saving
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Use the exact filename as spot name
            spot_name = os.path.basename(spot)
            
            # Create filename
            filename = f"{spot_name}_{current_date}.txt"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Save report
            success = self.saveReport(filepath)
            if success:
                print(f"Report saved successfully to: {filepath}")
            else:
                print(f"Failed to save report to: {filepath}")
            
        except Exception as e:
            print(f"Error auto-saving report: {str(e)}")

    def clearReport(self):
        self.report = {}
        self.setActive()

    def isEmpty(self):
        return not bool(self.report)