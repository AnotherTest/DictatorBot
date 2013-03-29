from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twisted.python import log
import Utils, Command

def isEmote(msg):
    """Checks whether msg is a single emote."""
    emotes = [":)", ":(", ";)", ":p", ":d", ":o", ":]", ":[", ":l", ":3", "<3", "^_^", ":|", "xd", "xp"]
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

def getLast3Messages(user, logs):
    logs2 = logs
    logs2.reverse()
    result = []
    for pair in logs2:
        if pair[0] == user:
            result.append(pair)
        if len(result) == 3:
            break

    return result

def detectSpam(user, logs):
    msg = getLast3Messages(user, logs)
    if len(msg) < 3:
        return False
    return len([x for x in msg if x[1] == x[1].upper()]) == len(msg)

class IRCBot(irc.IRCClient):
    _users = dict() # maps names to warning levels
    _threshold = 3
    _interpreter = None
    _logs = [] # stores previous messages
    
    def __init__(self):
        self._interpreter = Command.Interpreter("functions.p")

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        print 'Connection established.'
        self.join(self.factory.channel)
        print 'Joined channel', self.factory.channel
    
    def kickUser(self, user, reason):
        self.msg("chanserv", "kick " + self.factory.channel + " " + user
                 + " " + reason)
        if user in self._users:
            del self._users[user]

    def warnUser(self, user, warning):
        if not (user in self._users):
            self._users[user] = 0
        self._users[user] += 1
        self.msg(user, "May I remind you, " + user + ", that " + warning 
                 + " is not appreciated.")
        if self._users[user] >= self._threshold:
            self.kickUser(user, "User received at least " + str(self._threshold)
                          + " warning(s).")
    
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        self._logs.append((user, msg))
        if msg[0] == "`":
            self.runCommand(user, msg[1:])
        result = checkMessage(user, msg)
        if result[0] == False:
            self.warnUser(user, result[1])
        if detectSpam(user, self._logs):
            self.kickUser(user, "Quit spamming.")

    def runCommand(self, user, msg):
        try:
            tokens = []
            parser = Command.getEbnfParser(tokens)
            parser.parseString(msg, True)
            print tokens
            for s in self._interpreter.interpret(tokens):
                if s != None:
                    self.msg(self.factory.channel, s)
        except:
            self.msg(self.factory.channel, ("Oops, seems like something "
                    "went wrong..."))
            raise           

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


host, port = "localhost", 6667
fact = IRCFactory("samantus", "", "#")
reactor.connectTCP(host, port, fact)
reactor.run()
