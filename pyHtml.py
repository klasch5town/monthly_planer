# -------------------------------------------------------------------------------
# Name:		pyHtml
# Purpose:
#
# Author:	  shark
#
# Created:	 18.12.2014
# Copyright:   (c) shark 2014
# Licence:	 <your licence>
# -------------------------------------------------------------------------------
import sys
import os.path

class c_HtmlTag:
    def __init__(self, pTagName, pTagText=""):
        self.tagName = pTagName
        self.tagText = pTagText
        self.attributeDict = {}
        self.subTagList = []

    def addAttribute(self, pName, pValue):
        if pName in self.attributeDict:
            self.attributeDict[pName] += ' ' + pValue
        else:
            self.attributeDict[pName] = pValue
        return


    def addClass(self, pClassName):
        self.addAttribute("class", pClassName)
        return


    def setText(self, pText):
        self.tagText = pText
        return


    def addSubTag(self, pTag):
        self.subTagList.append(pTag)

    def writeOpen(self, pOut):
        pOut.write("<" + self.tagName)
        for attribute in self.attributeDict:
            pOut.write(' ' + attribute + '="')
            pOut.write(self.attributeDict[attribute] + '"')
        pOut.write('>')
        return

    def writeClose(self, pOut):
        pOut.write("</" + self.tagName + ">\n")

    def writeTag(self, pOut):
        self.writeOpen(pOut)
        pOut.write(self.__getHtmlTxt(self.tagText))
        for subTag in self.subTagList:
            subTag.writeTag(pOut)
        self.writeClose(pOut)

    def __getHtmlTxt(self, pTxt):
        outTxt  =   pTxt.replace("ä","&auml;")
        outTxt  = outTxt.replace("Ä","&Auml;")
        outTxt  = outTxt.replace("ö","&ouml;")
        outTxt  = outTxt.replace("Ö","&Ouml;")
        outTxt  = outTxt.replace("ü","&uuml;")
        outTxt  = outTxt.replace("Ü","&Uuml;")
        outTxt  = outTxt.replace("ß","&szlig;")
        return outTxt

class CParagraphTag(c_HtmlTag):
    def __init__(self, pTagTxt="", pClass=""):
        c_HtmlTag.__init__(self, "p", pTagTxt)
        if not pClass is None:
            self.addClass(pClass)


class CDivTag(c_HtmlTag):
    def __init__(self, pTagTxt="", pClass=""):
        c_HtmlTag.__init__(self, "div", pTagTxt)
        if not pClass is None:
            self.addClass(pClass)


class c_CssTag(c_HtmlTag):
    def __init__(self, pCssFile, pMediaType="all"):
        c_HtmlTag.__init__(self, "link")
        self.addAttribute("rel", "stylesheet")
        self.addAttribute("type", "text/css")
        self.addAttribute("href", pCssFile)
        self.addAttribute("media", pMediaType)


class c_HtmlFile:
    def __init__(self, pFileName, pTargetDir="."):
        self.fileName = pFileName
        self.targetDir = pTargetDir
        self.bodyTagList = []

    def addTag(self, pTag):
        self.bodyTagList.append(pTag)

    def doPrint(self):
        self.doWrite(sys.stdout)

    def doSave(self):
        fileNamePath = os.path.join(self.targetDir, self.fileName + ".html")
        hOutFile = open(fileNamePath, 'w')
        self.doWrite(hOutFile)
        hOutFile.close()

    def doWrite(self, pOut):
        docType = c_HtmlTag("!doctype html")
        docType.writeOpen(pOut)

        htmlTag = c_HtmlTag("html")
        htmlTag.writeOpen(pOut)

        headTag = c_HtmlTag("head")
        hCSS_Tag = c_CssTag("stylesheet.css")
        headTag.addSubTag(hCSS_Tag)
        hTitleTag = c_HtmlTag("title", self.fileName)
        headTag.addSubTag(hTitleTag)
        headTag.writeTag(pOut)

        hBodyTag = c_HtmlTag("body")
        hBodyTag.writeOpen(pOut)

        for tag in self.bodyTagList:
            tag.writeTag(pOut)

        hBodyTag.writeClose(pOut)

        htmlTag.writeClose(pOut)


def main():
    myHtmlFile = c_HtmlFile("Monat")
    for item in range(1, 30):
        newTag = c_HtmlTag("p", str(item))
        myHtmlFile.addTag(newTag)

    myHtmlFile.doSave()


if __name__ == '__main__':
    main()
