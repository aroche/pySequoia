
# -*- coding: utf-8 -*-
# Parser Gedcom

import re

class Gedcom_line:

	
	def __init__(self):
		self.level = 0
		self.tag = ''
		self.xref = ''
		self.value = ''


class Gedcom_file:

	
	def __init__(self):
		self.indiPos = 0
		self.content = []
		self.encoding = 'iso-8859-1'
	
	def loadFromFile(self, fileName):
		try:
			txt = open(fileName, 'r')
		except:
			raise
		self.sourceFile = fileName
		self.content = []
		reg = re.compile('(\d+) (@(\D?\d+\D?)@)?([_A-Z]{3,5})? ?(.*)')
		for li in txt:
			li = li.strip()
			if li == '':
				continue
			li = li.decode(self.encoding)
			res = reg.search(li)
			if res:
				lirec = Gedcom_line()
				lirec.level = int(res.group(1))
				if lirec.level == 0 and res.group(2) != '':
					lirec.tag = res.group(5)[0:4]
					if res.group(3):
						lirec.xref = res.group(3)
					lirec.value = res.group(2)
				else: # niveau inférieur
					lirec.tag = res.group(4)[-4:]
					lirec.value = res.group(5)
				self.content.append(lirec)
		txt.close()
		if len(self.content) == 0:
			return False

		# Remplissage des indexs
		self.indexXrefsI = {}
		self.indexXrefsF = {}
		for t in range(len(self.content)):
			lirec = self.content[t]
			#pdb.set_trace()
			if not lirec.xref or lirec.level != 0:
				continue
			if lirec.tag.upper() == 'INDI':
				self.indexXrefsI[lirec.xref] = t
			elif lirec.tag.upper()[0:3] == 'FAM':
				self.indexXrefsF[lirec.xref] = t

	def _getRecordAt(self, line):
		res = Ged_record(self)
		res._setHeader(self.content[line])
		t = line + 1
		while t < len(self.content) and self.content[t].level > res.header.level:
			res.code.append(self.content[t])
			t = t+1
		return res

	def getRecordAtXref(self, xref, xrefType='indi'):
		"""Finds a record corresponding to xref and type ('indi', 'fam')"""
		if xrefType == 'indi':
			table = self.indexXrefsI
		else:
			table = self.indexXrefsF
		try:
			indice = table[xref]
		except KeyError:
			return None
		return self._getRecordAt(indice)

	def getIndividualAtXref(self, xref):
		i = self.getRecordAtXref(xref, 'indi')
		return Ged_individual(i)
		

class Ged_record:

	
	def __init__(self, parent):
		self.parent = parent
		self.recordType = 'undef'
		self.code = []

	def getLine(self, indx):
		if indx < len(self.code):
			return self.code[indx]
		else :
			return None

	def getRecordAt(self, line):
		if line >= len(self.code):
			return None
		res = Ged_record(self.parent)
		res._setHeader(self.code[line])
		t = line + 1
		#pdb.set_trace()
		while t < self.getNumLines() and self.code[t].level > res.header.level:
			res.code.append(self.code[t])
			t = t + 1
		return res

	def getTag(self, tag):
		"Gets first record having tag"
		if len(self.code) == 0:
			return None
		t = 0
		while t < len(self.code) and self.code[t].tag != tag:
			t = t+1
		return self.getRecordAt(t)

	def getTagValue(self, tag, number=1):
		"""Gets value of nth record having tag. Begins at 1."""
		occu = 0
		t = 0
		while occu < number and t < len(self.code):
			if self.getLine(t).tag == tag:
				occu = occu + 1
			t = t+1
		if occu < number:
			return ''
		else:
			return self.getLine(t-1).value

	def getTagList(self, tag):
		"""List of records with tag"""
		res = Ged_recordList()
		res.recordType = self._tag2recordType(tag)
		for t in range(len(self.code)):
			if self.code[t].tag == tag:
				res.add(self.getRecordAt(t))
		return res

	def _setHeader(self, gedline):
		self.header = gedline
		self.recordType = self._tag2recordType(gedline.tag)

	def getNumLines(self):
		return len(self.code)

	def get_xref(self):
		return self.header.xref

	def getNote(self):
		# returns the note associated to the record or '' if not exists
		res = ''
		recnote = self.getTag('NOTE')
		if recnote != None:
			if recnote.header.level == self.header.level + 1:
				res = recnote.header.value
				for li in recnote.code:
					if li.value == '':
						res = res + "\n"
					else:
						res = res + li.value
		return res
			

	def _tag2recordType(self, tag):
		tag = tag.lower()
		if tag == 'indi':
			return 'individual'
		elif tag == 'fam':
			return 'family'
		elif tag in ('birt', 'deat', 'chan', 'marr', 'bapt', 'even'):
			return 'event'
		else:
			return 'undef'

	def _valXref(self, xref):
		"""Gets Xref from text value"""
		reg = re.compile('@(\D?\d+\D?)@')
		res = reg.match(xref)
		if res:
			try:
				val = res.group(1)
			except:
				val = ""
		else:
			val = ""
		return val


