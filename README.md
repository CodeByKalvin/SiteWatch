## SiteWatch

A Python-based website monitoring application designed to check website availability, send notifications, and manage settings.

This application continuously monitors the status of specified websites, alerting you through email, Slack, or Telegram when a site goes down. It provides a simple web interface to manage the monitored sites and notification settings.

**CodeByKalvin**

### Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Website Status Monitoring](#website-status-monitoring)
  - [Notifications](#notifications)
  - [Configuration](#configuration)
  - [Adding or removing Website](#adding-or-removing-website)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)

---

### Features

-   **Website Status Monitoring**: Checks if websites are up or down by making requests.
-   **Real-Time Status:** Displays the current status (UP or DOWN) of monitored websites in a web interface.
-   **Notifications**: Notifies users via email, Slack, and Telegram when a website's status changes.
-   **Web-Based Configuration**: Allows users to add, remove websites, change notification settings and modify website configurations all through an easy to use web interface.
-   **External CSS**: Uses a style sheet for a better UI.
-    **Initial check**: Checks the website status when a new website is added.

---

### Installation

To run SiteWatch locally, follow these steps:

#### 1. Clone the Repository

```bash
git clone https://github.com/CodeByKalvin/SiteWatch.git
cd SiteWatch
```

#### 2. Install Dependencies

Make sure you have **Python 3** installed. Install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

The `requirements.txt` should contain the following:

```txt
Flask
Flask-SocketIO
requests
python-dotenv
beautifulsoup4
SQLAlchemy
```
---

### Usage

Once installed, you can run the application from the command line using:

```bash
python sitewatch.py
```

This will launch the SiteWatch web interface, where you can monitor websites, modify settings, and view the results.

---

#### Website Status Monitoring
- When the application is running you will automatically start checking the websites, and they will appear on the main page.

---

#### Notifications

- SiteWatch has Email, Slack, and Telegram notifications.
    - Modify the settings in the `Configuration` section on the main page.
    - Change the notification settings in the `.env` file as explained in `configuration` section of this file.
- Notifications are automatically sent to the specified channels when a website’s status changes to up or down.

---
#### Configuration

- The application is configured using a `config.json` file and a `.env` file
   - modify notification settings in the `.env` file and website settings in `config.json`. Both can be modified from the web interface
- `.env` file parameters:
    *   `EMAIL_ENABLED`:  Enable or disable email notifications (True/False).
    *   `SMTP_SERVER`:  SMTP server address (e.g., `smtp.gmail.com`).
    *   `SMTP_PORT`:  SMTP port number (e.g., `587`).
    *   `SMTP_USER`:  Your email address for sending notifications.
    *   `SMTP_PASSWORD`: Your email password (consider using an app password for Gmail).
    *   `RECIPIENT_EMAIL`: The email address to receive alerts.
    *   `SLACK_ENABLED`: Enable or disable Slack notifications (True/False).
    *   `SLACK_WEBHOOK_URL`:  Slack webhook URL.
    *   `TELEGRAM_ENABLED`: Enable or disable Telegram notifications (True/False).
    *   `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
    *   `TELEGRAM_CHAT_ID`: The ID of the Telegram chat to receive messages.

- `config.json` parameters:
    *   `url`:  Website URL to monitor.
    *   `interval`: Polling interval in seconds.
    *   `headers`: HTTP headers to send with the requests in a JSON dictionary e.g. `{"User-Agent": "Custom Agent"}`.
         *   **IMPORTANT**: Include a  `User-Agent` in the headers.
    *   `method` (optional): HTTP method e.g. GET, POST (defaults to GET).
    *  `data` (optional): data sent in post requests as JSON.
    *   `timeout` (optional): Time in seconds until requests time out (default is 10).
    *   `content_check` (optional): a string that should be found within the websites html body.
- An example of the `config.json` is shown below:

    ```json
        [
            {
                "url": "https://google.com",
                "interval": 60,
                 "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                   },
                "method": "GET",
                "data": {},
                "timeout": 10,
                "content_check": ""
            }
        ]
    ```

---
#### Adding or removing Website
- Use the form to add new websites to monitor.
    - Enter the url of the website and click on `Add Website` to add the new website.
- Use the `remove` button to remove an individual website that is being monitored.
---

### Project Structure

```
SiteWatch/
│
├── sitewatch.py                # Main Python script
├── README.md                # This README file
├── requirements.txt         # List of dependencies
├── static/                    # Folder containing the style.css
│    └── style.css
└── templates/                  # Folder containing the index.html
    └── index.html
```

---

### Requirements

-   **Python 3** or higher
-   **Pip** to install dependencies
-   Required Python libraries (in `requirements.txt`):
    *   `Flask`: For the web application.
    *  `Flask-SocketIO`: For real-time updates via websockets.
    *   `requests`: For making HTTP requests to the websites.
    *  `python-dotenv`: For loading environment variables from the .env file
    *   `beautifulsoup4`: For content checking of websites
    *    `SQLAlchemy`: For database access.

To install the dependencies:

```bash
pip install -r requirements.txt
```

---

### Contributing

If you want to contribute to this project, feel free to submit a pull request or create an issue with a detailed description of the feature or bug you're addressing.

#### Steps to Contribute:

1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature-name`).
3.  Make your changes.
4.  Test your changes.
5.  Commit your changes (`git commit -m 'Add some feature'`).
6.  Push to your branch (`git push origin feature-name`).
7.  Create a pull request.

---

### License

This project is open-source and available under the [MIT License](LICENSE).

---

### Future Improvements

-   Add more advanced status checks, such as checking for specific HTTP status codes.
-   More detailed information on the monitored websites (e.g., response times and history charts).
-   User authentication for restricted access to the web UI.
-   More options on how to add website configurations.

---

### Authors

-   **CodeByKalvin** - *Initial work* - [GitHub Profile](https://github.com/codebykalvin)
