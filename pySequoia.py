#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
pySequoia

Version python de Sequoia

Author : Augustin Roche

Spring 2012
"""

import sys, os
from PyQt4 import QtCore, QtGui
from ui.pySequoia_form_princ import Ui_MainWindow
from ui.select_indiv_dialog import Ui_select_indiv_dialog
from ui.options import Ui_Options
from gedcom2 import *
import tree
from gettext import gettext as _
import pdb


class Application(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #self.xref_base_indiv = '3179'

        self.optionDialog = Option_dialog()

        # Connections
        QtCore.QObject.connect(self.ui.openButton,QtCore.SIGNAL("clicked()"), self.file_open_dialog)
        QtCore.QObject.connect(self.ui.saveButton,QtCore.SIGNAL("clicked()"), self.file_save_dialog)
        QtCore.QObject.connect(self.ui.button_reload_file,QtCore.SIGNAL("clicked()"), self.read_gedcom)
        QtCore.QObject.connect(self.ui.buttonBox,QtCore.SIGNAL("accepted()"), self.traite_fichier)
        QtCore.QObject.connect(self.ui.pushButton_3,QtCore.SIGNAL("clicked()"), self.select_base_indiv)
        QtCore.QObject.connect(self.ui.actionPreferences,QtCore.SIGNAL("triggered()"), self.options_dialog)
        QtCore.QObject.connect(self.ui.encoding,QtCore.SIGNAL("currentIndexChanged()"), self.change_encoding)

        QtCore.pyqtRemoveInputHook()

        self.updateUiFromOptions()

        
    def file_open_dialog(self):
        """Dialogue d'ouverture de fichier Gedcom"""
        options = QtCore.QSettings("A3X", "pySequoia")
        fd = QtGui.QFileDialog(self)
        fd.setNameFilter('Gedcom files (*.ged)')
        path = os.path.dirname(str(options.value("gedcomFile", os.getcwd()).toString())) + '/'
        fd.setDirectory(path)
        fd.exec_()
        if len(fd.selectedFiles()) > 0:
            path = fd.selectedFiles()[0]
            options.setValue("gedcomFile", path)
            self.ui.lineEdit.setText(path)
            self.gedcom = Gedcom_file()
            self.read_gedcom()

    def file_save_dialog(self):
        """Dialogue d'enregistrement du PDF"""
        options = QtCore.QSettings("A3X", "pySequoia")
        fd = QtGui.QFileDialog(self)
        fd.setNameFilter('PDF files (*.pdf)')
        fd.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        path = os.path.dirname(str(options.value("saveFile", os.getcwd()).toString())) + '/'
        fd.setDirectory(path)
        fd.exec_()
        if len(fd.selectedFiles()) > 0:
            path = fd.selectedFiles()[0]
            self.ui.lineEdit_2.setText(path)

    def read_gedcom(self):
        """Recharge le fichier Gedcom"""
        path = str(self.ui.lineEdit.text())
        if os.path.isfile(path):
            self.ui.statusbar.showMessage(_("Reading Gedcom file"))
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
                self.gedcom.encoding = str(self.ui.encoding.currentText())
                self.gedcom.loadFromFile(path)
            except UnicodeDecodeError:
                QtGui.QMessageBox.warning(self, _("Read error"), _("Check the file encoding"))
            except:
                #pdb.post_mortem()
                e = sys.exc_info()[1]
                QtGui.QMessageBox.warning(self, _("Error"), _("File is not a valid Gedcom:\n" + str(e)))
            else:
                #pdb.set_trace()
                xr = self.gedcom.indexXrefsI.keys()[0]
                ind = self.gedcom.getIndividualAtXref(xr)
                self.ui.label_4.setText(ind.get_cased_name())
                self.xref_base_indiv = xr
                self.ui.buttonBox.setEnabled(True)
                self.ui.pushButton_3.setEnabled(True)
                self.ui.button_reload_file.setEnabled(True)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
                self.ui.statusbar.clearMessage()

    def options_dialog(self):
        self.optionDialog.exec_()

    def change_encoding(self):
        if self.ui.lineEdit.text():
            self.ui.button_reload_file.setEnabled(True)

    def select_base_indiv(self):
        dialg = Select_indiv(self.gedcom)
        dialg.exec_()
        xr = dialg.getXref()
        if xr:
            ind = self.gedcom.getIndividualAtXref(xr)
            self.ui.label_4.setText(ind.get_cased_name())
            self.xref_base_indiv = xr

    def updateUiFromOptions(self):
        # Positionnement des controles selon les options enregistrees
        options = QtCore.QSettings("A3X", "pySequoia")
        # fenetre principale
        self.ui.encoding.setCurrentIndex(
            self.ui.encoding.findText(options.value("gedcomEncoding", "utf-8").toString()))
        val = options.value("treeType", 'ascending').toString()
        self.ui.treeType_ascending.setChecked(val == "ascending")
        self.ui.treeType_descending.setChecked(val == "descending")
        val = options.value("pageOrientation", "portrait").toString()
        self.ui.orientation_portrait.setChecked(val == "portrait")
        self.ui.orientation_landscape.setChecked(val == "landscape")
        self.ui.include_images.setChecked(options.value("printImages", True).toBool())
        self.ui.generation_nb.setValue(options.value("max_generations", 10).toInt()[0])
        self.ui.create_index.setChecked(options.value("createIndex", True).toBool())
        # options avancees
        self.optionDialog.setColor('F', options.value("womenColor", (1,0,0)).toPyObject())
        self.optionDialog.setColor('M', options.value("menColor", (0,0,1)).toPyObject())
        vals = options.value("printElements", []).toPyObject()
        if vals:
            self.optionDialog.ui.infos_dates.setChecked("dates" in vals)
            self.optionDialog.ui.infos_occupation.setChecked("profession" in vals)
            self.optionDialog.ui.infos_notes.setChecked("notes" in vals)
        self.optionDialog.setFontSize(options.value("fontSize", 10).toInt()[0])
        self.optionDialog.ui.image_size.setValue(options.value("imageSize", 28).toInt()[0])
        

    def setOptions(self):
        """Traite les options choisies"""
        options = QtCore.QSettings("A3X", "pySequoia")
        options.setValue('saveFile', self.ui.lineEdit_2.text())
        options.setValue("gedcomFile", self.ui.lineEdit.text())
        options.setValue("printImages", self.ui.include_images.isChecked())
        options.setValue("createIndex", self.ui.create_index.isChecked())
        options.setValue("max_generations", self.ui.generation_nb.value())
        options.setValue("gedcomEncoding", self.ui.encoding.currentText())
        if self.ui.orientation_portrait.isChecked():
            options.setValue("pageOrientation", 'portrait')
        else:
            options.setValue("pageOrientation", 'landscape')
        if self.ui.treeType_ascending.isChecked():
            options.setValue("treeType", 'ascending')
        else:
            options.setValue("treeType", 'descending')
        options.setValue("menColor", self.optionDialog.getColor('M'))
        options.setValue("womenColor", self.optionDialog.getColor('F'))
        options.setValue("fontSize", self.optionDialog.getFontSize())
        # TODO : prévoir les dialogues pour ça
        options.setValue("fontName", "Helvetica")
        options.setValue("imageSize", self.optionDialog.ui.image_size.value())
        # Elements à ajouter aux individus
        elts = []
        if self.optionDialog.ui.infos_dates.isChecked():
            elts.append('dates')
        if self.optionDialog.ui.infos_occupation.isChecked():
            elts.append('profession')
        if self.optionDialog.ui.infos_notes.isChecked():
            elts.append('notes')
        options.setValue("printElements", elts)

    def traite_fichier(self):
        """Fonction principale lançant le traitement"""
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        options = QtCore.QSettings("A3X", "pySequoia")
        self.setOptions()
        if not os.path.isdir(os.path.dirname(options.value("saveFile").toString())):
            QtGui.QMessageBox.warning(self, _("Error"), _("Enter a PDF file name"))
            QtGui.QApplication.restoreOverrideCursor()
            return
        myTree = tree.Tree(self.gedcom)
        myTree.base_indiv = self.gedcom.getIndividualAtXref(self.xref_base_indiv)
        myTree.initDoc()
        if options.value("treeType") == 'ascending':
            myTree.ascending_tree()
        else:
            myTree.descending_tree()
        if options.value("createIndex").toBool():
            myTree.index_alpha()
        myTree.endDoc()
        QtGui.QApplication.restoreOverrideCursor()
        QtGui.QMessageBox.information(self, _("Done"), _("PDF file was successfully created"))


