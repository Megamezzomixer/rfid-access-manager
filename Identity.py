class Identity:
    _name = ""
    _uid = 0
    _ident = ""


    def __init__(self, name="", ident="", uid=0):
        self._name = name
        self._ident = str.replace(ident, " ", "")
        self._uid = uid

    def getName(self):
        return self._name

    def getUID(self):
        return self._uid

    def getIdent(self):
        return self._ident

    def setName(self, name: str):
        self._name = name

    def setUID(self, uid: int):
        self._uid = uid

    def setIdent(self, ident: str):
        self._ident = ident