import requests
import json
import os
import time
import re
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

# --- PWM CONFIGURATION (Server Safe) ---
# Works on Raspberry Pi, ignores errors on servers/PCs
PWM_PATH = "/sys/class/pwm/pwmchip0"
PWM_PERIOD = 100000 

def init_pwm():
    if not os.path.exists(PWM_PATH): return
    try:
        if not os.path.exists(f"{PWM_PATH}/pwm0"):
            try:
                with open(f"{PWM_PATH}/export", "w") as f: f.write("0")
            except OSError: pass
        time.sleep(0.1)
        with open(f"{PWM_PATH}/pwm0/period", "w") as f: f.write(str(PWM_PERIOD))
        with open(f"{PWM_PATH}/pwm0/duty_cycle", "w") as f: f.write(str(PWM_PERIOD))
        with open(f"{PWM_PATH}/pwm0/enable", "w") as f: f.write("1")
        os.system(f"sudo chmod 666 {PWM_PATH}/pwm0/duty_cycle")
    except: pass

def set_brightness(percent):
    if not os.path.exists(f"{PWM_PATH}/pwm0/duty_cycle"): return
    if percent < 0: percent = 0
    if percent > 100: percent = 100
    duty = int((percent / 100) * PWM_PERIOD)
    try:
        with open(f"{PWM_PATH}/pwm0/duty_cycle", "w") as f: f.write(str(duty))
    except: pass

# --- HISTORY MANAGEMENT ---
def get_history_filename(sensor_id):
    # Filename based on Sensor ID.
    safe_id = re.sub(r'[^a-zA-Z0-9]', '', str(sensor_id))
    if not safe_id: safe_id = "no_sensor"
    return f"history_{safe_id}.json"

def load_history(sensor_id):
    filename = get_history_filename(sensor_id)
    if not os.path.exists(filename): return []
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return []

def save_history(sensor_id, data_list):
    filename = get_history_filename(sensor_id)
    now = time.time()
    # Keep data only for the last 24h
    one_day_ago = now - (24 * 3600)
    clean_list = [d for d in data_list if d.get('dt', 0) > one_day_ago]
    try:
        with open(filename, 'w') as f: json.dump(clean_list, f)
    except: pass
    return clean_list

# --- API REQUESTS ---

def get_community_pm(sensor_id):
    if not sensor_id: return None
    try:
        url = f"https://data.sensor.community/airrohr/v1/sensor/{sensor_id}/"
        r = requests.get(url, timeout=3)
        data = r.json()
        if not data: return None
        latest = data[0]
        values = latest.get('sensordatavalues', [])
        val_pm10 = None
        val_pm25 = None
        for v in values:
            if v['value_type'] == 'P1': val_pm10 = float(v['value'])
            if v['value_type'] == 'P2': val_pm25 = float(v['value'])
        if val_pm10 is not None and val_pm25 is not None:
            return {'pm10': round(val_pm10, 1), 'pm2_5': round(val_pm25, 1)}
        return None
    except: return None

def get_owm_air_data(api_key, lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        r = requests.get(url, timeout=3)
        data = r.json()
        if "list" in data and len(data["list"]) > 0:
            c = data["list"][0]["components"]
            return {
                'nox': round(c.get("no", 0) + c.get("no2", 0), 1),
                'pm2_5': round(c.get("pm2_5", 0), 1),
                'pm10': round(c.get("pm10", 0), 1)
            }
        return None
    except: return None

def get_current_data(api_key, sensor_id, lat, lon):
    try:
        # A) Weather (Set lang=en for English)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=en"
        w_res = requests.get(weather_url, timeout=3).json()
        if w_res.get("cod") != 200: return None

        # B) Air Data
        # Strategy: Get OWM first, overwrite with local sensor if available
        air_data = get_owm_air_data(api_key, lat, lon)
        
        val_nox = 0
        val_pm25 = 0
        val_pm10 = 0
        
        if air_data:
            val_nox = air_data['nox']
            val_pm25 = air_data['pm2_5']
            val_pm10 = air_data['pm10']
        
        # Overwrite if Sensor-ID is present and valid
        if sensor_id:
            comm_data = get_community_pm(sensor_id)
            if comm_data:
                val_pm25 = comm_data['pm2_5']
                val_pm10 = comm_data['pm10']

        # Brightness (Server-Safe)
        hour = datetime.now().hour
        if hour >= 22 or hour < 7: set_brightness(30)
        else: set_brightness(100)

        data = {
            "dt": time.time(),
            "time_str": datetime.now().strftime("%H:%M"),
            "temp": round(w_res["main"]["temp"], 1),
            "desc": w_res["weather"][0]["description"].title(),
            "icon": w_res["weather"][0]["icon"],
            "humidity": w_res["main"]["humidity"],
            "pressure": w_res["main"]["pressure"],
            "wind_speed": round(w_res["wind"]["speed"] * 3.6, 1),
            "visibility": round(w_res.get("visibility", 10000) / 1000, 1),
            "pm2_5": val_pm25,
            "pm10": val_pm10,
            "nox": val_nox,
            "location": w_res.get("name", "Unknown")
        }
        return data

    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def index():
    # Read parameters from URL
    user_owm = request.args.get('owm')
    user_sensor = request.args.get('sensor') 
    user_lat = request.args.get('lat')
    user_lon = request.args.get('lon')
    
    current = None
    history = []
    
    # Only load if mandatory parameters (Key + Coordinates) are present
    if user_owm and user_lat and user_lon:
        history = load_history(user_sensor)
        current = get_current_data(user_owm, user_sensor, user_lat, user_lon)
        
        if current:
            # Save only every 4 minutes
            if not history or (current['dt'] - history[-1]['dt'] > 240):
                history.append(current)
                history = save_history(user_sensor, history)
    
    now = datetime.now()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    date_day = f"{days[now.weekday()]}, {now.strftime('%m/%d/%Y')}"
    
    return render_template('index.html', 
                           time=now.strftime("%H:%M"), 
                           date=date_day, 
                           weather=current, 
                           history=history)

if __name__ == '__main__':
    init_pwm()
    app.run(host='0.0.0.0', port=5000, debug=True)