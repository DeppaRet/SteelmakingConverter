import hashlib

class Hash(object):
    status = ""

    def getHash(tmp):
        #password = code.readline()
        global encrypt
        result = hashlib.md5(tmp.encode())
        return result.hexdigest()

