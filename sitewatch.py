import requests
import time
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv, set_key
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import threading
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
ENV_PATH = ".env"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///monitor.db")

# --- Notification Settings ---
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SLACK_ENABLED = os.getenv("SLACK_ENABLED", "False").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "False").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(r"""
  _____  _             _____            _           
 |  __ \| |           |  _  |          | |          
 | |__) | | ___   ___ | | | | ___   ___| | __ _ ___ 
 |  ___/| |/ _ \ / _ \| | | |/ _ \ / _ \ |/ _` / __|
 | |    | | (_) | (_) |\ \_/ / (_) |  __/ | (_| \__ \\
 |_|    |_|\___/ \___/  \___/ \___/ \___|_|\__,_|___/
                                       CodeByKalvin
""")

# --- Database Setup ---
Base = declarative_base()

class WebsiteStatus(Base):
    __tablename__ = 'website_statuses'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    status = Column(Boolean)
    last_checked = Column(DateTime)
    error = Column(String)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- Helper Functions for DB Interaction ---
def get_session():
    return Session()

def update_db(obj):
    session = get_session()
    session.add(obj)
    session.commit()
    session.close()

def query_db(model, **kwargs):
    session = get_session()
    result = session.query(model).filter_by(**kwargs).first()
    session.close()
    return result

def query_db_all(model, order_by=None, order="desc", **kwargs):
    session = get_session()
    query = session.query(model).filter_by(**kwargs)
    if order_by:
      if order == "asc":
         query = query.order_by(order_by)
      else:
         query = query.order_by(order_by.desc())
    results = query.all()
    session.close()
    return results

def delete_db(model, **kwargs):
    session = get_session()
    objects = session.query(model).filter_by(**kwargs).all()
    for obj in objects:
        session.delete(obj)
    session.commit()
    session.close()

# --- Notification Functions ---
def send_email_alert(url, status, error=None):
    if not all([EMAIL_ENABLED, SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL]):
        return
    try:
        message = MIMEMultipart()
        message['From'] = SMTP_USER
        message['To'] = RECIPIENT_EMAIL
        message['Subject'] = f"Website {url} is {'UP' if status else 'DOWN'}"
        body = f"Website {url} is now {'up' if status else 'down'}!\n{error or ''}"
        message.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)

    except Exception as e:
        print(f"Error sending email for {url}: {e}")


def send_slack_alert(url, status, error=None):
    if not SLACK_ENABLED or not SLACK_WEBHOOK_URL:
        return
    try:
        message = f"Website *{url}* is now {'UP' if status else 'DOWN'}!"
        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification for {url}: {e}")
    except Exception as e:
         print(f"An unexpected error occurred sending Slack notification for {url}: {e}")


def send_telegram_alert(url, status, error=None):
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        message = f"Website {url} is now {'UP' if status else 'DOWN'}!"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
       print(f"Error sending telegram notification for {url}: {e}")
    except Exception as e:
       print(f"An unexpected error occurred sending telegram notification for {url}: {e}")

def send_alert(url, status, error=None):
    if EMAIL_ENABLED:
        send_email_alert(url, status, error)
    if SLACK_ENABLED:
        send_slack_alert(url, status, error)
    if TELEGRAM_ENABLED:
        send_telegram_alert(url, status, error)

def check_website(config):
    url = config["url"]
    headers = config.get("headers", {})
    method = config.get("method", "GET")
    data = config.get("data", None)
    timeout = config.get("timeout", 10)
    start_time = time.time()
    try:
        response = requests.request(method, url, headers=headers, data=data, timeout=timeout)
        response.raise_for_status()
        response_time = int((time.time() - start_time) * 1000)
        if content_check := config.get("content_check"):
            soup = BeautifulSoup(response.text, 'html.parser')
            if not soup.find(string=lambda text: text and content_check in text):
                return False, f"Content check failed: '{content_check}' not found", headers, response_time
        return True, None, headers, response_time
    except requests.exceptions.RequestException as e:
      return False, str(e), headers, None
    except Exception as e:
        return False, str(e), headers, None

def monitor_website(config):
    url = config["url"]
    interval = config.get("interval", 60)
    status = True

    website_status_db = query_db(WebsiteStatus, url=url)
    if not website_status_db:
        website_status_db = WebsiteStatus(url=url, status=status, last_checked=datetime.now())
        update_db(website_status_db)
    update_website_status(website_status_db)
    while True:
        is_up, error, headers, response_time = check_website(config)
        if is_up != status:
          website_status_db = query_db(WebsiteStatus, url=url)
          website_status_db.status = is_up
          website_status_db.last_checked = datetime.now()
          website_status_db.error = error
          update_db(website_status_db)
          send_alert(url, is_up, error)
          update_website_status(website_status_db)
          socketio.emit('update', {'statuses': get_all_statuses()}, namespace='/')
          status = is_up
        time.sleep(interval)

def update_website_status(website_status_db):
     socketio.emit('update', {'statuses': get_all_statuses()}, namespace='/')

