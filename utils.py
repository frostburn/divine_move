def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)

def str_base(number, base):
    if number < 0:
        return '-' + str_base(-number, base)
    d, m = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)


chars64 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"


def int_to_code(i, size):
    code = ""
    for _ in xrange(size):
        code += chars64[i % 64]
        i //= 64
    return code


def code_to_int(code):
    result = 0
    for char in reversed(code):
        result *= 64
        result += chars64.index(char)
    return result