class Ged_individual(Ged_record):

	
	def __init__(self, record):
		Ged_record.__init__(self, record.parent)
		self.exists = False
		self._setHeader(record.header)
		self.code = record.code

	def get_xref(self):
		return self.header.xref

	def get_given_names(self):
		return self.getTagValue('GIVN')

	def get_birth(self):
		return self.getEventFromTag('BIRT')

	def get_death(self):
		return self.getEventFromTag('DEAT')

	def get_name_for_classment(self):
		surname = self.getTagValue('SURN')
		res = re.sub("^(de |de la |d'|des |von |van )(.+)", r'\2\1', surname, 1, re.I)
		res += self.get_given_names()
		return res.lower()

	def get_number_of_unions(self):
		res = 0
		for li in self.code:
			if li.tag == 'FAMS':
				res = res + 1
		return res

	def get_occupation(self):
		return self.getTagValue('OCCU')

	def _get_parent_from_tag(self, tag):
		val = self.getTagValue('FAMC')
		res = None
		if val:
			xr = self._valXref(val)
			recFam = self.parent.getRecordAtXref(xr, 'fam')
			valpar = recFam.getTagValue(tag)
			if valpar:
				xrpar = self._valXref(valpar)
				rec = self.parent.getRecordAtXref(xrpar, 'indi')
				if rec:
					res = Ged_individual(rec)
		#pdb.set_trace()
		return res

	def getEventFromTag(self, tag):
		rectmp = self.getTag(tag)
		if rectmp:
			return Ged_event(rectmp)
		else:
			return None

	def get_union(self, index):
		"""Trouve la famille à l'index demandé (commence à 1)"""
		val = self.getTagValue('FAMS', index)
		if val:
			xr = self._valXref(val)
			return Ged_family(self.parent.getRecordAtXref(xr, 'fam'))
		else:
			return None

	def get_father(self):
		return self._get_parent_from_tag('HUSB')

	def get_mother(self):
		return self._get_parent_from_tag('WIFE')

	def get_cased_name(self):
		nom = self.getTagValue("NAME")
		res = re.search('(.*) ?\/(.*)\/', nom)
		if res:
			return res.group(1)+' '+res.group(2).upper()
		else:
			return ""
		#recNom = self.getTag('NAME')
		#if recNom:
			#return recNom.getTagValue('GIVN')+' '+recNom.getTagValue('SURN').upper()
		#else:
			#return ''

	def get_sex(self):
		s = self.getTagValue('SEX')
		if s:
			return s[0]
		else:
			return ''

	def get_surname(self):
		return self.getTagValue('SURN')


class Ged_family(Ged_record):

	
	def __init__(self, record):
		Ged_record.__init__(self, record.parent)
		self._setHeader(record.header)
		self.code = record.code
	
	def get_child(self, index):
		val = self.getTagValue('CHIL', index)
		if val != None:
			xr = self._valXref(val)
			return Ged_individual(self.parent.getRecordAtXref(xr,'indi'))
		else:
			return None

	def _get_parent(self, tag):
		val = self.getTagValue(tag)
		#pdb.set_trace()
		if val:
			xr = self._valXref(val)
			return Ged_individual(self.parent.getRecordAtXref(xr,'indi'))
		else:
			return None

	def get_father(self):
		return self._get_parent('HUSB')
		
	def get_mother(self):
		return self._get_parent('WIFE')

	def getNumberOfChildren(self):
		res = 0
		for li in self.code:
			if li.tag == 'CHIL':
				res = res+1
		return res


class Ged_event(Ged_record):
	def __init__(self, record):
		Ged_record.__init__(self, record.parent)
		self._setHeader(record.header)
		self.code = record.code

	def get_date(self):
		return self.getTagValue('DATE')

	def get_place(self):
		return self.getTagValue('PLAC')

	def get_formated_year(self):
		"""Year with appropriate symbols"""
		res = u''
		date = self.get_date()
		if date != '':
			rech = re.search('\d\d\d\d?', date)
			if rech:
				SYMBOLS = {'ABT':u'~', 'BEF':u'<', 'AFT':u'>'}
				res = rech.group(0)
				if res[0] == '0':
					res = res[1:]
				for s in SYMBOLS:
					if date.find(s) != -1:
						res = SYMBOLS[s] + res
		return res


class Ged_recordList:

	
	def __init__(self):
		self.items = []
		self.recordType = ''

	def add(self, record):
		self.items.append(record)

	def get(self, index):
		if index < len(self.items):
			return self.items[index]
		else:
			return False
		