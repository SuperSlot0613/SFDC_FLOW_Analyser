import httpx
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

"""
NLP Bridge Utility for AI Failure Analysis
This module provides a method to send error payloads to an AI/NLP model for analysis.
The actual integration (API call, model invocation) should be implemented in the core method.
"""



class NLPBridge:
    enabled = True # Set to False to disable AI

    # ----------------------------------------------------------------------
    # Prompt template (unchanged – paste the same block you already had)
    # ----------------------------------------------------------------------
    _PROMPT_TEMPLATE = """You are a test‑reporting assistant.

Your task is to read a raw failure dump (the **INPUT** below) that may contain one or more test‑case iterations.

**Iteration delimiter** – each iteration starts with a line that:
* begins with the emoji `🔹`
* is followed by a space, then the iteration name in **bold**, ending with a colon (`:`)

Example delimiter line (the only thing that matters):
    🔹 **ONE_STEP_CREATE_CASE_1**:

All text after a delimiter line belongs to that iteration until the next delimiter line (or end‑of‑input).  
Create **one Markdown table row for each delimiter you find** – no more, no less.

### Output (the ONLY thing you must output)

| # | Iteration (Test‑case) | Error ID | Primary exception | Root‑cause line (in code) | Traceback (summary) | Failure description | Technical categorisation | Outcome | Severity (suggested) |
|---|-----------------------|----------|-------------------|---------------------------|---------------------|----------------------|--------------------------|---------|----------------------|
| 1 | … | … | … | … | … | … | … | … | … |

**Column rules**

* **#** – serial number, starting at 1, incremented per delimiter.
* **Iteration (Test‑case)** – the text inside the bold markup (e.g. `ONE_STEP_CREATE_CASE_1`).
* **Error ID** – the identifier that appears after `Error_id:` (case‑insensitive, e.g. `TUE31364`).
* **Primary exception** – the *wrapper* exception that is finally raised (the one after the last `raise …`).  
  If it is an `AssertionError`, prefix it with `→ `, e.g. `→ AssertionError: 'name'`.
* **Root‑cause line (in code)** – the exact line of source that triggered the inner exception (the line just before the innermost `KeyError`, `TargetClosedError`, etc.).
* **Traceback (summary)** – a concise one‑line chain of modules/functions separated by `→`, ending with the *wrapper* exception name you placed in **Primary exception**. Include only the frames that appear between the first `File "...` line after the delimiter and the final `raise` line.
* **Failure description** – a short natural‑language sentence explaining why the iteration stopped (e.g., “A `KeyError: 'name'` was raised when accessing `creds['name']`; the framework re‑raised it as an `AssertionError`, causing the test to abort.”).
* **Technical categorisation** – a precise technical label derived from the wrapper exception, e.g.  
  - `Missing Data – KeyError on 'name'`  
  - `Environment / Browser – TargetClosedError`  
  - `Other – AssertionError`  
  Do **not** use the generic “Other” label; always provide a concrete reason.
* **Outcome** – exactly: `Iteration stopped. Total 0 validations are failed.`
* **Severity (suggested)** – `CRITICAL` for *Missing Data*, `BLOCKER` for *Environment / Browser*, `NORMAL` for *Other*.

### Additional constraints
1. **Do not fabricate** any value – use only what is present in the input.
2. If the same root‑cause line appears for several iterations, repeat it in each row (the table must be self‑contained).
3. Preserve the order of the delimiters as they appear in the input.
4. **Output ONLY the Markdown table** – no explanatory text before or after it.
5. Use a deterministic generation setting (temperature = 0 or the lowest available) to avoid hallucinated extra rows.

### INPUT
{raw_input}
    """

    @staticmethod
    def ask_llm(prompt):
        if not NLPBridge.enabled:
            return "[NLP BRIDGE DISABLED.. TO MAKE IT ENABLE IN SET NLPBridge=True in base config]"
        custom_client = httpx.Client(verify=False)

        # For your internal LLM auth
        API_KEY = "c3VtaXQuc2luZ2gxMjpOZXdqb2JAMjAwMg=="
        LLM_MODEL_NAME = "/app/models/Qwen3-14B-FP8"
        LLM_API_BASE = "https://llm-api.iservebetter.idfcfirstbank.com/qwen3-14b/v1"

        llm = ChatOpenAI(
            model_name=LLM_MODEL_NAME,
            openai_api_key=SecretStr(API_KEY),
            openai_api_base=LLM_API_BASE,
            temperature=0,
            http_client=custom_client
        )
        message = {
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }
        response = llm.invoke([message])
        return response.content if hasattr(response, "content") else str(response)

    @staticmethod
    def analyze_failure(raw_input) -> str:
        print("raw input ->", raw_input)
        if not NLPBridge.enabled:
            return "[AI ANALYSIS DISABLED]"
        # ------------------- 4️⃣ Build the prompt -------------------------
        prompt = NLPBridge()._PROMPT_TEMPLATE.replace("<<<RAW_INPUT>>>", raw_input)
        response = NLPBridge.ask_llm(prompt)
        return response