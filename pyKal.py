# -------------------------------------------------------------------------------
# Name:		pyKal
# Purpose:
#
# Author:	  klasch5town
#
# Created:	 02.01.2022
# Copyright:   (c) klasch5town 2022
# Licence:	 MIT
# -------------------------------------------------------------------------------

import sys, os, os.path, datetime, csv, logging, argparse
import ephem
from pyHtml import c_HtmlFile
from pyHtml import c_HtmlTag
from pyHtml import CDivTag
from pyICalendar import *
from calendar import Calendar
from shutil import copy
from dateutil.easter import *
from dateutil.relativedelta import *


class CDay:
    def __init__(self, pWeekDayString, pDayOfMonth, pCalendarWeek):
        self.WeekDayString = pWeekDayString
        self.DayOfMonth    = pDayOfMonth
        self.CalendarWeek  = pCalendarWeek
        self.EventList     = []
        self.birthdayList  = []
        self.holiday       = False
        self.publicHoliday = False
        self.garbageCollection = ""

    def set_event(self, pEvent):
        self.EventList.append(pEvent)
        return


    def getEvents(self):
        return (self.EventList)


    def addBirthday(self, pEvent):
        self.birthdayList.append(pEvent)
        return


    def printEvents(self):
        for Event in self.EventList:
            print(Event)


    def getDayString(self):
        outString  = self.WeekDayString + " "
        outString += str(self.DayOfMonth) + " [KW"
        outString += str(self.CalendarWeek) + "]"
        return outString


