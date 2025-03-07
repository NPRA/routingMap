
import folium
import io
from PIL import Image
import folium.features
import json
import requests
from folium.plugins import FloatImage
import base64
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Oppsett av logging 
import logging
import logging.handlers

LOG_FILENAME = 'Log Freight Info.log'

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

myLogger = logging.getLogger('myLogger')
myLogger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when = 'D', interval = 1, backupCount=90)
handler.setFormatter(formatter)
myLogger.addHandler(handler)

myLogger.info("################################################################")
myLogger.info("#      Starter nedlasting av strekninger                       #")
myLogger.info("################################################################")
# Oppsett av kartet
map = folium.Map([69.1, 15.8],zoom_start=10,zoom_control=False)

# Oppsett av standard verdier for kalulasjoner
#
showPopup = True # vis popup med info om stengte veier når kartet åpnes
makeImage = True # lag bilde av kartet
makeWeb = True # Lager en hjemmeside av resultatet
height = 0 # høyde på kjøretøy, i meter
bruksklasse = "Bk_10_50" # mulige bruksklasser (sett til "" for vanlig bil): [ Bk_6_28, Bk_8_32, Bk_T8_40, Bk_T8_50, Bk_10_42, Bk_10_50, Bk_10_56, Bk_10_60 ]


#baseurl = 'https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/best'
baseurl = "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/bruksklasseNormalTransport"

myLogger.info("Base url used: " + baseurl)

# Rutene som skal beregnes og legges inn i kartet
ruter = [["Trondheim", "Bergen"],
         ["Oslo", "Trondheim"],
         ["Oslo", "Bergen"],
         ["Oslo", "Stavanger"],
         ["Trondheim", "Fauske"],
         ["Fauske", "Bodø"],
         ["Fauske", "Nordkjosbotn"],
         ["Nordkjosbotn", "Tromsø"],
         ["Nordkjosbotn", "Alta"],
         ["Alta", "Kirkenes"]
         ]

# Ferdig med setting parametere 
############################################################

