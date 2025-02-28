"""
Created on Tue Nov 19 11:51 2024
Updated on Mon Feb 17 12:43 2025
Version 0.5.3

@author: Thomas_JA
"""
import io
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import os
import ezdxf

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

 
#######################################################################################################################################################
#######################################################################################################################################################
#######################################################################################################################################################

def check_left_right(style_row, index):
    """
    style_row - array of characters: p, n, x, f
    index     - integer of where a pinch or fade is said to be

    Uses the index to search the style_row for the direction of pinching and fading.
    """
    # If it is the last item in the array then the direction is left
    if index == (len(style_row)-1) and style_row[index - 1] == 'n' :
        return 'left'
    # If it is the first item in the array then the direction is right
    elif index == 0 and style_row[index + 1] == 'n':
        return 'right'
    # If both directions are void, then pinch in both directions
    elif style_row[index - 1] == 'n' and style_row[index + 1] == 'n':
        return 'both'
    # If the item before is void, pinch to the left
    elif style_row[index - 1] == 'n':
        return 'left'
    # If the item after is void pinch to the right
    elif style_row[index + 1] == 'n':
        return 'right'

#######################################################################################################################################################

def find_bottom(style_array, row, index, direction):
    """
    style_array - array of characters: n, p, f, x.
    row         - integer, the row of the style array currently being worked
    index       - integer, the index at which the pinch of fade currently being calculated is at
    direction   - string: left, righ, both. The direction in which the formation pinches or fades

    Finds the non np.nan values for the slope calculation later.
    """
    #Creates an empty list to add row number to later
    slope_rows = []

    if direction == 'left':
        #If direction is left, it will grab the appropriate two values from the next row
        slope_points = style_array[row+1][[index-1, index]]
        n=0 # Increment for rows of the style array, used in the while loop
        #Then checks if they both are not np.nan
        if np.all(slope_points == ['x', 'x']):
            slope_rows.append(row+1) # Adds to the list if not np.nan
        else:
            while np.any(slope_points != ['x', 'x']): #Searches downwards until it finds 2 values that aren't np.nan
                n += 1
                slope_points=style_array[row+1+n][[index, index+1]]
            slope_rows.append(row+1+n)
            

    elif direction == 'right':
        #If direction is right, it will grab the appropriate two values from the next row
        slope_points = style_array[row+1][[index, index+1]]
        n=0 # Increment for rows of the style array, used in the while loop
        if np.all(slope_points == ['x', 'x']):
            slope_rows.append(row+1)# Adds to the list if not np.nan
        else:
            while np.any(slope_points != ['x', 'x']): #Searches downwards until it finds 2 values that aren't np.nan
                n += 1
                slope_points=style_array[row+1+n][[index, index+1]]
            slope_rows.append(row+1+n)
            

    elif direction == 'both': 
        #If direction is both we must grab four values to check the value to the left and right of the pinch point
        slope_right=style_array[row+1][[index, index+1]]
        slope_left=style_array[row+1][[index-1, index]]
        n=0 # Increment for rows of the style array, used in the while loop
        if np.all(slope_left == ['x','x']): #This checks the left side for np.nan values
            slope_rows.append(row+1)# Adds to the list if not np.nan
        else:
            while np.any(slope_left != ['x', 'x']):
                n += 1
                slope_left=style_array[row+1+n][[index, index+1]]
            slope_rows.append(row+1+n)
            
        n=0 # Increment for rows of the style array, used in the while loop
        if np.all(slope_right == ['x', 'x']): #This checks the right side for np.nan values
            slope_rows.append(row+1)# Adds to the list if not np.nan
        else:
            while np.any(slope_right != ['x', 'x']):
                n += 1
                slope_right=style_array[row+1+n][[index, index+1]]
            slope_rows.append(row+1+n)

    return slope_rows

#######################################################################################################################################################

def slope_calculator(formations_array, style_array, distance, row, index, direction, midpoint_ratio1, midpoint_ratio2=2):
    """
    formations_array - array of floats, top depth of formations
    style_array      - array of characters: n, p, f, x
    distance         - array of integers or floats, indicating the distance from the start of the cross section that each well is at
    row              - integer, the row of the style array currently being worked
    index            - integer, the index at which the pinch of fade currently being calculated is at
    direction        - string: left, righ, both. The direction in which the formation pinches or fades 
    """
    
    if direction == 'right':
        slope_rows = find_bottom(style_array, row, index, direction)
        depth1 = formations_array[slope_rows, index][0]
        depth2 = formations_array[slope_rows, index+1][0]

        distance1 = distance[index]
        distance2 = distance[index+1]
        

        slope = (depth1 - depth2) / (distance1 - distance2)
        midpoint = midpoint_ratio1
        yintercept = depth1 - (slope * distance1)
        point = (slope * midpoint) + yintercept


        new_point = np.array([[point], [point], [midpoint]])

        return new_point

    elif direction == 'left':
        slope_rows = find_bottom(style_array, row, index, direction)
        depth1 = formations_array[slope_rows, index][0]
        depth2 = formations_array[slope_rows, index-1][0]

        distance1 = distance[index]
        distance2 = distance[index-1]
        

        slope = (depth1 - depth2) / (distance1 - distance2)
        midpoint = midpoint_ratio1
        yintercept = depth1 - (slope * distance1)
        point = (slope * midpoint) + yintercept

        new_point = np.array([[point], [point], [midpoint]])

        return new_point

    
    elif direction == 'both':
        left_right_points = []
        slope_rows = find_bottom(style_array, row, index, direction)
        #Calculate the left point
        
        depth1 = formations_array[slope_rows[0], index]
        depth2 = formations_array[slope_rows[0], index-1]

        distance1 = distance[index]
        distance2 = distance[index-1]
        
        slope = (depth1 - depth2) / (distance1 - distance2)
        midpoint = midpoint_ratio1
        yintercept = depth1 - (slope * distance1)
        point = (slope * midpoint) + yintercept

        new_point = np.array([[point], [point], [midpoint]])
        left_right_points.append(new_point)

        #Calculate the right point
        depth1 = formations_array[slope_rows[1], index]
        depth2 = formations_array[slope_rows[1], index+1]

        distance1 = distance[index]
        distance2 = distance[index+1]
        
        slope = (depth1 - depth2) / (distance1 - distance2)
        midpoint = midpoint_ratio2
        yintercept = depth1 - (slope * distance1)
        point = (slope * midpoint) + yintercept

        new_point = np.array([[point], [point], [midpoint]])
        left_right_points.append(new_point)

        return left_right_points


def hex_to_rgb(hex_color):
    """
    Convert hex color (e.g., '#FF5733') to RGB integer.
    """
    
    hex_color = hex_color.lstrip("#")
    return int(hex_color, 16)


#######################################################################################################################################################
#######################################################################################################################################################
#######################################################################################################################################################


# =============================================================================
#region GraphWindow
# =============================================================================
class GraphWindow(QtWidgets.QWidget):  # Subclass QWidget for the second window
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graph Window")
        self.setGeometry(200, 200, 600, 400)

        # Add a label to the second window
        self.graphWindow_label = QtWidgets.QLabel('Graph Window', self)
        self.graphWindow_label.setAlignment(QtCore.Qt.AlignCenter)
        self.graphWindow_label.setGeometry(5, 5, 595, 395)
        self.graphWindow_label.setObjectName("graphWindow_label")
        self.graphWindow_label.setFrameShape(QtWidgets.QFrame.Box)
        
        # Set initial geometry for the label
        self.update_label_geometry()


    def resizeEvent(self, event):
        """
        Override resizeEvent to resize the label dynamically.
        """
        
        self.update_label_geometry()
        super().resizeEvent(event)


    def update_label_geometry(self):
        """
        Update the geometry of the label based on the window size.
        """
        
        window_width = self.width()
        window_height = self.height()

        # Adjust label size to 50% of window width and 25% of window height
        label_width = int(window_width * 0.99)
        label_height = int(window_height * 0.99)

        # Center the label in the window
        label_x = (window_width - label_width) // 2
        label_y = (window_height - label_height) // 2

        self.graphWindow_label.setGeometry(label_x, label_y, label_width, label_height)