class CCal:
    WeekDayStringList = (None,"Mo","Di","Mi","Do","Fr","Sa","So")
    MonthStringList   = ("Januar", "Februar", "März", "April",
                         "Mai", "Juni", "Juli", "August",
                         "September", "Oktober", "November", "Dezember")
    garbageType       = { "":"", "Restmüll":"RM", "Gelber":"GS", "Papiertonne":"PT", "Schadstoffmobil":"SM", "Biotonne":'BT'}
    publicHolidays = [ # [datetime, summary, public-holiday]
        [ "easter(self.startYear) + datetime.timedelta(days=-48)", "Rosenmontag",         False],
        [ "easter(self.startYear) + datetime.timedelta(days=-47)", "Fastnacht",           False],
        [ "easter(self.startYear) + datetime.timedelta(days=-46)", "Aschermittwoch",      False,
        [ "easter(self.startYear) + datetime.timedelta(days= -7)", "Palmsonntag"],        True],
        [ "easter(self.startYear) + datetime.timedelta(days= -3)", "Gründonnerstag",      False],
        [ "easter(self.startYear) + datetime.timedelta(days= -2)", "Karfreitag",          True],
        [ "easter(self.startYear) + datetime.timedelta(days= -1)", "Karsamstag",          False],
        [ "easter(self.startYear)"                               , "Ostersonntag",        True],
        [ "easter(self.startYear) + datetime.timedelta(days=  1)", "Ostermontag",         True],
        [ "easter(self.startYear) + datetime.timedelta(days= 39)", "Christi Himmelfahrt", True],
        [ "easter(self.startYear) + datetime.timedelta(days= 49)", "Pfingstsonntag",      True],
        [ "easter(self.startYear) + datetime.timedelta(days= 50)", "Pfingstmontag",       True],
        [ "easter(self.startYear) + datetime.timedelta(days= 60)", "Fronleichnam",        True],
        [ "datetime.datetime(self.startYear, 1, 1)",               "Neujahr",             True],
        [ "datetime.datetime(self.startYear,1, 6)",                "Hl. drei Könige",     True],
        [ "datetime.datetime(self.startYear,2, 2)",                "Lichtmess",           False],   # 40 days after Christmas
        [ "datetime.datetime(self.startYear,2,14)",                "Valentinstag",        False],
        [ "datetime.datetime(self.startYear,5, 1)",                "Tag d. Arbeit",       True],
        [ "datetime.datetime(self.startYear,8, 8)",                "Augsburger Friedensfest", False],
        [ "datetime.datetime(self.startYear,8,15)",                "Mariä Himmelfahrt",   True],
        [ "datetime.datetime(self.startYear,11, 1)",               "Allerheiligen",       True],
        [ "datetime.datetime(self.startYear,11, 2)",               "Allerseelen",         False],
        [ "datetime.datetime(self.startYear,11,11)",               "St. Martin",          False],
        [ "datetime.datetime(self.startYear,12, 6)",               "Nikolaus",            False],
        [ "datetime.datetime(self.startYear,12,24)",               "Hl. Abend",           False],
        [ "datetime.datetime(self.startYear,12,25)",               "1. Weihnachtsfeiertag", True],
        [ "datetime.datetime(self.startYear,12,26)",               "2. Weihnachtsfeiertag", True],
        [ "datetime.datetime(self.startYear,12,31)",               "Silvester",           False],
        [ "datetime.datetime(self.startYear,5,1)  +relativedelta(weekday=SU(+2))", "Muttertag",       False],
       # [ "datetime.datetime(self.startYear,10,1) +relativedelta(weekday=SU(+1))", "Erntedank",       False],
        [ "datetime.datetime(self.startYear,11,23)+relativedelta(weekday=WE(-1))", "Buß- und Bettag", False],
        [ "datetime.datetime(self.startYear,12,25)+relativedelta(weekday=SU(-5))", "Totensonntag",    False],
        [ "datetime.datetime(self.startYear,12,25)+relativedelta(weekday=SU(-4))", "1.Advent",        False],
        [ "datetime.datetime(self.startYear,12,25)+relativedelta(weekday=SU(-3))", "2.Advent",        False],
        [ "datetime.datetime(self.startYear,12,25)+relativedelta(weekday=SU(-2))", "3.Advent",        False],
        [ "datetime.datetime(self.startYear,12,25)+relativedelta(weekday=SU(-1))", "4.Advent",        False],
    ]

    def __init__(self,pStart,pEnd):
        if len(pStart) != 8 or len(pEnd) != 8:
            raise Exception("wrong start-format - need string with 'YYYYMMDD'")
        self.startYear  = int(pStart[0:4])
        self.startMonth = int(pStart[4:6])
        self.startDay   = int(pStart[6:8])
        self.endYear    = int(pEnd[0:4])
        self.endMonth   = int(pEnd[4:6])
        self.endDay     = int(pEnd[6:8])
        self.schedule = []

        for YearCount in range(self.startYear, self.endYear+1):
            for MonthCount in range(self.startMonth, self.endMonth+1):
                myCal = Calendar()
                dayList = []
                for Week in myCal.monthdatescalendar(YearCount,MonthCount):
                    for Day in Week:
                        if Day.month is MonthCount:
                            isoDay = Day.isocalendar()
                            CalWeek = isoDay[1]
                            WeekDay = isoDay[2]
                            thisDay = CDay(self.WeekDayStringList[WeekDay], Day.day, CalWeek)
                            dayList.append(thisDay)
                self.schedule.append(dayList)
        self.__computePublicHolidays()


    def __computePublicHolidays(self):

        for item in self.publicHolidays:
            itemDate = eval(item[0])
            self.schedule[itemDate.month-1][itemDate.day-1].publicHoliday = item[2]
            thisEvent = CiEvent()
            thisEvent.setDateStart(itemDate.strftime("%Y%m%d"))
            thisEvent.Summary = item[1]
            self.addEvent(thisEvent)
        return

    def parseIcsFile(self, pFileName, pCategory="", pDayOffset=0):
        print(pFileName)
        hIcal = CiCalendar(pFileName)
        hIcal.read(pDayOffset)
        for event_obj in hIcal.eventList:
            if pCategory != "":
                event_obj.setCategories(pCategory)
            event_date = event_obj.DateStart
            if event_obj.DateEnd is None:
                event_obj.DateEnd = event_obj.DateStart
            while event_date <= event_obj.DateEnd:
                if event_date.year < self.startYear or event_date.year > self.endYear:
                    event_date = event_date + datetime.timedelta(days=1)
                    continue
                if event_obj.Categories == "holiday":
                    self.schedule[event_date.month-1][event_date.day-1].holiday = True
                elif event_obj.Categories == "garbage":
                    self.schedule[event_date.month-1][event_date.day-1].garbageCollection = event_obj.Summary.split()[0]
                    event_date = event_obj.DateEnd # if event spans more than one day
                else:
                    self.schedule[event_date.month-1][event_date.day-1].set_event(event_obj)
                event_date = event_date + datetime.timedelta(days=1)
                if event_date.year > self.endYear:
                    break
            print("{}: {}".format(event_obj.DateStart, event_obj.Summary))

    def parseBirthdayFile(self, pFileName):
        hIcal = CiCalendar(pFileName)
        hIcal.read()
        for event_obj in hIcal.eventList:
            self.schedule[event_obj.DateStartMonth-1][event_obj.DateStartDay-1].addBirthday(event_obj)

    def parseBirthdayCsvFile(self, pFileName):
        with open(pFileName) as csvfile:
            birthdayreader = csv.reader(csvfile, delimiter='\t', quotechar='"')
            for birthday in birthdayreader:
                # print(birthday)
                birthdayEvent = CiEvent()
                birthdayEvent.setDateStart(birthday[0].replace('-',''))
                birthdayEvent.setSummary('GT: ' + birthday[1])
                birthdayEvent.setStatus(eval(birthday[2]))
                self.addBirthday(birthdayEvent)

    def parseNameDayCsvFile(self, pFileName, pYear):
        with open(pFileName) as csvfile:
            line_number=1
            name_day_reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
            for name_day in name_day_reader:
                logging.info(line_number)
                name_day_event = CiEvent()
                name_day_event.setDateStart('{}'.format(pYear)+name_day[0].replace('-',''))
                name_day_event.setSummary('NT: ' + name_day[1])
                self.addEvent(name_day_event)
                line_number += 1

    def parse_event_csv_file(self, event_file):
        try:
            with open(event_file) as csv_file:
                event_reader = csv.reader(csv_file, delimiter='\t', quotechar='"')
                for event in event_reader:
                    event_item = CiEvent()
                    event_item.setDateStart(event[0].replace('-', ''))
                    event_item.setSummary(event[1])
                    self.addEvent(event_item)
        except:
            logging.warning('could not open: {}'.format(event_file))

    def addEvent(self, pEvent):
        if self.schedule is None:
            return
        self.schedule[pEvent.DateStart.month-1][pEvent.DateStart.day-1].set_event(pEvent)
        return

    def addBirthday(self, pEvent):
        if self.schedule is None:
            return
        self.schedule[pEvent.DateStart.month-1][pEvent.DateStart.day-1].addBirthday(pEvent)
        return

    def getMoonPhaseStr(self, pYear, pMonth, pDay):
        dateString = str(pYear) + '/' + str(pMonth) + '/' + str(pDay) + " 12:00:00"
        moon = ephem.Moon(dateString)
        moonPhase = round(moon.moon_phase, 3)
        return str(moonPhase)


    def printRange(self):
        outString  = str(self.startDay) + "."
        outString += str(self.startMonth) + "."
        outString += str(self.startYear) + " - "
        outString += str(self.endDay) + "."
        outString += str(self.endMonth) + "."
        outString += str(self.endYear)
        print(outString)
        return


    def printSchedule(self):
        self.writeSchedule(sys.stdout)
        return


    def writeSchedule(self,hOut):
        return


    def saveScheduleToHtml(self):
        build_folder = os.path.join('.', 'build', '{}'.format(self.startYear))
        if self.schedule is None:
            return
        if not os.path.exists(build_folder):
            os.makedirs(build_folder)
        actual_year = self.startYear
        for month_idx,month_obj in enumerate(self.schedule):
            filename  = self.MonthStringList[month_idx]
            filename += "_" + str(actual_year)
            hHtmlFile = c_HtmlFile(filename, build_folder)
            hHeadlineTag = c_HtmlTag("h1", filename)
            hHtmlFile.addTag(hHeadlineTag)
            for day_idx,day_obj in enumerate(month_obj):
                dayTag = CDivTag(pClass = "day")
                weekDayTagClass = "week_day"
                if day_obj.WeekDayString is self.WeekDayStringList[6]:
                    dayTag.addClass("saturday")
                elif day_obj.WeekDayString is self.WeekDayStringList[7]:
                    dayTag.addClass("sunday")
                if day_obj.publicHoliday:
                    weekDayTagClass += " public_holiday"
                weekDayTag = CDivTag(day_obj.WeekDayString, weekDayTagClass)
                dayTag.addSubTag(weekDayTag)
                dayOfMonthTag = CDivTag(str(day_obj.DayOfMonth), "day_of_month")
                if day_obj.holiday:
                    dayOfMonthTag.addClass("holiday")
                dayTag.addSubTag(dayOfMonthTag)

                metaInfoTag = CDivTag(self.getMoonPhaseStr(actual_year, (month_idx + 1), day_obj.DayOfMonth), "meta_info")
                dayTag.addSubTag(metaInfoTag)

                calendarDayString = ""
                if day_obj.WeekDayString is self.WeekDayStringList[1]:
                    calendarDayString = "KW"+str(day_obj.CalendarWeek)
                kwTag = CDivTag(calendarDayString, "calendar_week")
                dayTag.addSubTag(kwTag)

                birthdayBlockTag = CDivTag(pClass="birthday_block")
                for event in day_obj.birthdayList:
                    summary = event.Summary + event.getAgeString(self.startYear)
                    eventTag = CDivTag(summary, "birthday")
                    birthdayBlockTag.addSubTag(eventTag)
                dayTag.addSubTag(birthdayBlockTag)

                eventBlockTag = CDivTag(pClass="event_block")
                for event in day_obj.EventList:
                    eventTag = CDivTag(event.Summary, "event")
                    eventBlockTag.addSubTag(eventTag)
                dayTag.addSubTag(eventBlockTag)

                garbageClass = "garbage"
                if day_obj.garbageCollection != "":
                    garbageClass += " " + self.garbageType[day_obj.garbageCollection]
                #print("garbageCollection: {}".format(day_obj.garbageCollection))
                garbageTag = CDivTag(self.garbageType[day_obj.garbageCollection], garbageClass)
                dayTag.addSubTag(garbageTag)

                hHtmlFile.addTag(dayTag)

            hHtmlFile.doSave()

            if month_idx == 11:
                actual_year += 1


