# coding=utf-8

from datetime import date, timedelta
from time import time, mktime

QUARTER = {
    1: 1, 2: 2, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4, 11: 4, 12: 4
}

QUARTER_MONTHS = {
    1: [1, 2, 3],
    2: [4, 5, 6],
    3: [7, 8, 9],
    4: [10, 11, 12]
}


def timestamp(day):
    return int(mktime(day.timetuple()))


def now():
    return int(time())


def today():
    return timestamp(date.today())


def yesterday():
    return timestamp(date.today() - timedelta(1))


def tomorrow():
    return timestamp(date.today() + timedelta(1))


def this_month():
    t = date.today()
    first_day = date(t.year, t.month, 1)
    return timestamp(first_day)


def next_month():
    t = date.today()
    if t.month == 12:
        next = date(t.year + 1, 1, 1)
    else:
        next = date(t.year, t.month + 1, 1)
    return timestamp(next)


def last_month():
    t = date.today()
    if t.month == 1:
        last = date(t.year - 1, 12, 1)
    else:
        last = date(t.year, t.month - 1, 1)
    return timestamp(last)


def this_quarter():
    t = date.today()
    quarter = QUARTER[t.month]
    first_month = (quarter - 1) * 3 + 1
    return timestamp(date(t.year, first_month, 1))


def next_quarter():
    t = date.today()
    quarter = QUARTER[t.month]
    first_month = (quarter - 1) * 3 + 1
    if first_month == 10:
        next = date(t.year + 1, 1, 1)
    else:
        next = date(t.year, first_month + 3, 1)
    return timestamp(next)


def last_quarter():
    t = date.today()
    quarter = QUARTER[t.month]
    first_month = (quarter - 1) * 3 + 1
    if first_month == 1:
        last = date(t.year - 1, 10, 1)
    else:
        last = date(t.year, first_month - 3, 1)
    return timestamp(last)


def get_month_range(year_month):
    year_month = year_month.split('-')
    year = int(year_month[0])
    month = int(year_month[1])
    begin = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return timestamp(begin), timestamp(end)


def get_quarter_range(year_quarter):
    year_quarter = year_quarter.split('#')
    year = int(year_quarter[0])
    quarter = int(year_quarter[1])
    begin = date(year, (quarter - 1) * 3 + 1, 1)
    if quarter == 4:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, quarter * 3 + 1, 1)
    return timestamp(begin), timestamp(end)


def get_year_range(year):
    year = int(year)
    begin = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    return timestamp(begin), timestamp(end)


YEAR = '{year}'
YEAR_MONTH = '{year}-{month:0>2}'
YEAR_QUARTER = '{year}#{quarter}'
DAY = '{year}-{month:0>2}-{day:0>2}'


class Time(object):
    def __init__(self, value=None):
        """
        Args:
            value: can be None, Date object or (year, month, day) tuple
        """
        if value is None:
            self.time = date.today()
        elif isinstance(value, date):
            self.time = value
        elif isinstance(value, tuple) and len(value) == 3:
            year, month, day = value
            self.time = date(year, month, day)
        else:
            raise TypeError('vale must be None, Date object '
                            'or (year, month, day) tuple.')

        self._month = YEAR_MONTH.format(
                year=self.time.year, month=self.time.month)
        self.quarter_number = QUARTER[self.time.month]
        self._quarter = YEAR_QUARTER.format(
                year=self.time.year, quarter=self.quarter_number)
        self._day = DAY.format(
                year=self.time.year, month=self.time.month,
                day=self.time.day
        )

    @property
    def year(self):
        return self.time.year

    @property
    def month(self):
        return self._month

    @property
    def quarter(self):
        return self._quarter

    @property
    def day(self):
        return self._day

    def day_range(self):
        begin = timestamp(self.time)
        end = begin + 24 * 3600
        return begin, end

    def quarter_months(self):
        months = []
        for month in QUARTER_MONTHS[self.quarter_number]:
            months.append(YEAR_MONTH.format(
                    year=self.time.year, month=month))
        return months

    def year_quarters(self):
        quarters = []
        for i in range(1, 5):
            quarters.append('{year}#{quarter}'.format(
                    year=self.time.year, quarter=i
            ))
        return quarters

    def time_ago(self, interval, number):
        pass

    def month_ago(self, number=0):
        tmp = 0
        if self.time.month <= number:
            tmp = (number - self.time.month) / 12 + 1
        return YEAR_MONTH.format(
                year=self.time.year - tmp,
                month=self.time.month + tmp * 12 - number
        )

    def quarter_ago(self, number=0):
        tmp = 0
        if self.quarter_number <= number:
            tmp = (number - self.quarter_number) / 4 + 1
        return YEAR_QUARTER.format(
                year=self.time.year - tmp,
                quarter=self.quarter_number + tmp * 4 - number
        )

    def year_ago(self, number=0):
        return YEAR.format(year=self.time.year - number)

    def get_recent(self, interval, number):
        recent = []
        if interval == 'month':
            for i in xrange(number):
                recent.append(self.month_ago(i))
        elif interval == 'quarter':
            for i in xrange(number):
                recent.append(self.quarter_ago(i))
        elif interval == 'year':
            for i in xrange(number):
                recent.append(self.year_ago(i))
        else:
            raise ValueError('Argument interval must be '
                             'month, quarter or year.')
        return recent

    def get_recent_ranges(self, interval, number):
        time_range = []
        if interval == 'month':
            for i in xrange(number):
                month_ago = self.month_ago(i)
                time_range.append((month_ago, get_month_range(month_ago)))
        elif interval == 'quarter':
            for i in xrange(number):
                quarter_ago = self.quarter_ago(i)
                time_range.append(
                        (quarter_ago, get_quarter_range(quarter_ago)))
        elif interval == 'year':
            for i in xrange(number):
                year_ago = self.year_ago(i)
                time_range.append((year_ago, get_year_range(year_ago)))
        else:
            raise ValueError('Argument interval must be '
                             'month, quarter or year.')
        return time_range
