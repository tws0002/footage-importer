import math


def to_time_string(duration, hour_str='h', min_str='m', sec_str='s'):
    h = int(math.floor(duration / 60 / 60))
    m = int(math.floor((duration - h * 60 * 60) / 60))
    s = duration % 60
    text = ''
    if h > 0:
        text += '{}{} '.format(h, hour_str)
    if m > 0:
        text += '{}{} '.format(m, min_str)
        text += '{}{}'.format(int(round(s)), sec_str)
    else:
        text += '{:.1f}{}'.format(s, sec_str)
    return text
