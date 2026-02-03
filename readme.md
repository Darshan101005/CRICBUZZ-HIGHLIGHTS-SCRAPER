<div align="center">

<img src="https://crystalpng.com/wp-content/uploads/2025/10/cricbuzz-logo.png" alt="Cricbuzz Logo" width="200"/>

# Cricbuzz Highlights Scraper API

**A high-performance Flask API that scrapes, processes, and serves high-quality Cricket highlight links.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-black?style=for-the-badge&logo=flask&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

</div>

---

## ⚡ Overview

This tool automatically fetches cricket match highlights from Cricbuzz based on a specified date range. It filters for extended highlights, extracts the **highest resolution streaming URLs (M3U8)**, generates high-quality thumbnails, and serves the data via a RESTful JSON API.

## 🚀 Key Features

* **Dynamic Date Filtering:** Fetch highlights for the past `N` days.
* **Smart Extraction:** Automatically parses master playlists to find the highest resolution (1080p/720p) stream.
* **HQ Thumbnails:** Reconstructs high-definition thumbnail URLs from internal IDs.
* **Multi-threaded:** Uses `concurrent.futures` for rapid parallel scraping.
* **Precision Matching:** Uses `difflib` sequence matching to ensure video titles match the correct stream URLs.
* **Rich Metadata:** Returns timestamps, authors, duration, and content timestamps.

## 🛠️ Technologies Used

* **Python 3** - Core Logic
* **Flask** - Web Server & API Endpoint
* **Requests** - HTTP Handling
* **Concurrent Futures** - Multi-threading
* **RegEx** - Pattern Matching

---

## 🔧 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Darshan101005/CRICBUZZ-HIGHLIGHTS-SCRAPER.git
    cd CRICBUZZ-HIGHLIGHTS-SCRAPER
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server**
    ```bash
    python app.py
    ```

## 📡 API Usage

Once the server is running on `localhost:5000`, use the following endpoint:

### **GET** `/fetch`

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `days` | `int` | `1` | Number of past days to scan for highlights. |

#### **Example Request**
Fetch highlights for the last 5 days:
`http://localhost:5000/fetch?days=5`

#### **Example Response**
```json
{
    "lastRefresh": "04-02-2026 10:30 AM",
    "author": "@Darshan_101005",
    "timeFrame": "2026-01-30 to 2026-02-04",
    "totalHighlights": 12,
    "data": [
        {
            "id": "159937",
            "title": "Highlights: IND vs AUS | Final",
            "m3u8": "https://original-url.m3u8",
            "m3u8_1": "https://highest-res-url.m3u8",
            "logo_url": "[https://static.cricbuzz.com/.../full-hd.jpg](https://static.cricbuzz.com/.../full-hd.jpg)",
            "durationStr": "16:42",
            "creationDate": "1738590000000"
        }
    ]
}
