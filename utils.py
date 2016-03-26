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


def int_to_code(i, size, num_chars=64):
    code = ""
    for _ in xrange(size):
        code += chars64[i % num_chars]
        i //= num_chars
    return code


def code_to_int(code, num_chars=64):
    result = 0
    for char in reversed(code):
        result *= num_chars
        result += chars64.index(char)
    return result
