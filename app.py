from flask import Flask, jsonify, render_template, send_file
from scraper import scrape_weworkremotely
import threading
import time
import os
import logging
import traceback

app = Flask(__name__)

# Configure logging to file for production error diagnosis
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'app.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

logger = logging.getLogger(__name__)

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
            # Log full exception to file for diagnosis
            logger.exception('Error during job scraping')
        time.sleep(CACHE_DURATION)

# Start the background thread when the app receives its first request.
# This avoids starting threads at import time which can cause issues under
# some WSGI process managers (and helps troubleshooting Internal Server Errors).
@app.before_request
def start_background_thread():
    # Use before_request and a flag to ensure we only start the thread once.
    try:
        if not getattr(app, 'job_thread_started', False):
            app.job_thread = threading.Thread(target=refresh_jobs, daemon=True)
            app.job_thread.start()
            app.job_thread_started = True
            logger.info('Background job thread started')
    except Exception:
        logger.exception('Failed to start background thread')

@app.route('/')
def home():
    """Serve the HTML frontend."""
    try:
        return render_template('index.html')
    except:
        # Fallback to static file if template not found
        return send_file('index.html')

@app.route('/api/jobs')
def get_jobs():
    """Return the list of jobs from the cache (JSON)."""
    global jobs_cache, last_refresh
    try:
        # If cache is empty and hasn't been refreshed recently, do it now
        if not jobs_cache and (time.time() - last_refresh > 5):
            logger.info('Cache empty, doing immediate refresh...')
            jobs_cache = scrape_weworkremotely()
            last_refresh = time.time()
            logger.info(f'Immediate refresh returned {len(jobs_cache)} jobs')
        
        if not jobs_cache:
            return jsonify({"message": "Job cache is being built, please try again in a few seconds."}), 202
        return jsonify(jobs_cache)
    except Exception as e:
        logger.exception('Error in /api/jobs: %s', e)
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(500)
def internal_server_error(e):
    # Log full traceback to app.log for diagnosis on the live server
    tb = traceback.format_exc()
    logger.error('Unhandled exception: %s\n%s', e, tb)
    # Try to render the frontend; if rendering fails, return a minimal response
    try:
        return render_template('index.html'), 500
    except Exception:
        try:
            return send_file('index.html'), 500
        except Exception:
            logger.exception('Failed to render error page')
            return ('Internal server error', 500)


@app.route('/health')
def health():
    """Health endpoint for monitoring: returns last refresh timestamp and job count."""
    try:
        return jsonify({
            'status': 'ok',
            'last_refresh': last_refresh,
            'jobs_cached': len(jobs_cache)
        })
    except Exception:
        logger.exception('Error in /health')
        return jsonify({'status': 'error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
