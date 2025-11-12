#!/usr/bin/env python3
"""
Fidelity Learning Center Article Scraper
Scrapes article cards from Fidelity's learning center pages
"""

import json
import time
import re
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# List of URLs to scrape
FIDELITY_URLS = [
    "https://www.fidelity.com/learning-center/personal-finance/saving-and-budgeting-money",
    "https://www.fidelity.com/learning-center/personal-finance/managing-debt",
    "https://www.fidelity.com/learning-center/personal-finance/retirement/saving-for-retirement",
    "https://www.fidelity.com/learning-center/personal-finance/working-and-income",
    "https://www.fidelity.com/learning-center/personal-finance/managing-health-care",
    "https://www.fidelity.com/learning-center/personal-finance/talking-to-family-about-money",
    "https://www.fidelity.com/learning-center/personal-finance/personal-finance-for-students",
    "https://www.fidelity.com/learning-center/personal-finance/managing-taxes/managing-taxes",
    "https://www.fidelity.com/learning-center/personal-finance/managing-estate-planning",
    "https://www.fidelity.com/learning-center/personal-finance/charitable-giving/making-charitable-donations",
    "https://www.fidelity.com/learning-center/life-events/career-planning",
    "https://www.fidelity.com/learning-center/life-events/prepare-for-college",
    "https://www.fidelity.com/learning-center/life-events/getting-divorced",
    "https://www.fidelity.com/learning-center/life-events/parenting",
    "https://www.fidelity.com/learning-center/life-events/caring-for-the-aging",
    "https://www.fidelity.com/learning-center/life-events/marriage",
    "https://www.fidelity.com/learning-center/life-events/selling-and-buying-house",
    "https://www.fidelity.com/learning-center/personal-finance/retirement/planning-your-retirement",
    "https://www.fidelity.com/learning-center/life-events/loss-of-loved-one",
    "https://www.fidelity.com/learning-center/life-events/major-purchase",
    "https://www.fidelity.com/learning-center/life-events/injury-and-illness",
    "https://www.fidelity.com/learning-center/life-events/disabilities-and-special-needs",
    "https://www.fidelity.com/learning-center/life-events/aging-well",
    "https://www.fidelity.com/learning-center/life-events/how-to-become-self-employed",
    "https://www.fidelity.com/learning-center/trading-investing/investing-for-beginners",
    "https://www.fidelity.com/learning-center/trading-investing/trading-for-beginners",
    "https://www.fidelity.com/learning-center/trading-investing/crypto/crypto-for-beginners",
    "https://www.fidelity.com/learning-center/trading-investing/crypto/crypto-advanced",
    "https://www.fidelity.com/learning-center/trading-investing/finding-stocks-and-sector-ideas",
    "https://www.fidelity.com/learning-center/trading-investing/investing-for-income",
    "https://www.fidelity.com/learning-center/trading-investing/fundamental-analysis/analyzing-stock-fundamentals",
    "https://www.fidelity.com/learning-center/trading-investing/technical-analysis/using-technical-analysis",
    "https://www.fidelity.com/learning-center/investment-products/etf/etfs",
    "https://www.fidelity.com/learning-center/investment-products/mutual-funds/mutual-funds",
    "https://www.fidelity.com/learning-center/investment-products/stocks/stocks",
    "https://www.fidelity.com/learning-center/investment-products/fixed-income-bonds/fixed-income-bonds-cds",
    "https://www.fidelity.com/learning-center/investment-products/annuities",
    "https://www.fidelity.com/learning-center/investment-products/closed-end-funds/closed-end-funds",
    "https://www.fidelity.com/learning-center/trading-investing/using-margin",
    "https://www.fidelity.com/learning-center/investment-products/options/options-for-beginners",
    "https://www.fidelity.com/learning-center/investment-products/options/options",
    "https://www.fidelity.com/learning-center/trading-investing/more-trading-strategies",
    "https://www.fidelity.com/learning-center/trading-investing/trading-platforms/using-trader-plus",
    "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/overview",
    "https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/overview",
    "https://www.fidelity.com/learning-center/viewpoints",
    "https://www.fidelity.com/learning-center/smart-money",
    "https://www.fidelity.com/learning-center/money-unscripted",
    "https://www.fidelity.com/learning-center/trading-post",
    "https://www.fidelity.com/learning-center/women-talk-money",
    "https://www.fidelity.com/learning-center/wealth-management-insights"
]

