# Screenshots

This folder holds the visuals shown in the main `README.md`. Drop your captured PNG/GIF files here and they'll be picked up automatically.

## What to capture

For maximum impact on portfolio viewers, capture these five visuals in order. Run both servers first (`uvicorn main:app --reload --port 8000` and `npm run dev`), open the app at `http://localhost:5173`, then:

| Filename | What to show | Why it matters |
|---|---|---|
| `01-hero.png` | Full chat window after the greeting message, sidebar visible | The first thing visitors see — sets the design tone |
| `02-product-search.png` | Result of *"find me a minimalist gift under 6000"* — the 3 product cards rendered in chat | Proves the AI filtering works |
| `03-cart.png` | Result of *"show my cart"* with 2-3 items, subtotal & shipping visible | Shows real cart logic |
| `04-order-tracking.png` | Result of *"track order TRK-8829145"* with the timeline | Shows rich block rendering |
| `05-demo.gif` | 15-30 second screen recording of a full conversation | Animated demos triple repo engagement |

## Recording tools

**Windows** — [ScreenToGif](https://www.screentogif.com/) (free, open-source, can record and trim)
**macOS** — [Kap](https://getkap.co/) (free, native, exports to .gif and .mp4)
**Linux** — [Peek](https://github.com/phw/peek) (apt install peek)

## Embedding in the README

Once you have the files, add this section near the top of the main `README.md` (right after the description, before "What it does"):

```markdown
## 📸 Preview

![Chat interface](docs/screenshots/01-hero.png)

<details>
<summary>More screenshots</summary>

![Product search](docs/screenshots/02-product-search.png)
![Cart](docs/screenshots/03-cart.png)
![Order tracking](docs/screenshots/04-order-tracking.png)

</details>

![Demo](docs/screenshots/05-demo.gif)
```

## Capture tips

- Use a window width of **1280–1400px** for crisp screenshots
- Set your OS to **dark mode** so the chrome matches the app
- Keep file sizes reasonable: PNG under ~300KB each, GIF under 5MB
- For GIFs, target 10–15fps and 800px width to balance quality with size
