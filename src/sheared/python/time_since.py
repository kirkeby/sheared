import time

def time_since(when, now=None, multipliers=(12, 30, 24, 60, 60)):
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

    durations = list(multipliers)
    for i in range(len(durations) - 1, 0, -1):
        durations[i - 1] = durations[i - 1] * durations[i]

    diff = now - when
    result = [0] * (len(durations) + 1)
    for i in range(len(durations)):
        while diff >= durations[i]:
            diff = diff - durations[i]
            result[i] = result[i] + 1
    result[-1] = diff

    return tuple(result)
