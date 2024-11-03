# NOTE: "# type: ignore" is for Pylance
# NOTE: Requires CircuitPython 8.0 or later

import os # type: ignore
import adafruit_lps2x # type: ignore
import adafruit_sht4x # type: ignore
import board # type: ignore
import busio # type: ignore
import socketpool # type: ignore
import ipaddress # type: ignore
import wifi # type: ignore
from adafruit_httpserver import Server, Request, Response, MIMETypes # type: ignore


# Set static IP address
ipv4 = ipaddress.IPv4Address("192.168.0.100")
netmask = ipaddress.IPv4Address("255.255.255.0")
gateway = ipaddress.IPv4Address("192.168.0.1")
wifi.radio.set_ipv4_address(ipv4=ipv4,netmask=netmask,gateway=gateway)

ssid = os.getenv('CIRCUITPY_WIFI_SSID')
password = os.getenv('CIRCUITPY_WIFI_PASSWORD')

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/resources", debug=False)

MIMETypes.configure(
    default_to="text/html",
    # Unregistering unnecessary MIME types can save memory
    keep_for=[".html", ".css", ".ico"],
)

print("Connecting to", ssid)
while not wifi.radio.ipv4_address:
    try:
        wifi.radio.connect(ssid, password)
    except ConnectionError as e:
        print("could not connect to AP, retrying: ", e)
print("Connected to", str(wifi.radio.ap_info.ssid, "utf-8"), "\tRSSI:", wifi.radio.ap_info.rssi)
print(f"Listening on http://{wifi.radio.ipv4_address}:5000")

i2c = busio.I2C(board.SCL1, board.SDA1, frequency=125000) # uses esp32-S2 board.SCL1 and board.SDA1

# Initialise sensors
sht = adafruit_sht4x.SHT4x(i2c)
sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
lps = adafruit_lps2x.LPS22(i2c)

# Get readings from the sensors
def temp():
    temperature = sht.temperature
    return temperature

def rel_humidity():
    relative_humidity = sht.relative_humidity
    return relative_humidity

def temp_conv_f():
    temp_F = (temp() * 9/5) + 32
    return temp_F

def abs_pressure():
    pressure = lps.pressure
    return pressure

def webpage():
    html = f"""<!doctype html>\n\
<html lang='en'>\n\
<head>\n\
<meta charset='utf-8'>\n\
<meta name='viewport' content='width=device-width, initial-scale=1'>\n\
<meta http-equiv='refresh' content='60'>\n\
<link rel='icon' href='favicon.ico'>\n\
<link rel='stylesheet' href='index.css'>\n\
<title>Dashboard</title>\n\
</head>\n\
<body>\n\
<h5>Air Temperature</h5>\n\
<h1>{temp():.1f}&deg;C / {temp_conv_f():.1f}&deg;F</h1>\n\
<h5>Relative Humidity</h5>\n\
<h1>{rel_humidity():.1f}%</h1>\n\
<h5>Absolute Pressure</h5>\n\
<h1>{abs_pressure():.1f} hPa</h1>\n\
</body>\n\
</html>"""
    return html

@server.route("/")
def base(request: Request):
    """Return the current sensor readings in an HTML page"""
    return Response(request, str(webpage()), content_type="text/html")

# Never returns
server.serve_forever(str(wifi.radio.ipv4_address), 5000)
