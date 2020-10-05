
def from_hex(x, y):
    x = x + .5 if y % 2 else x
    y = y * 3**0.5 / 2
    return -x, y


def to_hex(x, y):
    y = round(y / (3**0.5 / 2))
    x = round(x + .5 if y % 2 else x)
    return -x, y
