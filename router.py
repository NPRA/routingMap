#https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/best?Stops=9.513474%2C63.428633%3B9.35194%2C63.490839&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry&AvoidTrafficMessageTypes=roadclosed

import folium
import io
from PIL import Image
import folium.features
import json
import requests
x = requests.get('https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingservice/api/Route/best?Stops=9.513474%2C63.428633%3B9.35194%2C63.490839&InputSRS=EPSG_4326&OutputSRS=EPSG_4326&ReturnFields=Geometry&AvoidTrafficMessageTypes=roadclosed')


def style_function(feature):
    props = feature.get('properties')
    markup = f"""
            <div style="font-family: courier new; font-size: 3em;">
            <div style="width: 10px;
                        height: 10px;
                        border: 1px solid black;
                        border-radius: 5px;
                        background-color: red;">
            </div>
            {props.get('id')}
        </div>
    """
    return {"html": markup}

def create_map():
    m = folium.Map([69.1, 15.8],zoom_start=10,zoom_control=False)
    #lambda x: {x['properties']['id']},
    #folium.DivIcon(html=f"""<div style="font-family: courier new; color: blue">{lambda x: {x['properties']['id']}}</div>""")
    #folium.DivIcon(html=f"""<div style="font-family: courier new; color: blue">{lambda x: {x['properties']['id']}}</div>""")
    #gjson = json.load(open("Jammertest_locations.geojson"))
    gjson = x.json()
    #print(gjson)
    newgjson = {
        "type": "FeatureCollection",
        "features": gjson['routes'][0]['features']
    }


    g = folium.GeoJson(newgjson,).add_to(m)
    folium.FitOverlays(max_zoom=12).add_to(m)


    img_data = m._to_png(5)
    img = Image.open(io.BytesIO(img_data))
    img.save('gjson.png')

create_map()