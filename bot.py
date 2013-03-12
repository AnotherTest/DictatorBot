from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twisted.python import log

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

def isEmote(msg):
    """Checks whether msg is a single emote."""
    emotes = [":)", ":(", ";)", ":p", ":d", ":o", ":]", ":[", ":l", ":3", "<3", "^_^"]
    return msg.lower() in emotes

def isFutile(msg):
    """Checks whether msg is a futile message, that is a message without much purpose (typically considered spam)."""
    futiles = ["wat", "wut", "wtf", "ftw", "omg", "omfg", "zomg", "zomfg", "uh", "lmao"]
    return msg.lower() in futiles


def checkMessage(user, msg):
    """
    Checks whether a given message is acceptable and returns a tuple:
        ( acceptable, error message if any)
    """
    if isEmote(msg):
        return (False, "overuse of emoticons") 
    if isFutile(msg):
        return (False, "use of noobish interjects")
    return (True, "")


class IRCBot(irc.IRCClient):
    nickname = "samantus"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        print 'Connection established.'
        self.join(self.factory.channel)
        print 'Joined channel', self.factory.channel

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if msg[0] == "`":
            self.runCommand(msg[1:])
        result = checkMessage(user, msg)
        if result[0] == False:
            self.msg(user, "May I remind you, " + user + ", that " + result[1] + " is not appreciated.")
    
    def runCommand(self, msg):
        if msg.lower() == "welcome":
            self.msg(self.factory.channel, doCaps("Welcome to IRCX, a place of joy. I hope you will enjoy your stay. We only have 2 rules: 1. Praise sam 2. Do anything this bot tells you", msg))


class IRCFactory(protocol.ClientFactory):
    protocol = IRCBot
    channel = ""
    def __init__(self, channel):
        self.channel = channel

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: %s" % reason
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost: %s" % reason
        connector.connect()


host, port = "i.r.cx", 6667
fact = IRCFactory("#brows")
reactor.connectTCP(host, port, fact)
reactor.run()