def main(args):
    if args.year is None:
        my_kal_year = datetime.datetime.today().year+1
    else:
        my_kal_year = args.year
    my_kal_build_folder = os.path.join('.', 'build', '{}'.format(my_kal_year))
    logging.info('build-folder: '+my_kal_build_folder)
    my_kal_source_folder = os.path.join('.', 'src')
    logging.info('source-folder: '+my_kal_source_folder)
    my_kal_common_folder = os.path.join(my_kal_source_folder, 'common'.format(my_kal_year))
    logging.info('common-folder: '+ my_kal_common_folder)
    my_kal_year_folder = os.path.join(my_kal_source_folder, '{}'.format(my_kal_year))
    my_kal_prev_year_folder = os.path.join(my_kal_source_folder, '{}'.format(my_kal_year-1))
    logging.info('year-folder: '+ my_kal_year_folder)
    # perso folder is for personal data - will not be committed to git
    my_kal_personal_folder = os.path.join(my_kal_source_folder, 'perso')

    myKal = CCal('{}0101'.format(my_kal_year), '{}1231'.format(my_kal_year))
    myKal.printRange()
    myKal.parseNameDayCsvFile(os.path.join(my_kal_common_folder, "Namenstage.csv"), my_kal_year)

    # import school holidays from previous year in order to get proper Christmas Holidays in January
    # pDayOffset=-1 is necessary as the ics-files from schulferien.org have DTEND set to the day when school begins.
    myKal.parseIcsFile(os.path.join(my_kal_prev_year_folder, "ferien_bayern_{}.ics".format(my_kal_year-1)), pCategory="holiday", pDayOffset=-1)
    myKal.parseIcsFile(os.path.join(my_kal_year_folder, "ferien_bayern_{}.ics".format(my_kal_year)), pCategory="holiday", pDayOffset=-1)
    # import public holidays
    myKal.parseIcsFile(os.path.join(my_kal_year_folder, "feiertage_bayern_{}.ics".format(my_kal_year)), pCategory="holiday")
    # import garbage collection
    myKal.parseIcsFile(os.path.join(my_kal_year_folder, "Abfuhrkalender-Fünfstetten-{}.ics".format(my_kal_year)), pCategory="garbage")
    # import birthday events - replace by your personal data
    myKal.parseBirthdayCsvFile(os.path.join(my_kal_personal_folder, "myGeburtstage.csv"))
    # import general events - replace by your personal data
    myKal.parse_event_csv_file(os.path.join(my_kal_personal_folder, "my_events.csv"))
    # export/save planer to html files located in the build/<year> folder
    myKal.saveScheduleToHtml()
    copy(os.path.join(my_kal_common_folder, 'stylesheet.css'),my_kal_build_folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='create a calendar')
    parser.add_argument('--verbose', action='store_true', default=False, help='show more information')
    parser.add_argument('--debug', action='store_true', default=False, help='run in debug mode')
    parser.add_argument('--year', type=int, help='define the year for the planer.')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    main(args)
