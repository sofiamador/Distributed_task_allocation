import threading

mail = {}
lock = threading.Lock()


def SendAlgoData(msg: str, to: str):
    lock.acquire()
    lst = mail.get(to, [])
    lst.append(msg)
    mail[to] = lst
    lock.release()


def GetAlgoData(to):
    lock.acquire()
    ans = mail.get(to, [])
    mail[to] = []
    lock.release()
    return ans
