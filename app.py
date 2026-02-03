from flask import Flask, request, Response
import requests
import json
import time
from datetime import datetime
import re
import concurrent.futures
from difflib import SequenceMatcher
import logging
app = Flask(__name__)
app.json.compact = False
app.json.sort_keys = False
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CricScraper")
def get_current_time_ms():
    return int(time.time() * 1000)
def get_readable_date(timestamp_ms):
    try:
        return datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown Date"
def get_headers():
    return {
        'authority': 'www.cricbuzz.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
def parse_duration_minutes(duration_str):
    if not duration_str:
        return 0
    parts = duration_str.split(':')
    if len(parts) == 2:
        return int(parts[0])
    elif len(parts) == 3:
        return int(parts[0]) * 60 + int(parts[1])
    return 0
def get_highest_res_m3u8(master_url):
    try:
        response = requests.get(master_url, timeout=10)
        if response.status_code != 200:
            return None
        lines = response.text.split('\n')
        best_res = 0
        best_url = None
        for i, line in enumerate(lines):
            if "
                res_match = re.search(r'RESOLUTION=(\d+)x(\d+)', line)
                if res_match:
                    pixels = int(res_match.group(1)) * int(res_match.group(2))
                    if pixels > best_res:
                        if i + 1 < len(lines) and lines[i+1].strip().startswith('http'):
                            best_res = pixels
                            best_url = lines[i+1].strip()
        return best_url
    except Exception as e:
        logger.error(f"Resolution negotiation failed: {str(e)}")
        return None
def process_video_item(item):
    try:
        click_url = item.get('onCardClick', '')
        if not click_url:
            return item
        full_url = "https://www.cricbuzz.com" + click_url
        headers = get_headers()
        response = requests.get(full_url, headers=headers, timeout=15)
        if response.status_code == 200:
            content = response.text
            patterns = [
                r'\\"videoUrl\\":\\"(.*?)\\"',
                r'"videoUrl":"(.*?)"'
            ]
            candidate_url = None
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    raw_url = match.group(1).replace('\\/', '/')
                    title_check_pattern = r'title\\?":\\?"(.*?)\\"'
                    start_pos = match.start()
                    snippet = content[start_pos:start_pos+1000] 
                    title_match = re.search(title_check_pattern, snippet)
                    if title_match:
                        found_title = title_match.group(1)
                        ratio = SequenceMatcher(None, item.get('title', '').lower(), found_title.lower()).ratio()
                        if ratio > 0.6:
                            candidate_url = raw_url
                            break
                    if not candidate_url:
                        candidate_url = raw_url
                if candidate_url:
                    break
            if candidate_url:
                item['m3u8'] = candidate_url
                final_m3u8 = get_highest_res_m3u8(candidate_url)
                if final_m3u8:
                    item['m3u8_1'] = final_m3u8
                    video_date = get_readable_date(item.get('creationDate', 0))
                    logger.info(f"Captured: {item['title'][:30]}... | Date: {video_date}")
                else:
                    logger.warning(f"Resolution extraction failed for: {item['title'][:30]}...")
            else:
                logger.warning(f"Video source URL not found for: {item['title'][:30]}...")
    except Exception as e:
        logger.error(f"Error processing item '{item.get('title', 'Unknown')}': {e}")
    return item
def execute_scraping(days_to_look_back):
    current_time_ms = get_current_time_ms()
    cutoff_time_ms = current_time_ms - (days_to_look_back * 24 * 60 * 60 * 1000)
    start_date = get_readable_date(current_time_ms)
    end_date = get_readable_date(cutoff_time_ms)
    collected_fixtures = []
    headers = get_headers()
    next_timestamp = current_time_ms
    page = 1
    logger.info(f"Initiating extraction sequence. Target Range: {start_date} to {end_date} ({days_to_look_back} days)")
    while next_timestamp > cutoff_time_ms:
        url = f"https://www.cricbuzz.com/api/cricket-videos/collection-pagination/1/{next_timestamp}"
        cursor_date = get_readable_date(next_timestamp)
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 204:
                logger.info(f"Stream ended at {cursor_date} (204 No Content).")
                break
            if response.status_code != 200:
                logger.error(f"API Error at {cursor_date}: Status {response.status_code}")
                break
            data = response.json()
            items = data.get('data', [])
            if not items:
                break
            count = 0
            for item in items:
                click_url = item.get('onCardClick', '').lower()
                duration_str = item.get('durationStr', '0:00')
                if 'highlight' in click_url:
                    minutes = parse_duration_minutes(duration_str)
                    if minutes >= 14:
                        collected_fixtures.append(item)
                        count += 1
            logger.info(f"Scanned Page {page} | Content Date: {cursor_date} | Qualifying Highlights: {count}")
            new_last_pt = data.get('lastPt')
            if not new_last_pt or int(new_last_pt) >= next_timestamp:
                break
            next_timestamp = int(new_last_pt)
            page += 1
            time.sleep(0.5)
        except Exception as e:
            logger.critical(f"Pagination interruption at {cursor_date}: {e}")
            break
    logger.info(f"Collection complete. Found {len(collected_fixtures)} total items. Commencing video URL extraction...")
    final_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_video_item, item) for item in collected_fixtures]
        for future in concurrent.futures.as_completed(futures):
            final_data.append(future.result())
    final_data.sort(key=lambda x: x.get('creationDate', 0), reverse=True)
    return final_data
@app.route('/fetch', methods=['GET'])
def fetch_fixtures():
    try:
        days = int(request.args.get('days', 1))
    except ValueError:
        return Response(json.dumps({"error": "Invalid days parameter"}), status=400, mimetype='application/json')
    data = execute_scraping(days)
    file_path = 'fixtures.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    logger.info(f"Payload successfully serialized to {file_path}")
    return Response(
        json.dumps(data, indent=4, ensure_ascii=False),
        mimetype='application/json'
    )
if __name__ == "__main__":
    logger.info("Starting Flask Server on Port 5000...")
    app.run(port=5000, debug=True, use_reloader=False)
