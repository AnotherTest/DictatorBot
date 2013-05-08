from collections import defaultdict
import random, pickle, os, Utils, string

class AiBrain:
    def __init__(self, fname, nick, rate):
        self._chain = defaultdict(list)
        self._length = 2
        self._eos = "\n"
        self._filename = fname
        self._nickname = nick
        self.chat_rate = rate
        
        if not os.path.isfile(self._filename):
            self.save()
        with open(self._filename, "rb") as f:
            self._chain = pickle.load(f)

    def _getRandomWord(self):
        """ Gets a random word from the chain. """
        return random.choice(self._chain[random.choice(self._chain.keys())])

    def _cleanValue(self, val):
        """ Cleans up a given word: removes punctuation and lowercases. """
        return filter(lambda x: x in string.printable, Utils.stripAll(val,
             [".", ",", "?", ";", "!", "(", ")", '"', "'"]
        ).lower())
    
    def learn(self, msg):
        """ Parses msg and adds it to the Markov chain. """
        buf = [self._eos] * self._length
        for word in msg.split():
            word = self._cleanValue(word)
            if not word.replace("-", "").isalnum():
                continue
            self._chain[tuple(buf)].append(word)
            del buf[0]
            buf.append(word)
        self._chain[tuple(buf)].append(self._eos)
   
    def _extractWords(self, msg):
        """ Extracts and cleans all proper words from a list of words. """
        return [x for x in self._cleanValue(msg).split() if x.isalnum() and
                x != self._nickname]

    def isChatty(self):
        """ Returns whether the AI bot feels like talking. """
        return random.random() <= self.chat_rate

    def _getInitWords(self, words):
        """
        Selects 2 random words from a list, usable as the beginning of a
        response.
        """
        i = random.choice(range(len(words) - 1))
        return [words[i], words[i + 1]]
        
    def respond(self, msg, max_length = 10000):
        """ Responds to a given msg. """
        words = self._extractWords(msg)
        if len(words) < self._length:
            message = [self._getRandomWord() for i in range(self._length)]
        else:
            message = self._getInitWords(words)

        for i in xrange(max_length):
            try:
                next_word = random.choice(self._chain[tuple(message[-2:])])
            except IndexError:
                continue
            if next_word == self._eos:
                break
            message.append(next_word)
        return " ".join(message).capitalize()
   
    def save(self):
        """ Saves the brain for later loading. """
        with open(self._filename, "wb") as f:
            pickle.dump(self._chain, f)
 
