import os
import requests
import csv
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from base64 import b64decode

# Load environment variables
load_dotenv()
API_KEY = os.getenv("ZYTE_API_KEY")

if not API_KEY:
    raise ValueError("Please set ZYTE_API_KEY in your .env file")

# CONFIGURATION
# Target: The North Face UK - Men's Jackets
BASE_URL = "https://www.thenorthface.co.uk/shop/en-gb/tnf-gb/men-jackets"
OUTPUT_FILE = "tnf_mens_jackets.csv"
MAX_PAGES = 3  # limit for MVP to keep costs low

def get_page_content(url):
    """
    Sends the URL to Zyte API to render the JS and return HTML.
    """
    api_url = "https://api.zyte.com/v1/extract"
    
    # Payload requests a headless browser render from Zyte
    payload = {
        "url": url,
        "browserHtml": True,
        "javascript": True,
        # specific geolocation to ensure we get UK site
        "geolocation": "GB" 
    }

    try:
        response = requests.post(
            api_url,
            auth=(API_KEY, ""),
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("browserHtml")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_products(html):
    """
    Extracts product data from the HTML.
    Note: Selectors are based on standard VF Corp structure. 
    """
    soup = BeautifulSoup(html, 'html.parser')
    products = []

    # VF Corp / TNF sites usually use grid structures. 
    # We look for the main product card container.
    # Note: These class names are standard but can change. 
    product_cards = soup.select('div.product-block') 

    if not product_cards:
        # Fallback for alternative layout
        product_cards = soup.select('[data-role="product-card"]')

    print(f"Found {len(product_cards)} products on this page.")

    for card in product_cards:
        try:
            # 1. Product Name
            name_tag = card.select_one('.product-block-name-wrapper a, .product-content a')
            name = name_tag.get_text(strip=True) if name_tag else "N/A"

            # 2. Product URL
            product_url = "https://www.thenorthface.co.uk" + name_tag['href'] if name_tag and name_tag.has_attr('href') else "N/A"

            # 3. ID / SKU
            # Usually found in data attributes or ID of the div
            product_id = card.get('data-part-number') or card.get('id') or "N/A"

            # 4. Image URL
            img_tag = card.select_one('img.product-block-image')
            image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else "N/A"
            if image_url != "N/A" and image_url.startswith('//'):
                image_url = "https:" + image_url

            # 5. Price
            # Handling sale vs regular price
            price_tag = card.select_one('.product-price-amount, .price-sales')
            sale_tag = card.select_one('.product-price-sales, .price-standard') # The old price usually
            
            # Logic: If sale tag exists, current price is the sale price
            current_price = price_tag.get_text(strip=True) if price_tag else "N/A"
            
            products.append({
                "Product Name": name,
                "Price": current_price,
                "Product URL": product_url,
                "Image URL": image_url,
                "SKU": product_id
            })
        except Exception as e:
            # Skip bad items to keep script running
            continue

    return products

def main():
    all_products = []
    
    # Loop for pagination
    # TNF uses ?start=0, ?start=20 usually for pagination offsets
    items_per_page = 20
    
    for page in range(MAX_PAGES):
        offset = page * items_per_page
        current_url = f"{BASE_URL}?start={offset}&sz={items_per_page}"
        
        print(f"Scraping Page {page + 1}: {current_url}")
        
        html = get_page_content(current_url)
        
        if html:
            batch = parse_products(html)
            if not batch:
                print("No products found, stopping.")
                break
            all_products.extend(batch)
        else:
            print("Failed to retrieve HTML.")
            break
            
        # Polite delay not strictly needed with Zyte, but good practice
        time.sleep(1)

    # Save to CSV
    if all_products:
        keys = all_products[0].keys()
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_products)
        print(f"\nSuccess! Scraped {len(all_products)} items. Saved to {OUTPUT_FILE}")
    else:
        print("\nNo data extracted.")

if __name__ == "__main__":
    main()