# AI Event Operations Agent

This agent helps event coordinators decide what to follow up on first. Ask a question in plain English to check registrations, find upcoming deadlines, or see which event needs attention and why.

This project grew out of my work on an event analytics platform at TruAbutment. All four events, their registrations, and their deadlines are fictional. The demo uses a fixed date of November 19, 2026 so you can reproduce the examples.

## Try a conversation

1. Ask “Show Systems Summit performance.” The event has 84 confirmed registrations against a goal of 120. That leaves 36 seats to fill.
2. In the same tab, ask “What is its deadline?” The app remembers you were discussing Systems Summit and finds its November 21 catering deadline.
3. Ask “Remember a 3-day deadline window,” then “Show deadlines.” You’ll see Sensor Lab’s overdue shipment and Systems Summit’s upcoming catering deadline. Edge Expo’s deposit is six days away, so it falls outside your window.
4. Ask “Rank operational risks.” Sensor Lab comes first. All 40 seats are filled, but its demo kits were due to ship November 18. The agent recommends confirming whether they shipped.

Expand “evidence” beneath an answer to see the records used. The risk ranking checks all open tasks, even when you’ve narrowed the deadline list.

## Run the free demo

You’ll need Python 3.12. From the project folder, run these commands in a terminal on macOS or Linux:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python -m uvicorn eventops.web:app --host 127.0.0.1 --port 8000

On Windows PowerShell, use `.\.venv\Scripts\Activate.ps1` for the activation step. Open http://127.0.0.1:8000 in your browser. The demo runs on your computer without an API key. It recognizes a limited set of question patterns, so start with the examples above.

## Follow a question through the code

1. Receive the question. The web form in `eventops/index.html` sends the question and a session ID to `POST /chat`. FastAPI validates the request in `eventops/web.py`.
2. Load context. `eventops/store.py` retrieves the session’s four most recent turns and the operator’s saved deadline window from SQLite. Conversation history helps resolve “its.” The saved window carries over to a new session.
3. Choose a lookup. In demo mode, `eventops/agent.py` uses rules to select an event and one of three tools: performance, deadlines, or risks. In live mode, `eventops/live.py` lets an OpenAI model choose the tool and event through the Agents SDK.
4. Retrieve the facts. `eventops/tools.py` runs parameterized SQL queries. Only confirmed registrations count toward a goal. The risk tool ranks overdue work first, tasks due within two days second, and remaining registration shortfalls third. Larger seat gaps break ties.
5. Show the answer. Python formats the tool’s results, saves the turn, and returns the answer and evidence to the browser. You can check both the selected event and the figures.

The first launch creates `eventops.sqlite3` with 224 confirmed and nine cancelled registration records. Set `EVENTOPS_DB` to choose a different database path. This version is designed for one local operator.

## Optional live OpenAI mode

Live questions can incur API charges. Set `OPENAI_API_KEY` in your shell or secret manager. Stop the demo server before starting the live server on the same port. On macOS or Linux:

    export EVENTOPS_ALLOW_PAID=yes
    export OPENAI_MODEL=gpt-4.1-mini
    EVENTOPS_MODE=live python -m uvicorn eventops.web:app --host 127.0.0.1 --port 8000

Live mode sends the question and recent conversation context to the model. Use synthetic questions. To try a single paid Responses API request separately, run `python -m eventops.first_request` after setting the key and paid opt-in.

## Tests and results

The offline demo passed 31 of 31 evaluation cases. Each case checks the chosen tool, event, and expected evidence or clarification. This catches errors such as returning an accurate registration count for the wrong workshop. The full suite passed 37 tests, including a failed lookup, saved preferences, and an Agents SDK tool call with a simulated model response.

Run the checks from the project folder:

    python -m pytest -q
    python evaluate.py

The questions are in `tests/cases.json`. The recorded offline accuracy, latency, and error rate are in `docs/evaluation.json`. Live-model accuracy and latency are still unmeasured. Running the evaluator in live mode with paid requests enabled makes multiple API calls.

## Portfolio and interview notes

- Built a local FastAPI agent with three typed Python tools for registration counts, deadline checks, and risk ranking. SQLite stores conversation history and the operator’s saved deadline window. Each lookup shows the records behind the answer.
- Built a 37-test suite that includes 31 evaluation cases. Additional tests cover tool access restrictions, how the app handles a failed lookup, and how the OpenAI Agents SDK executes a tool call from a simulated model response.

### What does the conversation add to a dashboard?

After checking Systems Summit’s registrations, a coordinator can ask “What is its deadline?” The agent uses the previous turn to identify the event and queries its deadline. If the coordinator saves a three-day window, future deadline lists use that preference, including in a new session.

### Where does reliability engineering come in?

I started with three ways an answer could mislead a coordinator. Counting cancellations would turn 84 confirmed seats into 87, so the test data includes both registration statuses. Looking up the wrong event could return a plausible number, so the evaluation checks both the selected tool and the event ID. If a lookup fails, a separate test verifies that the API returns HTTP 503 and the coordinator sees an error message.

### What would I build next?

For warehouse data, I’d add a read-only BigQuery connection that returns the same fields as the SQLite tools. For a team rollout, I’d add sign-in and tie each session and preference to its owner. To measure live-model accuracy, I’d run the chosen model against a separate set of questions held back during development and report those results alongside the offline baseline.