# =============================================================================
#region MainWindow
# =============================================================================
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1511, 930)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(10, 5, 1491, 900))
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        
        self.selectFile_button = QtWidgets.QPushButton(self.tab)
        self.selectFile_button.setGeometry(QtCore.QRect(0, 10, 91, 31))
        self.selectFile_button.setObjectName("selectFile_button")
        
        self.mainUpdate_button = QtWidgets.QPushButton(self.tab)
        self.mainUpdate_button.setGeometry(QtCore.QRect(100, 10, 111, 31))
        self.mainUpdate_button.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.mainUpdate_button.setObjectName("mainUpdate_button")
        
        self.main_xsecplot = QtWidgets.QLabel(self.tab)
        self.main_xsecplot.setGeometry(QtCore.QRect(10, 80, 1300, 780))
        self.main_xsecplot.setFrameShape(QtWidgets.QFrame.Box)
        self.main_xsecplot.setText("")
        self.main_xsecplot.setAlignment(QtCore.Qt.AlignCenter)
        self.main_xsecplot.setObjectName("main_xsecplot")
        
        self.adjustPinchFade_combox = QtWidgets.QComboBox(self.tab)
        self.adjustPinchFade_combox.setGeometry(QtCore.QRect(310, 40, 69, 22))
        self.adjustPinchFade_combox.setObjectName("adujstPinchFade_combox")
        
        self.adjustPinchFadeFormation_combox = QtWidgets.QComboBox(self.tab)
        self.adjustPinchFadeFormation_combox.setGeometry(QtCore.QRect(390, 40, 69, 22))
        self.adjustPinchFadeFormation_combox.setObjectName("adjustPinchFadeFormation_combox")
        
        self.adjustPinchFadeIndex_combox = QtWidgets.QComboBox(self.tab)
        self.adjustPinchFadeIndex_combox.setGeometry(QtCore.QRect(470, 40, 110, 22))
        self.adjustPinchFadeIndex_combox.setObjectName("adjustPinchFadeIndex_combox")
        
        self.adjustPinchFade_slider = QtWidgets.QSlider(self.tab)
        self.adjustPinchFade_slider.setGeometry(QtCore.QRect(600, 40, 160, 22))
        self.adjustPinchFade_slider.setOrientation(QtCore.Qt.Horizontal)
        self.adjustPinchFade_slider.setObjectName("adjustPinchFade_slider")
        
        self.adjustPinchFadeMin_label = QtWidgets.QLabel(self.tab)
        self.adjustPinchFadeMin_label.setGeometry(QtCore.QRect(580, 20, 47, 20))
        self.adjustPinchFadeMin_label.setText("")
        self.adjustPinchFadeMin_label.setObjectName("adjustPinchFadeMin_label")
        self.adjustPinchFadeMin_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.adjustPinchFadeMax_label = QtWidgets.QLabel(self.tab)
        self.adjustPinchFadeMax_label.setGeometry(QtCore.QRect(730, 20, 47, 20))
        self.adjustPinchFadeMax_label.setText("")
        self.adjustPinchFadeMax_label.setObjectName("adjustPinchFadeMax_label")
        self.adjustPinchFadeMax_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.adjustPinchFadetitle_label = QtWidgets.QLabel(self.tab)
        self.adjustPinchFadetitle_label.setGeometry(QtCore.QRect(333, 10, 230, 20))
        self.adjustPinchFadetitle_label.setText('Adjust Pinch / Fade Locations')
        self.adjustPinchFadetitle_label.setObjectName('adjustPinchFadetitle_label')
        self.adjustPinchFadetitle_label.setAlignment(QtCore.Qt.AlignCenter)
        font = self.adjustPinchFadetitle_label.font()
        font.setPointSize(12)
        self.adjustPinchFadetitle_label.setFont(font)
        
        self.numberOfTeeth_textbox = QtWidgets.QTextEdit(self.tab)
        self.numberOfTeeth_textbox.setGeometry(QtCore.QRect(800, 40, 30, 20))
        self.numberOfTeeth_textbox.setObjectName("numberOfTeeth_textedit")
        self.numberOfTeeth_textbox.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.numberOfTeeth_label = QtWidgets.QLabel(self.tab)
        self.numberOfTeeth_label.setGeometry(QtCore.QRect(785, 20, 60, 20))
        self.numberOfTeeth_label.setText('# of teeth')
        self.numberOfTeeth_label.setObjectName('numberOfTeeth_label')
        self.numberOfTeeth_label.setAlignment(QtCore.Qt.AlignCenter)
        font = self.numberOfTeeth_label.font()
        font.setPointSize(10)
        self.numberOfTeeth_label.setFont(font)
        
        self.changePlotSize_label = QtWidgets.QLabel(self.tab)
        self.changePlotSize_label.setGeometry(QtCore.QRect(900, 20, 101, 20))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.changePlotSize_label.setFont(font)
        self.changePlotSize_label.setObjectName("changePlotSize_label")
        self.changePlotSize_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.changePlotSizeSmaller_button = QtWidgets.QPushButton(self.tab)
        self.changePlotSizeSmaller_button.setGeometry(QtCore.QRect(900, 40, 51, 23))
        self.changePlotSizeSmaller_button.setObjectName("changePlotSizeSmaller_Button")
        
        self.changePlotSizeLarger_button = QtWidgets.QPushButton(self.tab)
        self.changePlotSizeLarger_button.setGeometry(QtCore.QRect(950, 40, 51, 23))
        self.changePlotSizeLarger_button.setObjectName("changePlotSizeLarger_button")
        
        self.openSecondWindow_button = QtWidgets.QPushButton(self.tab)
        self.openSecondWindow_button.setGeometry(QtCore.QRect(0, 43, 120, 31))
        self.openSecondWindow_button.setObjectName('openSecondWindow_button')
        
        self.formation_id_labels = QtWidgets.QLabel(self.tab)
        self.formation_id_labels.setGeometry(QtCore.QRect(1250, 40, 300, 50))
        self.formation_id_labels.setText("Formation Colors / Labels")
        font = QtGui.QFont()
        font.setPointSize(12)
        self.formation_id_labels.setFont(font)
        self.formation_id_labels.setObjectName('formationId_labels')
        self.formation_id_labels.setAlignment(QtCore.Qt.AlignCenter)
        self.formation_id_labels.hide()
        
        self.form1Color_label = QtWidgets.QLabel(self.tab)
        self.form1Color_label.setGeometry(QtCore.QRect(1325, 80, 25, 25))
        self.form1Color_label.setObjectName('form1Color_label')
        
        self.form2Color_label = QtWidgets.QLabel(self.tab)
        self.form2Color_label.setGeometry(QtCore.QRect(1325, 130, 25, 25))
        self.form2Color_label.setObjectName('form2Color_label')

        self.form3Color_label = QtWidgets.QLabel(self.tab)
        self.form3Color_label.setGeometry(QtCore.QRect(1325, 180, 25, 25))
        self.form3Color_label.setObjectName('form3Color_label')

        self.form4Color_label = QtWidgets.QLabel(self.tab)
        self.form4Color_label.setGeometry(QtCore.QRect(1325, 230, 25, 25))
        self.form4Color_label.setObjectName('form4Color_label')

        self.form5Color_label = QtWidgets.QLabel(self.tab)
        self.form5Color_label.setGeometry(QtCore.QRect(1325, 280, 25, 25))
        self.form5Color_label.setObjectName('form5Color_label')

        self.form6Color_label = QtWidgets.QLabel(self.tab)
        self.form6Color_label.setGeometry(QtCore.QRect(1325, 330, 25, 25))
        self.form6Color_label.setObjectName('form6Color_label')

        self.form7Color_label = QtWidgets.QLabel(self.tab)
        self.form7Color_label.setGeometry(QtCore.QRect(1325, 380, 25, 25))
        self.form7Color_label.setObjectName('form7Color_label')

        self.form8Color_label = QtWidgets.QLabel(self.tab)
        self.form8Color_label.setGeometry(QtCore.QRect(1325, 430, 25, 25))
        self.form8Color_label.setObjectName('form8Color_label')

        self.form9Color_label = QtWidgets.QLabel(self.tab)
        self.form9Color_label.setGeometry(QtCore.QRect(1325, 480, 25, 25))
        self.form9Color_label.setObjectName('form9Color_label')

        self.form10Color_label = QtWidgets.QLabel(self.tab)
        self.form10Color_label.setGeometry(QtCore.QRect(1325, 530, 25, 25))
        self.form10Color_label.setObjectName('form10Color_label')

        self.form11Color_label = QtWidgets.QLabel(self.tab)
        self.form11Color_label.setGeometry(QtCore.QRect(1325, 580, 25, 25))
        self.form11Color_label.setObjectName('form11Color_label')

        self.form12Color_label = QtWidgets.QLabel(self.tab)
        self.form12Color_label.setGeometry(QtCore.QRect(1325, 630, 25, 25))
        self.form12Color_label.setObjectName('form12Color_label')

        self.form13Color_label = QtWidgets.QLabel(self.tab)
        self.form13Color_label.setGeometry(QtCore.QRect(1325, 680, 25, 25))
        self.form13Color_label.setObjectName('form13Color_label')

        self.form14Color_label = QtWidgets.QLabel(self.tab)
        self.form14Color_label.setGeometry(QtCore.QRect(1325, 730, 25, 25))
        self.form14Color_label.setObjectName('form14Color_label')
        
        self.form15Color_label = QtWidgets.QLabel(self.tab)
        self.form15Color_label.setGeometry(QtCore.QRect(1325, 780, 25, 25))
        self.form15Color_label.setObjectName('form15Color_label')
        
        self.form16Color_label = QtWidgets.QLabel(self.tab)
        self.form16Color_label.setGeometry(QtCore.QRect(1325, 820, 25, 25))
        self.form16Color_label.setObjectName('form16Color_label')
        
        self.formation_color_label_list = [self.form1Color_label, self.form2Color_label, self.form3Color_label, self.form4Color_label, self.form5Color_label, self.form6Color_label, self.form7Color_label, self.form8Color_label, self.form9Color_label, self.form10Color_label, self.form11Color_label, self.form12Color_label, self.form13Color_label, self.form14Color_label, self.form15Color_label, self.form16Color_label]
        
        self.form1Name_label = QtWidgets.QLabel(self.tab)
        self.form1Name_label.setGeometry(QtCore.QRect(1375, 80, 200, 25))
        self.form1Name_label.setObjectName('form1Name_label')
        
        self.form2Name_label = QtWidgets.QLabel(self.tab)
        self.form2Name_label.setGeometry(QtCore.QRect(1375, 130, 200, 25))
        self.form2Name_label.setObjectName('form2Name_label')

        self.form3Name_label = QtWidgets.QLabel(self.tab)
        self.form3Name_label.setGeometry(QtCore.QRect(1375, 180, 200, 25))
        self.form3Name_label.setObjectName('form3Name_label')

        self.form4Name_label = QtWidgets.QLabel(self.tab)
        self.form4Name_label.setGeometry(QtCore.QRect(1375, 230, 200, 25))
        self.form4Name_label.setObjectName('form4Name_label')

        self.form5Name_label = QtWidgets.QLabel(self.tab)
        self.form5Name_label.setGeometry(QtCore.QRect(1375, 280, 200, 25))
        self.form5Name_label.setObjectName('form5Name_label')

        self.form6Name_label = QtWidgets.QLabel(self.tab)
        self.form6Name_label.setGeometry(QtCore.QRect(1375, 330, 200, 25))
        self.form6Name_label.setObjectName('form6Name_label')

        self.form7Name_label = QtWidgets.QLabel(self.tab)
        self.form7Name_label.setGeometry(QtCore.QRect(1375, 380, 200, 25))
        self.form7Name_label.setObjectName('form7Name_label')

        self.form8Name_label = QtWidgets.QLabel(self.tab)
        self.form8Name_label.setGeometry(QtCore.QRect(1375, 430, 200, 25))
        self.form8Name_label.setObjectName('form8Name_label')

        self.form9Name_label = QtWidgets.QLabel(self.tab)
        self.form9Name_label.setGeometry(QtCore.QRect(1375, 480, 200, 25))
        self.form9Name_label.setObjectName('form9Name_label')

        self.form10Name_label = QtWidgets.QLabel(self.tab)
        self.form10Name_label.setGeometry(QtCore.QRect(1375, 530, 200, 25))
        self.form10Name_label.setObjectName('form10Name_label')

        self.form11Name_label = QtWidgets.QLabel(self.tab)
        self.form11Name_label.setGeometry(QtCore.QRect(1375, 580, 200, 25))
        self.form11Name_label.setObjectName('form11Name_label')

        self.form12Name_label = QtWidgets.QLabel(self.tab)
        self.form12Name_label.setGeometry(QtCore.QRect(1375, 630, 200, 25))
        self.form12Name_label.setObjectName('form12Name_label')

        self.form13Name_label = QtWidgets.QLabel(self.tab)
        self.form13Name_label.setGeometry(QtCore.QRect(1375, 680, 200, 25))
        self.form13Name_label.setObjectName('form13Name_label')

        self.form14Name_label = QtWidgets.QLabel(self.tab)
        self.form14Name_label.setGeometry(QtCore.QRect(1375, 730, 200, 25))
        self.form14Name_label.setObjectName('form14Name_label')
        
        self.form15Name_label = QtWidgets.QLabel(self.tab)
        self.form15Name_label.setGeometry(QtCore.QRect(1375, 780, 200, 25))
        self.form15Name_label.setObjectName('form15Name_label')
        
        self.form16Name_label = QtWidgets.QLabel(self.tab)
        self.form16Name_label.setGeometry(QtCore.QRect(1375, 830, 200, 25))
        self.form16Name_label.setObjectName('form16Name_label')
        
        self.formation_name_labels_list = [self.form1Name_label, self.form2Name_label, self.form3Name_label, self.form4Name_label, self.form5Name_label, self.form6Name_label, self.form7Name_label, self.form8Name_label, self.form9Name_label, self.form10Name_label, self.form11Name_label, self.form12Name_label, self.form13Name_label, self.form14Name_label, self.form15Name_label, self.form16Name_label]
        
        self.verticalExaggeration_label = QtWidgets.QLabel(self.tab)
        self.verticalExaggeration_label.setGeometry(QtCore.QRect(1180, 20, 120, 25))
        
        self.verticalExaggeration_textbox = QtWidgets.QTextEdit(self.tab, plainText = "100")
        self.verticalExaggeration_textbox.setGeometry(QtCore.QRect(1200, 40, 50, 25))
        
        self.totalDepth_label = QtWidgets.QLabel(self.tab)
        self.totalDepth_label.setGeometry(QtCore.QRect(1055, 20, 120, 25))
        
        self.totalDepth_texbox = QtWidgets.QTextEdit(self.tab, placeholderText="TD")
        self.totalDepth_texbox.setGeometry(QtCore.QRect(1075, 40, 50, 25))
        

        # =============================================================================
        #region Tab 1 End
        # =============================================================================

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(resource_path("picture--pencil.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabWidget.addTab(self.tab, icon, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        
        self.formationsUpdate_button = QtWidgets.QPushButton(self.tab_2)
        self.formationsUpdate_button.setGeometry(QtCore.QRect(10, 10, 111, 31))
        self.formationsUpdate_button.setObjectName("formationsUpdate_button")
        
        self.formations_table = QtWidgets.QTableWidget(self.tab_2)
        self.formations_table.setGeometry(QtCore.QRect(0, 50, 1481, 401))
        self.formations_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.formations_table.setObjectName("formations_table")
        self.formations_table.setColumnCount(0)
        self.formations_table.setRowCount(0)
        
        self.TopDepthOfFormations_label = QtWidgets.QLabel(self.tab_2)
        self.TopDepthOfFormations_label.setGeometry(QtCore.QRect(150, 0, 261, 51))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.TopDepthOfFormations_label.setFont(font)
        self.TopDepthOfFormations_label.setObjectName("TopDepthOfFormations_label")
        self.TopDepthOfFormations_label.setText("Top Depth of Formations")
        
        self.formationPolygons_table = QtWidgets.QTableWidget(self.tab_2)
        self.formationPolygons_table.setGeometry(QtCore.QRect(0, 501, 1481, 311))
        self.formationPolygons_table.setObjectName("formationPolygons_table")
        self.formationPolygons_table.setColumnCount(0)
        self.formationPolygons_table.setRowCount(0)
        
        self.formationPolygons_label = QtWidgets.QLabel(self.tab_2)
        self.formationPolygons_label.setGeometry(QtCore.QRect(0, 460, 211, 41))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.formationPolygons_label.setFont(font)
        self.formationPolygons_label.setObjectName("formationPolygons_label")
        
        self.formationPolygons_combox = QtWidgets.QComboBox(self.tab_2)
        self.formationPolygons_combox.setGeometry(QtCore.QRect(220, 461, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.formationPolygons_combox.setFont(font)
        self.formationPolygons_combox.setObjectName("formationPolygons_combox")
        
        # =============================================================================
        #region Tab 2 End
        # =============================================================================

        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(resource_path("table-heatmap.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabWidget.addTab(self.tab_2, icon1, "")
        
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        
        self.styleUpdate_button = QtWidgets.QPushButton(self.tab_3)
        self.styleUpdate_button.setGeometry(QtCore.QRect(10, 10, 111, 31))
        self.styleUpdate_button.setObjectName("styleUpdate_button")
        
        self.style_table = QtWidgets.QTableWidget(self.tab_3)
        self.style_table.setGeometry(QtCore.QRect(0, 220, 1261, 271))
        self.style_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.style_table.setObjectName("style_table")
        self.style_table.setColumnCount(0)
        self.style_table.setRowCount(0)
        
        self.colors_table = QtWidgets.QTableWidget(self.tab_3)
        self.colors_table.setGeometry(QtCore.QRect(1270, 320, 211, 491))
        self.colors_table.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.colors_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.colors_table.setObjectName("colors_table")
        self.colors_table.setColumnCount(0)
        self.colors_table.setRowCount(0)
        
        self.sampleType_table = QtWidgets.QTableWidget(self.tab_3)
        self.sampleType_table.setGeometry(QtCore.QRect(0, 580, 1261, 231))
        self.sampleType_table.setObjectName("sampleType_table")
        self.sampleType_table.setColumnCount(0)
        self.sampleType_table.setRowCount(0)
        
        self.formationStyle_lable = QtWidgets.QLabel(self.tab_3)
        self.formationStyle_lable.setGeometry(QtCore.QRect(0, 190, 181, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.formationStyle_lable.setFont(font)
        self.formationStyle_lable.setObjectName("formationStyle_lable")
        self.formationStyle_lable.setText("Formation Style")
        
        self.sampleType_label = QtWidgets.QLabel(self.tab_3)
        self.sampleType_label.setGeometry(QtCore.QRect(0, 550, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.sampleType_label.setFont(font)
        self.sampleType_label.setObjectName("sampleType_label")
        self.sampleType_label.setText('Sample Type')
        
        self.sampleType_combox = QtWidgets.QComboBox(self.tab_3)
        self.sampleType_combox.setGeometry(QtCore.QRect(240, 550, 69, 22))
        self.sampleType_combox.setObjectName("sampleType_combox")
        
        self.sampleChangesWithDepth_label = QtWidgets.QLabel(self.tab_3)
        self.sampleChangesWithDepth_label.setGeometry(QtCore.QRect(190, 530, 191, 16))
        self.sampleChangesWithDepth_label.setObjectName("sampleChangesWithDepth_label")
        
        self.styleGuide_label = QtWidgets.QLabel(self.tab_3)
        self.styleGuide_label.setGeometry(QtCore.QRect(10, 40, 300, 150))
        self.styleGuide_label.setObjectName("styleGuide_label")
        font = QtGui.QFont()
        font.setPointSize(14)
        self.styleGuide_label.setFont(font)
        
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(resource_path("palette-paint-brush.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabWidget.addTab(self.tab_3, icon2, "")
        
        # =============================================================================
        #region Tab 3 End
        # =============================================================================

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1511, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuSave = QtWidgets.QMenu(self.menuFile)
        self.menuExport_Data = QtWidgets.QMenu(self.menubar)
        self.menuExport_Data.setObjectName("menuExport_Data")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(resource_path("disk-black.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.menuSave.setIcon(icon3)
        self.menuSave.setObjectName("menuSave")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        self.actionSave_as_DXF = QtWidgets.QAction(MainWindow)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(resource_path("blue-document-smiley.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_DXF.setIcon(icon11)
        self.actionSave_as_DXF.setObjectName('actionSave_as_DXF')
        
        self.actionSave_as_PDF = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(resource_path("blue-document-pdf.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_PDF.setIcon(icon3)
        self.actionSave_as_PDF.setObjectName("actionSave_as_PDF")
        
        self.actionSave_as_PNG = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(resource_path("blue-document-image.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_PNG.setIcon(icon4)
        self.actionSave_as_PNG.setObjectName("actionSave_as_PNG")
        
        self.actionSave_as_JPEG = QtWidgets.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(resource_path("application-image.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_JPEG.setIcon(icon5)
        self.actionSave_as_JPEG.setObjectName("actionSave_as_JPEG")
        
        self.actionSave_as_TIFF = QtWidgets.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(resource_path("blue-document-attribute-t.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_TIFF.setIcon(icon6)
        self.actionSave_as_TIFF.setObjectName("actionSave_as_TIFF")
        
        self.actionSave_as_EPS = QtWidgets.QAction(MainWindow)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(resource_path("blue-document-sticky-note.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_EPS.setIcon(icon7)
        self.actionSave_as_EPS.setObjectName("actionSave_as_EPS")
        
        self.actionExport_as_Excel = QtWidgets.QAction(MainWindow)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(resource_path("table-excel.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionExport_as_Excel.setIcon(icon9)
        self.actionExport_as_Excel.setObjectName("actionExport_as_Excel")
        
        self.actionExport_as_CSV = QtWidgets.QAction(MainWindow)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(resource_path("document-excel-csv.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionExport_as_CSV.setIcon(icon10)
        self.actionExport_as_CSV.setObjectName("actionExport_as_CSV")
        
        self.actionSave_as_AutoCadDXF = QtWidgets.QAction(MainWindow)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(resource_path("blue-document-smiley.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave_as_AutoCadDXF.setIcon(icon11)
        self.actionSave_as_AutoCadDXF.setObjectName("actionSave_as_AutoCadDXF")
        
        
        self.menuSave.addAction(self.actionSave_as_PDF)
        self.menuSave.addAction(self.actionSave_as_PNG)
        self.menuSave.addAction(self.actionSave_as_JPEG)
        self.menuSave.addAction(self.actionSave_as_TIFF)
        self.menuSave.addAction(self.actionSave_as_EPS)
        self.menuFile.addAction(self.menuSave.menuAction())
        self.menuExport_Data.addAction(self.actionExport_as_Excel)
        self.menuExport_Data.addAction(self.actionExport_as_CSV)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuExport_Data.menuAction())
        self.menuSave.addAction(self.actionSave_as_DXF)
        self.menuSave.addAction(self.actionSave_as_AutoCadDXF)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        self.formations_updated = False
        self.style_updated      = False
        self.polygon_updated    = False
        self.sampleType_updated = False
        self.colors_updated     = False
        self.pinchFadeslider_changed = False
        self.toothNumber_changed = False
        self.figSize_changed = False
        
        self.table_font = QtGui.QFont('MS Shell Dlg 2', 12)
        
        self.sampleType_combox.addItem('No', False)
        self.sampleType_combox.addItem('Yes', True)
        
        self.adjustPinchFade_combox.addItem('Pinch')
        self.adjustPinchFade_combox.addItem('Fade')
        
        
        
        self.default_figsize = [24, 12]
        self.figsize = [24, 12]
        
        
        self.colors_list = ['#c0392b', '#e74c3c', '#9b59b6', '#8e44ad', '#2980b9', '#3498db', '#1abc9c', '#16a085', '#27ae60', '#2ecc71', '#f1c40f', '#f39c12', '#e67e22', '#d35400', '#34495e', '#2c3e50']
        self.formation_colors = {"qh": "#E0A74D", "qbd": "#FFDB96", "qu": "#EBEB98", "tqu": "#DCC27D", "tc": "#CCCCCC", "th": "#75E5AB", "thp": "#92C272", "that": "#DEA0CB", "ts": "#B7B1F1", "to": "#6CD1E8", "tap": "#3460C1", "tha": "#FAC0CC" }
        self.plotting_colors = []
        
        self.mainUpdate_button.clicked.connect(self.update_figure)
        self.changePlotSizeLarger_button.clicked.connect(self.bigger_fig)
        self.changePlotSizeSmaller_button.clicked.connect(self.smaller_fig)
        self.changePlotSizeLarger_button.clicked.connect(self.fig_size_status)
        self.changePlotSizeSmaller_button.clicked.connect(self.fig_size_status)
        self.formationsUpdate_button.clicked.connect(self.update_figure)
        self.styleUpdate_button.clicked.connect(self.update_figure)
        self.selectFile_button.clicked.connect(self.select_file)
        self.formationPolygons_combox.activated.connect(self.create_formation_polygons_table)
        self.formationPolygons_table.itemChanged.connect(self.polygon_updated_status)
        self.formations_table.itemChanged.connect(self.formation_updated_status)
        self.style_table.itemChanged.connect(self.style_updated_status)
        self.sampleType_table.itemChanged.connect(self.sample_type_updated_status)
        self.colors_table.itemChanged.connect(self.colors_status)
        self.verticalExaggeration_textbox.textChanged.connect(self.vertical_exaggeration_status)
        self.totalDepth_texbox.textChanged.connect(self.max_TD_status)
        
        self.sampleType_combox.activated.connect(self.sample_changes)
        
        
        self.adjustPinchFadeFormation_combox.activated.connect(self.pinch_fade_index_combox)
        self.adjustPinchFade_combox.activated.connect(self.pinch_fade_index_combox)
        self.adjustPinchFade_slider.valueChanged.connect(self.pinch_fade_slider)
        self.adjustPinchFade_slider.setEnabled(False)
        
        self.adjustPinchFadeIndex_combox.activated.connect(self.pinch_fade_slider_setup)
        
        self.numberOfTeeth_textbox.textChanged.connect(self.tooth_number_status)
        self.adjustPinchFade_combox.currentIndexChanged.connect(self.update_visibility)
        self.adjustPinchFadeIndex_combox.currentIndexChanged.connect(self.update_visibility)
        self.adjustPinchFadeIndex_combox.currentIndexChanged.connect(self.pinch_fade_exists)
        self.numberOfTeeth_textbox.hide()
        self.numberOfTeeth_label.hide()
        
        
        self.actionSave_as_PDF.triggered.connect(self.save_pdf)
        self.actionSave_as_PNG.triggered.connect(self.save_png)
        self.actionSave_as_TIFF.triggered.connect(self.save_tiff)
        self.actionSave_as_JPEG.triggered.connect(self.save_jpeg)
        self.actionSave_as_EPS.triggered.connect(self.save_eps)
        self.actionSave_as_DXF.triggered.connect(self.save_illustrator_dxf)
        self.actionSave_as_AutoCadDXF.triggered.connect(self.save_autocad_dxf)
        
        self.actionExport_as_Excel.triggered.connect(self.export_as_excel)
        
        self.openSecondWindow_button.clicked.connect(self.open_second_window)
        
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.original_geometry = MainWindow.geometry()
        # =============================================================================
        #region Resize Widgets
        # =============================================================================
        self.widget_geometries = {
            self.formation_id_labels: self.formation_id_labels.geometry(),
            self.form1Color_label: self.form1Color_label.geometry(),
            self.form2Color_label: self.form2Color_label.geometry(),
            self.form3Color_label: self.form3Color_label.geometry(),
            self.form4Color_label: self.form4Color_label.geometry(),
            self.form5Color_label: self.form5Color_label.geometry(),
            self.form6Color_label: self.form6Color_label.geometry(),
            self.form7Color_label: self.form7Color_label.geometry(),
            self.form8Color_label: self.form8Color_label.geometry(),
            self.form9Color_label: self.form9Color_label.geometry(),
            self.form10Color_label: self.form10Color_label.geometry(),
            self.form11Color_label: self.form11Color_label.geometry(),
            self.form12Color_label: self.form12Color_label.geometry(),
            self.form13Color_label: self.form13Color_label.geometry(),
            self.form14Color_label: self.form14Color_label.geometry(),
            self.form1Name_label: self.form1Name_label.geometry(),
            self.form2Name_label: self.form2Name_label.geometry(),
            self.form3Name_label: self.form3Name_label.geometry(),
            self.form4Name_label: self.form4Name_label.geometry(),
            self.form5Name_label: self.form5Name_label.geometry(),
            self.form6Name_label: self.form6Name_label.geometry(),
            self.form7Name_label: self.form7Name_label.geometry(),
            self.form8Name_label: self.form8Name_label.geometry(),
            self.form9Name_label: self.form9Name_label.geometry(),
            self.form10Name_label: self.form10Name_label.geometry(),
            self.form11Name_label: self.form11Name_label.geometry(),
            self.form12Name_label: self.form12Name_label.geometry(),
            self.form13Name_label: self.form13Name_label.geometry(),
            self.form14Name_label: self.form14Name_label.geometry(),
            self.tabWidget: self.tabWidget.geometry(),
            self.selectFile_button: self.selectFile_button.geometry(),
            self.mainUpdate_button: self.mainUpdate_button.geometry(),
            self.main_xsecplot: self.main_xsecplot.geometry(),
            self.adjustPinchFade_combox: self.adjustPinchFade_combox.geometry(),
            self.adjustPinchFadeFormation_combox: self.adjustPinchFadeFormation_combox.geometry(),
            self.adjustPinchFadeIndex_combox: self.adjustPinchFadeIndex_combox.geometry(),
            self.adjustPinchFade_slider: self.adjustPinchFade_slider.geometry(),
            self.adjustPinchFadeMin_label: self.adjustPinchFadeMin_label.geometry(),
            self.adjustPinchFadeMax_label: self.adjustPinchFadeMax_label.geometry(),
            self.adjustPinchFadetitle_label: self.adjustPinchFadetitle_label.geometry(),
            self.numberOfTeeth_textbox: self.numberOfTeeth_textbox.geometry(),
            self.numberOfTeeth_label: self.numberOfTeeth_label.geometry(),
            self.formationsUpdate_button: self.formationsUpdate_button.geometry(),
            self.formations_table: self.formations_table.geometry(),
            self.TopDepthOfFormations_label: self.TopDepthOfFormations_label.geometry(),
            self.formationPolygons_table: self.formationPolygons_table.geometry(),
            self.formationPolygons_label: self.formationPolygons_label.geometry(),
            self.formationPolygons_combox: self.formationPolygons_combox.geometry(),
            self.styleUpdate_button: self.styleUpdate_button.geometry(),
            self.style_table: self.style_table.geometry(),
            self.colors_table: self.colors_table.geometry(),
            self.sampleType_table: self.sampleType_table.geometry(),
            self.formationStyle_lable: self.formationStyle_lable.geometry(),
            self.sampleType_label: self.sampleType_label.geometry(),
            self.sampleType_combox: self.sampleType_combox.geometry(),
            self.sampleChangesWithDepth_label: self.sampleChangesWithDepth_label.geometry(),
            self.changePlotSize_label: self.changePlotSize_label.geometry(),
            self.changePlotSizeSmaller_button: self.changePlotSizeSmaller_button.geometry(),
            self.changePlotSizeLarger_button: self.changePlotSizeLarger_button.geometry(), 
            self.openSecondWindow_button: self.openSecondWindow_button.geometry(),
            self.verticalExaggeration_textbox: self.verticalExaggeration_textbox.geometry(),
            self.styleGuide_label: self.styleGuide_label.geometry(),
            self.verticalExaggeration_label: self.verticalExaggeration_label.geometry(),
            self.totalDepth_label: self.totalDepth_label.geometry(),
            self.totalDepth_texbox: self.totalDepth_texbox.geometry()
            }
        
        self.graph_window = None
        self.open_second_window()
        
        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Josh\'s Cross Section Tool"))
        self.selectFile_button.setText(_translate("MainWindow", "Select File"))
        self.mainUpdate_button.setText(_translate("MainWindow", "Update Figure"))
        self.mainUpdate_button.setShortcut(_translate("MainWindow", "Return"))
        self.changePlotSize_label.setText(_translate("MainWindow", "Change Plot Size"))
        self.changePlotSizeSmaller_button.setText(_translate("MainWindow", "Smaller"))
        self.changePlotSizeLarger_button.setText(_translate("MainWindow", "Larger"))
        self.openSecondWindow_button.setText(_translate('MainWindow', "Open Second Window"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Main"))
        self.formationsUpdate_button.setText(_translate("MainWindow", "Update Figure"))
        self.formationsUpdate_button.setShortcut(_translate("MainWindow", "Return"))
        self.TopDepthOfFormations_label.setText(_translate("MainWindow", "Top Depth of Formations"))
        self.formationPolygons_label.setText(_translate("MainWindow", "Formation Polygons"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Formations"))
        self.styleUpdate_button.setText(_translate("MainWindow", "Update Figure"))
        self.styleUpdate_button.setShortcut(_translate("MainWindow", "Return"))
        self.formationStyle_lable.setText(_translate("MainWindow", "Formation Style"))
        self.sampleType_label.setText(_translate("MainWindow", "Sample Type"))
        self.sampleChangesWithDepth_label.setText(_translate("MainWindow", "Does sample type change with depth?"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Style"))
        self.menuFile.setTitle(_translate("MainWindow", "Cross Section"))
        self.menuSave.setTitle(_translate("MainWindow", "Save"))
        self.menuExport_Data.setTitle(_translate("MainWindow", "Export Data"))
        self.actionSave_as_PDF.setText(_translate("MainWindow", "Save as PDF"))
        self.actionSave_as_PNG.setText(_translate("MainWindow", "Save as PNG"))
        self.actionSave_as_JPEG.setText(_translate("MainWindow", "Save as JPEG"))
        self.actionSave_as_TIFF.setText(_translate("MainWindow", "Save as TIFF"))
        self.actionSave_as_EPS.setText(_translate("MainWindow", "Save as EPS"))
        self.actionSave_as_DXF.setText(_translate('MainWindow', 'Save as DXF'))
        self.actionSave_as_AutoCadDXF.setText(_translate('MainWindow', 'Save as AutoCad DXF'))
        self.actionExport_as_Excel.setText(_translate("MainWindow", "Export as Excel"))
        self.actionExport_as_CSV.setText(_translate("MainWindow", "Export as CSV"))
        self.verticalExaggeration_label.setText(_translate("MainWindow", 'Vertical Exaggeration'))
        self.totalDepth_label.setText(_translate("MainWindow", "Max Total Depth"))
        
        self.styleGuide_label.setText(_translate("Mainwindow", " - x = value/plot normally \n - p = Pinch \n - f = Fade \n - c = Connect \n - n = no value" ))
        
        
#######################################################################################################################################################################

# =============================================================================
#region Main Page Widgets
# =============================================================================
   
    def limit_TD(self):
        """
        Limits the TD of wells to the number entered
        """
        self.max_TD = -int(self.totalDepth_texbox.toPlainText())
        original_TD_copy = self.original_TD.copy()
        
        deeper_than_forced_TD = original_TD_copy < self.max_TD
        shallower_than_forced_TD = original_TD_copy > self.max_TD
        
        if np.any(deeper_than_forced_TD):
            self.formation_polygons[-1][1, deeper_than_forced_TD] = self.max_TD
        if np.any(shallower_than_forced_TD):
            self.formation_polygons[-1][1, shallower_than_forced_TD] = original_TD_copy[shallower_than_forced_TD]

        
       
    def hide_formation_labels(self):
        """ 
        Hides the formation labels next to the plot in the main window if there is nothing plotted
        """
        
        for color_label in self.formation_color_label_list:
            color_label.hide()
        for name_label in self.formation_name_labels_list:
            name_label.hide()
            
            
    def open_second_window(self):
        """ 
        Opens a second window for plot demonstration
        """
        
        if self.graph_window is None:
            self.graph_window = GraphWindow()
        self.graph_window.show()
  
    
    def bigger_fig(self):
        """ 
        Increases the dimensions of the figure when the button is pressed
        """
        self.figsize[1] += 1
        
        
    def smaller_fig(self):
        """ 
        Decreases the dimensions of the figure when the button is pressed
        """
        self.figsize[1] -= 1


    def teeth_of_fade(self):
        """
        Takes the number inputted into the textbox and converts that into the values required to create that many teeth
        in the fade
        """
        
        #Collects the row and index of the fade that is being edited
        row = self.adjustPinchFadeFormation_combox.currentData()
        index = self.adjustPinchFadeIndex_combox.currentIndex()
        #Collects the desired tooth number
        current_teeth_num = int(self.numberOfTeeth_textbox.toPlainText())
        
        #Changes the values used for that fade. Each fade has two values [linspace number, number of tiles]
        self.number_of_teeth_dict[row][0+(2*index)] = (current_teeth_num * 2) - 1
        self.number_of_teeth_dict[row][1+(2*index)] = current_teeth_num - 1
        
        
        
    def update_visibility(self):
        """
        Shows or hides the number of teeth textbox depending on the dropdown selections.
        This is to avoid confusion and programmatic issues with number being entered when they shouldnt be.        
        """    
        
        # Get the current values
        fade_text = self.adjustPinchFade_combox.currentText()
        fade_index_data = self.adjustPinchFadeIndex_combox.currentData()

        # Check if currently fade is being edited and that there is a fade to edit in this formation. Then updates visibility
        if fade_text == "Fade" and fade_index_data != "No Fade":
            self.numberOfTeeth_textbox.show()
            self.numberOfTeeth_label.show()
        else:
            self.numberOfTeeth_textbox.hide()
            self.numberOfTeeth_label.hide()
    

    def pinch_fade_slider(self, value):
        """ 
        Takes the value from the adjustPinchFade_slider and  changes the value of the pinch or fade at the selected formation and index.
        This function automatically collects the value from the slider in the 'value' variable
        """
        
        #Collects the style being edited, its row and index. 
        pinch_or_fade = self.adjustPinchFade_combox.currentText()
        row = self.adjustPinchFadeFormation_combox.currentData()
        index = self.adjustPinchFadeIndex_combox.currentIndex()
        
        #Adds an index correction so that it accesses the correct value in the list [left_borehole_distance, middle_distance, right_borehole_distance]
        #Lists of the previous format are all concatenated so that a single formation has one list containing all the needed values 
        index_correction = 3*index
        
        #Checks for the style being edited and changes the middle_distance value associated with that point
        if pinch_or_fade == 'Pinch':
            self.pinch_correction_dict[row][1+index_correction] = value
        else:
            self.fade_correction_dict[row][1+index_correction] = value
        #Changes the status of the slider change for the flow of data later
        self.pinchFadeslider_changed = True
        
        
    def pinch_fade_exists(self):
        """ 
        Checks the current value of the pinch fade correction combo box. Activates or deactivates the pinch fade slider if no pinch or fade is available.
        """
        
        text = self.adjustPinchFadeIndex_combox.currentText()
        if text == 'No Pinch' or text == 'No Fade':
            self.adjustPinchFade_slider.setEnabled(False)
        else:
            self.adjustPinchFade_slider.setEnabled(True)


    def pinch_fade_slider_setup(self):
        """
        Populates the labels above the slider and also creates the min, max and pointer values for the slider when a pinch or fade is selected.
        The left side of the slider if the left borehole's distance from the start of the cross section, the right side is the right borehole's distance
        The pointer value is by default the middle between the two, but will stay wherever you move it
        """
        
        #Gathers the row, type of style being edited and the data of the selection. The data can either be an index or a string
        current_value = self.adjustPinchFadeIndex_combox.currentData()
        pinch_or_fade = str(self.adjustPinchFade_combox.currentText())
        row = self.adjustPinchFadeFormation_combox.currentData()
        
        #Clears the labels and the ticks on the slider
        self.adjustPinchFadeMin_label.setText('')
        self.adjustPinchFadeMax_label.setText('')
        self.adjustPinchFade_slider.setTickPosition(QtWidgets.QSlider.NoTicks)
       
        if current_value in ['No Pinch', 'No Fade']:
            return  # Skip the rest if there's no pinch or fade
        
        else: #Creates an index correction so that it accesses the correct value in the list [left_borehole_distance, middle_distance, right_borehole_distance]
              #Lists of the previous format are all concatenated so that a single formation has one list containing all the needed values
            current_value = int(current_value)
            value_correction = 3 * current_value
            
        if pinch_or_fade == 'Pinch':
            self.adjustPinchFade_slider.blockSignals(True)  # Block signals to avoid accidentally changing the middle value
            self.adjustPinchFade_slider.setMinimum(int(self.pinch_correction_dict[row][0 + value_correction]))
            self.adjustPinchFade_slider.setMaximum(int(self.pinch_correction_dict[row][2 +value_correction ]))
            self.adjustPinchFade_slider.setValue(int(self.pinch_correction_dict[row][1 + value_correction]))
            self.adjustPinchFade_slider.blockSignals(False)  # Unblock signals
            
            self.adjustPinchFade_slider.setTickPosition(QtWidgets.QSlider.TicksBelow) #Adds ticks below the slider
            
            #Adds the distance to the labels above the slider
            self.adjustPinchFadeMin_label.setText(str(self.pinch_correction_dict[row][0 + value_correction]) + ' ft')
            self.adjustPinchFadeMax_label.setText(str(self.pinch_correction_dict[row][2 + value_correction]) + ' ft')
            
            #Automatically adjust the size of the labels to fit the text
            self.adjustPinchFadeMin_label.adjustSize()
            self.adjustPinchFadeMax_label.adjustSize()
        else:
            self.adjustPinchFade_slider.blockSignals(True)  # Block signals to avoid accidentally changing the middle value
            self.adjustPinchFade_slider.setMinimum(int(self.fade_correction_dict[row][0 + value_correction]))
            self.adjustPinchFade_slider.setMaximum(int(self.fade_correction_dict[row][2 + value_correction]))
            self.adjustPinchFade_slider.setValue(int(self.fade_correction_dict[row][1 + value_correction]))
            self.adjustPinchFade_slider.blockSignals(False)  # Unblock signals
            
            self.adjustPinchFade_slider.setTickPosition(QtWidgets.QSlider.TicksBelow) #Adds ticks below the slider
            
            #Adds the distance to the labels above the slider
            self.adjustPinchFadeMin_label.setText(str(self.fade_correction_dict[row][0 + value_correction]) + ' ft')
            self.adjustPinchFadeMax_label.setText(str(self.fade_correction_dict[row][2 + value_correction]) + ' ft')
            
            #Automatically adjust the size of the labels to fit the text
            self.adjustPinchFadeMin_label.adjustSize()
            self.adjustPinchFadeMax_label.adjustSize()
            

    def pinch_fade_index_combox(self):
        """
        Populates the pinch fade index dropdown with the appropriate values. It will fill with W# and direction if a pinch or fade exists for that formation and
        will fill with No Fade or No Pinch if not
        """
        
        #Clear the box so that the only options are the new options
        #If this is not done, options will continue to add even if a new file is selected
        self.adjustPinchFadeIndex_combox.clear()
        
        #Collect the style being edited and the formation being edited
        pinch_or_fade = str(self.adjustPinchFade_combox.currentText())
        row = self.adjustPinchFadeFormation_combox.currentData()
        
        #If the style is pinch then check the length of the the list for that formation
        if pinch_or_fade == 'Pinch':
            current_list = self.pinch_correction_dict[row] #Gather the data list
            well_list = self.pinch_well_dict[row] #Gather the well numbers associated
            number_of_pinches = int(len(current_list) / 3) #Calculate how many pinches are in this formation. Rounds to the nearest integer 
                                                           
            if number_of_pinches == 0: #If there is no pinch the previous calculation will round down to 0
                self.adjustPinchFadeIndex_combox.addItem('No Pinch', 'No Pinch') # This creates an entry with the text and data 'No Pinch'
            else:
                for pinch in range(number_of_pinches): #Loops for each pinch that is in that formation
                    self.adjustPinchFadeIndex_combox.addItem(str(well_list[pinch]), str(pinch)) # Creates an entry with the text of W-# direction, and data being an index
        else: # If the style is not pinch then it must be fade                                  # This allows a better understanding of what is being edited and still creates an easy way to acess the correct list location with the index
            current_list = self.fade_correction_dict[row] #Gather the data list
            well_list = self.fade_well_dict[row] #Gather the well numbers associated
            number_of_fades = int(len(current_list) / 3) #Calculate how many fades are in this formation. Rounds to the nearest integer
            if number_of_fades == 0:
                self.adjustPinchFadeIndex_combox.addItem('No Fade', 'No Fade') # This creates an entry with the text and data 'No Fade'
            else:
                for fade in range(number_of_fades):
                    self.adjustPinchFadeIndex_combox.addItem(str(well_list[fade]), str(fade)) # Creates an entry with the text of W-# direction, and data being an index
                                                                                                # This allows a better understanding of what is being edited and still creates an easy way to acess the correct list location with the index
        self.pinch_fade_slider_setup() #Calls the function to initially set up the slider


    def create_pinch_fade_correction_dict(self):
        """ 
        Creates dictionaries with pinch/fade lists, also creates well dictionaries for both and a tooth number dictionary.
        These dictionaries are locations necessary for the user to edit these features in the front end and create some sort of change in the plot
        """
        
        # Defining all the empty dictionaries
        self.pinch_correction_dict = {}
        self.fade_correction_dict = {}
        
        self.pinch_well_dict = {}
        self.fade_well_dict = {}
        
        self.number_of_teeth_dict = {}
        
        #Loop for each row(formation) of the style array
        for row in range(self.style_array.shape[0]):
            #Create empty lists for each row that can be used to assign to each row(formation) in the dictionary
            pinch_list = []
            fade_list = []
            fade_well_list = []
            pinch_well_list = []
            number_of_teeth_list = []
            
            #Loop for each column(well) in the style array
            for col in range(self.style_array.shape[1]):
                
                if self.style_array[row, col] == 'f': #Check for fading
                    direction = check_left_right(self.style_array[row], col) #Collect the direction to decide which locations values to add in what order
                    
                    if direction == 'left':
                        fade_list.append(self.locations[col-1]) #Add the left well first 
                        middle = (self.locations[col-1] + self.locations[col]) / 2 #Calculate the midpoint
                        fade_list.append(middle) #Add the midpoint second
                        fade_list.append(self.locations[col]) #Add the right well third
                        fade_well_list.append('W-'+ str(self.w_num[col]) + ' Left') #Create a string with the form W-# direction for ease of use to the user
                        number_of_teeth_list.append(7) # Add a default value for the teeth
                        number_of_teeth_list.append(3) # Add a default value for the teeth
                        
                    elif direction == 'right':
                        fade_list.append(self.locations[col]) #Add the left well first
                        middle = (self.locations[col] + self.locations[col+1]) / 2 #Calculate the midpoint
                        fade_list.append(middle) #Add the midpoint second
                        fade_list.append(self.locations[col+1]) #Add the right well third
                        fade_well_list.append('W-'+ str(self.w_num[col]) + ' Right') #Create a string with the form W-# direction for ease of use to the user
                        number_of_teeth_list.append(7) # Add a default value for the teeth
                        number_of_teeth_list.append(3) # Add a default value for the teeth
                        
                    elif direction == 'both': #In the case of both, the left point will be added first so that it is easy to read options as top-down = left-right
                        fade_list.append(self.locations[col-1]) #Add the left well first
                        middle = (self.locations[col-1] + self.locations[col]) / 2 #Calculate the midpoint
                        fade_list.append(middle) #Add the midpoint second
                        fade_list.append(self.locations[col]) #Add the right well third
                        fade_well_list.append('W-'+ str(self.w_num[col]) + ' Left') #Create a string with the form W-# direction for ease of use to the user
                        number_of_teeth_list.append(7) # Add a default value for the teeth
                        number_of_teeth_list.append(3) # Add a default value for the teeth
                        
                        fade_list.append(self.locations[col]) #Add the left well first
                        middle = (self.locations[col] + self.locations[col+1]) / 2 #Calculate the midpoint
                        fade_list.append(middle) #Add the midpoint second
                        fade_list.append(self.locations[col+1]) #Add the right point third
                        fade_well_list.append('W-'+ str(self.w_num[col]) + ' Right') #Create a string with the form W-# direction for ease of use to the user
                        number_of_teeth_list.append(7) # Add a default value for the teeth
                        number_of_teeth_list.append(3) # Add a default value for the teeth
                        
                elif self.style_array[row, col] == 'p': #Check for pinching
                    direction = check_left_right(self.style_array[row], col) #Collect the direction to decide which locations values to add in what order
                    
                    if direction == 'left':
                        pinch_list.append(self.locations[col-1]) #Add the left point first
                        middle = (self.locations[col-1] + self.locations[col]) / 2 #Calculate the midpoint
                        pinch_list.append(middle) #Add the midpoint second
                        pinch_list.append(self.locations[col]) #Add the right point third
                        pinch_well_list.append('W-'+ str(self.w_num[col]) + ' Left') #Create a string with the form W-# direction for ease of use to the user
    
                    elif direction == 'right':
                        pinch_list.append(self.locations[col]) #Add the left point first
                        middle = (self.locations[col] + self.locations[col+1]) / 2
                        pinch_list.append(middle) #Add the midpoint second
                        pinch_list.append(self.locations[col+1]) #Add the right point third
                        pinch_well_list.append('W-'+ str(self.w_num[col]) + ' Right') #Create a string with the form W-# direction for ease of use to the user
    
                    elif direction == 'both': #In the case of both, the left point will be added first so that it is easy to read options as top-down = left-right
                        pinch_list.append(self.locations[col-1]) #Add the left point first
                        middle = (self.locations[col-1] + self.locations[col]) / 2
                        pinch_list.append(middle) #Add the midpoint second
                        pinch_list.append(self.locations[col]) #Add the right point third
                        pinch_well_list.append('W-'+ str(self.w_num[col]) + ' Left') #Create a string with the form W-# direction for ease of use to the user
    
                        pinch_list.append(self.locations[col]) #Add the left point first
                        middle = (self.locations[col] + self.locations[col+1]) / 2
                        pinch_list.append(middle) #Add the midpoint second
                        pinch_list.append(self.locations[col+1]) #Add the right point third
                        pinch_well_list.append('W-'+ str(self.w_num[col]) + ' Right') #Create a string with the form W-# direction for ease of use to the user

            # Check if there is no pinching or fading in the formation and add that to the dictionary
            if len(pinch_list) == 0:
                pinch_list.append('No Pinch')
                pinch_well_list.append("No Pinch")
            if len(fade_list) == 0:
                fade_list.append('No Fade')
                fade_well_list.append('No Fade')
                number_of_teeth_list.append('No Fade')
            
            #Create a key (row number) and definition (list) for each formation
            self.pinch_correction_dict[row] = pinch_list
            self.fade_correction_dict[row] = fade_list
            
            self.pinch_well_dict[row] = pinch_well_list
            self.fade_well_dict[row] = fade_well_list
            
            self.number_of_teeth_dict[row] = number_of_teeth_list
            
    
    def formation_polygons_combo_box(self):
        """ 
        Populates the formation polygons and pinch fade formations dropdowns with formation names from the selected file
        """
        
        #Clear the dropdowns so that values can be added
        self.formationPolygons_combox.clear()
        self.adjustPinchFadeFormation_combox.clear()
        index=0 #Initiate a value that will be used as the data value for the dropdowns
        for form in self.formations_list[:-1]: #Exclude the last value in the formation list because that is the bottom or TD
            self.formationPolygons_combox.addItem(form, index) #Add the formation to the dropdown with the index as the data
            self.adjustPinchFadeFormation_combox.addItem(form, index) #Add the formation to the dropdown with the index as the data
            index += 1 #Increment the index
            
            
    def create_formation_polygons_table(self):
        """ 
        Populates the formation polygons table with the top, bottom and distance values of a polygon
        """
        
        #Pulls the currently selected formation and its polygon
        index = self.formationPolygons_combox.currentData()
        polygon = self.formation_polygons[index]
        
        #Creates the shape the table needs to be to fit the polygon
        self.formationPolygons_table.setRowCount(polygon.shape[0])
        self.formationPolygons_table.setColumnCount(polygon.shape[1])
        
        #Labels the rows
        self.formationPolygons_table.setVerticalHeaderLabels(['Formation Top', 'Formation Bottom', 'Distance'])
        
        column_titles = []
        for column in range(polygon.shape[1]):
            column_titles.append(str(column))
            
        for index, location in enumerate(self.locations):
            title_location = np.where(polygon[-1] == location)[0][0]
            
            column_titles[title_location] = self.w_num_headers[index]
        
        
        self.formationPolygons_table.setHorizontalHeaderLabels(column_titles)
        
        
            
        #Loops through the polygon array
        for i in range(polygon.shape[0]):
            for j in range(polygon.shape[1]):
                item = str(polygon[i, j])
                self.formationPolygons_table.setItem(i, j, QtWidgets.QTableWidgetItem(item)) #Adds each value to the table
                
        self.formationPolygons_table.setFont(self.table_font) #Set the font size larger
                
                
    def update_formation_polygon(self):
        """ 
        Updates the formation polygon array with any changes made by the user
        """
        
        #Pulls the currently selected formation and its polygon
        index = self.formationPolygons_combox.currentData()
        polygon = self.formation_polygons[index]
        
        #Loops through the polygon array
        for i in range(polygon.shape[0]):
            for j in range(polygon.shape[1]):
                item = self.formationPolygons_table.item(i, j) #Pulls the item in the polygon table
                polygon[i, j] = float(item.text()) #Converts it to a usable value and assigns it to the correct location
        

    def create_formations_table(self):
        """ 
        Populates the Top Depth of Formations table with data from the selected excel sheet
        """
        
        #Creates the shape the table needs to be for the data
        self.formations_table.setRowCount(self.formations_array.shape[0]+1)
        self.formations_table.setColumnCount(self.formations_array.shape[1])
        
        #Creates the W-# labels for each column of the table
        self.w_num_headers = [ "W-" + str(w) for w in self.w_num]
        row_headers = self.formations_list #Collects formation names to use as row labels
        row_headers.append("Distance") #Labels the last column as Distance
        
        #Sets the labels for the rows and columns
        self.formations_table.setVerticalHeaderLabels(self.formations_list)
        self.formations_table.setHorizontalHeaderLabels(self.w_num_headers)
        
        #Loops through the formations array
        for i in range(self.formations_array.shape[0]):
            for j in range(self.formations_array.shape[1]):
                item = str( self.formations_array[i,j]) 
                self.formations_table.setItem(i, j, QtWidgets.QTableWidgetItem(item)) #Add the values from the array to the table
        
                dist = str(self.locations[j])
                self.formations_table.setItem(self.formations_array.shape[0], j,  QtWidgets.QTableWidgetItem(dist)) #Add location values to the last row
                
        self.formations_table.setFont(self.table_font) #Set the font size larger
                
                
    def update_formations_array(self):
        """ 
        Updates the formation tops array when the Top Depth of Formations table is changed. That way any value that is changed within the program can be
        reflected in an exported excel sheet and in the plot
        """
        
        #Loop through the formation array
        for row in range(self.formations_array.shape[0]):
            for col in range(self.formations_array.shape[1]):
                item = self.formations_table.item(row, col) #Pulls the item in the formation table
                self.formations_array[row, col] = float(item.text()) #Converts it to a usable value and assigns it to the correct location
            
                
    def create_style_table(self):
        """
        Populates the data for formation style, sample type and colors tables.
        """
        
        #Create the table shape required for the data
        self.style_table.setRowCount(self.style_array.shape[0])
        self.style_table.setColumnCount(self.style_array.shape[1])
        
        #Labels the rows and columns with previously created labels or formations and W-#
        self.style_table.setVerticalHeaderLabels(self.formations_list)
        self.style_table.setHorizontalHeaderLabels(self.w_num_headers)
        
        #Loops through the style_array
        for i in range(self.style_array.shape[0]):
            for j in range(self.style_array.shape[1]):
                self.style_table.setItem(i, j, QtWidgets.QTableWidgetItem(self.style_array[i, j])) #Add style items to the 
        
        self.style_table.setFont(self.table_font) #Set the font size larger
        
        #Creates the table shape required to have 1 color for each formation
        self.colors_table.setRowCount(self.style_array.shape[0]-1)
        self.colors_table.setColumnCount(1)
        
        #Labels the formations and the column
        self.colors_table.setHorizontalHeaderLabels(["Formations Colors"])
        self.colors_table.setVerticalHeaderLabels(self.formations_list[:-1])
        self.colors_table.setColumnWidth(0, 170) #Sets the column width to fit the widget
        
        #Creates the sample type table with 1 row and the necessary columns
        self.sampleType_table.setRowCount(1)
        self.sampleType_table.setColumnCount(self.style_array.shape[1])
        
        #Labels each W-# and the row
        self.sampleType_table.setHorizontalHeaderLabels(self.w_num_headers)
        self.sampleType_table.setVerticalHeaderLabels(['Sample Type'])
        
        self.sampleType_table.setFont(self.table_font) #Set the font size larger
        
        #Loops through the style array columns
        for col in range(self.style_array.shape[1]):
            samp_type = str(self.core_or_cuttings[col]) #Pulls a values from each index in the sample type array
            self.sampleType_table.setItem(0, col, QtWidgets.QTableWidgetItem(samp_type)) #Adds these to the table
            
                
    def update_style_array(self):
        """ 
        Updates the style array with changes made by the user
        """
        
        #Loops through the style array
        for row in range(self.style_array.shape[0]):
            for col in range(self.style_array.shape[1]):
                item = self.style_table.item(row, col) #Pulls an item from the table
                self.style_array[row, col] = str(item.text()) #Converts the item to a usable value and inserts it into the appropriate location
                
                
    def update_colors_list(self):
        """ 
        Updates the color list if any colors are added by the user
        """
        
        #Uses try to avoid errors if colors are not added
        try:
            #Loop through the formations
            for row in range(self.style_array.shape[0]-1):
                color = self.colors_table.item(row, 0) # Pulls the colors from the table 
                self.plotting_colors[row] = str(color.text()) # Adds the colors to the list
        except:
            self.colors_list = [] #Clear the list if errors are encountered
            pass #If any error is encountered then just move on and ignore all this
            
# =============================================================================
#region Sample Type
# =============================================================================
    
    def sample_changes(self):
        """ 
        This expands the sample type table to allow changes in sample type at all formation contacts or collapses the table if not
        """

        #If the selection if yes then the current data is True
        if self.sampleType_combox.currentData():
            #Creates the table size needed for
            self.sampleType_table.setRowCount(self.style_array.shape[0])
            self.sampleType_table.setColumnCount(self.style_array.shape[1])
            
            #Labels the rows and columns
            self.sampleType_table.setVerticalHeaderLabels(self.formations_list)
            self.sampleType_table.setHorizontalHeaderLabels(self.w_num_headers)
            
            #Loops through the table
            for row in range(self.style_array.shape[0]):
                for col in range(self.style_array.shape[1]):
                    samp_type = str(self.core_or_cuttings[col]) 
                    self.sampleType_table.setItem(row, col, QtWidgets.QTableWidgetItem(samp_type)) #Adds items to the table
        else:
            #Creates the sample type table with 1 row and the necessary columns
            self.sampleType_table.setRowCount(1)
            self.sampleType_table.setColumnCount(self.style_array.shape[1])
            
            #Labels each W-# and the row
            self.sampleType_table.setHorizontalHeaderLabels(self.w_num_headers)
            self.sampleType_table.setVerticalHeaderLabels(['Sample Type'])
            
            #Loops through the style array columns
            for col in range(self.style_array.shape[1]):
                samp_type = str(self.core_or_cuttings[col]) #Pulls a values from each index in the sample type array
                self.sampleType_table.setItem(0, col, QtWidgets.QTableWidgetItem(samp_type)) #Adds these to the table
              
                
    def sample_type_table_to_array(self):
        """
        This creates an array for sample type by pulling from the sample type table
        """
        
        rows = self.sampleType_table.rowCount()
        cols = self.sampleType_table.columnCount()
        
        if rows > 1:
            self.core_or_cuttings = np.empty((rows, cols), dtype=object)
            for row in range(rows):
                for col in range(cols):
                    item = self.sampleType_table.item(row, col)
                    self.core_or_cuttings[row, col] = item.text()
        else:
            self.core_or_cuttings = np.empty(cols, dtype=object)
            for col in range(cols):
                item = self.sampleType_table.item(0, col)
                self.core_or_cuttings[col] = item.text()
                
    # =============================================================================
    #region Contact Line Arrays
    # =============================================================================
    def create_contact_line_arrays(self):
        """ 
        Creates 2 lists of line segments for solid and dashed contacts. Each line segment is created from the top row of formation polygons
        """
        
        self.dashed_contacts = []
        self.solid_contacts = []
        
        
        for row in range(self.style_array.shape[0]-1):
            for index in range(len(self.core_or_cuttings)-1):
                if self.core_or_cuttings[index] == 'CORE':
                    linestyle = '-'
                else:
                    linestyle = '--'
            
                if self.core_or_cuttings[index] != self.core_or_cuttings[index+1]: #Change in linestyle
                
                    # Checks for interlocking fades
                    if self.style_array[row, index] == 'f' and (self.style_array[row+1, index-1] == 'f' or self.style_array[row+1, index+1] == 'f'):
                        direction = check_left_right(self.style_array[row], index)
                        
                        below_left_direction = check_left_right(self.style_array[row+1], index-1)
                        below_right_direction = check_left_right(self.style_array[row+1], index+1)
                        
                        if direction == 'right':
                            
                            if below_right_direction == 'both' or below_right_direction == 'left':
                                left_distance = self.locations[index] 
                                left_elev_index = np.where(self.formation_polygons[row][-1] == left_distance)
                                left_elev = self.formation_polygons[row][0, left_elev_index][0,0]
                                
                                mask = (self.formation_polygons[row+1][-1] > self.locations[index]) & (self.formation_polygons[row+1][-1] < self.locations[index+1])
                                
                                right_elev = self.formation_polygons[row+1][0][mask][-1]
                                right_distance = self.formation_polygons[row+1][-1][mask][-1]
                                
                                line_segment = np.array([left_elev, right_elev])
                                distance_segment = np.array([left_distance, right_distance])
                                
                                line_stack = np.vstack((line_segment, distance_segment))
                                
                                if linestyle == '-':
                                    self.solid_contacts.append(line_stack)
                                else:
                                    self.dashed_contacts.append(line_stack)
                                
                                
                        elif direction == 'left':
                            
                            if below_left_direction == 'both' or below_left_direction == 'right':
                                right_distance = self.locations[index]
                                right_elev_index = np.where(self.formation_polygons[row][-1] == right_distance)
                                right_elev = self.formation_polygons[row][0, right_elev_index][0,0]
                                
                                mask = (self.formation_polygons[row+1][-1] > self.locations[index-1]) & (self.formation_polygons[row+1][-1] < self.locations[index])
                                
                                left_elev = self.formation_polygons[row+1][0][mask][0]
                                left_distance = self.formation_polygons[row+1][-1][mask][0]
                                
                                line_segment = np.array([left_elev, right_elev])
                                distance_segment = np.array([left_distance, right_distance])
                                
                                line_stack = np.vstack((line_segment, distance_segment))
                                
                                
                                if linestyle == '-':
                                    self.solid_contacts.append(line_stack)
                                else:
                                    self.dashed_contacts.append(line_stack)
                                
                                
                        elif direction == 'both':
                            if below_right_direction == 'both' or below_right_direction == 'left':
                                pass
                                
                            if below_left_direction == 'both' or below_left_direction == 'right':
                                pass
                    
                    
                    if self.style_array[row, index] == 'n':
                        
                        if index == len(self.core_or_cuttings)-2:
                            if linestyle == '-':
                                linestyle = '--'
                                mask = (self.formation_polygons[row][-1] > self.locations[index]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                                line_segment = self.formation_polygons[row][0][mask]
                                distance_segment = self.formation_polygons[row][-1][mask]
                            else:
                                linestyle = '-'
                                mask = (self.formation_polygons[row][-1] > self.locations[index]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                                line_segment = self.formation_polygons[row][0][mask]
                                distance_segment = self.formation_polygons[row][-1][mask]
                        else:       
                            continue
                    
                    
                    elif self.style_array[row, index] == 'f' or self.style_array[row, index] == 'p':
                        direction = check_left_right(self.style_array[row], index)
                        
                        
                        if direction == 'right':
                            #Create a mask where the values you want are starting at the left, but less than the right
                            mask = (self.formation_polygons[row][-1] >= self.locations[index]) & (self.formation_polygons[row][-1] < self.locations[index+1])
                            line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                            
                        elif direction == 'both':
                            mask = (self.formation_polygons[row][-1] > self.locations[index-1]) & (self.formation_polygons[row][-1] < self.locations[index+1])
                            line_segment = line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                            
                        else: #If direction is left
                            #Start at greater than the borehole before this one, and end halfway to the next borehole
                            mask = (self.formation_polygons[row][-1] > self.locations[index-1]) & (self.formation_polygons[row][-1] < self.locations[index+1])
                            line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                            
                            mask = (self.formation_polygons[row][-1] >= self.locations[index]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                                
                            temp_arr = self.formation_polygons[row][0][mask]
                            temp_arr_distance = self.formation_polygons[row][0][mask]
                            
                            left_elev = temp_arr[0]
                            right_elev = temp_arr[-1]
                            
                            left_location = self.locations[index]
                            right_location = self.locations[index+1]
                            
                            
                            midpoint = (right_location + left_location) / 2
                            slope = (right_elev - left_elev) / (right_location - left_location)
                                
                            yintercept = right_elev - (slope*right_location)
                                
                            midpoint_elev = (slope * midpoint) + yintercept
                            
                            
                            line_segment = np.append(line_segment, midpoint_elev)
                            distance_segment = np.append(distance_segment, midpoint)
                            
                            #Create a line segment that is the opposite linestyle of the current line segment
                            second_line_segment = np.array([midpoint_elev, right_elev])
                            second_distance_segment = np.array([midpoint, right_location])
                            second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                            #Add that line segment to the approriate list
                            if linestyle == '-':
                                self.dashed_contacts.append(second_line_stack)
                                    
                            else:
                                self.solid_contacts.append(second_line_stack)
                                
                            
                            #Do the whole slope calculation and create the mid point the line will stop at
                            if self.style_array[row-1, index] == 'f' or self.style_array[row-1, index] == 'p':
                                # Use the last point of the pinch or fade to end the line at
                                mask = (self.formation_polygons[row-1][-1] > self.locations[index]) & (self.formation_polygons[row-1][-1] < self.locations[index+1])
                                temp_arr = self.formation_polygons[row-1][0][mask]
                                temp_arr_distance = self.formation_polygons[row-1][-1][mask]
                                
                                line_segment = np.append(line_segment, temp_arr[-1])
                                distance_segment = np.append(distance_segment, temp_arr_distance[-1])
                                
                    
                    else:
                        #The line segment if its just a normal connection or a user defined connection
                        #Start at the left well and go halfway to the right well
                        mask = (self.formation_polygons[row][-1] >= self.locations[index]) & (self.formation_polygons[row][-1] < self.locations[index+1])
                        line_segment = self.formation_polygons[row][0][mask]
                        distance_segment = self.formation_polygons[row][-1][mask]
                        
                        #Do the whole slope calculation and create the mid point the line will stop at
                        if self.style_array[row-1, index] == 'f' or self.style_array[row-1, index] == 'p':
                            above_direction = check_left_right(self.style_array[row-1], index)
                            # Use the last point of the pinch or fade to end the line at
                            
                            if above_direction == 'right':
                                mask = (self.formation_polygons[row-1][-1] > self.locations[index]) & (self.formation_polygons[row-1][-1] < self.locations[index+1])
                                temp_arr = self.formation_polygons[row-1][0][mask]
                                temp_arr_distance = self.formation_polygons[row-1][-1][mask]
                                
                            
                                line_segment = np.append(line_segment, temp_arr[-1])
                                distance_segment = np.append(distance_segment, temp_arr_distance[-1])
                                
                                #Create a line segment that is the opposite linestyle of the current line segment
                                second_line_segment = np.array([temp_arr[-1], self.formation_polygons[row][0, index+1]])
                                second_distance_segment = np.array([temp_arr_distance[-1], self.formation_polygons[row][-1, index+1]])
                                second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                                #Add that line segment to the approriate list
                                if linestyle == '-':
                                    self.dashed_contacts.append(second_line_stack)
                                else:
                                    self.solid_contacts.append(second_line_stack)
                                    
                            elif above_direction == 'both':
                                mask = (self.formation_polygons[row-1][-1] > self.locations[index-1]) & (self.formation_polygons[row-1][-1] < self.locations[index+1])
                                temp_arr = self.formation_polygons[row-1][0][mask]
                                temp_arr_distance = self.formation_polygons[row-1][-1][mask]
                                
                                current_well_formation_index = np.where(self.formation_polygons[row][-1] == self.locations[index])
                                current_formation_top = self.formation_polygons[row][0, current_well_formation_index]
                                
                                line_segment = np.array([temp_arr[0], current_formation_top[0, 0], temp_arr[-1]])
                                
                                distance_segment = np.append(temp_arr_distance[0], self.locations[index])
                                distance_segment = np.append(distance_segment, temp_arr_distance[-1])
                                
                            
                                mask = (self.formation_polygons[row-1][-1] > self.locations[index]) & (self.formation_polygons[row-1][-1] < self.locations[index+1])
                                #Create a line segment that is the opposite linestyle of the current line segment
                                temp_arr = self.formation_polygons[row-1][0][mask]
                                temp_arr_distance = self.formation_polygons[row-1][-1][mask]
                                
                                right_well_index = np.where(self.formation_polygons[row][-1] == self.locations[index+1])
                                right_well_formation_top = self.formation_polygons[row][0, right_well_index]
                                
                                
                                
                                second_line_segment = np.array([temp_arr[-1], right_well_formation_top[0,0]])
                                second_distance_segment = np.array([temp_arr_distance[-1], self.locations[index+1]])
                                second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                                #Add that line segment to the approriate list
                                if linestyle == '-':
                                    self.dashed_contacts.append(second_line_stack)
                                else:
                                    self.solid_contacts.append(second_line_stack)
                                
                                
                            else: #If above_direction is left
                                left_location = self.locations[index]
                                right_location = self.locations[index+1]
                                
                                left_formation_polygon_index = np.where(self.formation_polygons[row][-1,:] == left_location)
                                right_formation_polygon_index = np.where(self.formation_polygons[row][-1,:] == right_location)
                            
                                left_elev = self.formation_polygons[row][0, left_formation_polygon_index]
                                right_elev = self.formation_polygons[row][0, right_formation_polygon_index]
                                
                                
                                midpoint = (right_location + left_location) / 2
                                slope = (right_elev - left_elev) / (right_location - left_location)
                                yintercept = right_elev - (slope*right_location)
                                midpoint_elev = (slope * midpoint) + yintercept
                                
                                line_segment = np.append(line_segment, midpoint_elev)
                                distance_segment = np.append(distance_segment, midpoint)
                                
                                #Create a line segment that is the opposite linestyle of the current line segment
                                second_line_segment = np.array([midpoint_elev[0,0], right_elev[0, 0]])
                                second_distance_segment = np.array([midpoint, right_location])
                                second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                                #Add that line segment to the approriate list
                                if linestyle == '-':
                                    self.dashed_contacts.append(second_line_stack)
                                else:
                                    self.solid_contacts.append(second_line_stack)
                        
                        elif self.style_array[row-1, index+1] == 'f' or self.style_array[row-1, index+1] == 'p':
                            above_right_direction = check_left_right(self.style_array[row-1], index+1)
                            if above_right_direction == 'left' or above_right_direction == 'both':
                                mask = (self.formation_polygons[row-1][-1] > self.locations[index]) & (self.formation_polygons[row-1][-1] < self.locations[index+1])
                                temp_arr = self.formation_polygons[row-1][0][mask]
                                temp_arr_distance = self.formation_polygons[row-1][-1][mask]
                                
                                line_segment = np.array([line_segment[0], temp_arr[0]])
                                distance_segment = np.array([distance_segment[0], temp_arr_distance[0]])
                                
                                right_well_index = np.where(self.formation_polygons[row][-1] == self.locations[index+1])[0][0]
                                
                                if above_right_direction == 'left':
                                    right_well_index = np.where(self.formation_polygons[row][-1] == self.locations[index+1])
                                    right_formation_top = self.formation_polygons[row][0, right_well_index]
                                    
                                    #Create a line segment that is the opposite linestyle of the current line segment
                                    second_line_segment = np.array([temp_arr[0], right_formation_top[0,0]])
                                    second_distance_segment = np.array([temp_arr_distance[0], self.locations[index+1]])
                                    second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                                    #Add that line segment to the approriate list
                                    if linestyle == '-':
                                        self.dashed_contacts.append(second_line_stack)
                                    else:
                                        self.solid_contacts.append(second_line_stack)
                                
                                
                                
                                    
                            else: #Normal midpoint calculation if above_right_direction is right
                                left_location = self.locations[index]
                                right_location = self.locations[index+1]
                            
                                left_formation_polygon_index = np.where(self.formation_polygons[row][-1,:] == left_location)
                                right_formation_polygon_index = np.where(self.formation_polygons[row][-1,:] == right_location)
                        
                                left_elev = self.formation_polygons[row][0, left_formation_polygon_index]
                                right_elev = self.formation_polygons[row][0, right_formation_polygon_index]
                            
                            
                                midpoint = (right_location + left_location) / 2
                                slope = (right_elev - left_elev) / (right_location - left_location)
                                yintercept = right_elev - (slope*right_location)
                                midpoint_elev = (slope * midpoint) + yintercept
                            
                                line_segment = np.append(line_segment, midpoint_elev)
                                distance_segment = np.append(distance_segment, midpoint)
                            
                                #Create a line segment that is the opposite linestyle of the current line segment
                                second_line_segment = np.array([midpoint_elev[0,0], right_elev[0, 0]])
                                second_distance_segment = np.array([midpoint, right_location])
                                second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                                #Add that line segment to the approriate list
                                if linestyle == '-':
                                    self.dashed_contacts.append(second_line_stack)
                                else:
                                    self.solid_contacts.append(second_line_stack)
                                
                                
                                
                            
                        else: #If there is no pinch or fade
                            left_location = self.locations[index]
                            right_location = self.locations[index+1]
                            
                            left_formation_polygon_index = np.where(self.formation_polygons[row][-1,:] == left_location)
                            right_formation_polygon_index = np.where(self.formation_polygons[row][-1,:] == right_location)
                        
                            left_elev = self.formation_polygons[row][0, left_formation_polygon_index]
                            right_elev = self.formation_polygons[row][0, right_formation_polygon_index]
                            
                            
                            midpoint = (right_location + left_location) / 2
                            slope = (right_elev - left_elev) / (right_location - left_location)
                            yintercept = right_elev - (slope*right_location)
                            midpoint_elev = (slope * midpoint) + yintercept
                            
                            line_segment = np.append(line_segment, midpoint_elev)
                            distance_segment = np.append(distance_segment, midpoint)
                            
                            
                            
                            #Create a line segment that is the opposite linestyle of the current line segment
                            second_line_segment = np.array([midpoint_elev[0,0], right_elev[0, 0]])
                            second_distance_segment = np.array([midpoint, right_location])
                            second_line_stack = np.vstack((second_line_segment, second_distance_segment))
                            #Add that line segment to the approriate list
                            if linestyle == '-':
                                self.dashed_contacts.append(second_line_stack)
                            else:
                                self.solid_contacts.append(second_line_stack)
                    
                    
                    
            ###########################################################################################################################        
                    
                    ########################################################################################################
                    
                else: #This borehole and the next are the same sample type
                    if self.style_array[row, index] == 'n':
                        
                        
                        if index == len(self.core_or_cuttings)-2 and self.style_array[row, index+1] != 'n': #Adresses the last borehole
                            mask = (self.formation_polygons[row][-1] > self.locations[index]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                            line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                            
                            
                        else:
                            continue
                
                    elif self.style_array[row, index] == 'f' or self.style_array[row, index] == 'p':
                        direction = check_left_right(self.style_array[row], index)
                        
                        if direction == 'right':
                            #Create a mask where the values you want are starting at the left and ending at the right
                            mask = (self.formation_polygons[row][-1] >= self.locations[index]) & (self.formation_polygons[row][-1] < self.locations[index+1])
                            line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                        
                        elif direction == 'both':
                            mask = (self.formation_polygons[row][-1] >= self.locations[index-1]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                            line_segment = line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                        
                        else: #If direction is left
                            #Start at greater than the borehole before this one, and end at the next borehole
                            mask = (self.formation_polygons[row][-1] > self.locations[index-1]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                            line_segment = self.formation_polygons[row][0][mask]
                            distance_segment = self.formation_polygons[row][-1][mask]
                            
                    else:
                        #The line segment if its just a normal connection or a user defined connection
                        #Start at the left well and end at the right well
                        mask = (self.formation_polygons[row][-1] >= self.locations[index]) & (self.formation_polygons[row][-1] <= self.locations[index+1])
                        line_segment = self.formation_polygons[row][0][mask]
                        distance_segment = self.formation_polygons[row][-1][mask]
                
                line_stack = np.vstack((line_segment, distance_segment))
                
                """
                print('Row:', row)
                print("Index:", index)
                print(line_stack)
                """
                
                if linestyle == '-':
                    self.solid_contacts.append(line_stack)
                else:
                    self.dashed_contacts.append(line_stack)
                    
        
       
        
        
# =============================================================================
#region Data Updates
# =============================================================================
    """    
     These are all for checking if the user has made any changes to a piece of data. Each updates a unique status variable to be used in 
     the decision tree when the update figure button is pressed.
    """

    def formation_updated_status(self):
        self.formations_updated = True
        
    def style_updated_status(self):
        self.style_updated = True

    def polygon_updated_status(self):
        self.polygon_updated = True

    def sample_type_updated_status(self):
        self.sampleType_updated = True
        
    def colors_status(self):
        self.colors_updated = True
        
    def tooth_number_status(self):
        self.toothNumber_changed = True
        
    def fig_size_status(self):
        self.figSize_changed = True
        
    def vertical_exaggeration_status(self):
        self.figSize_changed = True
        
    def max_TD_status(self):
        self.max_TD_changed = True
            
######################################################################################################################################################
    #region Update Figure
    def update_figure(self):
        plt.close()

        # Early exits for simple changes that don't require lots of calculations
        if self.toothNumber_changed:
            self.handle_tooth_number_change()
            return

        if self.pinchFadeslider_changed:
            self.handle_pinch_fade_slider_change()
            return
        
        updates_made = False
        # Handle grouped updates systematically
        if self.formations_updated:
            self.handle_formations_update()
            updates_made = True
            
        if self.style_updated:
            self.handle_style_update()
            updates_made = True
            
        if self.polygon_updated:
            self.handle_polygon_update()
            updates_made = True          
            
        if self.sampleType_updated:
            self.handle_sample_type_update()
            updates_made = True
            
        if self.colors_updated:
            self.handle_colors_update()
            updates_made = True
            
        if self.figSize_changed and updates_made == False:
            self.create_plot()
            return
        
        if self.max_TD_changed:
            self.handle_limit_TD()
            updates_made = True
        
        if updates_made:
            # Final updates
            self.create_plot()
            self.pinch_fade_index_combox()
            self.create_formation_polygons_table()
            self.polygon_updated = False


######################################################################################################################################################
    """
    These are grouped function for specific update cases. It is likely that several of these could use reviewing an improving
    """

    # Modular Methods for Specific Updates
    def handle_tooth_number_change(self):
        self.teeth_of_fade()
        self.calculate_polygons()
        self.create_plot()
        self.create_formation_polygons_table()
        self.numberOfTeeth_textbox.clear()
        self.toothNumber_changed = False

    def handle_pinch_fade_slider_change(self):
        self.calculate_polygons()
        self.create_plot()
        self.create_formation_polygons_table()
        self.pinchFadeslider_changed = False

    def handle_formations_update(self):
        self.update_formations_array()
        self.create_initial_polygon_list()
        self.calculate_polygons()
        self.formations_updated = False

    def handle_style_update(self):
        self.update_style_array()
        self.create_pinch_fade_correction_dict()
        self.formation_polygons_combo_box()
        self.calculate_polygons()
        self.style_updated = False

    def handle_polygon_update(self):
        self.update_formation_polygon()
        self.polygon_updated = False

    def handle_sample_type_update(self):
        self.sample_type_table_to_array()
        self.sampleType_updated = False

    def handle_colors_update(self):
        self.update_colors_list()
        self.colors_updated = False

    def handle_limit_TD(self):
        self.limit_TD()
        self.max_TD_changed = False

# =============================================================================
#region Select File
# =============================================================================
    
    def select_file (self):
        """
        Opens a file selection dialog and pulls in an excel sheet. Then goes through the full suite of functions to create the plot
        """

        fname = QtWidgets.QFileDialog.getOpenFileName(None, 'Open File', '') #Opens a file selection dialog in a random filepath
        self.filepath = fname[0] #Once a file is selected, this grabs the actual filepath as a string
        
        self.plotting_colors = []
        
        self.create_initial_info()
        self.create_pinch_fade_correction_dict()
        self.formation_polygons_combo_box()
        self.create_initial_polygon_list()
        self.calculate_polygons()
        self.original_TD = self.formation_polygons[-1][1].copy()
        self.create_plot()
        self.create_formations_table()
        self.create_style_table()
        
        self.pinch_fade_index_combox()
        self.create_formation_polygons_table()
            
        self.formations_updated = False
        self.style_updated      = False
        self.polygon_updated    = False
        self.sampleType_updated = False
        self.colors_updated     = False
        self.pinchFadeslider_changed = False
        self.toothNumber_changed = False
        self.figSize_changed = False
        
        
        
        
    # =============================================================================
    #region Create Plot
    # =============================================================================
    def create_plot (self):
        """ 
        Creates the plot and populates it in the application window.
        """
        
        self.create_contact_line_arrays()
        self.hide_formation_labels()
        #Get the top of the bottom formation to use as the bottom of the surface formation
        self.top_of_bottom = np.nanmax(self.formation_polygons[-1][0])
        self.tallest_borehole = np.max(self.well_elev)
        self.deepest_borehole = min(self.formation_polygons[-1][1])
    
        self.vertical_exaggeration_inputted = int(self.verticalExaggeration_textbox.toPlainText())
        vertical_exaggeration_ratio = ((self.locations[-1]) / (self.tallest_borehole - self.deepest_borehole)) / self.vertical_exaggeration_inputted
        self.figsize[0] = vertical_exaggeration_ratio * self.figsize[1]
        self.figsize[1] = self.figsize[1]
            
        #Creates the figures and axes
        fig, ax = plt.subplots(figsize=(self.figsize[0], self.figsize[1]))
        
        #Plots the surface elevation and outline
        ax.fill_between(self.distance, self.top_of_bottom, self.elev, color="#FFE563")
        ax.plot(self.distance, self.elev, color='k', linewidth=0.8, zorder=14)
        
        #Loops through the formation polygon and plots them with user inputted colors if possible
        runs = 0
        for formation in self.formation_polygons:
            ax.fill_between(formation[-1], formation[0], formation[1], color=self.plotting_colors[runs]) #Attempts to use inputted colors
            self.formation_color_label_list[runs].setStyleSheet('background-color: {}'.format(self.plotting_colors[runs]))
            self.formation_color_label_list[runs].setFrameShape(QtWidgets.QFrame.Box)
            self.formation_color_label_list[runs].show()
            
            self.formation_name_labels_list[runs].setText(self.formations_list[runs])
            self.formation_name_labels_list[runs].show()
            self.formation_id_labels.show()
    
            runs+=1
        
        #Plots the contact lines
        for line in self.solid_contacts:
            ax.plot(line[1], line[0], linestyle='-', color='k', zorder = 12)
            
        for line in self.dashed_contacts:
            ax.plot(line[1], line[0], linestyle='--', color='k', zorder = 12)
            
        ax.fill_between(self.distance, self.elev, self.tallest_borehole+50, color='w', zorder = 13)
        
        #Plots the borehole lines to indicate location and depth, also adds W-#
        for n in range(len(self.w_num)):
            bottom_index = np.where(self.formation_polygons[-1][-1] == self.locations[n])[0][0]
            
            ax.vlines(self.locations[n], color='k', ymin=self.formation_polygons[-1][1, bottom_index], ymax=self.well_elev[n])
            ax.annotate("W-" + str(self.w_num[n]), (self.locations[n] - self.locations[-1]*0.01 , self.tallest_borehole + 80)) #Note that this uses 1% of the total length to offset labels over well lines
        
       
            
        #Set x and y axis labels
        ax.set_xlabel("Distance (ft)")
        ax.set_ylabel('Elevation (ft)')
        
        ax.set_ylim(self.deepest_borehole-50, self.tallest_borehole+100)
        #Creates a memory buffer where the plot is temporarily saved, this is required because the window only accepts images. So the plot is saved as an image temporarily and then immediately uploaded to the window
        image_buffer = io.BytesIO()
        fig.savefig(image_buffer, format='png')
        image_buffer.seek(0)
        # Convert buffer data to QPixmap and display it
        plot_image = image_buffer.getvalue()
        self.pixmap = QtGui.QPixmap()
        success = self.pixmap.loadFromData(plot_image) #ChatGPT wanted there to be a success variable for some reason, it works so im not messing with it

        if success: #Again i not sure why ChatGPT decided this if statement need to be here but it works so im not messing with it
            self.main_xsecplot.setPixmap(self.pixmap)
            self.graph_window.graphWindow_label.setPixmap(self.pixmap)
                
    # =============================================================================
    #region Intial Info
    # =============================================================================
    def create_initial_info (self):
        """
        Pulls info from the selected excel sheet and generates arrays with formation tops, style, elevation, distance, w numbers and sample type.
        """
        
        #Pulls in data from excel sheets
        df_elev = pd.read_excel(self.filepath, sheet_name='Elev')
        #This creates an array that can be plotted later. Surface elevation
        self.elev = df_elev['LiDAR_Elev'].tolist()
        self.distance = df_elev["ACTUAL_DISTANCE"].tolist()
        self.elev_array = np.array([self.elev, self.distance])
            
        
        df_cross = pd.read_excel(self.filepath, sheet_name='Xsecs')

        #Here we split the well info sheet into formations and styles
        df_formations = df_cross.set_index('W_NUM').loc[:, 'FORM_START' : 'STYLE_START'].drop(columns=['FORM_START', 'STYLE_START'])
        df_style      = df_cross.set_index('W_NUM').loc[:, 'STYLE_START':'CORE_OR_CUTTINGS'].drop(columns=['STYLE_START', 'CORE_OR_CUTTINGS'])
        
        self.w_num = df_cross['W_NUM'].tolist()
        self.core_or_cuttings = df_cross['CORE_OR_CUTTINGS'].tolist()

        #This extracts the distances for each well and the elevation of each well
        self.locations = df_cross['DIST_FT'].tolist()
        for index, location in enumerate(self.locations):
            if index == 0:
                self.locations[index] = 0 
            else:
                self.locations[index] = self.locations[index-1] + self.locations[index]
        
        
        self.well_elev = np.array(df_cross['DEM_ELEV'].tolist(), dtype=np.float64)

        #This creates a list of all the formation names from the formation dataframe column headers
        self.formations_list = df_formations.columns.tolist()

        #This creates an array of the formation tops
        all_formations = []
        for formation in self.formations_list:
            temp_list = df_formations[formation].tolist()
            all_formations.append(temp_list)
        self.formations_array = np.array(all_formations, dtype=np.float64)

        #Creates a mask that is used for the true formation depth calculation later
        not_elev = self.formations_array != 0
        #Creates an array of repeated well elevations that is used to calculate true formation depth
        elev_stack = np.repeat([self.well_elev], self.formations_array.shape[0], axis=0)

        #Calculates true formation depth by the difference of elevation and formation top only for values that arent equal to 0
        self.formations_array[not_elev] = elev_stack[not_elev] - self.formations_array[not_elev]
        #Calculates true formation depth by the sum of elevation and formation top for the values that are 0
        self.formations_array[~not_elev] = elev_stack[~not_elev] + self.formations_array[~not_elev]

        #########################################################################################################################################################

        #Creates a list of style column headers
        style_columns = df_style.columns.tolist()

        #Creates an array of the style indicators that can be used for the polygon calculation decisions
        all_styles = []
        for style in style_columns:
            temp_list = df_style[style].tolist()
            all_styles.append(temp_list)
        self.style_array = np.array(all_styles).astype('U')
        
        runs = 0
        for formation in self.formations_list:
            if formation.lower() in self.formation_colors.keys():
                self.plotting_colors.append(self.formation_colors[formation.lower()])
            else:
                self.plotting_colors.append(self.colors_list[runs])
                runs += 1
                
        
            
    def create_initial_polygon_list(self):
        """ 
        Creates some rough formation polygons that can be added to and reshaped slightly in the formation polygon calculation below
        """
        
        #Creates a copy of the formation array so that the original is preserved
        big_array = np.copy(self.formations_array)

        #Creates initial polygons for each formation, making sure that if the top of the formation is np.nan the bottom is too. 
        #Also makes sure that if the formation below has np.nan as a value, it searches the next one down to make sure it has a number in the formation bottom
        self.initial_polygon_list = []
        for row in range(big_array.shape[0] - 1):
            first_row = np.copy(big_array[row])
            nan_template = np.isnan(first_row)

            second_row = np.copy(big_array[row + 1])
            second_row[nan_template] = np.nan
            nan_second = np.isnan(second_row)

            run = 2
            while not np.array_equal(nan_template, nan_second):
                values_needed = nan_template != nan_second
                second_row[values_needed] = big_array[row + run][values_needed]
                run += 1
                nan_second = np.isnan(second_row)
            #Append each initial polygon to a list where they can be accessed during the final polygon calculation
            self.initial_polygon_list.append(np.array([first_row, second_row]))

    # =============================================================================
    #region Calculate Polygons
    # =============================================================================
    def calculate_polygons(self):
        """
        ########################################################################################################################################################
        # The final polygon creation                                                                                                                           #
        # Each polygon will be created in the same form 3-rows, 2Dimensions                                                                                    #
        # Row-1 is the formation top                                                                                                                           #
        # Row-2 is the formation bottom                                                                                                                        #
        # Row-3 is the corresponding x value for the depths in rows 1&2                                                                                        #
        # Polygons will not necessarily be of the same length, this is why they are added to a list and calulated seperately.                                  #
        # That is also why the polygons all will contain their own x values within them.                                                                       #
        ########################################################################################################################################################
        """
        
        self.formation_polygons = []
        fade_teeth_offset = self.locations[-1] * 0.01
        
        for row in range(len(self.initial_polygon_list)):
            self.formation_polygons.append('placeholder')

        for row in range(self.style_array.shape[0]-1, -1, -1):
        #Calculates the polygons for formations that fade
            
                
            if row == self.style_array.shape[0]-2:
                sorted_fade_index = 'NO'
                midpoint_correction_index = 0 #Used to keep track of which number to use in the midpoint correction list for this row. Found in pinch_fade_correction_dict
                tooth_index_correction = 0
                
            elif row == self.style_array.shape[0]-1:
                total_stack = self.initial_polygon_list[row-1].copy()
                total_stack = np.vstack((total_stack, self.locations))
                sorted_fade_index = 'NO'
                midpoint_correction_index = 0 #Used to keep track of which number to use in the midpoint correction list for this row. Found in pinch_fade_correction_dict
                tooth_index_correction = 0
                
            else: 
                total_stack = self.initial_polygon_list[row].copy()
                total_stack = np.vstack((total_stack, self.locations))
                sorted_fade_index = 'NO'
                midpoint_correction_index = 0 #Used to keep track of which number to use in the midpoint correction list for this row. Found in pinch_fade_correction_dict
                tooth_index_correction = 0
            
            # =============================================================================
            #region Fade
            # =============================================================================
           #Calculates formations thatn pinch
            if np.any(self.style_array[row] == 'f') and row != self.style_array.shape[0]-1:
                

                fade_index = np.where(self.style_array[row] == 'f')[0]
                sorted_fade_index = np.sort(fade_index)
                insert_index_correction = 0 #Used to keep track of where to insert style features

                for fade in fade_index:
                    direction = check_left_right(self.style_array[row], fade)
                    
            #Calculates the fade polygon if the formation fades left
                    if direction == 'left':
                        insert_location = fade + insert_index_correction
                        #Check for interlocking vs pool case
                        if row != 0:
                            #In interlocking cases, the above formation will be blocky and the below formation will have the teeth
                            if np.all(self.style_array[row-1, fade-1:fade+1] == ['f', 'n']): #Interlocking above
                               
                                #Calculate the universal values for this interlocking figure
                                midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                                midpoint_correction_index += 3
                                teeth_point = midpoint + fade_teeth_offset
                                #Calculate the bottom slope values
                                bottom_slope = (self.initial_polygon_list[row+1][0, fade-1] - self.initial_polygon_list[row][1, fade] ) / (self.locations[fade-1] - self.locations[fade])
                                yintercept = self.initial_polygon_list[row][1, fade] - (bottom_slope * self.locations[fade])
                                bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                                bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept
                                #Calculate the top elev with thickness and bottom midpoint elevation
                                top_slope = (self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row-1][0, fade-1]) / (self.locations[fade] - self.locations[fade-1])
                                yintercept = self.initial_polygon_list[row][0, fade] - (top_slope * self.locations[fade])
                                top_midpoint_elev = (top_slope * midpoint) + yintercept
                                
                                #Calculate the points between top and bottom
                                peaks_and_troughs = np.linspace(bottom_midpoint_elev, top_midpoint_elev, num = self.number_of_teeth_dict[row][0+tooth_index_correction])
                                peak_locations  = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction] ), midpoint))
                                bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))   

                                interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
                                
                                total_stack = np.insert(total_stack, [insert_location], interlock_figure_array, axis=1)
                                insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                                tooth_index_correction += 2

                            elif np.all(self.style_array[row+1, fade-1:fade+1] == ['f', 'n']):#Creates a blocky polygon to draw over if the formation below interlocks
                                new_stack = np.array([[self.initial_polygon_list[row+1][0,fade-1]], [self.initial_polygon_list[row+1][1,fade-1]], [self.locations[fade-1]]])
                                total_stack = np.insert(total_stack, [insert_location], new_stack, axis=1)
                                insert_index_correction += 1
                            
                            else:
                                #Calculate the universal values for this interlocking figure
                                thickness = self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row][1, fade]
                                midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                                midpoint_correction_index += 3
                                teeth_point = midpoint + fade_teeth_offset
                                #Calculate the bottom slope values
                                bottom_slope = (self.initial_polygon_list[row+1][0, fade-1] - self.initial_polygon_list[row][1, fade] ) / (self.locations[fade-1] - self.locations[fade])
                                yintercept = self.initial_polygon_list[row][1, fade] - (bottom_slope * self.locations[fade])
                                bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                                bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept
                                #Calculate the top elev with thickness and bottom midpoint elevation
                                top_midpoint_elev = bottom_midpoint_elev + thickness
            
                                #Calculate the points between top and bottom
                                peaks_and_troughs = np.linspace(bottom_midpoint_elev, top_midpoint_elev, num = self.number_of_teeth_dict[row][0+tooth_index_correction])
                                peak_locations  = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                                bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                                
                                interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
                                
                                total_stack = np.insert(total_stack, [insert_location], interlock_figure_array, axis=1)
                                insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                                tooth_index_correction += 2

                #Calculates the fade polygon if the formation fades right
                    elif direction == 'right':
                        insert_location = fade + insert_index_correction
                        
                        #Check for interlocking vs pool case
                        if row != 0:
                            #In interlocking cases, the above formation will be blocky and the below formation will have the teeth
                            if np.all(self.style_array[row-1, fade:fade+2] == ['n', 'f']): #Interlocking above
                                midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                                midpoint_correction_index += 3
                                teeth_point = midpoint - fade_teeth_offset

                                top_slope = (self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row-1][0, fade+1]) / (self.locations[fade] - self.locations[fade+1])
                                yintercept = self.initial_polygon_list[row][0, fade] - (top_slope * self.locations[fade])
                                top_midpoint_elev = (top_slope * midpoint) + yintercept

                                bottom_slope = (self.initial_polygon_list[row][1, fade] - self.initial_polygon_list[row-1][1, fade+1]) / (self.locations[fade] - self.locations[fade+1])
                                yintercept = self.initial_polygon_list[row][1, fade] - (bottom_slope * self.locations[fade])
                                bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                                bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept
                                
                                top_slope = (self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row-1][0, fade+1]) / (self.locations[fade] - self.locations[fade+1])
                                yintercept = self.initial_polygon_list[row][0, fade] - (top_slope * self.locations[fade])
                                top_midpoint_elev = (top_slope * midpoint) + yintercept

                                peaks_and_troughs = np.linspace(top_midpoint_elev, bottom_midpoint_elev, num=self.number_of_teeth_dict[row][0+tooth_index_correction])
                                peak_locations = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                                bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                                
                                interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
            
                                total_stack = np.insert(total_stack, [insert_location+1], interlock_figure_array, axis=1)
                                insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                                tooth_index_correction += 2
                                
                            elif np.all(self.style_array[row+1, fade:fade+2] == ['n', 'f']): #Creates a blocky polygon to draw over if the formation below interlocks
                                new_stack = np.array([[self.initial_polygon_list[row+1][0,fade+1]], [self.initial_polygon_list[row+1][1,fade+1]], [self.locations[fade+1]]])
                                total_stack = np.insert(total_stack, [insert_location+1], new_stack, axis=1)
                                insert_index_correction += 1

                            else:
                                
                                thickness = self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row][1, fade]
                                midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                                midpoint_correction_index += 3
                                teeth_point = midpoint - fade_teeth_offset
                                
                                left_borehole_index = np.where(self.formation_polygons[row+1][-1] == self.locations[fade])[0][0]
                                right_borehole_index = np.where(self.formation_polygons[row+1][-1] == self.locations[fade+1])[0][0]
                                
                                bottom_slope = (self.formation_polygons[row+1][0, left_borehole_index] - self.formation_polygons[row+1][0, right_borehole_index]) / (self.locations[fade] - self.locations[fade+1])
                                yintercept = self.formation_polygons[row+1][0, left_borehole_index] - (bottom_slope * self.locations[fade])
                                bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                                bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept
                                
                            
                                
                                top_midpoint_elev = bottom_midpoint_elev + thickness

                                peaks_and_troughs = np.linspace(top_midpoint_elev, bottom_midpoint_elev, num=self.number_of_teeth_dict[row][0+tooth_index_correction])
                                peak_locations = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                                bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                                
                                interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))

                                total_stack = np.insert(total_stack, [insert_location+1], interlock_figure_array, axis=1)
                                insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                                tooth_index_correction += 2
                                
                        

                    elif direction == 'both':
                        insert_location = fade + insert_index_correction

                        #In interlocking cases, the above formation will be blocky and the below formation will have the teeth
                        if np.all(self.style_array[row-1, fade-1:fade+1] == ['f', 'n']): #Interlocks above
                            #Calculate the universal values for this interlocking figure
                            thickness = self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row][1, fade]
                            midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                            midpoint_correction_index += 3
                            teeth_point = midpoint + fade_teeth_offset
                            #Calculate the bottom slope values
                            bottom_slope = (self.initial_polygon_list[row+1][0, fade-1] - self.initial_polygon_list[row][1, fade] ) / (self.locations[fade-1] - self.locations[fade])
                            yintercept = self.initial_polygon_list[row][1, fade] - (bottom_slope * self.locations[fade])
                            bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                            bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept
                            #Calculate the top elev with thickness and bottom midpoint elevation
                            top_midpoint_elev = bottom_midpoint_elev + thickness
                            
                            #Calculate the points between top and bottom
                            peaks_and_troughs = np.linspace(bottom_midpoint_elev, top_midpoint_elev, num = self.number_of_teeth_dict[row][0+tooth_index_correction])
                            peak_locations  = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                            bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                            
                            interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
                            
                            total_stack = np.insert(total_stack, [insert_location], interlock_figure_array, axis=1)
                            insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                            tooth_index_correction += 2
                                
                            #Creates a blocky polygon to draw over if the formation below interlocks
                        elif np.all(self.style_array[row+1, fade-1:fade+1] == ['f', 'n']): #Interlocks below
                            new_stack = np.array([[self.initial_polygon_list[row+1][0,fade-1]], [self.initial_polygon_list[row+1][1,fade-1]], [self.locations[fade-1]]])
                            total_stack = np.insert(total_stack, [insert_location], new_stack, axis=1)
                            insert_index_correction += 1
                            
                        else: #No interlocking
                            #Calculate the universal values for this interlocking figure
                            thickness = self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row][1, fade]
                            midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                            midpoint_correction_index += 3
                            teeth_point = midpoint + fade_teeth_offset
                            #Calculate the bottom slope values
                            bottom_slope = (self.initial_polygon_list[row][1, fade] - self.initial_polygon_list[row+1][0, fade-1]) / (self.locations[fade] - self.locations[fade-1])
                            yintercept = self.initial_polygon_list[row][1, fade] - (bottom_slope * self.locations[fade])
                            bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                            bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept
                            #Calculate the top elev with thickness and bottom midpoint elevation
                            top_midpoint_elev = bottom_midpoint_elev + thickness
                            
                            #Calculate the points between top and bottom
                            peaks_and_troughs = np.linspace(bottom_midpoint_elev, top_midpoint_elev, num = self.number_of_teeth_dict[row][0+tooth_index_correction])
                            peak_locations  = np.hstack((np.tile([midpoint, teeth_point],self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                            bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev],self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                            
                            interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
                            
                            total_stack = np.insert(total_stack, [insert_location], interlock_figure_array, axis=1)
                            insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                            tooth_index_correction += 2

                        insert_location = fade + insert_index_correction
                        #In interlocking cases, the above formation will be blocky and the below formation will have the teeth
                        if np.all(self.style_array[row-1, fade:fade+2] == ['n', 'f']): #Interlocks above
                            midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                            midpoint_correction_index += 3
                            teeth_point = midpoint - fade_teeth_offset

                            top_slope = (self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row-1][0, fade+1]) / (self.locations[fade] - self.locations[fade+1])
                            yintercept = self.initial_polygon_list[row][0, fade] - (top_slope * self.locations[fade])
                            top_midpoint_elev = (top_slope * midpoint) + yintercept
                               
                            bottom_slope = (self.initial_polygon_list[row][1, fade] - self.initial_polygon_list[row-1][1, fade+1]) / (self.locations[fade] - self.locations[fade+1])
                            yintercept = self.initial_polygon_list[row][0, fade] - (bottom_slope * self.locations[fade])
                            bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                            bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept

                            peaks_and_troughs = np.linspace(top_midpoint_elev, bottom_midpoint_elev, num=self.number_of_teeth_dict[row][0+tooth_index_correction])
                            peak_locations = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                            bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                            
                            interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
                            
                            total_stack = np.insert(total_stack, [insert_location], interlock_figure_array, axis=1)
                            insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                            tooth_index_correction += 2
                                
                            #Creates a blocky polygon to draw over if the formation below interlocks
                        elif np.all(self.style_array[row+1, fade:fade+2] == ['n', 'f']): #Interlocks below
                            new_stack = np.array([[self.initial_polygon_list[row+1][0,fade+1]], [self.initial_polygon_list[row+1][1,fade+1]], [self.locations[fade+1]]])
                            total_stack = np.insert(total_stack, [insert_location+1], new_stack, axis=1)
                            insert_index_correction += 1
                           
                        else: #No interlocking
                            thickness = self.initial_polygon_list[row][0, fade] - self.initial_polygon_list[row][1, fade]
                            midpoint = self.fade_correction_dict[row][1 + midpoint_correction_index]
                            midpoint_correction_index += 3
                            teeth_point = midpoint - fade_teeth_offset

                            bottom_slope = (self.initial_polygon_list[row][1, fade] - self.initial_polygon_list[row+1][0, fade+1]) / (self.locations[fade] - self.locations[fade+1])
                            yintercept = self.initial_polygon_list[row][1, fade] - (bottom_slope * self.locations[fade])
                            bottom_midpoint_elev = (bottom_slope * midpoint) + yintercept
                            bottom_teeth_elev = (bottom_slope * teeth_point) + yintercept

                            top_midpoint_elev = bottom_midpoint_elev + thickness

                            peaks_and_troughs = np.linspace(top_midpoint_elev, bottom_midpoint_elev, num=self.number_of_teeth_dict[row][0+tooth_index_correction])
                            peak_locations = np.hstack((np.tile([midpoint, teeth_point], self.number_of_teeth_dict[row][1+tooth_index_correction]), midpoint))
                            bottom_array = np.hstack((np.tile([bottom_midpoint_elev, bottom_teeth_elev], self.number_of_teeth_dict[row][1+tooth_index_correction]), bottom_midpoint_elev))
                            
                            interlock_figure_array = np.vstack((peaks_and_troughs, bottom_array, peak_locations))
                            
                            total_stack = np.insert(total_stack, [insert_location+1], interlock_figure_array, axis=1)
                            insert_index_correction += self.number_of_teeth_dict[row][0+tooth_index_correction]
                            tooth_index_correction += 2
                            
        ########################################################################################################################################################
        # =============================================================================
        #region Pinch
        # =============================================================================

        #Calculates the polygons for formations that pinch
            if np.any(self.style_array[row] == 'p') and row != self.style_array.shape[0]-1:
                pinch_index = np.where(self.style_array[row] == 'p')[0]
                pinch_insert_correction = 0 #Keeps track of how many points have been added to the array to make sure next points are placed correctly
                midpoint_correction_index = 0
                
                for pinch in pinch_index:

                    if type(sorted_fade_index) != str:
                        #Check which fade indexes have a direction of both and double index correction accordingly
                        index_compared_to_fade  = np.searchsorted(sorted_fade_index, pinch)
                        runs = 0
                        for fade in sorted_fade_index[:index_compared_to_fade]:
                            fade_direction = check_left_right(self.style_array[row], fade)
                            if fade_direction == 'both':
                                pinch_insert_correction += self.number_of_teeth_dict[row][runs*2]
                                runs += 1
                                pinch_insert_correction += self.number_of_teeth_dict[row][runs*2]
                                runs += 1
                            else:
                                pinch_insert_correction += self.number_of_teeth_dict[row][runs*2]
                                runs += 1
                    else:
                        pinch_insert_correction =  pinch_insert_correction

                    #Figure out direction of pinch
                    direction = check_left_right(self.style_array[row], pinch)
                    #Calculate midpoint of next formation top
                    
                    #Inserts the new data point into the polygon at the right location
                    if direction == 'left':
                        #new_point = slope_calculator(self.formations_array, self.style_array, self.locations, row, pinch, direction, self.pinch_correction_dict[row][1+midpoint_correction_index])
                        
                        
                        distance1 = self.locations[pinch]
                        distance2 = self.locations[pinch-1]
                        
                        if row == len(self.initial_polygon_list)-1:
                        
                            depth1 = self.formations_array[row+1, pinch]
                            depth2 = self.formations_array[row+1, pinch-1]
                            
                        else:
                            depth2 = np.nan
                            runs = 1
                            
                            while np.isnan(depth2):
                                
                                depth1_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance1)[0][0]
                                depth2_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance2)[0][0]
                            
                                depth1 = self.formation_polygons[row+runs][0, depth1_formation_index]
                                depth2 = self.formation_polygons[row+runs][0, depth2_formation_index]
                                
                                runs += 1
                        
                        
                        
                        slope = (depth1 - depth2) / (distance1 - distance2)
                        midpoint = self.pinch_correction_dict[row][1+midpoint_correction_index]
                        yintercept = depth1 - (slope * distance1)
                        point = (slope * midpoint) + yintercept


                        new_point = np.array([[point], [point], [midpoint]])
                        
                        
                        
                        
                        midpoint_correction_index += 3
                        insert_location = pinch + pinch_insert_correction 
                        total_stack = np.insert(total_stack, insert_location, new_point.flatten(), axis=1)
                        pinch_insert_correction +=1
                        
                    #Adds the point to the right by adding one to the insert location index
                    elif direction == 'right':
                        #new_point = slope_calculator(self.formations_array, self.style_array, self.locations, row, pinch, direction, self.pinch_correction_dict[row][1+midpoint_correction_index])
                        distance1 = self.locations[pinch]
                        distance2 = self.locations[pinch+1]
                        
                        if row == len(self.initial_polygon_list)-1:
                        
                            depth1 = self.formations_array[row+1, pinch]
                            depth2 = self.formations_array[row+1, pinch+1]
                            
                        else:
                            depth2 = np.nan
                            runs = 1
                            
                            while np.isnan(depth2):
                                
                                depth1_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance1)[0][0]
                                depth2_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance2)[0][0]
                            
                                depth1 = self.formation_polygons[row+runs][0, depth1_formation_index]
                                depth2 = self.formation_polygons[row+runs][0, depth2_formation_index]
                                
                                runs += 1
                        
                        
                        
                        slope = (depth1 - depth2) / (distance1 - distance2)
                        midpoint = self.pinch_correction_dict[row][1+midpoint_correction_index]
                        yintercept = depth1 - (slope * distance1)
                        point = (slope * midpoint) + yintercept


                        new_point = np.array([[point], [point], [midpoint]])
                        
                        
                        midpoint_correction_index += 3
                        insert_location = pinch + pinch_insert_correction + 1
                        total_stack = np.insert(total_stack, insert_location, new_point.flatten(), axis=1)
                        pinch_insert_correction +=1


                    #Combines the two methods from before to add in two points, one left and one right
                    elif direction == 'both':
                        left_right_points = []
                        #new_point = slope_calculator(self.formations_array, self.style_array, self.locations, row, pinch, direction, self.pinch_correction_dict[row][1+midpoint_correction_index], self.pinch_correction_dict[row][4+midpoint_correction_index])
                        distance1 = self.locations[pinch]
                        distance2 = self.locations[pinch-1]
                        distance3 = self.locations[pinch+1]
                        
                        
                        if row == len(self.initial_polygon_list)-1:
                        
                            depth1 = self.formations_array[row+1, pinch]
                            depth2 = self.formations_array[row+1, pinch-1]
                            
                        else:
                            depth2 = np.nan
                            runs = 1
                            
                            while np.isnan(depth2):
                                
                                depth1_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance1)[0][0]
                                depth2_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance2)[0][0]
                            
                                depth1 = self.formation_polygons[row+runs][0, depth1_formation_index]
                                depth2 = self.formation_polygons[row+runs][0, depth2_formation_index]
                                
                                runs += 1
                        
                        
                        
                        slope = (depth1 - depth2) / (distance1 - distance2)
                        midpoint = self.pinch_correction_dict[row][1+midpoint_correction_index]
                        yintercept = depth1 - (slope * distance1)
                        point = (slope * midpoint) + yintercept
                        midpoint_correction_index += 3

                        new_point = np.array([[point], [point], [midpoint]])
                        left_right_points.append(new_point)
                        
                        
                        
                        if row == len(self.initial_polygon_list)-1:
                        
                            depth1 = self.formations_array[row+1, pinch]
                            depth3 = self.formations_array[row+1, pinch+1]
                            
                        else:
                            depth3 = np.nan
                            runs = 1
                            
                            while np.isnan(depth3):
                                
                                depth1_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance1)[0][0]
                                depth3_formation_index = np.where(self.formation_polygons[row+runs][-1] == distance3)[0][0]
                            
                                depth1 = self.formation_polygons[row+runs][0, depth1_formation_index]
                                depth3 = self.formation_polygons[row+runs][0, depth3_formation_index]
                                
                                runs += 1
                        
                        
                        slope = (depth1 - depth3) / (distance1 - distance3)
                        midpoint = self.pinch_correction_dict[row][1+midpoint_correction_index]
                        yintercept = depth1 - (slope * distance1)
                        point = (slope * midpoint) + yintercept
                        
                        new_point = np.array([[point], [point], [midpoint]])
                        left_right_points.append(new_point)
                        
                        
                        insert_location= pinch + pinch_insert_correction
                        left_stack = np.insert(total_stack, insert_location, left_right_points[0].flatten(), axis=1)
                        pinch_insert_correction +=1

                        insert_location = pinch + pinch_insert_correction + 1
                        total_stack = np.insert(left_stack, insert_location, left_right_points[1].flatten(), axis=1)
                        pinch_insert_correction +=1
                        midpoint_correction_index += 6
                    
        ########################################################################################################################################################
        # =============================================================================
        #region Normal
        # =============================================================================
        #Calculates the polygons for formations that dont fade or pinch
            if ~np.any(self.style_array[row] == 'p') and ~np.any(self.style_array[row] == 'f') and row != self.style_array.shape[0]-1:
                #Checks if the next formation down pinches or fades
                if np.any(self.style_array[row+1] == 'f') or np.any(self.style_array[row+1] == 'p'):
                    #If it does, the index of where it pinches or fades will be used to replace the bottom value of the top formation with the bottom value
                    #of the lower formation, this is for ease of plotting later on.
                    total_stack = self.initial_polygon_list[row].copy()
                    bottom_replacements = (self.style_array[row+1] == 'f') | (self.style_array[row+1] == 'p')
                    total_stack[1][bottom_replacements] = self.initial_polygon_list[row+1][1][bottom_replacements]
                    #Lastly it creates the final polygon in the form of a 3-row 2D array and adds it to a list
                    if row != len(self.initial_polygon_list)-2 :
                        bottom_replacements = (self.style_array[row+2] == 'f') | (self.style_array[row+2] == 'p')
                        total_stack[1][bottom_replacements] = self.initial_polygon_list[row+2][1][bottom_replacements]
                        
                    #Connect formation across data gaps, particularly below shallow wells this is important
                    if total_stack.shape[0] == 2:
                        total_stack = np.vstack((total_stack, self.locations))
                    
                if np.any(self.style_array[row+1] == 'c'):
                    connection_below = np.where(self.style_array[row+1] == 'c')[0]
                    for connection in connection_below:
                        
                        if row != self.style_array.shape[0]-2:
                            connection_top_index = np.where(self.formation_polygons[row+1][-1] == self.locations[connection])[0]
                            connection_top = self.formation_polygons[row+1][1, connection_top_index]
                        
                        
                            if np.isin(self.locations[connection], total_stack[-1]):
                                bottom_to_be_replaced = np.where(total_stack[-1] == self.locations[connection])
                                total_stack[1,bottom_to_be_replaced] = connection_top
                            
                            else:
                                bottom_replace_index = np.searchsorted(total_stack[-1], self.locations[connection])
                                total_stack = np.insert(total_stack, bottom_replace_index, connection_top)
                       
                
                if total_stack.shape[0] == 2:
                    total_stack = np.vstack((total_stack, self.locations))
                
      ###############################################################################################################################################################          
            # =============================================================================
            #region Connect
            # =============================================================================
            #Calculates polygons with connections
            if np.any(self.style_array[row] == 'c'):
                connect_index = np.where(self.style_array[row] == 'c')[0] #Creates an array of all the indexes where the style is c
               
                
                
                #Initiates some empty diccionaries and lists to work with
                connect_groups = {}
                current_group = []
                group_id = 1

                # Iterates through connect_index to group consecutive indices
                for i in range(len(connect_index)):
                    if i == 0 or connect_index[i] == connect_index[i - 1] + 1:
                        # Add to current group if index is consecutive
                        current_group.append(connect_index[i])
                    else:
                        # Save the current group and start a new one
                        connect_groups[group_id] = current_group
                        group_id += 1
                        current_group = [connect_index[i]]

                # Add the last group
                if current_group:
                    connect_groups[group_id] = current_group
                    
                #Begins using the previously made groups to calculate points
                for group in connect_groups.keys():
                    if row != len(self.initial_polygon_list):
                        left_index = connect_groups[group][0] - 1
                        right_index = connect_groups[group][-1] + 1
                        
                        left_dist = self.locations[left_index]
                        left_elev = self.initial_polygon_list[row][0, left_index]
                    
                        right_dist = self.locations[right_index]
                        right_elev = self.initial_polygon_list[row][0, right_index]
                        
                    #Calculate the slope of the top
                        slope = (right_elev - left_elev) / (right_dist - left_dist)
                        y_intercept = right_elev - (right_dist * slope)
                    
                    else:
                        left_index = connect_groups[group][0] - 1
                        right_index = connect_groups[group][-1] + 1
                    
                    for connection in connect_groups[group]:
                        if row != len(self.initial_polygon_list):
                            connection_point = self.locations[connection] * slope + y_intercept
                        
                            
                        if row == len(self.initial_polygon_list):
                            
                            
                            
                            slope = (self.initial_polygon_list[row-1][1, right_index] - self.initial_polygon_list[row-1][1, left_index]) / (self.locations[right_index] - self.locations[left_index])
                            y_intercept = self.initial_polygon_list[row-1][1, right_index] - (self.locations[right_index] * slope)
                            
                            connection_point_bottom = self.locations[connection] * slope + y_intercept
                            
                            replacement_index = np.where(total_stack[-1] == self.locations[connection])[0]
                            total_stack[1, replacement_index] = connection_point_bottom
                            
                           
                        elif row == len(self.initial_polygon_list)-1:
                            connection_point_bottom = (self.formations_array[row+1, left_index] + self.formations_array[row+1, right_index]) / 2
                                
                        else:
                            if self.style_array[row+1, connection] == 'c' or self.style_array[row+1, connection] == 'x':
                                bottom_connection_point_index = np.where(self.formation_polygons[row+1][-1] == self.locations[connection])[0][0]
                                connection_point_bottom = self.formation_polygons[row+1][0, bottom_connection_point_index]
                                
                            elif self.style_array[row+1, connection] == 'f' or self.style_array[row+1, connection] == 'p':
                                bottom_connection_point_index = np.where(self.formation_polygons[row+1][-1] == self.locations[connection])[0][0]
                                connection_point_bottom = self.formation_polygons[row+1][1, bottom_connection_point_index]

                            else:
                                runs = 1 
                                while self.style_array[row+runs, connection] == 'n':
                                    runs += 1
                                    bottom_connection_point_index = np.where(self.formation_polygons[row+runs][-1] == self.locations[connection])[0][0]
                                    connection_point_bottom = self.formation_polygons[row+runs][1, bottom_connection_point_index]
                        
                        if row != len(self.initial_polygon_list):
                            point_array = np.array([[connection_point], [connection_point_bottom], [self.locations[connection]]])
                            insert_index = np.where(total_stack[-1] == self.locations[connection])[0]
                            total_stack[:, insert_index] = point_array
            
            """
            print("Row", row)
            print(total_stack)
            """
            
            if row != len(self.initial_polygon_list):
                self.formation_polygons[row] = total_stack
            
            
            
######################################################################################################################################################################

# =============================================================================
#region Exports
# =============================================================================

    def export_as_excel(self):
        df_export = pd.DataFrame({
            'DIST_FT' : self.locations,
            'W_NUM' : self.w_num,
            'DEM_ELEV' : self.well_elev,
            'FORM_START': np.nan
            })
        
        for index in range(self.formations_array.shape[0]):
            df_export[str(self.formations_list[index])] = self.formations_array[index]
            
        df_export['STYLE_START'] = np.nan
        
        for index in range(self.formations_array.shape[0]):
            df_export[(str(self.formations_list[index]) + '_style')] = self.style_array[index]
            
        df_export['CORE_OR_CUTTINGS'] = self.core_or_cuttings
        
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.xlsx'
        
        df_export.to_excel(save_path, index=False)
            
########################################################################################################################################################################

    # =============================================================================
    #region Illustrator DXF
    # =============================================================================
    def save_illustrator_dxf(self):
        """ 
        Uses ezdxf to create an illustrator compatible file with layers. Hatches and contact lines included with this file
        """
        
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.dxf'
        
        formation_chunk_dict = {}
        ve_polygons = []
        shortened_locations = np.array(self.locations) / self.vertical_exaggeration_inputted
        shortened_distance  = np.array(self.distance) / self.vertical_exaggeration_inputted
        
        for polygon in self.formation_polygons:
            shortened_bottom = polygon[-1] / self.vertical_exaggeration_inputted
            exaggerated_polygon = np.vstack((polygon[0:2], shortened_bottom))
            ve_polygons.append(exaggerated_polygon)
            
            
        
        for row, style in enumerate(self.style_array[:-1]):
            null_indices = np.where(style == 'n')[0]
            formation_chunk_dict[row] = []
            
            if null_indices.shape[0] == 0:
                formation_polygon_chunk = ve_polygons[row].copy()
                formation_chunk_dict[row].append(formation_polygon_chunk)
                
            else:
                for null_index ,null in enumerate(null_indices):
                    
                    #Check if it is the last null
                    if null_index == len(null_indices)-1:
                        
                        if null == self.style_array.shape[1]-1:
                            
                            if len(null_indices) == 1:
                                formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                                formation_polygon_chunk = ve_polygons[row][:, :formation_null_index].copy()
                                
                                #Handles interlocking fades at the end of formations, weird edge case that could show up
                                if self.style_array[row, null-1] == 'f' and self.style_array[row+1, null] == 'f':
                                    formation_polygon_chunk = ve_polygons[row].copy()
                                    no_nulls_columns = ~np.any(np.isnan(formation_polygon_chunk), axis=0)
                                    formation_polygon_chunk = formation_polygon_chunk[:, no_nulls_columns]
                                    
                                    formation_chunk_dict[row].append(formation_polygon_chunk)
                            else:
                                continue
                        
                        elif len(null_indices) == 1:
                            #The formation chunk starts at the beginning of the array and ends at this null
                            formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                            formation_polygon_chunk = ve_polygons[row][:, :formation_null_index].copy()
                            formation_chunk_dict[row].append(formation_polygon_chunk)
                            
                            formation_polygon_chunk = ve_polygons[row][:, formation_null_index+1:].copy()
                            
                        else:
                            # The formation polygon chunk is the entire thing after this null
                            formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                            formation_polygon_chunk = ve_polygons[row][:, formation_null_index+1:].copy()

                    #Check if it is the first null
                    elif null_index == 0:
                        #Check if there are any other nulls
                        if len(null_indices) == 1:
                            
                            if null == 0:
                                #The formation polygon chunk is the entire thing minus the first point
                                formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                                formation_polygon_chunk = ve_polygons[row][:, formation_null_index+1:].copy()
                                
                                
                            else: #The formation chunk starts at the beginning of the array and ends at this null
                                formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                                formation_polygon_chunk = ve_polygons[row][:, :formation_null_index].copy()
                                
                                formation_chunk_dict[row].append(formation_polygon_chunk)
                                
                                formation_polygon_chunk = ve_polygons[row][:, formation_null_index+1:].copy()
                                
                                
                        #Check if it has a null immediately after it
                        elif null == null_indices[null_index+1]-1:
                            formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                            formation_polygon_chunk = ve_polygons[row][:, :formation_null_index].copy()
                            
                            
                        elif null == 0: #The formation polygon chunk starts after this null and ends at the next null
                            formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                            next_formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null_indices[null_index+1]])[0][0]
                            formation_polygon_chunk = ve_polygons[row][:, formation_null_index+1:next_formation_null_index].copy()
                            
                            
                            
                        else: #The formation chunk starts at the beginning of the array and ends at this null
                            formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                            formation_polygon_chunk = ve_polygons[row][:, :formation_null_index].copy()
                            
                        
                    #Check if the null is just a normal null in the middle
                    else:
                        #Check if it has a null immediately after it
                        if null == null_indices[null_index+1]-1:
                            continue #Skip to the next null
                            
                        else:#The formation polygon chunk starts after this null and ends at the next null
                            formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null])[0][0]
                            next_formation_null_index = np.where(ve_polygons[row][-1] == shortened_locations[null_indices[null_index+1]])[0][0]
                            formation_polygon_chunk = ve_polygons[row][:, formation_null_index+1:next_formation_null_index].copy()
                        
                        
                    if formation_polygon_chunk.shape[1] != 0:
                        formation_chunk_dict[row].append(formation_polygon_chunk)
                        
            
                
        
        #print(formation_chunk_dict)
        doc = ezdxf.new()
        msp = doc.modelspace()
        
        doc.layers.add(name='Formation_Polygons')
        doc.layers.add(name='Solid_Contact_Lines')
        doc.layers.add(name='Boreholes')
        doc.layers.add(name='Dashed_Contact_Lines')
        doc.layers.add(name='W-Numbers')
        doc.layers.add(name='Scale_Bar')
        
        if "DASHED" not in doc.linetypes:
            doc.linetypes.new("DASHED", dxfattribs={"description": "Dashed __ __ __", "pattern": [20, 10, -10]})
        
        line_points_list = []
        for i in range(len(self.elev)):
            if i == 0:
                line_points_list.append((shortened_distance[i], self.top_of_bottom))
                line_points_list.append((shortened_distance[i], self.elev[i]))
                
            elif i == len(self.elev)-1:
                line_points_list.append((shortened_distance[i], self.elev[i]))
                line_points_list.append((shortened_distance[i], self.top_of_bottom))
                
            else:
                line_points_list.append((shortened_distance[i], self.elev[i]))
        
        hatch = msp.add_hatch(dxfattribs={'layer':'Formation_Polygons'})
        hatch.dxf.true_color = hex_to_rgb("#FFE563")
        hatch.paths.add_polyline_path(line_points_list, is_closed = True)
        
        for row, formation_chunk_list in formation_chunk_dict.items():
            
            for formation_chunk in formation_chunk_list:
                hatch_polyline_list = []
                for i in range(formation_chunk.shape[1]):
                    hatch_polyline_list.append((formation_chunk[-1, i], formation_chunk[0, i]))
            
                for j in range(formation_chunk.shape[1]-1, -1, -1):
                    hatch_polyline_list.append((formation_chunk[-1, j], formation_chunk[1, j]))
                
                hatch = msp.add_hatch(dxfattribs={'layer':'Formation_Polygons'})
                hatch.dxf.true_color = hex_to_rgb(self.plotting_colors[row])
                hatch.paths.add_polyline_path(hatch_polyline_list, is_closed = True)
                
        
        for line in self.solid_contacts:
            line_points_list = []
            for i in range(line.shape[1]):
                line_points_list.append((line[-1, i] / self.vertical_exaggeration_inputted, line[0, i]))
            msp.add_lwpolyline(line_points_list, dxfattribs={'layer':"Solid_Contact_Lines"})
        
        for line in self.dashed_contacts:
            line_points_list = []
            for i in range(line.shape[1]):
                line_points_list.append((line[-1, i] / self.vertical_exaggeration_inputted, line[0, i]))
            msp.add_lwpolyline(line_points_list, dxfattribs={'linetype': 'DASHED', 'layer':"Dashed_Contact_Lines"})
    
        for n in range(len(self.w_num)):
            msp.add_line((shortened_locations[n], self.formations_array[-1, n]), (shortened_locations[n], self.well_elev[n]), dxfattribs={'layer': 'Boreholes'} )
            msp.add_text(self.w_num_headers[n], dxfattribs={'insert':(shortened_locations[n], self.tallest_borehole+80), 'layer':'W-Numbers'})
        
        line_points_list = []
        for i in range(len(self.elev)):
            line_points_list.append((shortened_distance[i], self.elev[i]))
        msp.add_lwpolyline(line_points_list, dxfattribs={'layer':"Solid_Contact_Lines"})
    
        
        rounded_top = round(self.tallest_borehole/50) * 50
        rounded_bottom = round(self.deepest_borehole/50) * 50
        
        meters_top = int(rounded_top / 3.281)
        meters_bottom = int(rounded_bottom / 3.281)
        
        if rounded_top < self.tallest_borehole:
            rounded_top += 50 
        if rounded_bottom > self.deepest_borehole:
            rounded_bottom -= 50
        
        #Adds vertical scale bar
        msp.add_line((shortened_locations[0]-50, rounded_bottom), (shortened_locations[0]-50, rounded_top), dxfattribs={'layer':'Scale_Bar'})
        
        #Adds the depth lines on the scale bar in feet
        for depth in range(rounded_bottom, rounded_top+1, 10):
            if depth % 50 == 0:
                msp.add_line((shortened_locations[0]-70, depth), (shortened_locations[0]-50, depth), dxfattribs={'layer':'Scale_Bar'})
                msp.add_text(str(depth), dxfattribs={'insert':(shortened_locations[0]-90, depth), 'layer':'Scale_Bar'})
            else:
                msp.add_line((shortened_locations[0]-60, depth), (shortened_locations[0]-50, depth), dxfattribs={'layer':'Scale_Bar'})

        #Adds the depth lines on the scale bar in meters
        for depth in range(meters_top):
            if depth % 20 == 0:
                msp.add_line((shortened_locations[0]-30, depth*3.281), (shortened_locations[0]-50, depth*3.281), dxfattribs={'layer':'Scale_Bar'})
                msp.add_text(str(depth), dxfattribs={'insert':(shortened_locations[0]-20, depth*3.281), 'layer':'Scale_Bar'})
                
        for depth in range(meters_bottom, 0):
            if depth % 20 == 0:
                msp.add_line((shortened_locations[0]-30, depth*3.281), (shortened_locations[0]-50, depth*3.281), dxfattribs={'layer':'Scale_Bar'})
                msp.add_text(str(depth), dxfattribs={'insert':(shortened_locations[0]-20, depth*3.281), 'layer':'Scale_Bar'})
        
        #Adds horizontal scale bar
        shortened_mile = 5280 / self.vertical_exaggeration_inputted
        msp.add_line((0, self.deepest_borehole - 500), (shortened_mile, self.deepest_borehole-500), dxfattribs={'layer': 'Scale_Bar'})
        
        for distance_feet in range(5281):
            if distance_feet % 1000 == 0:
                msp.add_line((distance_feet/self.vertical_exaggeration_inputted, self.deepest_borehole-500), (distance_feet/self.vertical_exaggeration_inputted, self.deepest_borehole-450), dxfattribs={'layer': "Scale_Bar"})
                msp.add_text(str(distance_feet), dxfattribs={"insert":(distance_feet/self.vertical_exaggeration_inputted, self.deepest_borehole-430)})
        
        doc.saveas(save_path)


    # =============================================================================
    #region Autocad DXF
    # =============================================================================
    def save_autocad_dxf(self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.dxf'
        
        formation_chunk_dict = {}
        
        for row, style in enumerate(self.style_array[:-1]):
            null_indices = np.where(style == 'n')[0]
            formation_chunk_dict[row] = []
            
            if null_indices.shape[0] == 0:
                formation_polygon_chunk = self.formation_polygons[row].copy()
                formation_chunk_dict[row].append(formation_polygon_chunk)
                
            else:
                for null_index ,null in enumerate(null_indices):
                    
                    #Check if it is the last null
                    if null_index == len(null_indices)-1:
                        
                        if null == self.style_array.shape[1]-1:
                            
                            if len(null_indices) == 1:
                                formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                                formation_polygon_chunk = self.formation_polygons[row][:, :formation_null_index].copy()
                                
                                #Handles interlocking fades at the end of formations, weird edge case that could show up
                                if self.style_array[row, null-1] == 'f' and self.style_array[row+1, null] == 'f':
                                    formation_polygon_chunk = self.formation_polygons[row].copy()
                                    no_nulls_columns = ~np.any(np.isnan(formation_polygon_chunk), axis=0)
                                    formation_polygon_chunk = formation_polygon_chunk[:, no_nulls_columns]
                                    
                                    formation_chunk_dict[row].append(formation_polygon_chunk)
                            else:
                                continue
                        
                        elif len(null_indices) == 1:
                            #The formation chunk starts at the beginning of the array and ends at this null
                            formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                            formation_polygon_chunk = self.formation_polygons[row][:, :formation_null_index].copy()
                            formation_chunk_dict[row].append(formation_polygon_chunk)
                            
                            formation_polygon_chunk = self.formation_polygons[row][:, formation_null_index+1:].copy()
                            
                        else:
                            # The formation polygon chunk is the entire thing after this null
                            formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                            formation_polygon_chunk = self.formation_polygons[row][:, formation_null_index+1:].copy()

                    #Check if it is the first null
                    elif null_index == 0:
                        #Check if there are any other nulls
                        if len(null_indices) == 1:
                            
                            if null == 0:
                                #The formation polygon chunk is the entire thing minus the first point
                                formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                                formation_polygon_chunk = self.formation_polygons[row][:, formation_null_index+1:].copy()
                                
                                
                            else: #The formation chunk starts at the beginning of the array and ends at this null
                                formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                                formation_polygon_chunk = self.formation_polygons[row][:, :formation_null_index].copy()
                                
                                formation_chunk_dict[row].append(formation_polygon_chunk)
                                
                                formation_polygon_chunk = self.formation_polygons[row][:, formation_null_index+1:].copy()
                                
                                
                        #Check if it has a null immediately after it
                        elif null == null_indices[null_index+1]-1:
                            formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                            formation_polygon_chunk = self.formation_polygons[row][:, :formation_null_index].copy()
                            
                            
                        elif null == 0: #The formation polygon chunk starts after this null and ends at the next null
                            formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                            next_formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null_indices[null_index+1]])[0][0]
                            formation_polygon_chunk = self.formation_polygons[row][:, formation_null_index+1:next_formation_null_index].copy()
                            
                            
                            
                        else: #The formation chunk starts at the beginning of the array and ends at this null
                            formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                            formation_polygon_chunk = self.formation_polygons[row][:, :formation_null_index].copy()
                            
                        
                    #Check if the null is just a normal null in the middle
                    else:
                        #Check if it has a null immediately after it
                        if null == null_indices[null_index+1]-1:
                            continue #Skip to the next null
                            
                        else:#The formation polygon chunk starts after this null and ends at the next null
                            formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null])[0][0]
                            next_formation_null_index = np.where(self.formation_polygons[row][-1] == self.locations[null_indices[null_index+1]])[0][0]
                            formation_polygon_chunk = self.formation_polygons[row][:, formation_null_index+1:next_formation_null_index].copy()
                        
                        
                    if formation_polygon_chunk.shape[1] != 0:
                        formation_chunk_dict[row].append(formation_polygon_chunk)
                        
            
        #print(formation_chunk_dict)
        doc = ezdxf.new("R2000")
        msp = doc.modelspace()
        
        doc.layers.add(name='Formation_Polygons')
        doc.layers.add(name='Solid_Contact_Lines')
        doc.layers.add(name='Boreholes')
        doc.layers.add(name='Dashed_Contact_Lines')
        doc.layers.add(name='W-Numbers')
        doc.layers.add(name='Scale_Bar')
        
        if "DASHED" not in doc.linetypes:
            doc.linetypes.new("DASHED", dxfattribs={"description": "Dashed __ __ __", "pattern": [100, 50, -50]})
            
        
        for n in range(len(self.w_num)):
            msp.add_line((self.locations[n], self.formations_array[-1, n]), (self.locations[n], self.well_elev[n]), dxfattribs={'layer': 'Boreholes'} )
            msp.add_text(self.w_num_headers[n], dxfattribs={'insert':(self.locations[n], self.tallest_borehole+80), 'layer':'W-Numbers'})
        
        line_points_list = []
        for i in range(len(self.elev)):
            line_points_list.append((self.distance[i], self.elev[i]))
        msp.add_lwpolyline(line_points_list, dxfattribs={'layer':"Solid_Contact_Lines"})
    
        
        rounded_top = round(self.tallest_borehole/50) * 50
        rounded_bottom = round(self.deepest_borehole/50) * 50
        
        meters_top = int(rounded_top / 3.281)
        meters_bottom = int(rounded_bottom / 3.281)
        
        if rounded_top < self.tallest_borehole:
            rounded_top += 50 
        if rounded_bottom > self.deepest_borehole:
            rounded_bottom -= 50
            
        msp.add_line((self.locations[0]-50, rounded_bottom), (self.locations[0]-50, rounded_top), dxfattribs={'layer':'Scale_Bar'})
        
        for depth in range(rounded_bottom, rounded_top+1, 10):
            
            if depth % 50 == 0:
                msp.add_line((self.locations[0]-70, depth), (self.locations[0]-50, depth), dxfattribs={'layer':'Scale_Bar'})
                msp.add_text(str(depth), dxfattribs={'insert':(self.locations[0]-90, depth), 'layer':'Scale_Bar'})
            else:
                msp.add_line((self.locations[0]-60, depth), (self.locations[0]-50, depth), dxfattribs={'layer':'Scale_Bar'})
             
        for depth in range(meters_top):
            if depth % 20 == 0:
                msp.add_line((self.locations[0]-30, depth*3.281), (self.locations[0]-50, depth*3.281), dxfattribs={'layer':'Scale_Bar'})
                msp.add_text(str(depth), dxfattribs={'insert':(self.locations[0]-20, depth*3.281), 'layer':'Scale_Bar'})
                
        for depth in range(meters_bottom, 0):
            if depth % 20 == 0:
                msp.add_line((self.locations[0]-30, depth*3.281), (self.locations[0]-50, depth*3.281), dxfattribs={'layer':'Scale_Bar'})
                msp.add_text(str(depth), dxfattribs={'insert':(self.locations[0]-20, depth*3.281), 'layer':'Scale_Bar'})
        
        #Adds horizontal scale bar
        shortened_mile = 5280 / self.vertical_exaggeration_inputted
        msp.add_line((0, self.deepest_borehole - 500), (shortened_mile, self.deepest_borehole-500), dxfattribs={'layer': 'Scale_Bar'})
        
        for distance_feet in range(5281):
            if distance_feet % 1000 == 0:
                msp.add_line((distance_feet/self.vertical_exaggeration_inputted, self.deepest_borehole-500), (distance_feet/self.vertical_exaggeration_inputted, self.deepest_borehole-450), dxfattribs={'layer': "Scale_Bar"})
                msp.add_text(str(distance_feet), dxfattribs={"insert":(distance_feet/self.vertical_exaggeration_inputted, self.deepest_borehole-430)})
        
        
        doc.saveas(save_path)
    
    
    
    # =============================================================================
    #region PDF
    # =============================================================================
    def save_pdf (self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.pdf'
        
        #Get the top of the bottom formation to use as the bottom of the surface formation
        top_of_bottom = np.max(self.formations_array[-1])
        
        #Creates the figures and axes
        fig, ax = plt.subplots(figsize=(self.default_figsize[0], self.default_figsize[1]))
        
        #Plots the surface elevation and outline
        ax.fill_between(self.distance, top_of_bottom, self.elev)
        ax.plot(self.distance, self.elev, color='k', linewidth=0.8)
        
        #Loops through the formation polygon and plots them with user inputted colors if possible
        runs = 0
        for formation in self.formation_polygons:
            ax.fill_between(formation[-1], formation[0], formation[1], color=self.colors_list[runs]) #Attempts to use inputted colors
            self.formation_color_label_list[runs].setStyleSheet('background-color: {}'.format(self.colors_list[runs]))
            self.formation_color_label_list[runs].setFrameShape(QtWidgets.QFrame.Box)
            self.formation_color_label_list[runs].show()
            
            self.formation_name_labels_list[runs].setText(self.formations_list[runs])
            self.formation_name_labels_list[runs].show()
            
            runs+=1
        
        #Plots the borehole lines to indicate location and depth, also adds W-#
        for n in range(len(self.w_num)):
            ax.vlines(self.locations[n], color='k', ymin=(self.formations_array[-1, n] -10), ymax=self.well_elev[n])
            ax.annotate("W-" + str(self.w_num[n]), (self.locations[n] - self.locations[-1]*0.01 , self.well_elev[n]+10)) #Note that this uses 1% of the total length to offset labels over well lines
        
        
        fig.savefig(save_path, format='pdf', dpi=300)
        
    # =============================================================================
    #region PNG
    # =============================================================================
    def save_png (self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.png'
        
        #Get the top of the bottom formation to use as the bottom of the surface formation
        top_of_bottom = np.max(self.formations_array[-1])
        
        #Creates the figures and axes
        fig, ax = plt.subplots(figsize=(self.default_figsize[0], self.default_figsize[1]))
        
        #Plots the surface elevation and outline
        ax.fill_between(self.distance, top_of_bottom, self.elev)
        ax.plot(self.distance, self.elev, color='k', linewidth=0.8)
        
        #Loops through the formation polygon and plots them with user inputted colors if possible
        runs = 0
        for formation in self.formation_polygons:
            ax.fill_between(formation[-1], formation[0], formation[1], color=self.colors_list[runs]) #Attempts to use inputted colors
            self.formation_color_label_list[runs].setStyleSheet('background-color: {}'.format(self.colors_list[runs]))
            self.formation_color_label_list[runs].setFrameShape(QtWidgets.QFrame.Box)
            self.formation_color_label_list[runs].show()
            
            self.formation_name_labels_list[runs].setText(self.formations_list[runs])
            self.formation_name_labels_list[runs].show()
            
            runs+=1
        
        #Plots the borehole lines to indicate location and depth, also adds W-#
        for n in range(len(self.w_num)):
            ax.vlines(self.locations[n], color='k', ymin=(self.formations_array[-1, n] -10), ymax=self.well_elev[n])
            ax.annotate("W-" + str(self.w_num[n]), (self.locations[n] - self.locations[-1]*0.01 , self.well_elev[n]+10)) #Note that this uses 1% of the total length to offset labels over well lines
        
        
        fig.savefig(save_path, format='png', dpi=300)
        
        
    def save_tiff (self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.tiff'
        
        #Get the top of the bottom formation to use as the bottom of the surface formation
        top_of_bottom = np.max(self.formations_array[-1])
        
        #Creates the figures and axes
        fig, ax = plt.subplots(figsize=(self.default_figsize[0], self.default_figsize[1]))
        
        #Plots the surface elevation and outline
        ax.fill_between(self.distance, top_of_bottom, self.elev)
        ax.plot(self.distance, self.elev, color='k', linewidth=0.8)
        
        #Loops through the formation polygon and plots them with user inputted colors if possible
        runs = 0
        for formation in self.formation_polygons:
            ax.fill_between(formation[-1], formation[0], formation[1], color=self.colors_list[runs]) #Attempts to use inputted colors
            self.formation_color_label_list[runs].setStyleSheet('background-color: {}'.format(self.colors_list[runs]))
            self.formation_color_label_list[runs].setFrameShape(QtWidgets.QFrame.Box)
            self.formation_color_label_list[runs].show()
            
            self.formation_name_labels_list[runs].setText(self.formations_list[runs])
            self.formation_name_labels_list[runs].show()
            
            runs+=1
        
        #Plots the borehole lines to indicate location and depth, also adds W-#
        for n in range(len(self.w_num)):
            ax.vlines(self.locations[n], color='k', ymin=(self.formations_array[-1, n] -10), ymax=self.well_elev[n])
            ax.annotate("W-" + str(self.w_num[n]), (self.locations[n] - self.locations[-1]*0.01 , self.well_elev[n]+10)) #Note that this uses 1% of the total length to offset labels over well lines
        
        
        fig.savefig(save_path, format='tiff', dpi=300)    
        
    # =============================================================================
    #region JPEG
    # =============================================================================
    def save_jpeg (self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.jpeg'
        
        #Get the top of the bottom formation to use as the bottom of the surface formation
        top_of_bottom = np.max(self.formations_array[-1])
        
        #Creates the figures and axes
        fig, ax = plt.subplots(figsize=(self.default_figsize[0], self.default_figsize[1]))
        
        #Plots the surface elevation and outline
        ax.fill_between(self.distance, top_of_bottom, self.elev)
        ax.plot(self.distance, self.elev, color='k', linewidth=0.8)
        
        #Loops through the formation polygon and plots them with user inputted colors if possible
        runs = 0
        for formation in self.formation_polygons:
            ax.fill_between(formation[-1], formation[0], formation[1], color=self.colors_list[runs]) #Attempts to use inputted colors
            self.formation_color_label_list[runs].setStyleSheet('background-color: {}'.format(self.colors_list[runs]))
            self.formation_color_label_list[runs].setFrameShape(QtWidgets.QFrame.Box)
            self.formation_color_label_list[runs].show()
            
            self.formation_name_labels_list[runs].setText(self.formations_list[runs])
            self.formation_name_labels_list[runs].show()
            
            runs+=1
        
        #Plots the borehole lines to indicate location and depth, also adds W-#
        for n in range(len(self.w_num)):
            ax.vlines(self.locations[n], color='k', ymin=(self.formations_array[-1, n] -10), ymax=self.well_elev[n])
            ax.annotate("W-" + str(self.w_num[n]), (self.locations[n] - self.locations[-1]*0.01 , self.well_elev[n]+10)) #Note that this uses 1% of the total length to offset labels over well lines
        
        
        fig.savefig(save_path, format='jpeg', dpi=300)
        
    # =============================================================================
    #region EPS
    # =============================================================================
    def save_eps (self):
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', '')
        save_path += '.eps'
        
        #Get the top of the bottom formation to use as the bottom of the surface formation
        top_of_bottom = np.max(self.formations_array[-1])
        
        #Creates the figures and axes
        fig, ax = plt.subplots(figsize=(self.default_figsize[0], self.default_figsize[1]))
        
        #Plots the surface elevation and outline
        ax.fill_between(self.distance, top_of_bottom, self.elev)
        ax.plot(self.distance, self.elev, color='k', linewidth=0.8)
        
        #Loops through the formation polygon and plots them with user inputted colors if possible
        runs = 0
        for formation in self.formation_polygons:
            ax.fill_between(formation[-1], formation[0], formation[1], color=self.colors_list[runs]) #Attempts to use inputted colors
            self.formation_color_label_list[runs].setStyleSheet('background-color: {}'.format(self.colors_list[runs]))
            self.formation_color_label_list[runs].setFrameShape(QtWidgets.QFrame.Box)
            self.formation_color_label_list[runs].show()
            
            self.formation_name_labels_list[runs].setText(self.formations_list[runs])
            self.formation_name_labels_list[runs].show()
            
            runs+=1
        
        #Plots the borehole lines to indicate location and depth, also adds W-#
        for n in range(len(self.w_num)):
            ax.vlines(self.locations[n], color='k', ymin=(self.formations_array[-1, n] -10), ymax=self.well_elev[n])
            ax.annotate("W-" + str(self.w_num[n]), (self.locations[n] - self.locations[-1]*0.01 , self.well_elev[n]+10)) #Note that this uses 1% of the total length to offset labels over well lines
        
        
        fig.savefig(save_path, format='eps', dpi=300)
        
##################################################################################################################################################
# =============================================================================
#region Run Program
# =============================================================================
#Creates a subclass that allows people to resize the window and the widgets will change accordignly
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Store the initial size for resizing reference
        self.original_geometry = self.geometry()
        self.widget_geometries = self.ui.widget_geometries

    def resizeEvent(self, event):
        """Override resizeEvent to adjust widget positions and sizes."""
        new_size = self.size()
        width_ratio = new_size.width() / self.original_geometry.width()
        height_ratio = new_size.height() / self.original_geometry.height()

        for widget, original_geometry in self.widget_geometries.items():
            new_x = int(original_geometry.x() * width_ratio)
            new_y = int(original_geometry.y() * height_ratio)
            new_width = int(original_geometry.width() * width_ratio)
            new_height = int(original_geometry.height() * height_ratio)
            widget.setGeometry(new_x, new_y, new_width, new_height)

        super().resizeEvent(event)
    
    def closeEvent(self, event):
        """Ensure that closing the main window closes all windows."""
        for widget in QtWidgets.QApplication.topLevelWidgets():
            widget.close()  # Close all open windows explicitly
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path('TheBox.png')))

    # Instantiate and show the MainWindow subclass
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())