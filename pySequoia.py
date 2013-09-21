#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
pySequoia

Version python de Sequoia

Auteur : Augustin Roche

Printemps 2012
"""

import sys, os
from PyQt4 import QtCore, QtGui
from pySequoia_form_princ import Ui_MainWindow
from select_indiv_dialog import Ui_select_indiv_dialog
from options import Ui_Options
from gedcom import *
import arbre
#import pdb


class Application(QtGui.QMainWindow):

    
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.xref_base_indiv = '3179'

        self.optionDialog = Fenetre_Options()

        # Connections
        QtCore.QObject.connect(self.ui.openButton,QtCore.SIGNAL("clicked()"), self.file_open_dialog)
        QtCore.QObject.connect(self.ui.saveButton,QtCore.SIGNAL("clicked()"), self.file_save_dialog)
        QtCore.QObject.connect(self.ui.button_reload_file,QtCore.SIGNAL("clicked()"), self.read_gedcom)
        QtCore.QObject.connect(self.ui.buttonBox,QtCore.SIGNAL("accepted()"), self.traite_fichier)
        QtCore.QObject.connect(self.ui.pushButton_3,QtCore.SIGNAL("clicked()"), self.select_indiv_base)
        QtCore.QObject.connect(self.ui.actionPreferences,QtCore.SIGNAL("triggered()"), self.options_dialog)
        QtCore.QObject.connect(self.ui.encodage,QtCore.SIGNAL("currentIndexChanged()"), self.change_encodage)

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
            self.ui.statusbar.showMessage(u"Lecture du fichier Gedcom.")
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
                self.gedcom.encoding = str(self.ui.encodage.currentText())
                self.gedcom.loadFromFile(path)
            except UnicodeDecodeError:
                QtGui.QMessageBox.warning(self, "Erreur de lecture", u"Vérifiez que l'encodage choisi est le bon.")
            except:
                #pdb.post_mortem()
                QtGui.QMessageBox.warning(self, "Erreur", u"Le fichier n'est pas valide.")
            else:
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

    def change_encodage(self):
        if self.ui.lineEdit.text():
            self.ui.button_reload_file.setEnabled(True)

    def select_indiv_base(self):
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
        self.ui.encodage.setCurrentIndex(
            self.ui.encodage.findText(options.value("gedcomEncoding", "utf-8").toString()))
        val = options.value("treeType", 'ascendant').toString()
        self.ui.typeArbre_ascendant.setChecked(val == "ascendant")
        self.ui.typeArbre_descendant.setChecked(val == "descendant")
        val = options.value("pageOrientation", "portrait").toString()
        self.ui.orientation_portrait.setChecked(val == "portrait")
        self.ui.orientation_paysage.setChecked(val == "landscape")
        self.ui.inclure_images.setChecked(options.value("printImages", True).toBool())
        self.ui.nb_generations.setValue(options.value("max_generations", 10).toInt()[0])
        self.ui.creer_index.setChecked(options.value("createIndex", True).toBool())
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
        options.setValue("printImages", self.ui.inclure_images.isChecked())
        options.setValue("createIndex", self.ui.creer_index.isChecked())
        options.setValue("max_generations", self.ui.nb_generations.value())
        options.setValue("gedcomEncoding", self.ui.encodage.currentText())
        if self.ui.orientation_portrait.isChecked():
            options.setValue("pageOrientation", 'portrait')
        else:
            options.setValue("pageOrientation", 'landscape')
        if self.ui.typeArbre_ascendant.isChecked():
            options.setValue("treeType", 'ascendant')
        else:
            options.setValue("treeType", 'descendant')
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
            QtGui.QMessageBox.warning(self, "Erreur", u"Indiquez un fichier PDF")
            QtGui.QApplication.restoreOverrideCursor()
            return
        monArbre = arbre.Arbre(self.gedcom)
        monArbre.indiv_base = self.gedcom.getIndividualAtXref(self.xref_base_indiv)
        monArbre.initDoc()
        if options.value("treeType") == 'ascendant':
            monArbre.arbre_ascendant()
        else:
            monArbre.arbre_descendant()
        if options.value("createIndex").toBool():
            monArbre.index_alpha()
        monArbre.endDoc()
        QtGui.QApplication.restoreOverrideCursor()
        QtGui.QMessageBox.information(self, u"Terminé", u"Le fichier PDF a été créé.")
        #os.system(options.saveFile)


class Select_indiv(QtGui.QDialog):
    """Dialogue de choix de l'individu de base"""
    nbLimit = 100
    
    def __init__(self, gedcom):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_select_indiv_dialog()
        self.ui.setupUi(self)
        self.gedcom = gedcom
        QtCore.QObject.connect(self.ui.filtre,QtCore.SIGNAL("textChanged(QString)"), self.peupler_liste)
        self.peupler_liste()
        self.ui.filtre.setFocus()

    def peupler_liste(self):
        self.ui.liste_indiv.clear()
        filtre = self.ui.filtre.text().toLower()
        for xr in self.gedcom.indexXrefsI:
            ind = self.gedcom.getIndividualAtXref(xr)
            if ind.get_name_for_classment()[:len(filtre)] == filtre or len(filtre)==0:
                item = QtGui.QListWidgetItem(ind.get_cased_name())
                item.xref = xr
                self.ui.liste_indiv.addItem(item)
                if len(self.ui.liste_indiv) > self.nbLimit:
                    #TODO signaler limite atteinte
                    break

    def getXref(self):
        """Renvoie l'xref de l'individu sélectionné"""
        it = self.ui.liste_indiv.currentItem()
        if it:
            return it.xref
        else:
            return False


class Fenetre_Options(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_Options()
        self.ui.setupUi(self)
        QtCore.QObject.connect(self.ui.boutonCoulFemmes,QtCore.SIGNAL("clicked()"), lambda sex="F": self.selectColor(sex))
        QtCore.QObject.connect(self.ui.boutonCoulHommes,QtCore.SIGNAL("clicked()"), lambda sex="H": self.selectColor(sex))

        options = QtCore.QSettings("A3X", "pySequoia")

    def selectColor(self, dest):
        """Ouvre le sélecteur de couleur"""
        dlg = QtGui.QColorDialog(self)
        dlg.exec_()
        col = dlg.currentColor()
        if dest == 'F':
            bouton = self.ui.boutonCoulFemmes
        else:
            bouton = self.ui.boutonCoulHommes
        pal = bouton.palette()
        pal.setColor(0, QtGui.QPalette.Button, col)
        bouton.setPalette(pal)

    def getColor(self, sex):
        if sex == 'F':
            bouton = self.ui.boutonCoulFemmes
        else:
            bouton = self.ui.boutonCoulHommes
        col = bouton.palette().color(0, QtGui.QPalette.Button)
        return col.getRgbF()[:3]

    def getFontSize(self):
        return int(self.ui.fontSize.currentText())

    def setFontSize(self, size):
        self.ui.fontSize.setCurrentIndex(self.ui.fontSize.findText(str(size)))

    def setColor(self, sex, coul):
        if sex == 'F':
            bouton = self.ui.boutonCoulFemmes
        else:
            bouton = self.ui.boutonCoulHommes
        pal = bouton.palette()
        col = QtGui.QColor()
        col.setRgbF(coul[0], coul[1], coul[2])
        pal.setColor(0, QtGui.QPalette.Button, col)
        bouton.setPalette(pal)


        
def main():
    app = QtGui.QApplication(sys.argv)
    appli = Application()
    appli.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()