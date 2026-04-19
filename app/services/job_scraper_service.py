"""
Job Description Scraper Service
Fetches and extracts clean JD text from job posting URLs.
Supports: LinkedIn, Indeed, Greenhouse, Lever, Workday, generic pages.
"""
import re
import httpx
from bs4 import BeautifulSoup


# User-agent to avoid bot detection on most job boards
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# CSS selectors for known job board containers (most specific first)
PLATFORM_SELECTORS = {
    "linkedin.com": [
        ".description__text",
        ".jobs-description__content",
        ".jobs-box__html-content",
        "[class*='description']"
    ],
    "indeed.com": [
        "#jobDescriptionText",
        ".jobsearch-jobDescriptionText",
        "[class*='jobDescription']"
    ],
    "greenhouse.io": [
        "#content",
        ".job-post",
        "[class*='job-description']"
    ],
    "lever.co": [
        ".section-wrapper",
        "[class*='posting-content']",
        ".description"
    ],
    "workday.com": [
        "[data-automation-id='jobPostingDescription']",
        ".css-cygeeu",
        "[class*='job-description']"
    ],
    "myworkdayjobs.com": [
        "[data-automation-id='jobPostingDescription']",
        "[class*='job-description']"
    ],
    "ashbyhq.com": [
        ".ashby-job-posting-brief-description",
        "[class*='description']"
    ],
    "smartrecruiters.com": [
        ".job-description",
        "[class*='description']"
    ],
    "icims.com": [
        "#job-details",
        "[class*='job-description']"
    ],
}

# Generic fallback selectors (tried in order when platform not recognized)
GENERIC_SELECTORS = [
    "article",
    "main",
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[class*='description']",
    "[id*='job-description']",
    "[id*='jobDescription']",
    "[id*='description']",
    "[class*='posting']",
    "[class*='content']",
]

# Tags to remove before extracting text (noise elements)
NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe", "button", "form"]


def _detect_platform(url: str) -> str | None:
    """Return the matched platform key or None."""
    url_lower = url.lower()
    for platform in PLATFORM_SELECTORS:
        if platform in url_lower:
            return platform
    return None


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove junk lines."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are clearly nav/footer noise
        if len(stripped) < 3:
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned)


def _extract_from_soup(soup: BeautifulSoup, selectors: list[str]) -> str:
    """Try each selector in order, return first non-empty result."""
    for sel in selectors:
        try:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator="\n")
                text = _clean_text(text)
                if len(text) > 200:  # Sanity check — must have substantial content
                    return text
        except Exception:
            continue
    return ""


async def fetch_job_description(url: str, timeout: int = 15) -> dict:
    """
    Fetch a job posting URL and return extracted JD text.

    Returns:
        {
            "text": str,          # Extracted JD text (empty string on failure)
            "title": str,         # Page title if extractable
            "success": bool,
            "error": str | None
        }
    """
    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=timeout,
            verify=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as e:
        return {"text": "", "title": "", "success": False, "error": f"HTTP {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"text": "", "title": "", "success": False, "error": "Request timed out"}
    except Exception as e:
        return {"text": "", "title": "", "success": False, "error": str(e)}

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags
    for tag in NOISE_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # Extract page title
    title = ""
    title_el = soup.find("title")
    if title_el:
        title = title_el.get_text().strip()
        # LinkedIn-style: "Job Title at Company | LinkedIn" → extract job title
        title = re.split(r"\s*[|\-–—@]\s*", title)[0].strip()

    # Try platform-specific selectors first
    platform = _detect_platform(url)
    text = ""

    if platform and platform in PLATFORM_SELECTORS:
        text = _extract_from_soup(soup, PLATFORM_SELECTORS[platform])

    # Fall back to generic selectors
    if not text:
        text = _extract_from_soup(soup, GENERIC_SELECTORS)

    # Last resort: entire body text
    if not text:
        body = soup.find("body")
        if body:
            text = _clean_text(body.get_text(separator="\n"))

    # Trim to 6000 chars (enough for full JD, avoids token bloat)
    text = text[:6000]

    if len(text) < 100:
        return {
            "text": "",
            "title": title,
            "success": False,
            "error": "Could not extract meaningful job description from this URL. Please paste the JD manually."
        }

    return {"text": text, "title": title, "success": True, "error": None}


async def scrape_multiple_jobs(job_urls: list[str]) -> list[dict]:
    """
    Scrape multiple job URLs concurrently.
    Returns list of result dicts in same order as input.
    """
    import asyncio
    tasks = [fetch_job_description(url) for url in job_urls]
    return await asyncio.gather(*tasks)
