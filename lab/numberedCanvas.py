# -*- coding: utf-8 -*-

# Solution pour pourvoir revenir sur les pages au fur et à mesure
# à adapter à mes besoins
# source : http://code.activestate.com/recipes/576832/

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


class NumberedCanvas(canvas.Canvas):
	def __init__(self, *args, **kwargs):
		canvas.Canvas.__init__(self, *args, **kwargs)
		#self._saved_page_states = []
		self._codes = []

	def showPage(self):
		self._codes.append({'code': self._code, 'stack': self._codeStack})
		self._codeStack = []
		#self._saved_page_states.append(dict(self.__dict__))
		self._startPage()

	def save(self):
		"""add page info to each page (page x of y)"""
		#num_pages = len(self._saved_page_states)
		#for state in self._saved_page_states:
		for code in self._codes:
			#self.__dict__.update(state)
			self._code = code['code']
			#self._codeStack = code['stack']
			#self.draw_page_number(num_pages)
			canvas.Canvas.showPage(self)
		canvas.Canvas.save(self)
		#self._doc.SaveToFile(self._filename, self)

	def restore_page(self, pageNumber):
		"""Selectionne la page n° n. Attention : commence à 1"""
		#if pageNumber < len(self._saved_page_states):
			#self.__dict__.update(self._saved_page_states[pageNumber-1])
		if pageNumber < len(self._codes) and pageNumber != self.getPageNumber():
			self._code = self._codes[pageNumber-1]['code']
			self._codeStack = []
			#self._codeStack = self._codes[pageNumber-1]['stack']


	# inutile pour moi
	def draw_page_number(self, page_count):
		self.setFont("Helvetica", 7)
		self.drawRightString(200*mm, 20*mm,
		"Page %d of %d" % (self._pageNumber, page_count))