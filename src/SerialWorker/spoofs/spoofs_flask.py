import flask
import os
app = flask.Flask(__name__)
@app.route("/update",methods=["POST"])
def update_spoofs():
    pass
@app.route("/")
def index():
    gps_spoof = os.path.exists("/dev/ttyS_GPS")
    altimeter_spoof = os.path.exists("/dev/ttyS_GPS")
    return flask.render_template_string("""
<html>
    <head>
        <meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
        <script type="text/javascript" src="https://code.jquery.com/jquery-2.1.4.min.js"></script>
        <script src='https://api.mapbox.com/mapbox.js/v3.3.1/mapbox.js'></script>
        <link href='https://api.mapbox.com/mapbox.js/v3.3.1/mapbox.css' rel='stylesheet' />
        
        <style>
            body { margin:0; padding:0; }
            #map { width: 100%; height: 700px; }
        </style>
    </head>
    <body>
        <form>
        <div>GPS ALTI<input name="gps_altitude"></div>
        <div>GPS LATI<input name="gps_lat"></div>
        <div>GPS LONG<input name="gps_lon"></div>
        <div>GPS GEOID<input name="gps_geoid"></div>
        <div>ALTITUDE<input name="altitude"></div>
        <input type="submit" value="submit">
        </form>
        <div id="map"></div>
        <script>
            L.mapbox.accessToken = '{{ACCESS_KEY}}';
            var mapboxTiles = L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token={{ACCESS_KEY}}',
                        {
                   attribution: '<a href="https://www.mapbox.com/feedback/">Mapbox</a> <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                   tileSize: 512,
                   zoomOffset: -1
            })
            var map = L.mapbox.map('map');
            map.addLayer(mapboxTiles);
            map.setView([42.3610, -71.0587], 15);
            
        </script>
    </body>
</html>    
    """,ACCESS_KEY="pk.eyJ1Ijoiam9yYW5iZWFzbGV5IiwiYSI6ImNrNTdyeGJoYTA2cDczbHFxMGV3NWM5bXkifQ.jSykM5vl10p8tQINocpl3Q")
app.run(host="0.0.0.0",debug=True)
