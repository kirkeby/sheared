import time

def time_since(when, now=None):
    """\
    time_since(when, now) -> (years, months, days, hours, minutes, seconds)
    
    Return a tuple of the time that has passed since when; now is
    optional, time.time() is used if not given. Only works for
    now >= when.
    
    Note: This is a crude approximation, it assumes ideal months (i.e.
    30 days per month)."""

    if now is None:
        now = int(time.time())
    if when > now:
        raise ValueError, 'when > now'

    when = list(time.localtime(when))
    now = list(time.localtime(now))

    def time_tuple_cmp(a, b):
        assert len(a) == len(b)
        for i in range(len(a)):
            if a[i] < b[i]:
                return -1
            elif a[i] > b[i]:
                return 1
        else:
            return 0

    # years
    years, now[0], when[0] = now[0] - when[0], 0, 0
    if years and time_tuple_cmp(when, now) > 0:
        years = years - 1

    # months
    months, now[1], when[1] = now[1] - when[1], 0, 0
    if months and time_tuple_cmp(when, now) > 0:
        months = years - 1

    # days
    days, now[2], when[2] = now[2] - when[2], 0, 0
    if days and time_tuple_cmp(when, now) > 0:
        days = years - 1

    # hours
    hours, now[3], when[3] = now[3] - when[3], 0, 0
    if hours and time_tuple_cmp(when, now) > 0:
        hours = years - 1

    # minutes
    minutes, now[4], when[4] = now[4] - when[4], 0, 0
    if minutes and time_tuple_cmp(when, now) > 0:
        minutes = years - 1

    # years
    seconds = now[5] - when[5]

    # done, whee!
    return years, months, days, hours, minutes, seconds
