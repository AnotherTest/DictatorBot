import urllib2, ConfigParser

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
    if url[:7] != "http://":
        url = "http://" +  url
    return urllib2.urlopen(url).read()

def stripAll(s, replacements):
    """ Strips multiple strings at once from a given string. """    
    for value in replacements:
        s = s.replace(value, "")    
    return s

def compare(x, y):
    if x < y:
        return -1
    elif x > y:
        return 1
    else:
        return 0

def readConfig(filename):
    config = ConfigParser.RawConfigParser()
    config.read(filename)
    return config
