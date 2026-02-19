import requests
from bs4 import BeautifulSoup
import time

def scrape_weworkremotely():
    """
    Scrapes job listings from WeWorkRemotely categories:
    programming, design, devops.
    Returns a list of job dictionaries.
    """
    categories = {
        "programming": "https://weworkremotely.com/categories/remote-programming-jobs",
        "design": "https://weworkremotely.com/categories/remote-design-jobs",
        "devops": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs"
    }
    
    all_jobs = []
    
    for category_name, category_url in categories.items():
        print(f"Scraping {category_name}...")
        try:
            response = requests.get(category_url, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {category_url} – status {response.status_code}")
                continue
        except Exception as e:
            print(f"Error fetching {category_url}: {e}")
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all job listing <li> elements – they often have class 'feature' or are inside a specific section
        # We'll look for <li> that contain a .title element
        job_listings = soup.select('li')
        
        for li in job_listings:
            title_elem = li.select_one('.title')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            
            company_elem = li.select_one('.company')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Get the detail page link
            link_elem = li.select_one('a')
            detail_url = None
            if link_elem and link_elem.has_attr('href'):
                href = link_elem['href']
                if href.startswith('/'):
                    detail_url = "https://weworkremotely.com" + href
                else:
                    detail_url = href
            
            # For prototype, we don't have the real contact email.
            # We'll create a placeholder email based on company name.
            # In a real app you would scrape the detail page to find the application email.
            contact_email = f"apply@{company.lower().replace(' ', '')}.com"
            
            all_jobs.append({
                "title": title,
                "company": company,
                "description": "Scraped from WeWorkRemotely",  # placeholder
                "contact_email": contact_email,
                "url": detail_url,
                "source": "weworkremotely"
            })
        
        # Be polite – wait 2 seconds before the next request
        time.sleep(2)
    
    return all_jobs

# For testing this file directly (optional)
if __name__ == "__main__":
    jobs = scrape_weworkremotely()
    print(f"Found {len(jobs)} jobs")
    for job in jobs[:5]:  # print first 5
        print(job)