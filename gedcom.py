
# -*- coding: utf-8 -*-

# Parser Gedcom
#
# Copyright (C) 2013 Augustin Roche
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Please see the GPL license at http://www.gnu.org/licenses/gpl.txt


# TODO add decorators @property

import re
import codecs

class Gedcom_line:

    def __init__(self):
        self.level = 0
        self.tag = ''
        self.xref = ''
        self.value = ''
        
    def __str__(self):
        return str(self.level) + ' ' + self.xref + ' ' + self.tag + ' ' + self.value


class Gedcom_file:

    def __init__(self):
        self.indiPos = 0
        self.content = []
        self.encoding = 'iso-8859-1'
    
    def loadFromFile(self, fileName):
        try:
            txt = codecs.open(fileName, 'r', encoding=self.encoding)
        except:
            raise
        self.sourceFile = fileName
        self.content = []
        reg = re.compile('(\d+) (@(\D?\d+\D?)@)?([_A-Z]{3,5})? ?(.*)')
        for li in txt:
            li = li.strip()
            if li == '':
                continue
            #li = li.decode(self.encoding)
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
        """List of records with tag (generator)"""
        #res = []
        #res.recordType = self._tag2recordType(tag)
        for t in range(len(self.code)):
            if self.code[t].tag == tag:
                yield self.getRecordAt(t)

    def _setHeader(self, gedline):
        self.header = gedline
        self.recordType = self._tag2recordType(gedline.tag)

    def getNumLines(self):
        return len(self.code)

    def get_xref(self):
        return self.header.xref
        
    def getValue(self):
        return self.header.value

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
        
    def downgrade(self):
        """Descend tous les tags d'un niveau"""
        for li in self.code:
            if li.level > 0:
                li.level -= 1
            

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
            
    def get_unions(self):
        """Renvoie toutes les unions (generator)"""        
        for f in self.getTagList('FAMS'):
            val = f.getValue()
            xr = self._valXref(val)
            yield Ged_family(self.parent.getRecordAtXref(xr, 'fam'))

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
        
    def get_ancestors(self, limit=0):
        for a in self._recurse_ancestors([], 0, limit):
            yield a
            
    def _recurse_ancestors(self, index, generation, limit = 0):
        """Generator to recurse over parents """
        if self.get_xref() in index:
            return
        else:
            index.append(self.get_xref())
            
        if generation > limit and limit > 0:
            return
            
        yield self
        for parent in (self.get_mother(), self.get_father()):
            if parent:
                for i in parent._recurse_ancestors( index, generation+1, limit):
                    yield i

        
            


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
            
    def get_children(self):
        """(Generator)"""
        for child in self.getTagList('CHIL'):
            val = child.getValue()
            xr = self._valXref(val)
            yield Ged_individual(self.parent.getRecordAtXref(xr,'indi'))

    def _get_parent(self, tag):
        val = self.getTagValue(tag)
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
 
 
class Ged_place(Ged_record):
    def __init__(self, record):
        Ged_record.__init__(self, record.parent)
        self._setHeader(record.header)
        self.code = record.code
        
    def get_city(self):
        return self.getTagValue('CITY')
        
    def get_region(self):
        return self.getTagValue('STAE')
    
    def _process_coords(self, c):
        s = re.match('([WENS])([\d\.]+)', c)
        r = float(s.group(2))
        if s.group(1) == 'W' or s.group(1) == 'S':
            r = r * -1
        return r
    
    def get_coords(self):
        coords = [self.getTagValue(s) for s in ('LATI', 'LONG')]
        if coords[0] and coords[1]: 
            return [self._process_coords(s) for s in coords]
        else:
            return (None, None)
        
        
class Ged_event(Ged_record):
    def __init__(self, record):
        Ged_record.__init__(self, record.parent)
        self._setHeader(record.header)
        self.code = record.code

    def get_date(self):  
        return self.getTagValue('DATE')

    def get_place(self):
        pl = self.getTag('PLAC')
        if pl: 
            addr = self.getTag('ADDR')
            for li in addr.code:
                pl.code.append(li)
            return Ged_place(pl)

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

        
# obsolete !i hope
class _Ged_recordList:
  
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
        