class Select_indiv(QtGui.QDialog):
    """Dialog for selecting base person"""
    nbLimit = 100
    
    def __init__(self, gedcom):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_select_indiv_dialog()
        self.ui.setupUi(self)
        self.gedcom = gedcom
        QtCore.QObject.connect(self.ui.filter, QtCore.SIGNAL("textChanged(QString)"), self.fillList)
        self.fillList()
        self.ui.filter.setFocus()

    def fillList(self):
        self.ui.indiv_list.clear()
        nameFilter = self.ui.filter.text().toLower()
        for xr in self.gedcom.indexXrefsI:
            ind = self.gedcom.getIndividualAtXref(xr)
            if ind.get_name_for_classment()[:len(nameFilter)] == nameFilter or len(nameFilter)==0:
                item = QtGui.QListWidgetItem(ind.get_cased_name())
                item.xref = xr
                self.ui.indiv_list.addItem(item)
                if len(self.ui.indiv_list) > self.nbLimit:
                    #TODO signaler limite atteinte
                    break

    def getXref(self):
        """Get selected person xref"""
        it = self.ui.indiv_list.currentItem()
        if it:
            return it.xref
        else:
            return False


class Option_dialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_Options()
        self.ui.setupUi(self)
        QtCore.QObject.connect(self.ui.womenColorButton,QtCore.SIGNAL("clicked()"), lambda sex="F": self.selectColor(sex))
        QtCore.QObject.connect(self.ui.menColorButton,QtCore.SIGNAL("clicked()"), lambda sex="H": self.selectColor(sex))

        options = QtCore.QSettings("A3X", "pySequoia")

    def selectColor(self, dest):
        """Open color picker"""
        dlg = QtGui.QColorDialog(self)
        dlg.exec_()
        col = dlg.currentColor()
        if dest == 'F':
            bouton = self.ui.womenColorButton
        else:
            bouton = self.ui.menColorButton
        pal = bouton.palette()
        pal.setColor(0, QtGui.QPalette.Button, col)
        bouton.setPalette(pal)

    def getColor(self, sex):
        if sex == 'F':
            button = self.ui.womenColorButton
        else:
            button = self.ui.menColorButton
        col = button.palette().color(0, QtGui.QPalette.Button)
        return col.getRgbF()[:3]

    def getFontSize(self):
        return int(self.ui.fontSize.currentText())

    def setFontSize(self, size):
        self.ui.fontSize.setCurrentIndex(self.ui.fontSize.findText(str(size)))

    def setColor(self, sex, coul):
        if sex == 'F':
            button = self.ui.womenColorButton
        else:
            button = self.ui.menColorButton
        pal = button.palette()
        col = QtGui.QColor()
        col.setRgbF(coul[0], coul[1], coul[2])
        pal.setColor(0, QtGui.QPalette.Button, col)
        button.setPalette(pal)


        
def main():
    app = QtGui.QApplication(sys.argv)
    appli = Application()
    appli.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()