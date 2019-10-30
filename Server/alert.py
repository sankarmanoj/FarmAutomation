import urllib # Python URL functions
import urllib2 # Python URL functions
import json
def send_sms(message,phone_numbers):
    authkey = json.load(open("authkey.json","r"))
    authkey = "94916AlRR0HFvIxX561a6549" # Your authentication key.

    mobiles = "%s"%(phone_numbers[0]) # Multiple mobiles numbers separated by comma.
    for this_number in phone_numbers[1:]:
        mobiles +=",%s"%(this_number)

    sender = "RCKYFM" # Sender ID,While using route4 sender id should be 6 characters long.
    route = "4" # Define route
    # Prepare you post parameters
    values = {
              'authkey' : authkey,
              'mobiles' : mobiles,
              'message' : message,
              'sender' : sender,
              'route' : route
              }


    url = "http://api.msg91.com/api/sendhttp.php" # API URL
    print values

    postdata = urllib.urlencode(values) # URL encoding the data here.
    req = urllib2.Request(url, postdata)
    response = urllib2.urlopen(req)
    output = response.read() # Get Response

    print output # Print Response
