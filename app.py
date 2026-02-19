from flask import Flask, jsonify
from scraper import scrape_weworkremotely
import threading
import time
import os

app = Flask(__name__)

# Global cache for jobs
jobs_cache = []
last_refresh = 0
CACHE_DURATION = 3600  # refresh every hour (seconds)

def refresh_jobs():
    """Background task that periodically updates the job cache."""
    global jobs_cache, last_refresh
    while True:
        print("Refreshing job cache...")
        try:
            jobs_cache = scrape_weworkremotely()
            last_refresh = time.time()
            print(f"Job cache updated with {len(jobs_cache)} jobs.")
        except Exception as e:
            print(f"Error during job scraping: {e}")
        time.sleep(CACHE_DURATION)

# Start the background thread when the app starts
thread = threading.Thread(target=refresh_jobs, daemon=True)
thread.start()

@app.route('/')
def home():
    return jsonify({"message": "Job Matcher API is running!"})

@app.route('/api/jobs')
def get_jobs():
    """Return the list of jobs from the cache."""
    global jobs_cache
    if not jobs_cache:
        return jsonify({"message": "Job cache is being built, please try again in a few seconds."}), 202
    return jsonify(jobs_cache)

if __name__ == '__main__':
    # For production on Render, we need to listen on the correct port
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production