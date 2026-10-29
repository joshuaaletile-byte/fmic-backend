import os
import subprocess
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def clean_filename(text):
    return re.sub(r'[^a-zA-Z0-9]', '_', text)[:30]

def calculate_preroll(timestamp_str, preroll_seconds=15):
    parts = list(map(int, timestamp_str.split(':')))
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        return "00:00:00"

    total_secs = max(0, h * 3600 + m * 60 + s - preroll_seconds)
    out_h = total_secs // 3600
    out_m = (total_secs % 3600) // 60
    out_s = total_secs % 60
    return f"{out_h:02d}:{out_m:02d}:{out_s:02d}"

@app.route('/api/process-testimony', methods=['POST'])
def process_testimony():
    data = request.json or {}
    member_name = data.get('memberName', 'Member')
    service_date = data.get('serviceDate', '2026-10-29')
    category = data.get('category', 'Prophecy')
    timestamp = data.get('timestamp', '02:15:40')
    source_type = data.get('sourceType', 'youtube')

    print(f"\n📥 CLOUD REQUEST RECEIVED: {member_name} | Date: {service_date}")

    preroll_time = calculate_preroll(timestamp, preroll_seconds=15)
    output_filename = f"{clean_filename(member_name)}_{service_date}_{preroll_time.replace(':', 'h', 1).replace(':', 'm')}s.mp4"
    output_path = os.path.join(os.getcwd(), output_filename)

    if source_type == 'youtube':
        search_target = f"ytsearch1:GFDAVIDMINISTRIES service {service_date}"
        try:
            url_cmd = ["yt-dlp", "--get-url", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", search_target]
            res = subprocess.run(url_cmd, capture_output=True, text=True, timeout=30)
            stream_url = res.stdout.strip().splitlines()[0] if res.stdout else None

            if stream_url:
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-ss", preroll_time,
                    "-i", stream_url,
                    "-t", "180",
                    "-c", "copy",
                    output_path
                ]
                subprocess.run(ffmpeg_cmd)
        except Exception as e:
            print(f"Error processing stream: {e}")

    return jsonify({
        "status": "success",
        "memberName": member_name,
        "serviceDate": service_date,
        "prerollTimestamp": preroll_time,
        "filename": output_filename
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
