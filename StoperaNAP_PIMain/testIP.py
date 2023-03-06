from datetime import timedelta, datetime
import urllib.request
import constants
import json

if __name__ == "__main__":
    hours_24 = timedelta(hours=24)
    starttime = datetime.now() + timedelta(hours=23)
    req = urllib.request.Request(constants.IP_API)
    response = urllib.request.urlopen(req)
    body = response.read()
    if (response.status == 200):
        result = json.loads(body.decode("utf-8"))
        ip = result['ip']
        print("remote ip: %s" % ip)
