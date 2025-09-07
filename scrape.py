import requests

 

def google_search(query, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": num_results
    }
    response = requests.get(url, params=params)
    data = response.json()

    results = []
    if "items" in data:
        for item in data["items"]:
            results.append({
                "title": item["title"],
                "link": item["link"],
                "snippet": item.get("snippet", "")
            })
    return results


# Example usage
if __name__ == "__main__":
    keyword = "best SEO tools 2025"
    results = google_search(keyword, num_results=5)
    for r in results:
        print(r["title"], "-", r["link"])
