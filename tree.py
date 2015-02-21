# -*- coding: utf-8 -*-

# Creation of a PDF tree from gedcom and options


import os.path
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from lab.abstractLab import *
from PyQt4.QtCore import QSettings, QObject, QString

qo = QObject()
tr = qo.tr


class Tree:
	def __init__(self, gedcom):
		self.gedcom = gedcom
		self.options = QSettings("A3X", "pySequoia")
		self.max_generations = self.options.value("max_generations").toInt()[0]
		self.notes = []
		self.counter = 0

	def setProgressDialog(self, dialog):
		"""Gives a ProgressDialog for displaying progression"""
		self.progressDialog = dialog

	def setProgression(self, progress):
		if hasattr(self, 'progressDialog'):
			self.progressDialog.setValue(progress)

	def parents(self, indiv, generation):
		"""recursively builds ascending tree"""
		if generation > self.max_generations:
			self.lastpos = {}
			return False
		refi = indiv.get_xref()
		try:
			pos = self.index_indiv[refi]
		except KeyError:
			pos = None
		if pos: # indiv already exists
			self.write_indiv(indiv, generation, str(generation)+'.', pos)
			self.lastpos = {'page':self.pdf.curPage, 'ypos':self.ytxpos}
			return False
		else:
			generation = generation + 1
			indiv2 = indiv.get_father()
			rep = False
			if indiv2:
				rep = self.parents(indiv2, generation)
			# mettre la clause d'annulation
			self.write_indiv(indiv, generation-1, str(generation-1)+'.')
			self.counter = self.counter + 1
			pos = {'page':self.pdf.curPage, 'ypos':self.ytxpos}
			self.index_indiv[refi] = pos

			if rep:
				if indiv2 and generation-1 != self.max_generations:
					self.vertical_line(generation-1, True, self.index_indiv[indiv2.get_xref()], pos)
			elif self.lastpos:
				self.vertical_line(generation-1, True, self.lastpos, pos)
				self.lastpos = None

			indiv2 = indiv.get_mother()
			if indiv2:
				rep = self.parents(indiv2, generation)
				if rep:
					if generation-1 != self.max_generations:
						self.vertical_line(generation-1, True, self.index_indiv[indiv2.get_xref()], pos)
				else:
					self.vertical_line(generation-1, True, self.lastpos, pos)
					self.lastpos = None
			return True

			
	def list_children(self, indiv, generation, posPar):
		"""Recursion for descending tree"""
		if generation > self.max_generations:
			return False
		refi = indiv.get_xref()
		try:
			pos2 = self.index_indiv[refi]
		except KeyError:
			pos2 = None
		self.write_indiv(indiv, generation, str(generation)+'.', pos2)
		posindiv = {'ypos':self.ytxpos, 'page':self.pdf.curPage}
		if posPar != None:
			self.vertical_line(generation-1, True, posindiv, posPar)
		if pos2 is None:
			self.index_indiv[refi] = posindiv
		generation = generation+1
		self.counter = self.counter+1

		cpconj = indiv.get_number_of_unions()
		for t in range(cpconj):
			fs = indiv.get_union(t+1)
			if indiv.get_sex() == 'F':
				ep = fs.get_father()
			else:
				ep = fs.get_mother()
			try:
				pos2 = self.index_fam[fs.get_xref()]
			except KeyError:
				pos2 = None
			self.write_indiv(ep, generation-1, '  x ', pos2)
			if ep != None:
				try:
					pos = self.index_indiv[ep.get_xref()]
				except KeyError:
					pos = {'page':self.pdf.curPage, 'ypos':self.ytxpos}
					self.index_indiv[ep.get_xref()] = pos

			newcouple = False;
			if pos2 == None:
				pos2 = {}
				newcouple = True
			pos2['ypos'] = self.ytxpos
			pos2['page'] = self.pdf.curPage
			if newcouple:
				self.index_fam[fs.get_xref()] = pos2
			
			if t > 0: # other marriage
				mariage1 = indiv.get_union(t)
				if mariage1.getNumberOfChildren() > 0:
					pos = self.index_fam[mariage1.get_xref()]
					pos['ypos'] = pos['ypos'] - self.options.value("fontSize").toInt()[0]
					self.vertical_line(generation-1, False, pos, pos2, True)
				del mariage1
			else:
				posindiv['ypos'] = posindiv['ypos'] - self.options.value("fontSize").toInt()[0]
				self.vertical_line(generation-1, False, posindiv, pos2, True)
				
			if not newcouple:
				break
			
			for z in range(fs.getNumberOfChildren()):
				self.list_children(fs.get_child(z+1), generation, pos2)

		generation = generation - 1

			
	def ascending_tree(self):
		self.index_indiv = {}
		self.lastpos = {}
		self.parents(self.base_indiv, 1)

	def descending_tree(self):
		self.index_indiv = {}
		self.index_fam = {}
		self.list_children(self.base_indiv, 1, None)


	def initDoc(self):
		"""Initialise PDF"""
		self.pdf = AbstractLab(str(self.options.value("saveFile").toString()), self._get_pageSize())
		self.pdf.addPage()
		self.pdf.title = str(tr(self.options.value("treeType").toString()) + ' ' + tr(QString('from')) + ' ' \
			+ self.base_indiv.get_cased_name())
		self.ytxpos = self._get_pageHeight()-20*mm


	def endDoc(self):
		self.pdf.save()
		print tr("File saved")

	def new_page(self):
		self.pdf.addPage()

	def write_indiv(self, indiv, generation, prefix, link=None):
		"""Writes an individual's name in PDF"""
		SHIFT = generation*4
		height = self._get_pageHeight()
		width = self._get_pageSize()[0]
		fontSize = self.options.value("fontSize").toInt()[0]

		imgFile = ''
		if indiv != None and self.options.value("printImages").toBool():
			img = indiv.getTag("OBJE")
			if img and img.getTagValue('FORM').lower() in ('png', 'jpeg', 'jpg'):
				imgFile = img.getTagValue('FILE')

		if imgFile == '':
			interline = 1.4*mm
		else:
			interline = self.options.value("imageSize").toInt()[0]*mm
		self.ytxpos = self.ytxpos - fontSize - interline
		if self.ytxpos < 12*mm:
			self.new_page()
			self.ytxpos = height - 5*mm - interline - fontSize
		txt = TextElement(SHIFT*mm, self.ytxpos)
		txt.fontSize = fontSize
		if not indiv:
			line = prefix + '?'
			txt.setColor((0,0,0))
		else:
			if indiv.get_sex() == 'F':
				txt.setColor(self.options.value("womenColor").toPyObject())
			else:
				txt.setColor(self.options.value("menColor").toPyObject())
			line = prefix + ' ' + indiv.get_cased_name()+' '
		txt.addWord(line)

		if not indiv:
			self.pdf.addElement(txt)
			return

		if link == None:
			# complementary information
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
					# TODO: put in italic and reduce if needed
					txt.addWord(occu)
			# Notes
			if 'notes' in self.options.value("printElements").toPyObject():
				note = indiv.getNote()
				if note:
					#TODO
					self.notes.append({'page':self.pdf.curPage, 'x':txt.getX(), 'y':txt.getY(), 'txt':note })

			# Image
			if self.options.value("printImages").toBool() and imgFile:
				txt.fontName = str(self.options.value("fontName").toString())
				pos = (txt.getXmax() + 10*mm, txt.getY())
				if not os.path.isabs(imgFile):
					imgFile = os.path.dirname(self.gedcom.sourceFile) + '/' + imgFile
				self.pdf.addElement(ImageElement(imgFile, pos, self.options.value("imageSize").toInt()[0]*mm))
				
		else: # existing indiv (hyperlink)
			strLink = ' cf. p. ' + str(link['page'])
			txt.fontName = str(self.options.value("fontName").toString())
			maxX = txt.getXmax()
			rect = (maxX, txt.getY(), maxX + 20*mm, txt.getY() + fontSize) # largeur à ajuster
			lnk = LinkElement(str(tr('go')), link['page'], link['ypos'] + fontSize, rect)
			lnk.name = 'i' + str(indiv.get_xref())
			self.pdf.addElement(lnk)
			txt.setColor((0,0,.8))
			txt.addWord(strLink)
		self.pdf.addElement(txt)
		
	
	def vertical_line(self, generation, fl_hor, pos1, pos2, dashed=False):
		"""Draws a vertical line between positions"""
		SHIFT = 4*mm
		
		if not pos1 or not pos2:
			return
		if not fl_hor and pos1['page'] == pos2['page']: # and abs(...
			return

		father = False
		if pos1['page'] > pos2['page']:
			p1 = pos2
			p2 = pos1
		elif pos1['page'] == pos2['page']:
			if pos1['ypos'] > pos2['ypos']:
				p1 = pos1
				p2 = pos2
				father = True
			else:
				p1 = pos2
				p2 = pos1
		else:
			p1 = pos1
			p2 = pos2
			father = True

		curPage = self.pdf.curPage
		# horiz line
		if fl_hor:
			self.pdf.setCurrentPage(pos1['page'])
			self.pdf.addElement(LineElement((SHIFT * generation + 2*mm, pos1['ypos'] + 2, SHIFT * generation + 3*mm, pos1['ypos'] + 2)))

		# vertical line
		if fl_hor:
			offset = 2*mm
		else:
			offset = 1*mm
		self.pdf.setCurrentPage(p1['page'])
		if father:
			ajuste = 4
		else:
			ajuste = -2
		lineBegin = (SHIFT * generation + offset, p1['ypos'] + ajuste - 2)
		pp1 = p1.copy()
		pp2 = p2.copy()
		while pp1['page'] < pp2['page']:
			lineEnd = (SHIFT*generation+offset, 0)
			li = LineElement(lineBegin + lineEnd)
			li.dashed = dashed
			self.pdf.addElement(li)
			pp1['page'] = pp1['page']+1
			self.pdf.setCurrentPage(pp1['page'])
			lineBegin = (SHIFT * generation + offset, self._get_pageHeight())
		if father:
			ajuste = 10
		else:
			ajuste = 4
		lineEnd = (SHIFT*generation+offset, pp2['ypos']+ajuste-2)
		li = LineElement(lineBegin + lineEnd)
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
		fontSize = self.options.value("fontSize").toInt()[0]
		keyList = self.index_indiv.keys()
		keyList.sort(key = lambda x: self.gedcom.getIndividualAtXref(x).get_name_for_classment())
		self.new_page()
		topP = self._get_pageHeight()
		#TODO : Title and link to index at the beginning of the document

		colWidth = (self._get_pageSize()[0]-14*mm) / NBCOL
		ytxpos = topP - 25*mm
		column = 1
		for xref in keyList:
			indiv = self.gedcom.getIndividualAtXref(xref)
			x = (column - 1) * colWidth + 7*mm
			txt = TextElement(x, ytxpos)
			page = self.index_indiv[xref]['page']
			txt.addWord(indiv.get_cased_name())
			txt.addWord('.' * 20)
			txt.addWord(' p. ' + str(page))
			self.pdf.addElement(txt)
			rect = (x, ytxpos, column * colWidth - 7*mm, ytxpos + fontSize)
			self.pdf.addElement(LinkElement(str(tr('go')), page, self.index_indiv[xref]['ypos'] + fontSize, rect))
			ytxpos -= fontSize
			if ytxpos < 20*mm: # chgt de column
				column += 1
				ytxpos = topP - 25*mm
				if column > NBCOL:
					column = 1
					self.new_page()
