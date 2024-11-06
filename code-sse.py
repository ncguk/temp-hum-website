# NOTE: "# type: ignore" is for Pylance
# NOTE: Requires CircuitPython 8.0 or later

from time import monotonic # type: ignore
import adafruit_lps2x # type: ignore
import adafruit_sht4x # type: ignore
import board # type: ignore
import busio # type: ignore
import ipaddress # type: ignore
import socketpool # type: ignore
import wifi # type: ignore
from adafruit_httpserver import Server, Request, Response, SSEResponse, GET, MIMETypes # type: ignore


# Set static IP address
ipv4 = ipaddress.IPv4Address("192.168.0.100")
netmask = ipaddress.IPv4Address("255.255.255.0")
gateway = ipaddress.IPv4Address("192.168.0.1")
wifi.radio.set_ipv4_address(ipv4=ipv4,netmask=netmask,gateway=gateway)

i2c = busio.I2C(board.SCL1, board.SDA1, frequency=125000) # uses esp32-S2 board.SCL1 and board.SDA1

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/resources", debug=False)

MIMETypes.configure(
    default_to="text/event-stream",
    # Unregistering unnecessary MIME types can save memory
    keep_for=[".html", ".css", ".ico", ".js"],
)

sse_response1: SSEResponse = None
sse_response2: SSEResponse = None
sse_response3: SSEResponse = None
sse_response4: SSEResponse = None
next_event_time = monotonic()

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

HTML_TEMPLATE = """
<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <meta http-equiv='Cache-Control' content='no-cache'>
    <meta http-equiv='Content-Type' content='text/event-stream'>
    <link rel='icon' href='favicon.ico'>
    <link rel='stylesheet' href='index.css'>
    <title>Dashboard</title>
  </head>
  <body>
    <h5>Air Temperature</h5>
    <h1><span id='tempc'>-</span> / <span id='tempf'>-</span></h1>
    <h5>Relative Humidity</h5>
    <h1><span id='humid'>-</span></h1>
    <h5>Absolute Pressure</h5>
    <h1><span id='press'>-</span></h1>
    <script>
      const airTempc = document.getElementById('tempc');
      const eventSource1 = new EventSource('/connect-client1');
      eventSource1.onmessage = function(event) { airTempc.innerHTML = event.data + '&deg;C'; };
      <!--eventSource1.onerror = error => airTempc.textContent = error;-->

      const relHumi = document.getElementById('humid');
      const eventSource2 = new EventSource('/connect-client2');
      eventSource2.onmessage = function(event) { relHumi.innerHTML = event.data + '&percnt;'; };
      <!--eventSource2.onerror = error => relHumi.textContent = error;-->

      const absPres = document.getElementById('press');
      const eventSource3 = new EventSource('/connect-client3');
      eventSource3.onmessage = function(event) { absPres.innerHTML = event.data + ' hPa'; };
      <!--eventSource3.onerror = error => absPres.textContent = error;-->

      const airTempf = document.getElementById('tempf');
      const eventSource4 = new EventSource('/connect-client4');
      eventSource4.onmessage = function(event) { airTempf.innerHTML = event.data + '&deg;F'; };
      <!--eventSource4.onerror = error => airTempf.textContent = error;-->
    </script>
  </body>
</html>
"""


@server.route("/", GET)
def client(request: Request):
    return Response(request, HTML_TEMPLATE, content_type="text/html")

@server.route("/connect-client1", GET)
def connect_client1(request: Request):
    global sse_response1  # pylint: disable=global-statement

    if sse_response1 is not None:
        sse_response1.close()  # Close any existing connection

    sse_response1 = SSEResponse(request)

    return sse_response1

@server.route("/connect-client2", GET)
def connect_client2(request: Request):
    global sse_response2  # pylint: disable=global-statement

    if sse_response2 is not None:
        sse_response2.close()  # Close any existing connection

    sse_response2 = SSEResponse(request)

    return sse_response2

@server.route("/connect-client3", GET)
def connect_client3(request: Request):
    global sse_response3  # pylint: disable=global-statement

    if sse_response3 is not None:
        sse_response3.close()  # Close any existing connection

    sse_response3 = SSEResponse(request)

    return sse_response3

@server.route("/connect-client4", GET)
def connect_client4(request: Request):
    global sse_response4  # pylint: disable=global-statement

    if sse_response4 is not None:
        sse_response4.close()  # Close any existing connection

    sse_response4 = SSEResponse(request)

    return sse_response4


server.start(str(wifi.radio.ipv4_address))
while True:
    server.poll()

    # Send an event every n seconds
    if sse_response1 is not None and next_event_time < monotonic():
        air_temp = "%.1f" % temp()
        sse_response1.send_event(str(air_temp))
        #next_event_time = monotonic()

    # Send an event every n seconds
    if sse_response2 is not None and next_event_time < monotonic():
        rel_humi = "%.1f" % rel_humidity()
        sse_response2.send_event(str(rel_humi))
        #next_event_time = monotonic()

    # Send an event every n seconds
    if sse_response3 is not None and next_event_time < monotonic():
        abs_pres = "%.1f" % abs_pressure()
        sse_response3.send_event(str(abs_pres))
        #next_event_time = monotonic()

    # Send an event every n seconds
    if sse_response4 is not None and next_event_time < monotonic():
        air_tempf = "%.1f" % temp_conv_f()
        sse_response4.send_event(str(air_tempf))
        next_event_time = monotonic() + 1
