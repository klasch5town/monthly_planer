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
import os.path
import datetime
import logging
from dateutil.relativedelta import *

class CiCalendar:
    def __init__(self, pFileName):
        self.tokenHandleDict = {}
        self.tokenHandleDict["BEGIN"]       = self.__handleBegin
        self.tokenHandleDict["END"]         = self.__handleEnd
        self.tokenHandleDict["VERSION"]     = self.__handleVersion
        self.tokenHandleDict["DTSTART"]     = self.__handleEventStart
        self.tokenHandleDict["DTEND"]       = self.__handleEventEnd
        self.tokenHandleDict["CATEGORIES"]  = self.__handleEventCategories
        self.tokenHandleDict["SUMMARY"]     = self.__handleEventSummary

        self.item = None
        self.fileName  = pFileName
        self.eventList = []
        self.Category = ""
        return


    def read(self, pDayOffset=0):
        try:
            hFile = open(self.fileName, 'r')
        except:
            logging.warning("could not open: {}".format(self.fileName))
            return
        self.dayOffset = pDayOffset
        for line in hFile:
            if line[0] == '\n':
                continue
            self.__evaluate(line.rstrip('\n'))

    def __evaluate(self, pLine):
        tokenArray = pLine.split(':')
        if len(tokenArray) > 1:
            self.tokenTag   = tokenArray[0]
            if ';' in self.tokenTag:
                tokenTagArray       = self.tokenTag.split(';')
                self.tokenTag       = tokenTagArray[0]
                self.tokenAttribute = tokenTagArray[1]
            else:
                self.tokenAttribute = ""
            self.tokenValue = tokenArray[1]
        else:
            return
        if self.tokenTag in self.tokenHandleDict:
            self.tokenHandleDict[self.tokenTag]()

    def __handleBegin(self):
        self.item = self.tokenValue
        if "VEVENT" in self.tokenValue:
            thisEvent = CiEvent()
            self.eventList.append(thisEvent)
        return

    def __handleEnd(self):
        if self.item == "VEVENT":
            if self.eventList[-1].DateEnd is None:
                self.eventList[-1].setDateEnd(self.eventList[-1].DateStart)
        self.item = None
        return

    def __handleVersion(self):
        self.version = self.tokenValue
        return

    def __handleEventStart(self):
        result = self.__scan4eventDate()
        if len(result[0]) != 8:
            return
        self.eventList[-1].setDateStart(result[0])
        return

    def __handleEventEnd(self):
        result = self.__scan4eventDate()
        if len(result[0]) != 8:
            return
        self.eventList[-1].setDateEnd(result[0])
        if self.dayOffset != 0:
            self.eventList[-1].shiftEvent(self.dayOffset)
        return

    def __scan4eventDate(self):
        returnList = []
        DateTime = self.tokenValue.split('T')
        returnList.append(DateTime[0])
        if len(DateTime) > 1:
            returnList.append(DateTime[1].rstrip('Z'))
        return returnList

    def __handleEventCategories(self):
        self.eventList[-1].setCategories(self.tokenValue)
        return

    def __handleEventSummary(self):
        self.eventList[-1].setSummary(self.tokenValue)
        return


    def printEvents(self):
        for event in self.eventList:
            outString  = event.DateStart
            if not event.DateStart is event.DateEnd:
                outString += " - " + event.DateEnd
            outString += ": " + event.Summary
            if event.Categories != "":
                outString += " [" + event.Categories + "]"
            print(outString)

class CiEvent:
    def __init__(self):
        self.Summary    = ""
        self.Categories = ""
        self.DateStart  = None
        self.DateEnd    = None
        self.status     = None

    def __string2date(self, pDateString):
        dateDay   = int(pDateString[6:8])
        dateMonth = int(pDateString[4:6])
        dateYear  = int(pDateString[0:4])
        # check if we are in a leap-year
        if dateYear % 400 == 0:
            self.isLeapYear = True
        elif dateYear % 100 == 0:
            self.isLeapYear = False
        elif dateYear % 4 == 0:
            self.isLeapYear = True
        else:
            self.isLeapYear = False
        if dateMonth == 2 and dateDay == 29 and not self.isLeapYear:
            dateDay = 28
        thisDate = datetime.date(dateYear, dateMonth, dateDay)
        return thisDate

    def __dateShift(self, pDate, pDayOffset, pMonthOffset, pYearOffset):
        newDate =  pDate + relativedelta(years=pYearOffset, months=pMonthOffset, days=pDayOffset)
        return newDate

    def setDateStart(self, pDateStartString):
        self.DateStart = self.__string2date(pDateStartString)
        return

    def shiftEvent(self, pDayOffset, pMonthOffset=0, pYearOffset=0):
        self.shiftStartDate(pDayOffset, pMonthOffset, pYearOffset)
        self.shiftEndDate  (pDayOffset, pMonthOffset, pYearOffset)
        return

    def shiftStartDate(self, pDayOffset, pMonthOffset=0, pYearOffset=0):
        self.DateStart = self.__dateShift(self.DateStart, pDayOffset, pMonthOffset, pYearOffset)
        return

    def shiftEndDate(self, pDayOffset, pMonthOffset=0, pYearOffset=0):
        if self.DateEnd is None:
            return
        self.DateEnd = self.__dateShift(self.DateEnd, pDayOffset, pMonthOffset, pYearOffset)
        return

    def setDateEnd(self, pDateEndString):
        self.DateEnd = self.__string2date(pDateEndString)
        return


    def getAgeString(self, pYear):
        delta = relativedelta(datetime.date(pYear,12,31),self.DateStart)
        returnString = " " + str(delta.years) + "J"
        if not self.status:
            returnString = returnString + " ??"
        return returnString


    def setCategories(self, pCategories):
        self.Categories = pCategories
        return

    def setSummary(self, pSummary):
        self.Summary = pSummary
        return

    def setStatus(self, pStatus):
        self.status = pStatus
        return



##################################################################################
def main():
    #miCal = CiCalendar(os.path.join("..","events.vcs"))
    miCal = CiCalendar(os.path.join("..","Ferien_Bayern_2015.ics"))
    miCal.read()
    miCal.printEvents()

if __name__ == '__main__':
    main()