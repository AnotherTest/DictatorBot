from collections import defaultdict
import random, pickle, os

class AiBrain:
    _chain = defaultdict(list)
    _length = 2
    _eos = "\n"
    _filename = ""
    
    def __init__(self, fname):
        self._filename = fname
        if not os.path.isfile(self._filename):
            self.save()
        with open(self._filename, "rb") as f:
            self._chain = pickle.load(f)

    def _getRandomWord(self):
        return random.choice(self._chain[random.choice(self._chain.keys())])

    def _cleanValue(self, val):
        return val.replace(".", "").replace(",", "").replace("?", "")\
                   .replace(";", "").replace("!", "").lower()
    
    def learn(self, msg):
        print msg.split()
        buf = [self._eos] * self._length
        for word in msg.split():
            word = self._cleanValue(word)
            if not word.replace("-", "").replace("'", "").isalnum():
                continue
            self._chain[tuple(buf)].append(word)
            del buf[0]
            buf.append(word)
        self._chain[tuple(buf)].append(self._eos)
   
    def _extractWords(self, msg):
        return [x for x in self._cleanValue(msg).split() if x.isalnum()]

    def respond(self, msg, max_length = 10000):
        words = self._extractWords(msg)
        if len(words) < self._length:
            message = [self._getRandomWord() for i in range(self._length)]
        else:
            i = random.choice(range(len(words) - 1))
            message = [words[i], words[i + 1]]
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
        with open(self._filename, "wb") as f:
            pickle.dump(self._chain, f)
 
