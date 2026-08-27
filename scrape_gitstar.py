import os
from pathlib import Path
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup


def scrape_gitstar_users(max_pages=10, cache_dir="cache_gitstar_pages"):
    base_url = "https://gitstar-ranking.com/users"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    all_users = []

    print(f"Starting extraction for top {max_pages * 100} users...")

    for page in range(1, max_pages + 1):
        cache_file = cache_path / f"page_{page}.html"
        html_content = None

        if cache_file.exists():
            print(
                f"Loading Page {page}/{max_pages} from local cache: {cache_file.name}"
            )
            html_content = cache_file.read_text(encoding="utf-8")
        else:
            url = f"{base_url}?page={page}"
            print(f"Scraping Page {page}/{max_pages} from web: {url}")

            try:
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 429:
                    print("Rate limit encountered. Sleeping for 10 seconds...")
                    time.sleep(10)
                    response = requests.get(url, headers=headers, timeout=15)

                response.raise_for_status()
                html_content = response.text

                # Cache HTML locally
                cache_file.write_text(html_content, encoding="utf-8")

            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch page {page}. Error: {e}")
                break

            # Respectful crawling delay when making live network requests
            time.sleep(1.5)

        soup = BeautifulSoup(html_content, "html.parser")

        # Locate paginated user items: <a class="list-group-item paginated_item" href="/username">
        items = soup.select("a.paginated_item, a.list-group-item")

        page_items_extracted = 0

        for item in items:
            href = item.get("href", "").strip()
            # Ensure it is a user profile link (and not pagination or internal nav)
            if (
                not href
                or href.startswith("/users")
                or href.startswith("/organizations")
                or href.startswith("/repositories")
                or href.startswith("/search")
            ):
                continue

            try:
                # 1. Extract Username from inner span or href
                user_span = item.select_one(
                    ".name .hidden-xs, .name .hidden-sm, .name span"
                )
                username = user_span.text.strip() if user_span else href.lstrip("/")

                profile_url = (
                    f"https://gitstar-ranking.com{href}"
                    if not href.startswith("http")
                    else href
                )

                # 2. Extract Rank from .name (e.g. "1." -> 1)
                name_elem = item.select_one(".name")
                rank = None
                if name_elem:
                    rank_match = re.search(r"(\d+)\.", name_elem.text)
                    if rank_match:
                        rank = int(rank_match.group(1))

                # 3. Extract Star Count from .stargazers_count
                star_elem = item.select_one(".stargazers_count")
                stars = 0
                if star_elem:
                    stars_digits = re.sub(r"[^\d]", "", star_elem.text)
                    stars = int(stars_digits) if stars_digits else 0

                if username and rank is not None:
                    all_users.append(
                        {
                            "Rank": rank,
                            "Username": username,
                            "Stars": stars,
                            "Profile_URL": profile_url,
                        }
                    )
                    page_items_extracted += 1

            except (AttributeError, ValueError):
                continue

        print(f"Extracted {page_items_extracted} users from page {page}.")

    # Save to a structured DataFrame and export to CSV
    if all_users:
        df = pd.DataFrame(all_users)
        # Drop potential duplicates and sort by rank cleanly
        df = df.drop_duplicates(subset=["Username"]).sort_values(by="Rank")
        output_file = "gitstar_top_1000_users.csv"
        df.to_csv(output_file, index=False)
        print(f"\nSuccess! Saved {len(df)} unique records to '{output_file}'.")
    else:
        print("\nNo data was extracted. Please verify web structural classes.")


if __name__ == "__main__":
    scrape_gitstar_users(max_pages=10)
