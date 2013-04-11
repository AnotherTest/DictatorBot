import os

class AccessList:
    _filename = None
    _list = []

    def __init__(self, fname, owner):
        self._filename = fname
        if not os.path.isfile(self._filename):
            open(self._filename, "w+").write(owner + "\n")
        self._load()
    
    def _load(self):
        with open(self._filename, "r") as f:
            self._list = f.read().split()

    def _save(self):
        with open(self._filename, "w") as f:
            f.write("\n".join(self._list) + "\n")

    def hasAccess(self, user):
        """ Checks whether a given user (+ hostname) has access. """
        return user in self._list

    def add(self, user):
        """ Adds a user to the access list. """
        self._list.append(user)
        with open(self._filename, "a") as f:
            f.write(user)

    def remove(self, user):
        """ Removes a user from the access list. """
        self._list.remove(user)
        self._save()
