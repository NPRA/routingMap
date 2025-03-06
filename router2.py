# %%
import folium
import io
from PIL import Image
import folium.features
import json
import requests

# %%
m = folium.Map([69.1, 15.8],zoom_start=10,zoom_control=False)



def addroutetomap(steder):
    # %% [markdown]
    # Enter Parameters:

    # %%
    showPopup = False # vis popup med info om stengte veier når kartet åpnes

    # [start. via, .., stopp]

    bruksklasse = "" # mulige bruksklasser (sett til "" for vanlig bil): [ Bk_6_28, Bk_8_32, Bk_T8_40, Bk_T8_50, Bk_10_42, Bk_10_50, Bk_10_56, Bk_10_60 ]

    # %%

    locs = []
    for sted in steder:
        sok = requests.get(f"https://api.kartverket.no/stedsnavn/v1/navn?sok={sted}&utkoordsys=4258&treffPerSide=10&side=1")
        data = sok.json()
        locs.append([data["navn"][0]["representasjonspunkt"]["nord"],data["navn"][0]["representasjonspunkt"]["øst"]])
    print(locs)

    # %%
    stops = locs #[[63.428633,9.513474],[63.490839,9.35194]]
    stopParam =  ""
    for s in stops:
        stopParam = stopParam + str(s[1])+","+str(s[0])+";"
    print(stopParam[:-1])    
    stopParam = stopParam[:-1]

    # %%

    baseurl = 'https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/best'
    url1 = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry'
    if bruksklasse != "":
        baseurl = "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/bruksklasseTommerTransport"
        url1 = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry'
        url1 = url1 + "&Bruksklasse=" + bruksklasse
    x = requests.get(url1)
    print(x.url)
    gjson = x.json()
    if gjson.get('code') is not None and gjson['code'] == 9005:
        print("No route found")
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
                        folium.Marker(
                            icon=folium.Icon(color="red"),
                            location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                            popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150,show=showPopup) #feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                        ).add_to(m)
                    else:
                        folium.CircleMarker(
                        radius=4, fill_color="black", fill_opacity=0.8, color="black", weight=1,
                        location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                        popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150)#feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                    ).add_to(m)
                else:
                    if activeNow:
                        folium.CircleMarker(
                            radius=4, fill_color="orange", fill_opacity=0.8, color="black", weight=1,
                            location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                            popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150)#feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                        ).add_to(m)
                    else:
                        folium.CircleMarker(
                            radius=4, fill_color="gray", fill_opacity=0.8, color="black", weight=1,
                            location=[feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['y'], feat["properties"]["roadFeatures"]["trafficMessages"][0]['location']['x']],
                            popup=folium.Popup(feat["properties"]["trafficMsg"]+"</br>"+"Active: "+str(activeNow)+"</br>"+description,max_width=150)#feat["properties"]["roadFeatures"]["trafficMessages"][0]['type'],
                        ).add_to(m)
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
            ).add_to(m)
        folium.FitOverlays(max_zoom=12).add_to(m)

    # %%
    url = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry&AvoidTrafficMessageTypes=roadclosed'
    if bruksklasse != "":
        baseurl = "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/bruksklasseTommerTransport"
        url = baseurl+'?Stops='+stopParam+'&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry&AvoidTrafficMessageTypes=roadclosed'
        url = url + "&Bruksklasse=" + bruksklasse
    print(url)
    x = requests.get(url)

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
            }).add_to(m)
        folium.FitOverlays(max_zoom=12).add_to(m)

steder1 = ["Trondheim", "Bergen"]
steder2 = ["oslo", "stavanger"]
steder3 = ["trondheim", "mo i rana"]

addroutetomap(steder1)
addroutetomap(steder2)
addroutetomap(steder3)

# %%
img_data = m._to_png(5)
img = Image.open(io.BytesIO(img_data))
img.save('route.png')


