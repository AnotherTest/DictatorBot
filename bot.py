from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twisted.python import log
import Utils, AccessList, Command, MarkovAi, time, threading

def isEmote(msg):
    """Checks whether msg is a single emote."""
    emotes = [":)", ":(", ";)", ":p", ":d", ":o", ":]", ":[", ":l", ":3", "<3", "^_^", ":|", "xd", "xp", "o.o"]
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
    for data in logs2:
        if data[1] == user:
            result.append(data)
        if len(result) == 3:
            break
    result.reverse()
    return result

def detectSpam(user, logs):
    msg = getLast3Messages(user, logs)
    if len(msg) < 3:
        return False
    if (msg[0][2] == msg[1][2] == msg[2][2]):
        return True
    return len([x for x in msg if x[2] == x[2].upper()]) == len(msg)

class IRCBot(irc.IRCClient):
    def __init__(self, cfg):
        self._users = dict() # maps names to warning levels
        self._access_list = AccessList.AccessList(
            cfg.get("Bot", "accesslist"), cfg.get("Bot", "owner")
        )
        self._interpreter = Command.Interpreter(
            cfg.get("Bot", "functionsfile")
        )
        self._ai = MarkovAi.AiBrain(
            cfg.get("Bot", "brainfile"), 
            cfg.getfloat("Bot", "chatrate"), self.nickname
        )
        self._use_late_login = cfg.getboolean("Bot", "latelogin")
        self._flush_interval = 300
        self._logs = []
        self._startTimer()

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        if self._use_late_login:
            self.msg("nickserv", "identify " + self.nickname + " "\
                     + self.password)

        print "Connection established."
        self.join(self.factory.channel)
        print "Joined channel", self.factory.channel
    
    def kickUser(self, user, reason):
        """ Kicks a user from the channel. """
        #self.msg("chanserv", "kick " + self.factory.channel + " " + user
        #         + " " + reason)
        self.kick(self.factory.channel, user, reason)
        if user in self._users:
            del self._users[user]

    def warnUser(self, user, warning):
        """
        Warns a user by sending a message and increasing the warning count
        for this user.
        """
        if not (user in self._users):
            self._users[user] = 0
        self._users[user] += 1
        self.msg(user, "May I remind you, " + user + ", that " + warning 
                 + " is not appreciated.")
    
    def logMessage(self, user, msg):
        """ Appends a message to the (temporary) log. """
        self._logs.append((time.time(), user, msg))

    def sortLog(self):
        """ Sorts messages in the log based on receive time. """
        self._logs.sort(lambda m1, m2: Utils.compare(m1[0], m2[0]))

    def _writeLogMessages(self):
        """ Writes the temporary log to the filesystem and clears it. """
        self.sortLog()
        lines = ["[" + time.ctime(m[0]) + "] <" + m[1]
                 + "> " + m[2] + "\n" for m in self._logs]
        logfile = self.factory.channel[1:] + ".log"
        with open(logfile, "a+") as f:
            f.writelines(lines)
        del self._logs[:]

    def _startTimer(self):
        """ Starts the flush timer. """
        self._timer = threading.Timer(
            self._flush_interval, self._flush
        )
        self._timer.start()

    def _flush(self):
        """ Flushes all temporary data such as logs and the ai brain. """
        if len(self._logs) > 0:
            self._writeLogMessages()
        self._ai.save()
        self._startTimer()

    def _aiRespond(self, user, channel, msg):
        """ (Possibly) makes the AI reposnd to a received message. """
        if self._ai.isChatty():
            response = self._ai.respond(msg)
            self.msg(channel, "%s: %s" % (user, response))
   
    def _isHuman(self, user):
        """ Filters out a number of known bots. """
        return user and not (user.lower() in ["nickserv", "chanserv",
            "memoserv", "hostserv"])

    def _handleHumanMsg(self, user, access, channel, msg):
        """ Handles all messages that come from a human. """
        self._ai.learn(msg)
        if self.nickname in msg:
            self._aiRespond(user, channel, msg)
        result = checkMessage(user, msg)
        if result[0] == False:
            self.warnUser(user, result[1])
        if detectSpam(user, self._logs):
            self.kickUser(user, "Quit spamming.")
        if msg[0] == "`":
            self.runCommand(user, channel, msg[1:])
        elif msg[0] == "?" and access:
            self.runConfigCommand(user, channel, msg[1:])

    def privmsg(self, full_user, channel, msg):
        """ Handles all received messages. """
        user = full_user.split('!', 1)[0]
        if channel[0] != "#":
            channel = user
        self.logMessage(user, msg)
        if self._isHuman(user):
            access = self._access_list.hasAccess(full_user)
            self._handleHumanMsg(user, access, channel, msg)

    def topicUpdated(self, user, channel, topic):
        self.logMessage("SERVER", user + " has changed the topic of "
                        + channel + " to: " + topic)

    def userKicked(self, user, kickee, channel, kicker, message):
        self.logMessage("SERVER",
            " %s has kicked %s from %s. Reason: %s" % (kicker, kickee, 
            channel, message)
        )

    def userLeft(self, user, channel):
        self.logMessage("SERVER", "%s has left %s." % (user, channel))

    def userQuit(self, user, msg):
        self.logMessage("SERVER", "%s has quit (%s)." % (user, msg))
    
    def userJoined(self, user, channel):
        self.logMessage("SERVER", "%s has joined %s." % (user, channel))

    def modeChanged(self, user, channel, add, modes, args):
        self.logMessage("SERVER",
            "%s has set mode(s) to %s with args %s in %s." % (user, modes,
             str(args), channel)
        )

    def runCommand(self, user, channel, msg):
        """ Runs a command. """
        try:
            tokens = []
            parser = Command.getEbnfParser(tokens)
            parser.parseString(msg, True)
            print tokens
            for s in self._interpreter.interpret(tokens):
                if s != None:
                    self.msg(channel, "> " + s.replace("\n", "\\"))
        except:
            self.msg(user, "Oops, seems like something went wrong...")
            raise           

    def runConfigCommand(self, user, channel, msg):
        """ Runs a command to modify the configuration at run-time. """
        try:
            data = msg.split(":")
            cmd, args = data[0], data[1].split(",")
            if cmd == "chatrate":
                self._ai.chat_rate = float(args[0])
            elif cmd == "delfn":
                self._interpreter.loadUserFunctions()
                del self._interpreter.user_function_table[args[0].strip()]
                self._interpreter.saveUserFunctions() 
            elif cmd == "accessadd":
                self._access_list.add(args[0].strip())
            elif cmd == "accessdel":
                self._access_list.remove(args[0].strip())
        except:
            self.msg(user, "Oops, seems like something went wrong...")
            raise

    def userRenamed(self, oldname, newname):
        if oldname in self._users:
            self._users[newname] = self._users[oldname]
            del self._users[oldname]
        self.logMessage("SERVER",
            "%s is now known as %s." % (oldname, newname)
        )

    def kickedFrom(self, channel, kicker, message):
        self.join(self.factory.channel)

class IRCFactory(protocol.ClientFactory):
    def __init__(self, config):
        self.config = config
        self.nickname = config.get("Bot", "nickname")
        self.password = config.get("Bot", "password")
        self.channel = "#" + config.get("IRC", "channel")

    def buildProtocol(self, addr):
        bot = IRCBot(config)
        bot.factory = self
        bot.nickname = self.nickname
        bot.password = self.password
        return bot 

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed: %s" % reason
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost: %s" % reason
        connector.connect()

config = Utils.readConfig("dictatorbot.cfg")
host, port = config.get("IRC", "server"), config.getint("IRC", "port")
factory = IRCFactory(config)
reactor.connectTCP(host, port, factory)
reactor.run()