def load_config(file_path="config.json"):
    try:
      with open(file_path, 'r') as f:
        config = json.load(f)
        if not isinstance(config, list):
            raise ValueError("Configuration file must contain a list of website configurations.")
        for item in config:
          if "headers" not in item:
             item["headers"] = {}
          if "User-Agent" not in item["headers"]:
             item["headers"]["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        return config
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading config: {e}")
        return []

def save_config_to_file(config, file_path="config.json"):
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Website Configuration saved to {file_path}")
    except Exception as e:
        print(f"Error saving config to file: {e}")

def get_env_settings():
   return {
       "email_enabled": EMAIL_ENABLED,
       "smtp_server": SMTP_SERVER,
       "smtp_port": SMTP_PORT,
       "smtp_user": SMTP_USER,
       "smtp_password": SMTP_PASSWORD,
       "recipient_email": RECIPIENT_EMAIL,
       "slack_enabled": SLACK_ENABLED,
       "slack_webhook_url": SLACK_WEBHOOK_URL,
       "telegram_enabled": TELEGRAM_ENABLED,
       "telegram_bot_token": TELEGRAM_BOT_TOKEN,
       "telegram_chat_id": TELEGRAM_CHAT_ID
    }

def save_env_setting(key, value):
    try:
        set_key(ENV_PATH, key, str(value))
        return True
    except Exception as e:
        print(f"Error updating .env file {key}: {e}")
        return False

def get_all_statuses(sort_by="last_checked", order="desc"):
    statuses = query_db_all(WebsiteStatus, order_by=getattr(WebsiteStatus, sort_by, None), order=order)
    status_list = []
    for status in statuses:
        status_list.append({"url": status.url, "status": status.status, "last_checked": status.last_checked.strftime("%Y-%m-%d %H:%M:%S"), "error": status.error})
    return status_list

def get_response_time_data(url):
    return {}

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@app.route('/')
def index():
   return render_template('index.html', statuses=get_all_statuses(), configs=load_config(), env_settings = get_env_settings() )

@app.route('/save_env', methods=['POST'])
def save_env():
    try:
       for key in request.form:
           if not save_env_setting(key.upper(), request.form[key]):
               print(f"Error saving env setting {key}")
       # reloads the values into global variables
       load_dotenv()
       global EMAIL_ENABLED
       global SMTP_SERVER
       global SMTP_PORT
       global SMTP_USER
       global SMTP_PASSWORD
       global RECIPIENT_EMAIL
       global SLACK_ENABLED
       global SLACK_WEBHOOK_URL
       global TELEGRAM_ENABLED
       global TELEGRAM_BOT_TOKEN
       global TELEGRAM_CHAT_ID
       EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
       SMTP_SERVER = os.getenv("SMTP_SERVER")
       SMTP_PORT = os.getenv("SMTP_PORT")
       SMTP_USER = os.getenv("SMTP_USER")
       SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
       RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
       SLACK_ENABLED = os.getenv("SLACK_ENABLED", "False").lower() == "true"
       SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
       TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "False").lower() == "true"
       TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
       TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    except Exception as e:
        print(f"Error saving .env settings: {e}")
    return redirect(url_for('index'))

@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        new_config = request.form.get('config_data')
        if new_config:
            new_config = json.loads(new_config)
            save_config_to_file(new_config)
    except Exception as e:
        print(f"Error saving config: {e}")
    return redirect(url_for('index'))

@app.route('/add_website', methods=['POST'])
def add_website():
   try:
       new_url = request.form.get('new_url')
       if new_url:
         config = load_config()
         new_config = { "url": new_url, "interval": 60, "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
             }, "method": "GET", "data": {}, "timeout": 10, "content_check": ""}
         config.append(new_config)
         save_config_to_file(config)
         website_status_db = WebsiteStatus(url=new_url, status=False, last_checked=datetime.now())
         update_db(website_status_db)
         
         # Perform initial check
         is_up, error, headers, response_time = check_website(new_config)
         website_status_db.status = is_up
         website_status_db.error = error
         website_status_db.last_checked = datetime.now()
         update_db(website_status_db)
         update_website_status(website_status_db)
         threading.Thread(target=monitor_website, args=(new_config,)).start() # start a new thread for the added website
   except Exception as e:
         print(f"Error adding website: {e}")
   return redirect(url_for('index'))


@app.route('/remove_website', methods=['POST'])
def remove_website():
    try:
        url_to_remove = request.form.get('remove_url')
        if url_to_remove:
            config = load_config()
            config = [item for item in config if item["url"] != url_to_remove]
            save_config_to_file(config)
            delete_db(WebsiteStatus, url=url_to_remove)
    except Exception as e:
        print(f"Error removing website: {e}")
    return redirect(url_for('index'))

@app.route('/get_chart_data', methods=['GET'])
def get_chart_data_route():
    return jsonify({})

@socketio.on('connect', namespace='/')
def test_connect():
    emit('update', {'statuses': get_all_statuses()})

def run_monitor(configs):
    """Function to start the monitoring in a separate thread."""
    threads = []
    for config in configs:
      thread = threading.Thread(target=monitor_website, args=(config,))
      threads.append(thread)
      thread.daemon = True
      thread.start()
    for thread in threads:
        thread.join()

# --- Main Function ---
def main():
    config_file = "config.json"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    configs = load_config(config_file)

    # Start the monitor in a separate thread
    monitor_thread = threading.Thread(target=run_monitor, args=(configs,))
    monitor_thread.daemon = True
    monitor_thread.start()

    # Start Flask app
    socketio.run(app, debug=False, use_reloader=False)  #disable reloader in debug for multithreading

if __name__ == "__main__":
    main()
