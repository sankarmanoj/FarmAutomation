import json
import time

while True:
    try:

        with open("controls.json","r") as fp:
            controls = json.load(fp)

        controls['control-pump-main-tank'] = 1

        with open("controls.json","w") as fp:
            json.dump(controls,fp,indent = 4)
        time.sleep(5*60)




        with open("controls.json","r") as fp:
            controls = json.load(fp)

        controls['control-pump-main-tank'] = 0

        with open("controls.json","w") as fp:
            json.dump(controls,fp,indent = 4)

        time.sleep(15*60)
    except Exception as e:
        print e