def get_headers():
    """Return headers to mimic a real browser"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def extract_article_cards(soup, base_url):
    """Extract article cards from the page"""
    articles = []
    
    # Find all article cards - looking for the pvd-tile__content class
    cards = soup.find_all('div', class_='pvd-tile__content')
    
    # Also look for tile-container--content-container-body
    body_cards = soup.find_all('div', class_='tile-container--content-container-body')
    
    total_cards = len(cards) + len(body_cards)
    print(f"  Found {total_cards} article cards ({len(cards)} pvd-tile, {len(body_cards)} tile-container)")
    
    # Process pvd-tile__content cards
    for card in cards:
        try:
            article = {}
            
            # Extract title and link
            title_element = card.find('h3')
            if title_element:
                link_element = title_element.find('a')
                if link_element:
                    article['title'] = link_element.get_text(strip=True)
                    article['url'] = urljoin(base_url, link_element.get('href', ''))
            
            # Extract description
            desc_element = card.find('span', {'aria-label': True})
            if desc_element:
                article['description'] = desc_element.get_text(strip=True)
            
            # Extract image
            img_element = card.find('img', class_='top-img')
            if img_element:
                img_src = img_element.get('src', '')
                if img_src:
                    article['image'] = urljoin(base_url, img_src)
            
            # Extract metadata (Article type, reading time)
            list_items = card.find_all('li', class_='pvd-list-group__list-item')
            metadata = {}
            for item in list_items:
                text = item.get_text(strip=True)
                # Clean up the text
                text = re.sub(r'Content Type:', '', text)
                text = re.sub(r'Reading Time', '', text)
                text = text.strip()
                
                if 'Article' in text or 'Video' in text or 'Podcast' in text:
                    metadata['type'] = text
                elif 'min' in text:
                    metadata['duration'] = text
            
            if metadata:
                article['metadata'] = metadata
            
            # Only add if we got at least a title
            if 'title' in article:
                articles.append(article)
                print(f"    ✓ {article['title']}")
        
        except Exception as e:
            print(f"    ✗ Error parsing pvd-tile card: {e}")
            continue
    
    # Process tile-container--content-container-body cards
    for body_card in body_cards:
        try:
            article = {}
            
            # Extract title and link from h3 > a
            title_element = body_card.find('h3')
            if title_element:
                link_element = title_element.find('a')
                if link_element:
                    article['title'] = link_element.get_text(strip=True)
                    href = link_element.get('href', '')
                    if href:
                        article['url'] = urljoin(base_url, href)
            
            # Extract description from span
            desc_element = body_card.find('span', {'aria-label': lambda x: x and 'slide content' in x})
            if desc_element:
                article['description'] = desc_element.get_text(strip=True)
            
            # Try to get image from parent container
            parent = body_card.find_parent('div', class_='tile-container--content-container')
            if parent:
                img_container = parent.find('div', class_='tile-container--content-container-img')
                if img_container:
                    img_element = img_container.find('img', class_='top-img')
                    if img_element:
                        img_src = img_element.get('src', '')
                        if img_src:
                            article['image'] = urljoin(base_url, img_src)
            
            # Try to extract metadata from tile-tray (in parent pvd-tile__content)
            parent_tile = body_card.find_parent('div', class_='pvd-tile__content')
            if parent_tile:
                tile_tray = parent_tile.find('div', class_='tile-tray')
                if tile_tray:
                    list_items = tile_tray.find_all('li', class_='pvd-list-group__list-item')
                    metadata = {}
                    for item in list_items:
                        text = item.get_text(strip=True)
                        # Clean up the text
                        text = re.sub(r'Content Type:', '', text)
                        text = re.sub(r'Reading Time', '', text)
                        text = text.strip()
                        
                        if 'Article' in text or 'Video' in text or 'Podcast' in text:
                            metadata['type'] = text
                        elif 'min' in text:
                            metadata['duration'] = text
                    
                    if metadata:
                        article['metadata'] = metadata
            
            # Only add if we got at least a title and it's not a duplicate
            if 'title' in article:
                # Check if this article is already in the list (avoid duplicates)
                is_duplicate = any(a.get('url') == article.get('url') for a in articles if 'url' in a and 'url' in article)
                if not is_duplicate:
                    articles.append(article)
                    print(f"    ✓ {article['title']}")
        
        except Exception as e:
            print(f"    ✗ Error parsing tile-container card: {e}")
            continue
    
    return articles

def scrape_url(url, session):
    """Scrape a single URL and return articles found"""
    print(f"\n{'='*80}")
    print(f"Scraping: {url}")
    print(f"{'='*80}")
    
    try:
        response = session.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract articles
        articles = extract_article_cards(soup, url)
        
        # Also look for any additional article links in the page
        all_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/learning-center/' in href and href not in all_links:
                full_url = urljoin(url, href)
                if full_url.startswith('https://www.fidelity.com/learning-center/'):
                    all_links.append(full_url)
        
        return {
            'url': url,
            'success': True,
            'articles': articles,
            'total_articles': len(articles),
            'all_links_found': len(all_links),
            'links': all_links,
            'scraped_at': datetime.now().isoformat()
        }
    
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error fetching URL: {e}")
        return {
            'url': url,
            'success': False,
            'error': str(e),
            'scraped_at': datetime.now().isoformat()
        }

def main():
    """Main scraping function"""
    print("="*80)
    print("FIDELITY LEARNING CENTER ARTICLE SCRAPER")
    print("="*80)
    print(f"Total URLs to scrape: {len(FIDELITY_URLS)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    session = requests.Session()
    
    total_articles = 0
    successful = 0
    failed = 0
    
    for i, url in enumerate(FIDELITY_URLS, 1):
        print(f"\nProgress: {i}/{len(FIDELITY_URLS)}")
        
        result = scrape_url(url, session)
        results.append(result)
        
        if result['success']:
            successful += 1
            total_articles += result.get('total_articles', 0)
        else:
            failed += 1
        
        # Be respectful - wait between requests
        if i < len(FIDELITY_URLS):
            time.sleep(2)
    
    # Save results
    output_file = f'fidelity_articles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Create summary
    print("\n" + "="*80)
    print("SCRAPING COMPLETE")
    print("="*80)
    print(f"Total URLs processed: {len(FIDELITY_URLS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total articles found: {total_articles}")
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    # Create a flat list of all articles
    all_articles = []
    for result in results:
        if result['success']:
            for article in result.get('articles', []):
                article['source_page'] = result['url']
                all_articles.append(article)
    
    # Save flat article list
    articles_file = f'fidelity_articles_flat_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(articles_file, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)
    
    print(f"Flat article list saved to: {articles_file}")
    
    # Create CSV export
    try:
        import csv
        csv_file = f'fidelity_articles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if all_articles:
                fieldnames = ['title', 'url', 'description', 'type', 'duration', 'source_page']
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for article in all_articles:
                    row = {
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'description': article.get('description', ''),
                        'type': article.get('metadata', {}).get('type', ''),
                        'duration': article.get('metadata', {}).get('duration', ''),
                        'source_page': article.get('source_page', '')
                    }
                    writer.writerow(row)
        print(f"CSV export saved to: {csv_file}")
    except Exception as e:
        print(f"Could not create CSV: {e}")

if __name__ == "__main__":
    main()