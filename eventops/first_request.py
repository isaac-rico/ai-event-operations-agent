"""Run explicitly after enabling paid API usage."""
import os
from openai import OpenAI

if __name__ == "__main__":
    if os.getenv("EVENTOPS_ALLOW_PAID") != "yes":
        raise SystemExit("Set EVENTOPS_ALLOW_PAID=yes to authorize this paid request.")
    result = OpenAI().responses.create(model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),
                                       input="Explain event registration attainment in one sentence.")
    print(result.output_text)
