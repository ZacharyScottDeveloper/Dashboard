import board
import digitalio
from adafruit_rgb_display import st7789
from PIL import ImageDraw, ImageFont, Image
import time
from datetime import datetime, timezone, timedelta
import requests
import caldav
from icalendar import Calendar

# ---- Screen configuration ----
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 280
X_OFFSET = 0
Y_OFFSET = 20

# ---- Your info ----
LATITUDE = 0.0
LONGITUDE = 0.0
ICLOUD_EMAIL = "you@icloud.com"
ICLOUD_APP_PASSWORD = ""

# ---- Pins ----
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D27)
spi = board.SPI()
backlight = digitalio.DigitalInOut(board.D18)
backlight.direction = digitalio.Direction.OUTPUT
backlight.value = True

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=24000000,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    x_offset=X_OFFSET,
    y_offset=Y_OFFSET,
)

last_weather_fetch = 0
last_calendar_fetch = 0
weather_data = None
calendar_data = None

WEATHER_INTERVAL = 15 * 60
CALENDAR_INTERVAL = 12 * 60 * 60


def draw_centered_text(draw, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (DISPLAY_WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)


def fetch_weather():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        current = resp.json()["current_weather"]
        return {"temp": round(current["temperature"]), "code": current["weathercode"]}
    except Exception as e:
        print(f"[weather] fetch failed: {e}")
        return None


def fetch_calendar():
    try:
        client = caldav.DAVClient(
            url="https://caldav.icloud.com",
            username=ICLOUD_EMAIL,
            password=ICLOUD_APP_PASSWORD,
        )
        principal = client.principal()
        now_dt = datetime.now(timezone.utc)
        end_dt = now_dt + timedelta(days=90)
        upcoming = []

        for cal in principal.calendars():
            events = cal.search(start=now_dt, end=end_dt, event=True, expand=True)
            for event in events:
                ical = Calendar.from_ical(event.data)
                for component in ical.walk():
                    if component.name != "VEVENT":
                        continue
                    dtstart = component.get("dtstart").dt
                    if not hasattr(dtstart, "tzinfo") or dtstart.tzinfo is None:
                        continue
                    if dtstart < now_dt:
                        continue
                    upcoming.append((dtstart, str(component.get("summary"))))

        upcoming.sort(key=lambda pair: pair[0])
        return upcoming[:3]
    except Exception as e:
        print(f"[calendar] fetch failed: {e}")
        return []


def fetch_weather_calender_data():
    global last_weather_fetch, last_calendar_fetch, weather_data, calendar_data
    now = time.time()

    if now - last_weather_fetch > WEATHER_INTERVAL:
        weather_data = fetch_weather()
        last_weather_fetch = now

    if now - last_calendar_fetch > CALENDAR_INTERVAL:
        calendar_data = fetch_calendar()
        last_calendar_fetch = now


def draw_screen(weather, calendar):
    image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)

    now = datetime.now()
    time_str = now.strftime("%I:%M").lstrip("0")
    ampm = now.strftime("%p").lower()
    date_str = now.strftime("%A, %d %b")

    y = 15
    draw_centered_text(draw, y, "Hi Zachary!", font_small, (170, 168, 158))
    y += 30

    draw_centered_text(draw, y, f"{time_str} {ampm}", font_large, (255, 255, 255))
    y += 48

    draw_centered_text(draw, y, date_str, font_small, (216, 207, 196))
    y += 30

    if weather is not None:
        weather_str = f"{weather['temp']}°C"
    else:
        weather_str = "--°C"
    draw_centered_text(draw, y, weather_str, font_medium, (232, 149, 90))
    y += 35

    draw.line((15, y, DISPLAY_WIDTH - 15, y), fill=(60, 55, 50), width=1)
    y += 15

    draw_centered_text(draw, y, "Upcoming", font_small, (170, 168, 158))
    y += 24

    if calendar:
        for dtstart, summary in calendar:
            draw_centered_text(draw, y, summary, font_small, (255, 255, 255))
            y += 20
    else:
        draw_centered_text(draw, y, "No upcoming events", font_small, (170, 168, 158))

    display.image(image)


while True:
    fetch_weather_calender_data()
    draw_screen(weather_data, calendar_data)
    time.sleep(1)
EOF
