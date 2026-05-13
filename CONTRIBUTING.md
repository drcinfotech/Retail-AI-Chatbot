# Contributing to Retail AI Chatbot

Thanks for your interest in contributing. This guide will get you from zero to a working dev setup in about five minutes.

## Ways to contribute

- 🐛 **Bug reports** — open an issue using the bug report template
- 💡 **Feature ideas** — open an issue using the feature request template
- 📖 **Docs improvements** — typos, clarifications, new examples
- 🧠 **New intents** — extend the chatbot's understanding (see below)
- 🎨 **UI polish** — new block types, animations, accessibility improvements
- 🌍 **Internationalization** — translations of the bot's responses

## Development setup

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- Git

### Get the code

```bash
git clone https://github.com/YOUR-USERNAME/Retail-AI-Chatbot.git
cd Retail-AI-Chatbot
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python test_chatbot.py             # Verify your setup — should show 21/21 passing
uvicorn main:app --reload --port 8000
```

### Frontend (in a separate terminal)

```bash
cd frontend
npm install
npm run dev
```

The browser opens to `http://localhost:5173`. Both servers hot-reload on save.

### Or just use Docker

```bash
docker compose up --build
```

Same result, no local Python or Node needed.

## Adding a new intent

Three places to edit, in order:

**1. Define the intent** — `backend/app/intents.py`, append to `INTENTS`:

```python
IntentSpec(
    "wishlist_add",
    patterns=[r"\b(save|wishlist|favorite)\s+.+\b(for later)?\b"],
    keywords=["wishlist", "save", "favorite"],
),
```

Patterns score 2.0 each (high precision). Keywords score 0.6 each (cumulative). The classifier picks the highest scorer.

**2. Add a handler** — `backend/app/chatbot.py`:

```python
def _handle_wishlist(_c: Classification, session: Session):
    return (
        [_build_text("Saved! I'll let you know if it drops in price.")],
        ["Show my wishlist", "Browse trending"],
    )

# Register it in ChatbotEngine.respond's handler_map:
handler_map["wishlist_add"] = lambda: _handle_wishlist(c, session)
```

**3. Add a test** — `backend/test_chatbot.py`, append to `cases`:

```python
("save this for later", "wishlist_add"),
```

**4. (Frontend, optional)** — Only edit `frontend/src/components/Blocks.jsx` if you're introducing a brand-new *block type* (something beyond text/products/cart/order/promo). Existing intents reuse the existing block components.

## Code style

**Python**
- Use type hints on public functions and Pydantic models
- Prefer dataclasses over namedtuples for internal records
- Keep functions short; if a handler exceeds ~25 lines, split it
- Module-level constants in `UPPER_SNAKE`

**JavaScript / JSX**
- Two-space indentation
- Single quotes for strings, double quotes only for JSX attributes
- Hooks at the top of components, derived values next, handlers last, JSX last
- Tailwind utility classes preferred; reach for `index.css` only for custom utilities

**Commits**
- Use the imperative mood: *"Add wishlist intent"* not *"Added wishlist intent"*
- Keep the subject line under 72 characters
- Reference issues with `#123` when relevant

## Pull request checklist

Before opening a PR, please confirm:

- [ ] `python test_chatbot.py` passes locally (21/21 or more)
- [ ] `npm run build` completes without errors or new warnings
- [ ] You've added tests for any new intent, entity, or behavior
- [ ] The README is updated if you changed behavior visible to users
- [ ] You've manually exercised the changed flow in the browser
- [ ] No secrets, API keys, or personal data committed
- [ ] Commit messages are clear and reference relevant issues

## Filing issues

Good issues include:

- **What you tried** — the exact message you sent the bot, the action you took
- **What happened** — full error output, screenshots
- **What you expected** — what the correct behavior would be
- **Environment** — OS, Python version, Node version, browser

## Questions?

Open a discussion thread in the repo, or reach out to the maintainer via the contact info on their GitHub profile. We'll get back to you.
