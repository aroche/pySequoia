# -*- coding: utf-8 -*-

# Creation d'un arbre pdf à partir de gedcom et des options


import os.path
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from abstractLab import *
from PyQt4.QtCore import QSettings


class Arbre:
	def __init__(self, gedcom):
		self.gedcom = gedcom
		self.options = QSettings("A3X", "pySequoia")
		self.max_generations = self.options.value("max_generations").toInt()[0]
		self.notes = []
		self.compteur = 0

	def setProgressDialog(self, dialog):
		"""Gives a ProgressDialog for displaying progression"""
		self.progressDialog = dialog

	def setProgression(self, progress):
		if hasattr(self, 'progressDialog'):
			self.progressDialog.setValue(progress)

	def parents(self, indiv, generation):
		"""Fonction récursive de construction de l'arbre des ancetres"""
		if generation > self.max_generations:
			self.lastpos = {}
			return False
		#pdb.set_trace()
		refi = indiv.get_xref()
		try:
			pos = self.index_indiv[refi]
		except KeyError:
			pos = None
		if pos: # l'indiv existe dejà
			self.ecrire_indiv(indiv, generation, str(generation)+'.', pos)
			self.lastpos = {'page':self.pdf.curPage, 'ypos':self.ytxpos}
			return False
		else:
			generation = generation + 1
			indiv2 = indiv.get_father()
			rep = False
			if indiv2:
				rep = self.parents(indiv2, generation)
			# mettre la clause d'annulation
			self.ecrire_indiv(indiv, generation-1, str(generation-1)+'.')
			self.compteur = self.compteur + 1
			pos = {'page':self.pdf.curPage, 'ypos':self.ytxpos}
			self.index_indiv[refi] = pos

			if rep:
				if indiv2 and generation-1 != self.max_generations:
					self.ligne_vert(generation-1, True, self.index_indiv[indiv2.get_xref()], pos)
			elif self.lastpos:
				self.ligne_vert(generation-1, True, self.lastpos, pos)
				self.lastpos = None

			indiv2 = indiv.get_mother()
			if indiv2:
				rep = self.parents(indiv2, generation)
				if rep:
					if generation-1 != self.max_generations:
						self.ligne_vert(generation-1, True, self.index_indiv[indiv2.get_xref()], pos)
				else:
					self.ligne_vert(generation-1, True, self.lastpos, pos)
					self.lastpos = None
			return True

			
	def liste_enfants(self, indiv, generation, posPar):
		"""Recursion pour arbre descendant"""
		if generation > self.max_generations:
			return False
		refi = indiv.get_xref()
		try:
			pos2 = self.index_indiv[refi]
		except KeyError:
			pos2 = None
		self.ecrire_indiv(indiv, generation, str(generation)+'.', pos2)
		posindiv = {'ypos':self.ytxpos, 'page':self.pdf.curPage}
		if posPar != None:
			self.ligne_vert(generation-1, True, posindiv, posPar)
		if pos2 is None:
			self.index_indiv[refi] = posindiv
		generation = generation+1
		self.compteur = self.compteur+1

		cpconj = indiv.get_number_of_unions()
		for t in range(cpconj):
			fs = indiv.get_union(t+1)
			if indiv.get_sex() == 'F':
				ep = fs.get_father()
			else:
				ep = fs.get_mother()
			#pdb.set_trace()
			try:
				pos2 = self.index_fam[fs.get_xref()]
			except KeyError:
				pos2 = None
			self.ecrire_indiv(ep, generation-1, '  x ', pos2)
			if ep != None:
				try:
					pos = self.index_indiv[ep.get_xref()]
				except KeyError:
					pos = {'page':self.pdf.curPage, 'ypos':self.ytxpos}
					self.index_indiv[ep.get_xref()] = pos

			nouvcouple = False;
			if pos2 == None:
				pos2 = {}
				nouvcouple = True
			pos2['ypos'] = self.ytxpos
			pos2['page'] = self.pdf.curPage
			if nouvcouple:
				self.index_fam[fs.get_xref()] = pos2
			
			if t > 0: # mariage supplémentaire
				mariage1 = indiv.get_union(t)
				if mariage1.getNumberOfChildren() > 0:
					pos = self.index_fam[mariage1.get_xref()]
					pos['ypos'] = pos['ypos'] - self.options.value("fontSize").toInt()[0]
					self.ligne_vert(generation-1, False, pos, pos2, True)
				del mariage1
			else:
				posindiv['ypos'] = posindiv['ypos'] - self.options.value("fontSize").toInt()[0]
				self.ligne_vert(generation-1, False, posindiv, pos2, True)
				
			if not nouvcouple:
				break
			
			for z in range(fs.getNumberOfChildren()):
				self.liste_enfants(fs.get_child(z+1), generation, pos2)

		generation = generation - 1

			
	def arbre_ascendant(self):
		self.index_indiv = {}
		self.lastpos = {}
		self.parents(self.indiv_base, 1)

	def arbre_descendant(self):
		self.index_indiv = {}
		self.index_fam = {}
		self.liste_enfants(self.indiv_base, 1, None)


	def initDoc(self):
		"""Initialise le PDF"""
		self.pdf = AbstractLab(str(self.options.value("saveFile").toString()), self._get_pageSize())
		self.pdf.addPage()
		self.pdf.title = u'Arbre ' + unicode(self.options.value("treeType").toString()) + u' à partir de ' \
			+ self.indiv_base.get_cased_name()
		self.ytxpos = self._get_pageHeight()-20*mm


	def endDoc(self):
		self.pdf.save()
		print u"Fichier enregistré."

	def nouvelle_page(self):
		self.pdf.addPage()

	def ecrire_indiv(self, indiv, generation, prefixe, lien=None):
		"""Ecriture sur le pdf d'un nom d'individu"""
		DECAL = generation*4
		haut = self._get_pageHeight()
		larg = self._get_pageSize()[0]
		taillepol = self.options.value("fontSize").toInt()[0]

		#print "Ecriture de ", indiv.get_xref(), indiv.get_cased_name()
		fichImg = ''
		if indiv != None and self.options.value("printImages").toBool():
			img = indiv.getTag("OBJE")
			if img and img.getTagValue('FORM').lower() in ('png', 'jpeg', 'jpg'):
				fichImg = img.getTagValue('FILE')
		#pdb.set_trace()
		if fichImg == '':
			interligne = 1.4*mm
		else:
			interligne = self.options.value("imageSize").toInt()[0]*mm
		self.ytxpos = self.ytxpos - taillepol - interligne
		if self.ytxpos < 12*mm:
			self.nouvelle_page()
			self.ytxpos = haut-5*mm-interligne-taillepol
		txt = TextElement(DECAL*mm, self.ytxpos)
		txt.fontSize = taillepol
		if not indiv:
			ligne = prefixe + '?'
			txt.setColor((0,0,0))
		else:
			if indiv.get_sex() == 'F':
				txt.setColor(self.options.value("womenColor").toPyObject())
			else:
				txt.setColor(self.options.value("menColor").toPyObject())
			ligne = prefixe+' '+indiv.get_cased_name()+' '
		txt.addWord(ligne)

		if not indiv:
			self.pdf.addElement(txt)
			return

		if lien == None:
			# infos complémentaires
			txt.setColor((0,0,0))
			if 'dates' in self.options.value("printElements").toPyObject():
				evts = indiv.get_birth()
				lievt = u''
				if evts and evts.get_date():
					lievt = u' °' + evts.get_formated_year()
				evts = indiv.get_death()
				if evts and evts.get_date():
					lievt +=  u" \u2020" + evts.get_formated_year()
				txt.addWord(lievt)
			if 'profession' in self.options.value("printElements").toPyObject():
				occu = indiv.get_occupation()
				if occu:
					# TODO: mettre en italique et réduire si nécessaire
					txt.addWord(occu)
			# Notes
			if 'notes' in self.options.value("printElements").toPyObject():
				note = indiv.getNote()
				if note:
					#TODO
					self.notes.append({'page':self.pdf.curPage, 'x':txt.getX(), 'y':txt.getY(), 'txt':note })

			# Image
			if self.options.value("printImages").toBool() and fichImg:
				txt.fontName = str(self.options.value("fontName").toString())
				pos = (txt.getXmax() + 10*mm, txt.getY())
				if not os.path.isabs(fichImg):
					fichImg = os.path.dirname(self.gedcom.sourceFile) + '/' + fichImg
				self.pdf.addElement(ImageElement(fichImg, pos, self.options.value("imageSize").toInt()[0]*mm))
				
		else: # individu existant (lien hypertexte)
			strlien = ' cf. p. ' + str(lien['page'])
			txt.fontName = str(self.options.value("fontName").toString())
			try:
				maxX = txt.getXmax()
			except:
				pdb.post_mortem()
			rect = (maxX, txt.getY(), maxX+20*mm, txt.getY()+taillepol) # largeur à ajuster
			lnk = LinkElement(lien['page'], lien['ypos']+taillepol, rect)
			lnk.name = 'i'+str(indiv.get_xref())
			self.pdf.addElement(lnk)
			txt.setColor((0,0,.8))
			txt.addWord(strlien)
		self.pdf.addElement(txt)
		
	
	def ligne_vert(self, generation, fl_hor, pos1, pos2, dashed=False):
		"""Trace une ligne verticale entre positions"""
		DECAL = 4*mm
		
		if not pos1 or not pos2:
			return
		if not fl_hor and pos1['page'] == pos2['page']: # and abs(...
			return

		pere = False
		if pos1['page'] > pos2['page']:
			p1 = pos2
			p2 = pos1
		elif pos1['page'] == pos2['page']:
			if pos1['ypos'] > pos2['ypos']:
				p1 = pos1
				p2 = pos2
				pere = True
			else:
				p1 = pos2
				p2 = pos1
		else:
			p1 = pos1
			p2 = pos2
			pere = True

		curPage = self.pdf.curPage
		# ligne horiz
		if fl_hor:
			self.pdf.setCurrentPage(pos1['page'])
			self.pdf.addElement(LineElement((DECAL*generation+2*mm, pos1['ypos']+2, DECAL*generation+3*mm, pos1['ypos']+2)))

		# ligne verticale
		if fl_hor:
			offset = 2*mm
		else:
			offset = 1*mm
		self.pdf.setCurrentPage(p1['page'])
		if pere:
			ajuste = 4
		else:
			ajuste = -2
		debutLigne = (DECAL*generation+offset, p1['ypos']+ajuste-2)
		pp1 = p1.copy()
		pp2 = p2.copy()
		while pp1['page'] < pp2['page']:
			finLigne = (DECAL*generation+offset, 0)
			li = LineElement(debutLigne + finLigne)
			li.dashed = dashed
			self.pdf.addElement(li)
			pp1['page'] = pp1['page']+1
			self.pdf.setCurrentPage(pp1['page'])
			debutLigne = (DECAL*generation+offset, self._get_pageHeight())
		if pere:
			ajuste = 10
		else:
			ajuste = 4
		finLigne = (DECAL*generation+offset, pp2['ypos']+ajuste-2)
		li = LineElement(debutLigne + finLigne)
		li.dashed = dashed
		self.pdf.addElement(li)
		self.pdf.setCurrentPage(curPage)

	def _get_pageHeight(self):
		w, h = A4
		if self.options.value("pageOrientation").toString() == 'portrait':
			return h
		else:
			return w

	def _get_pageSize(self):
		w, h = A4
		if self.options.value("pageOrientation").toString() == 'portrait':
			return (w, h)
		else:
			return (h, w)

	def index_alpha(self):
		"""Creates an alphabetical index at the end of the document"""
		NBCOL = 2
		taillepol = self.options.value("fontSize").toInt()[0]
		liste = self.index_indiv.keys()
		liste.sort(key = lambda x: self.gedcom.getIndividualAtXref(x).get_name_for_classment())
		self.nouvelle_page()
		topP = self._get_pageHeight()
		#TODO : Titre et lien vers l'index en debut de document

		largcol = (self._get_pageSize()[0]-14*mm)/NBCOL
		ytxpos = topP-25*mm
		colonne = 1
		for xref in liste:
			indiv = self.gedcom.getIndividualAtXref(xref)
			x = (colonne-1)*largcol+7*mm
			txt = TextElement(x, ytxpos)
			#pdb.set_trace()
			page = self.index_indiv[xref]['page']
			txt.addWord(indiv.get_cased_name())
			txt.addWord('.'*20)
			txt.addWord(' p. ' + str(page))
			self.pdf.addElement(txt)
			rect = (x, ytxpos, colonne*largcol-7*mm, ytxpos+taillepol)
			self.pdf.addElement(LinkElement(page, self.index_indiv[xref]['ypos']+taillepol, rect))
			ytxpos -= taillepol
			if ytxpos < 20*mm: # chgt de colonne
				colonne += 1
				ytxpos = topP-25*mm
				if colonne > NBCOL:
					colonne = 1
					self.nouvelle_page()
