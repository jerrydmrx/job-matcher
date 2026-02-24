import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create a session with retries."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def scrape_weworkremotely():
    """
    Fetches remote jobs from multiple free APIs.
    Returns a list of job dictionaries compatible with your Flask app.
    """
    all_jobs = []
    session = create_session()

    # ----- Jobicy API (free, no auth) -----
    try:
        print("Fetching from Jobicy...")
        url = "https://jobicy.com/api/v2/remote-jobs"
        params = {"count": 20}  # get up to 20 jobs
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = session.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            for job in data.get('jobs', []):
                all_jobs.append({
                    "title": job.get('jobTitle', 'Unknown'),
                    "company": job.get('companyName', 'Unknown'),
                    "description": job.get('jobDescription', '')[:500],  # shorten
                    "contact_email": job.get('url', ''),  # Use URL as contact
                    "url": job.get('url', ''),
                    "source": "jobicy"
                })
            print(f"Jobicy: fetched {len([j for j in data.get('jobs', [])])} jobs")
        else:
            print(f"Jobicy returned status {response.status_code}")
    except Exception as e:
        print(f"Jobicy error: {e}")

    # Be polite between requests
    time.sleep(1)

    # ----- RemoteOK API (free, 24h delayed) -----
    try:
        print("Fetching from RemoteOK...")
        url = "https://remoteok.com/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # First item is metadata, skip it
            count = 0
            for job in data[1:21]:  # next 20 jobs
                try:
                    all_jobs.append({
                        "title": job.get('position', 'Unknown'),
                        "company": job.get('company', 'Unknown'),
                        "description": job.get('description', '')[:500],
                        "contact_email": job.get('apply_url', ''),  # Apply URL
                        "url": f"https://remoteok.com/{job.get('slug', '')}",
                        "source": "remoteok"
                    })
                    count += 1
                except Exception as e:
                    print(f"  Error parsing RemoteOK job: {e}")
                    continue
            print(f"RemoteOK: fetched {count} jobs")
        else:
            print(f"RemoteOK returned status {response.status_code}")
    except Exception as e:
        print(f"RemoteOK error: {e}")

    # Be polite between requests
    time.sleep(1)

    # ----- Remotive API (free) -----
    try:
        print("Fetching from Remotive...")
        url = "https://remotive.com/api/remote-jobs"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            count = 0
            for job in data.get('jobs', [])[:20]:  # limit to 20
                try:
                    # Filter for jobs open worldwide or not restricted to USA
                    location = job.get('candidate_required_location', '')
                    if location in ['Worldwide', ''] or 'USA' not in location:
                        all_jobs.append({
                            "title": job.get('title', 'Unknown'),
                            "company": job.get('company_name', 'Unknown'),
                            "description": job.get('description', '')[:500],
                            "contact_email": job.get('url', ''),  # Use URL
                            "url": job.get('url', ''),
                            "source": "remotive"
                        })
                        count += 1
                except Exception as e:
                    print(f"  Error parsing Remotive job: {e}")
                    continue
            print(f"Remotive: fetched {count} jobs")
        else:
            print(f"Remotive returned status {response.status_code}")
    except Exception as e:
        print(f"Remotive error: {e}")

    print(f"Total jobs collected: {len(all_jobs)}")
    return all_jobs


# For testing when you run this file directly
if __name__ == "__main__":
    jobs = scrape_weworkremotely()
    print(f"\nSample jobs:")
    for job in jobs[:5]:
        print(f"- {job['title']} at {job['company']} (via {job['source']})")
