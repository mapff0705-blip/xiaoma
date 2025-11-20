
import os
from crewai_tools import BaseTool
from tavily import TavilyClient
from pydantic import PrivateAttr
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


class TavilySearchResults(BaseTool):
    name: str = "Tavily Search Results"
    description: str = (
        "A tool that searches the web using Tavily API. "
        "Input should be a clear search query string."
    )

    # 声明私有属性（不会被 Pydantic 当作模型字段）
    _client: TavilyClient = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        api_key = TAVILY_API_KEY
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set.")
        self._client = TavilyClient(api_key=api_key)  # 使用 _client

    def _run(self, query: str) -> str:
        try:
            response = self._client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                max_results=5
            )
            results = []
            for res in response.get("results", []):
                results.append(
                    f"- {res['title']}\n  URL: {res['url']}\n  Content: {res['content'][:300]}..."
                )

            answer = response.get("answer", "")
            if answer:
                results.insert(0, f"Tavily AI Answer:\n{answer}\n")

            return "\n\n".join(results) if results else "No relevant results found."

        except Exception as e:
            return f"Error during Tavily search: {str(e)}"