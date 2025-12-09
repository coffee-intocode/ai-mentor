from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


def get_articles() -> List[Dict[str, str]]:
    try:
        # Fetch the webpage
        url = "https://www.paulgraham.com/articles.html"
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all article links
        articles = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if href and href.endswith(".html") and not href.startswith("http"):
                # Construct full URL for relative links
                full_url = f"https://www.paulgraham.com/{href}"
                articles.append({"title": link.text.strip(), "url": full_url})
        return articles
    except Exception as e:
        raise Exception(f"Failed to fetch articles: {str(e)}")


@app.get("/articles", response_class=JSONResponse)
async def get_pg_articles():
    try:
        articles = get_articles()
        return {"status": "success", "count": len(articles), "articles": articles}
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
