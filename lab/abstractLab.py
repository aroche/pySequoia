# -*- coding: utf-8 -*-

# inermediary class to make ReportLab multi-pages
# and easyer object manipulation

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth #, registerFont
#from reportlab.pdfbase.ttfonts import TTFont
import os
import pdb

class TextElement:
    """A text element that can contain several "words" in several colors"""
    def __init__(self, x, y, text=''):
        self.fontSize = 10
        self.fontName = 'helvetica'
        self.coords = (x, y)
        self.color = (0,0,0)
        self.words = []
        if text:
            self.addWord(text)

    def addWord(self, word):
        self.words.append({'txt':word, 'color':self.color})

    def getX(self):
        return self.coords[0]

    def getY(self):
        return self.coords[1]

    def setColor(self, col):
        self.color = col

    def getText(self):
        return " ".join([t['txt'] for t in self.words])

    # computed string width
    def getWidth(self):
        return stringWidth(self.getText(), self.fontName, self.fontSize)

    def getXmax(self):
        return self.coords[0] + self.getWidth()

    def render(self, canvas):
        if len(self.words) == 1:
            canvas.setFillColor(self.words[0]['color'])
            canvas.drawString(self.coords[0], self.coords[1], self.words[0]['txt'])
        elif len(self.words)>1:
            txt = canvas.beginText()
            txt.setTextOrigin(self.coords[0], self.coords[1])
            for elt in self.words:
                txt.setFillColor(elt['color'])
                txt.textOut(elt['txt'])
            canvas.drawText(txt)


class LineElement:
    def __init__(self, coords):
        self.coords = coords
        self.dashed = False

    def render(self, canvas):
        if self.dashed:
            canvas.setDash(1, 2)
        else:
            canvas.setDash([], 0)
        canvas.line(self.coords[0], self.coords[1], self.coords[2], self.coords[3])

        
class LinkElement:
    # NB: text is useless here
    def __init__(self, text, page, pos, rect):
        self.name = os.urandom(10)
        self.destPos = pos
        self.destPage = page
        self.coords = rect
        self.text = text

    def render(self, canvas):
        canvas.linkAbsolute(self.text, self.name, self.coords)

        
class ImageElement:
    def __init__(self, link, pos, height):
        self.link = link
        self.position = pos
        self.height = height

    def render(self, canvas):
        if os.path.isfile(self.link):
            im = ImageReader(self.link)
            #pdb.set_trace()
            size = int(self.height/mm*2.8)
            hh = size
            ww = int(im.getSize()[0]*hh/im.getSize()[1])
            #im.thumbnail((size, size))
            canvas.drawImage(im, self.position[0], self.position[1], ww, hh)
        else:
            print "File", self.link, "not found."
        #TODO : placeholder for non-existing image
    

class PDFPage:
    def __init__(self, num):
        self.elements = []
        self.numPage = num

    def addElement(self, elt):
        self.elements.append(elt)

    
class AbstractLab():
    def __init__(self, savefile, ps):
        self.canvas = canvas.Canvas(savefile, pagesize=ps)
        self.pages = []
        self.curPage = 0
        self.title = ''
        self.pageSize = ps
        self.font = 'Helvetica'
        self.fontSize = 10
        self.images = {}

    def save(self):
        # browse destinations
        dests = {}
        for page in self.pages:
            dests[page.numPage] = {}
        for page in self.pages:
            for elt in page.elements:
                if elt.__class__.__name__ == 'LinkElement':
                    dests[elt.destPage][elt.name] = elt.destPos
        
        # writing title
        if self.title:
            self.canvas.setFont(self.font, 20)
            self.canvas.drawCentredString(self.pageSize[0]/2, self.pageSize[1]-15*mm, unicode(self.title))
            self.canvas.setTitle(self.title)

        # keep trace of elements
        for page in self.pages:
            self.canvas.setFont(self.font, self.fontSize)
            for elt in page.elements:
                elt.render(self.canvas)

            for name in dests[page.numPage].keys():
                self.canvas.bookmarkPage(name, fit='FitH', top=dests[page.numPage][name])

            # n° de page
            self.canvas.setFillColor((0,0,0))
            self.canvas.drawRightString(self.pageSize[0]-8*mm, 5*mm, str(page.numPage))
            
            self.canvas.showPage()
        try:
            self.canvas.save()
        except:
            pdb.post_mortem()

    def addPage(self):
        self.curPage = len(self.pages)+1
        self.pages.append(PDFPage(self.curPage))

    def getPage(self, nb):
        return self.pages[nb-1]

    def addElement(self, elt):
        self.pages[self.curPage-1].addElement(elt)


    def setCurrentPage(self, nb):
        if nb <= len(self.pages):
            self.curPage = nb
