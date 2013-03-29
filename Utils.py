import urllib2

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

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
 
def find(value, l):
    try:
        return [i for (i, x) in enumerate(l) if x == value][0]
    except:
        return None

def httpGet(url):
    return urllib2.urlopen(url).read()
