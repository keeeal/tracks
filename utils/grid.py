def from_hex(x, y):
    return (
        -(x if y % 2 == 0 else x + 0.5),
        y * 3**0.5 / 2,
    )
