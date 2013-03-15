from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twisted.python import log
import Utils

def isEmote(msg):
    """Checks whether msg is a single emote."""
    emotes = [":)", ":(", ";)", ":p", ":d", ":o", ":]", ":[", ":l", ":3", "<3", "^_^"]
    return msg.lower() in emotes

def isFutile(msg):
    """Checks whether msg is a futile message, that is a message without much purpose (typically considered spam)."""
    futiles = ["wat", "wut", "ftw", "omg", "omfg", "zomg", "zomfg", "uh"]
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
    _users = dict() # maps names to warning levels
    _threshold = 3

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        print 'Connection established.'
        self.join(self.factory.channel)
        print 'Joined channel', self.factory.channel
    
    def kickUser(self, user):
        self.msg("chanserv", "kick " + self.factory.channel + " " + user
                 + " User received at least " + str(self._threshold)
                 + " warning(s).")
        del self._users[user]

    def warnUser(self, user, warning): 
        if not (user in self._users):
            self._users[user] = 0
        self._users[user] += 1
        self.msg(user, "May I remind you, " + user + ", that " + warning 
                 + " is not appreciated.")
        if self._users[user] >= self._threshold:
            self.kickUser(user)
    
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if msg[0] == "`":
            self.runCommand(user, msg[1:])
        result = checkMessage(user, msg)
        if result[0] == False:
            self.warnUser(user, result[1])

    def runCommand(self, user, msg):
        cmd = msg.lower()
        if cmd == "welcome":
            self.msg(self.factory.channel, Utils.doCaps(
                "Welcome to IRCX, a place of joy. I hope you will enjoy"
                " your stay. We only have 2 rules: 1. Praise sam 2. Do"
                " anything this bot tells you", msg
            ))
        elif cmd == "help":
            self.msg(self.factory.channel, Utils.doCaps(
                "`help, `welcome", msg
            ))
 
    def userRenamed(self, oldname, newname):
        if oldname in self._users:
            self._users[newname] = self._users[oldname]
            del self._users[oldname]

class IRCFactory(protocol.ClientFactory):
    protocol = IRCBot
    channel = ""

    def __init__(self, nick, password, channel):
        self.protocol.nickname = nick
        self.protocol.password = password
        self.channel = channel

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: %s" % reason
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost: %s" % reason
        connector.connect()


host, port = "i.r.cx", 6667
fact = IRCFactory("samantus", "pass", "#brows")
reactor.connectTCP(host, port, fact)
reactor.run()
