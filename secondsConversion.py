intervals = (
    ('TJEDANA:', 604800),  # 60 * 60 * 24 * 7
    ('DANA:', 86400),    # 60 * 60 * 24
    ('SATI:', 3600),    # 60 * 60
    ('MINUTA:', 60),
    ('SEKUNDI:', 1),
    )

def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(name, value))
    return ', '.join(result[:granularity])