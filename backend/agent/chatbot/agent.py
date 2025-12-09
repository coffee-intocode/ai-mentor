from typing import Any, cast

from dotenv import load_dotenv

load_dotenv()

import logfire
import pydantic_ai

logfire.configure(send_to_logfire="if-token-present", console=False)
logfire.instrument_pydantic_ai()


agent = pydantic_ai.Agent(
    "anthropic:claude-sonnet-4-0",
    instructions="Help the user answer questions about two products ('repos'): Pydantic AI (pydantic-ai), an open source agent framework library, and Pydantic Logfire (logfire), an observability platform. Start by using the `search_docs` tool to search the relevant documentation and answer the question based on the search results. It uses a hybrid of semantic and keyword search, so writing either keywords or sentences may work. It's not searching google. Each search result starts with a path to a .md file. The file `foo/bar.md` corresponds to the URL `https://ai.pydantic.dev/foo/bar/` for Pydantic AI, `https://logfire.pydantic.dev/docs/foo/bar/` for Logfire. Include the URLs in your answer. The search results may not return complete files, or may not return the files you need. If they don't have what you need, you can use the `get_docs_file` tool. You probably only need to search once or twice, definitely not more than 3 times. The user doesn't see the search results, you need to actually return a summary of the info. To see the files that exist for the `get_docs_file` tool, along with a preview of the sections within, use the `get_table_of_contents` tool.",
)


if __name__ == "__main__":
    # print(agent.run_sync('how do i see errors').output)
    # search_docs("logfire", "errors debugging view errors logs")
    agent.to_cli_sync()
