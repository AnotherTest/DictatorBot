def doCaps(str1, str2): # pretty ugly, please cleanup
    """Makes str1 be capitalized exactly like str2."""
    i = 0
    result = ""
    for c in str1:
        if str2[i].isupper():
            result += c.upper()
        else:
            result += c
        i = (i + 1) % (len(str2) - 1)
    return result

