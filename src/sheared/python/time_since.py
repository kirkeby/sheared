# vim:syntax=python:textwidth=0
#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import time

def split_durations(duration, durations):
    """\
    split_durations(duration, durations) -> durations-tuple

    Calculate how many of each of durations there are in duration, going
    left-to-right removing already counted durations. Adding one extra
    element to the result-tuple with the remainder.

    For example:
    
      split_durations(42, (40,)) is (40, 2)
      split_durations(12, (5, 3)) is (2, 0, 1)

    See sheared.python.time_since.time_since and s.p.t_s.strftime_since
    for actual uses.
    """
    result = [0] * (len(durations) + 1)
    for i in range(len(durations)):
        while duration >= durations[i]:
            duration = duration - durations[i]
            result[i] = result[i] + 1
    result[-1] = duration

    return tuple(result)

def strftime_since(when, now=None, fields=None):
    """\
    strftime_since(when[, now]) -> string

    Format difference between now and when as a human-friendly string
    (e.g. "1 month, 2 hours")."""

    years, months, days, hours, minutes, _ = time_since(when, now)
    fragments = [(years, 'year'), (months, 'month'), (days, 'day'),
                 (hours, 'hour'), (minutes, 'minute'),]
    if not months:
        weeks, days = split_durations(days, (7,))
        fragments[1] = weeks, 'week'
        fragments[2] = days, 'day'

    fields_seen = 0
    stringses = [] # preeecious stringses
    for i, w in fragments:
        if i > 1:
            stringses.append('%d %ss' % (i, w))
        elif i > 0:
            stringses.append('%d %s' % (i, w))
        
        if stringses:
            fields_seen = fields_seen + 1
        if (not fields is None) and (fields_seen == fields):
            break

    if stringses:
        return ', '.join(stringses)
    else:
        return 'less than a minute'
    
def time_since(when, now=None, multipliers=(12, 30, 24, 60, 60)):
    """\
    time_since(when[, now]) -> (years, months, days, hours, minutes, seconds)
    
    Return a tuple of the time that has passed since when; now is
    optional, time.time() is used if not given. Only works for
    now >= when.
    
    Note: This is a crude approximation, it assumes ideal months (i.e.
    30 days per month)."""

    if now is None:
        now = int(time.time())
    if when > now:
        raise ValueError, 'when > now'

    durations = list(multipliers)
    for i in range(len(durations) - 1, 0, -1):
        durations[i - 1] = durations[i - 1] * durations[i]

    return split_durations(now - when, durations)
