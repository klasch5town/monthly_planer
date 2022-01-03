# README #

## Summary
This project is for generating a monthly calendar as html-file-set. Each month is represented by a single html-file.
Events, holidays etc. can be added with the help of ics-/vcs-files.

## How do I get set up? ###

The program is written for python3.

### Dependencies - add following modules

* https://pypi.python.org/pypi/ephem/ => sudo pip3 install ephem
* https://dateutil.readthedocs.org/en/latest/# => sudo pip3 install python-dateutil
* not yet: https://github.com/zulumarketing/html2pdf

### Configuration

At the moment most configuration must be done in code.

#### Holiday ical-file

Holiday can be added as ical-file: 
- http://www.schulferien.org/iCal/
- https://www.ferienwiki.de/exports/de

#### public holidays

Currently there are just german public holidays supported - hardcoded.

#### adding Birthdays

Adding birthdays can be done with two file-types:

* ics/ical files
* CSV-files

The setup of the CSV-file is:

* three columns separated by Tabulator
* First column: the birthday-date as string "YYYY-MM-DD"
* Second column: the Name of the Person having birthday
* Third column: the date is approved (True) or not (False)

**Note:** The third column was introduced as the pyKal-application calculates the age for all birth-dates and if you are sure of the day and month but not of the year it can happen that you face someone with it's wrong age. That can lead to a embarrassing situation. In order to avoid such mistakes the pyKal-app will add a question-mark if the birth-date is not marked as aproved.


### How to get it printed

#### Print it with browser
* enable printing of background-colors/-images at the printing-dialog of your browser (e.g. Firefox: Print-Dialog => Options-Tab: Print Background)
* disable printing header/footer

=> my Setup:
* print from browser (Firefox) in into file
* month with 31 day may need scaling at 97%
* open created PDF and adjust A3 und **landscape**
* print it

#### Print it with Pandoc
Not much experience yet.
* sudo apt-get install pandoc
* sudo apt-get install texlive
* sudo apt-get install lmodern
* example: pandoc -c stylesheet.css -o kalender_2018.pdf *.html

## TODO

* add graphical view of moon-phases (e.g. SVG)
* add event-time to calendar-output

## Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

## Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
