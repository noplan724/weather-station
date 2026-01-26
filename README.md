# MacTiny Weather Station 🌤️💾

![MacTiny Screenshot](https://i.ibb.co/9mZ4Zf71/tinymac2.png)

A retro weather station styled after the classic Macintosh OS (System 6/7). Designed for Raspberry Pi (with hardware PWM support) or any Linux server (Debian/Ubuntu/Proxmox).

The station displays weather data from OpenWeatherMap and local air quality values from Sensor.Community.

## 📋 Features

* **Retro Design:** Macintosh OS (System 6/7) interface.
* **Multi-User Capable:** Configuration via URL parameters (no hardcoded keys).
* **History:** Saves 24h history for each sensor individually.
* **Server-Safe:** Runs on standard servers (LXC/Docker), hardware functions are safely ignored.
* **Night Mode:** Automatic brightness control (Raspberry Pi only).

## 💡 Auto-Brightness (Raspberry Pi Only)

If the software is running on a Raspberry Pi and a display is connected via PWM on **GPIO 18** (e.g., Waveshare DPI displays), the station automatically adjusts brightness based on the time of day:

* **Daytime (07:00 - 22:00):** 100% Brightness.
* **Nighttime (22:00 - 07:00):** 30% Brightness.

*Note for Server Users:* On systems without the specific PWM chip (Proxmox, PC, Cloud), this function is automatically disabled. No errors will occur.

## 📂 Folder Structure

For the app to work, your folder structure must look exactly like this:

```text
wetterstation/
├── app.py                 # The main server (Python Code)
├── requirements.txt       # List of dependencies
├── templates/
│   └── index.html         # The design (HTML/CSS/JS)
└── static/
    └── fonts/
        └── ChicagoFLF.ttf # IMPORTANT: Place font here!

```
🚀 Installation
1. Clone & Prepare
Upload the code to your Server/Pi.

2. Get the Font
For licensing reasons, the font is not included in this repository.

Download ChicagoFLF here:
```
https://www.1001freefonts.com/de/chicago.font
```


Unzip the file.

Create the folder static/fonts/ in your project directory.

Copy the file ChicagoFLF.ttf into that folder.

3. Setup Environment (Recommended)
It is recommended to use a virtual environment:

```

# Enter folder
cd wetterstation

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install flask requests

```

▶️ Start
Start the server with the following command:
```

python3 app.py

```
The server runs on port 5000 by default. (If you close the console, the server stops. For continuous operation, use systemd or screen.)

🖥️ Usage & URL Parameters
The weather station is configured entirely via the URL. This allows you to share the link with friends so they can use their location and their API keys.

URL Structure: http://YOUR-IP:5000/?owm=KEY&lat=LAT&lon=LON&sensor=ID

The Parameters:

owm: Your OpenWeatherMap API Key (Free at openweathermap.org).

lat: The Latitude of your location (e.g. 52.52).

lon: The Longitude of your location (e.g. 13.40).

sensor (Optional): The ID of a fine dust sensor from maps.sensor.community (e.g. 12345).

Example Link:

Replace the placeholders with your actual values (Example: London):

http://192.168.1.50:5000/?owm=your_long_api_key&lat=51.5&lon=-0.1&sensor=12345

⚖️ License
The source code (Python/HTML) is licensed under the MIT License. The font "ChicagoFLF" is subject to its own license terms and is the property of its respective creator.


