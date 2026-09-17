# 🖥️ Desk Display

A Python script for a small SPI screen (Raspberry Pi + ST7789 display) that shows the time, date, current weather, and your next few calendar events — refreshing automatically all day.

## What does it do?

Every second, the script:

1. Checks whether it's time to refresh weather (every 15 minutes) or calendar (every 12 hours), and re-fetches only what's due.
2. Pulls current weather from the **Open-Meteo API** using your latitude/longitude.
3. Pulls upcoming events from your **iCloud calendar** over CalDAV, and keeps the next 3.
4. Redraws the screen with the current time, date, temperature, and your upcoming events.
5. Pushes the finished image to the physical display over SPI.

## What's on screen?

| Section | Content |
|---|---|
| Greeting | "Hi Zachary!" |
| Time | Large, current time (12-hour, no leading zero) |
| Date | Day of week + day + month |
| Weather | Current temperature in °C |
| Upcoming | Next 3 calendar events, soonest first |

## Files in this repo

| File | Description |
|---|---|
| `display.py` | Main loop — fetches weather/calendar data and renders it to the screen |

## Configuration

All the personal bits live at the top of the script:

| Setting | What it's for |
|---|---|
| `LATITUDE` / `LONGITUDE` | Used for the weather lookup |
| `ICLOUD_EMAIL` | Your iCloud account email |
| `ICLOUD_APP_PASSWORD` | An app-specific password (not your real iCloud password) for CalDAV access |
| `DISPLAY_WIDTH` / `DISPLAY_HEIGHT`, `X_OFFSET` / `Y_OFFSET` | Match these to your specific ST7789 panel |

## How it works

- **`draw_screen()`** builds a fresh 240×280 image every loop using Pillow (a Python imaging library) — drawing centered text for each line, a separator, then the event list.
- **`fetch_weather()`** hits Open-Meteo's forecast endpoint and returns the rounded current temperature and weather code.
- **`fetch_calendar()`** logs into iCloud via CalDAV, pulls events for the next 90 days from every calendar on the account, and returns the soonest 3 that haven't started yet.
- **`fetch_weather_calender_data()`** is the scheduler — it only re-fetches weather or calendar data once their respective interval has elapsed, so the Pi isn't hammering either API every second.
- The **main loop** ties it together: fetch (if due) → draw → sleep 1 second → repeat, forever.

## How to run it

Requirements: Python 3, a Raspberry Pi wired to an ST7789 SPI display, and these packages:

```bash
pip install adafruit-circuitpython-rgb-display pillow requests caldav icalendar
```

Fill in your latitude/longitude and iCloud credentials at the top of the script, then run:

```bash
python display.py
```

The screen will start updating immediately and keep running until stopped.

## Data sources

- Weather comes from [Open-Meteo](https://open-meteo.com/), a free open-source weather API that needs no API key.
- Calendar events come from Apple's iCloud CalDAV server, using an app-specific password generated from your Apple ID account page.
