# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'button_small.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form, btn, checkable=True):
        Form.setObjectName("Form")
        Form.resize(351, 20)
        Form.setMinimumSize(QtCore.QSize(0, 20))
        Form.setMaximumSize(QtCore.QSize(500, 300))
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setMinimumSize(QtCore.QSize(351, 21))
        self.frame.setMaximumSize(QtCore.QSize(351, 21))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.mtrNameFld = QtWidgets.QLabel(self.frame)
        self.mtrNameFld.setMinimumSize(QtCore.QSize(150, 0))
        self.mtrNameFld.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.mtrNameFld.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        self.mtrNameFld.setFont(font)
        self.mtrNameFld.setAutoFillBackground(True)
        self.mtrNameFld.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.mtrNameFld.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.mtrNameFld.setAlignment(QtCore.Qt.AlignCenter)
        self.mtrNameFld.setProperty("moving", False)
        self.mtrNameFld.setObjectName("mtrNameFld")
        self.horizontalLayout.addWidget(self.mtrNameFld)
        self.pushBtn = btn
        self.pushBtn.setParent(self.frame)
        self.pushBtn.setMinimumSize(QtCore.QSize(120, 19))
        self.pushBtn.setMaximumSize(QtCore.QSize(16777215, 19))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pushBtn.setFont(font)
        self.pushBtn.setAutoFillBackground(True)
        if(checkable):
            self.pushBtn.setCheckable(True)
        else:
            self.pushBtn.setCheckable(False)
        self.pushBtn.setObjectName("pushBtn")
        self.horizontalLayout.addWidget(self.pushBtn)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addWidget(self.frame)

        #self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.mtrNameFld.setText(_translate("Form", "mtrName"))
        self.pushBtn.setText(_translate("Form", "..."))