def leggRutePaaKart(map, steder, baseurl):

    stops = []
    for sted in steder:
        sok = requests.get(f"https://api.kartverket.no/stedsnavn/v1/navn?sok={sted}&fuzzy=true&utkoordsys=4258&treffPerSide=10&side=1")
        myLogger.info(sok.url)
        myLogger.info(f'Status code: {sok.status_code} - {sok.reason}')
        data = sok.json()
        stops.append([data["navn"][0]["representasjonspunkt"]["nord"],data["navn"][0]["representasjonspunkt"]["øst"]])

    #stops = locs 
    stopParam =  ""
    for s in stops:
        stopParam = stopParam + str(s[1])+","+str(s[0])+";"
    # print(stopParam[:-1])    
    stopParam = stopParam[:-1]    

    #baseurl = 'https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/best'
    url1 = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry'
    if bruksklasse != "":
        #baseurl = "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/bruksklasseNormalTransport"
        url1 = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry'
        url1 = url1 + "&Bruksklasse=" + bruksklasse
    if height > 0:
        url1 = url1 + "&Height="+str(height)
    x = requests.get(url1)
    myLogger.info(x.url)
    myLogger.info(f'Status code: {x.status_code} - {x.reason}')
    #print(x.url)
    gjson = x.json()
    if gjson.get('code') is not None and gjson['code'] == 9005:
        print("No route found")
        myLogger.critical("NO ROUTE FOUND between {steder[0]} and {steder[-1]}")
    else:
        newgjson = {
            "type": "FeatureCollection",
            "features": gjson['routes'][0]['features']
        }
        for feat in newgjson["features"]:
            if feat["properties"]["roadFeatures"]["trafficMessages"]:
                print(feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'])
                feat["properties"]["trafficMsg"] = feat["properties"]["roadFeatures"]["trafficMessages"][0]['type']

                ## Get traffic message details
                description = ""
                activeNow = True
                if True: #feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'] == "RoadClosed":
                    simpleDetailsUrl = feat["properties"]["roadFeatures"]["trafficMessages"][0]['simpleDetailsUrl']
                    trafficMessageReq = requests.get(simpleDetailsUrl,headers={"Accept":"application/vnd.svv.v1+json;charset=utf-8","X-System-ID": "kajshlkjahsdlkjh"})
                    print(simpleDetailsUrl)
                    trafficMessage = trafficMessageReq.json()
                    activeNow = trafficMessage['trafficMessages'][0]['isActiveNow']
                    description = trafficMessage['trafficMessages'][0]['descriptionOfTrafficMessage'].replace("|","</br>")

                ## Add markers for road closed and circle for other messages
                if feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'] == "RoadClosed":
                    if activeNow:
                        hendelser = folium.Marker(
                            icon=folium.Icon(color="red"),
                            location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                            popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150,show=showPopup) #feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                        )#.add_to(map)
                    else:
                        hendelser = folium.CircleMarker(
                        radius=4, fill_color="black", fill_opacity=0.8, color="black", weight=1,
                        location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                        popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150)#feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                    )#.add_to(map)
                else:
                    if activeNow:
                        hendelser = folium.CircleMarker(
                            radius=4, fill_color="orange", fill_opacity=0.8, color="black", weight=1,
                            location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                            popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150)#feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                        )#.add_to(map)
                    else:
                        hendelser = folium.CircleMarker(
                            radius=4, fill_color="gray", fill_opacity=0.8, color="black", weight=1,
                            location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                            popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150)#feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                        )#.add_to(map)
                #hendelser.add_to(map)
            else:
                feat["properties"]["trafficMsg"] = {"msgType":"No traffic messages"}

        popup = folium.GeoJsonPopup(fields=['trafficMsg'])
        g = folium.GeoJson(newgjson,
                style_function=lambda feature: {
                    "color": "red",
                    "weight": 2,
                    "dashArray": "5, 5",
                },
                popup=popup
            ).add_to(map)
        folium.FitOverlays(max_zoom=12).add_to(map)
        
    ## Henter ut den tilgjengelige ruta.    
    url = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry&AvoidTrafficMessageTypes=roadclosed'
    if bruksklasse != "":
        url = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry&AvoidTrafficMessageTypes=roadclosed'
        url = url + "&Bruksklasse=" + bruksklasse
    if height > 0:
        url = url + "&Height="+str(height)
    #print(url)
    x = requests.get(url)
    myLogger.info(x.url)
    myLogger.info(f'Status code: {x.status_code} - {x.reason}')

    gjson = x.json()
    if gjson.get('code') is not None and gjson['code'] == 9005:
        print("No route found")
    else:
        newgjson = {
            "type": "FeatureCollection",
            "features": gjson['routes'][0]['features']
        }


        g = folium.GeoJson(newgjson,style_function=lambda feature: {
                "color": "green",
                "weight": 2.5,
            }).add_to(map)
        folium.FitOverlays(max_zoom=12).add_to(map)
    # Tegner ut hendelsene på toppen - tror jeg
    hendelser.add_to(map)

for steder in ruter:
    leggRutePaaKart(map, steder, baseurl)

myLogger.info("Skriver resultat til fil")

now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d %H_%M_%S")

image = Image.new("RGB", (200, 70), "lightgray")
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("Junicode.ttf", size=10)
draw.text((10, 10), f"Status: {date_time} - {bruksklasse}", font=font, fill=(1, 1, 1))

font = ImageFont.truetype("Junicode.ttf", size=8)
draw.text((10, 30), f'Status for norske næringstransportruter basert', font=font, fill=(1, 1, 1))
draw.text((10, 40), f'på NVDB og VTS vegmeldinger', font=font, fill=(1, 1, 1))
draw.text((10, 60), f'ITS seksjonen Statens vegvesen', font=font, fill=(1, 1, 1))

image.save("result.png")

with open("result.png", 'rb') as lf:
  # open in binary mode, read bytes, encode, decode obtained bytes as utf-8 string
  b64_content = base64.b64encode(lf.read()).decode('utf-8')

FloatImage('data:image/png;base64,{}'.format(b64_content), bottom=0, left=0).add_to(map)
#FloatImage("result.png", bottom=10, left=15).add_to(m)


filnavn = "Freight info"

if makeImage:
    img_data = map._to_png(5)
    img = Image.open(io.BytesIO(img_data))
    img.save(f'{filnavn}.png')
    
if makeWeb:
    map.save(f'{filnavn}.html')

myLogger.debug("Kart med ruter er ferdig")    




