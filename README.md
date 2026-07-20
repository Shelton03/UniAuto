# Research OS

A personal, local Windows desktop tool for discovering AI/ML papers and lab news, reviewing each item, and manually sending selected items to Zotero and/or a single Obsidian landing folder.

Research OS never organizes or writes into your numbered Obsidian folders. Each destination is a separate button in the Review tab, so an item can be sent to Zotero, Obsidian, both, or neither.

## Setup

1. Install Python 3.11+ for Windows, then open PowerShell in this folder.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`, then create the Zotero credentials as described in [Zotero credentials](#zotero-credentials). For reliable Semantic Scholar discovery, also request an API key as described in [Semantic Scholar](#semantic-scholar). Do not commit or share `.env`.
4. Edit `config.yaml` before the first real run. Set `obsidian.vault_path` to the absolute vault path and confirm `obsidian.landing_folder` exactly matches the existing unnumbered inbox-style folder. Research OS deliberately refuses to create this folder.
5. Confirm that the Zotero collection named by `zotero.collection_name` exists (the default is `00 Inbox`). The tool will raise an error rather than creating a duplicate collection.

## Run it

Start the native desktop app:

```powershell
python gui\app.py
```

Use **Config** to manage tracked interests. Entries added there receive today’s date automatically. Use **Run now** to execute discovery without freezing the window; its live console is fed by a background worker. **Review** provides independent Zotero and Obsidian buttons. **History** searches logged discoveries, including ignored and dismissed items. **Trends** shows promoted-area coverage and age-aware blind spots.

The automation can also run without the GUI:

```powershell
python automation\weekly_update.py
```

Network/API source failures are reported in the run log but do not prevent the remaining sources from producing a digest. The log names each RSS or official-news-page fallback and reports the exact trending-item count.

## Zotero credentials

1. Sign in at [zotero.org/settings/keys](https://www.zotero.org/settings/keys).
2. Select **Create new private key**, give it a clear label such as `Research OS`, and enable **Allow library access** and **Allow write access**. Write permission is required because this app creates items in your existing `00 Inbox` collection.
3. Create the key and copy it immediately. Put it in `.env` as `ZOTERO_API_KEY=...`. Treat it like a password.
4. On the same API Keys page, copy the numeric **User ID** shown for your account and set `ZOTERO_USER_ID=...` in `.env`. It is not your username.
5. Keep the `00 Inbox` collection in Zotero. Research OS looks it up by name and will stop with a clear error instead of creating a duplicate.

Example `.env` (with your real values, never this placeholder text):

```ini
ZOTERO_API_KEY=paste-your-private-key-here
ZOTERO_USER_ID=your-numeric-user-id
```

## Semantic Scholar

Semantic Scholar works without a key, but anonymous traffic shares a public rate limit and can return `429 Too Many Requests`, which means its results will not appear for that run. For dependable coverage, request a free key through the [Semantic Scholar API page](https://www.semanticscholar.org/product/api), wait for the emailed key, and add it to `.env`:

```ini
SEMANTIC_SCHOLAR_API_KEY=paste-your-private-key-here
```

The run log and Review source summary make it clear when that source was throttled or yielded no eligible items.

## Sources and ranking

The paper discovery search terms are generated from `research_questions` and `research_areas`. arXiv, OpenAlex, and Semantic Scholar are enabled independently in `config.yaml`. News starts with Oxford, Cambridge, DeepMind, Anthropic, and OpenAI. Publishers sometimes retire or change RSS endpoints; `automation/discover_news.py` first uses a maintained RSS feed where available and otherwise uses that organisation's official news page, with the chosen route visible in the run log. To add a source, edit `NEWS_SOURCES` in that file.

Trending news is intentionally separate from personalised discovery. The original broad DuckDuckGo query returned category pages rather than articles, so the retained `duckduckgo_trending` toggle now collects current AI article headlines through Google News RSS. It clusters the coverage into named topic groups, lists the reporting websites under each topic, and assigns `trend score = reports + 2 × distinct sites`. Each article has a **Visit source** button as well as the independent Zotero and Obsidian actions.

Regular discovery queries use research questions, research areas, and tracked researchers—not university names. Items get one point for each matched research question, research area, and tracked researcher, plus a 0.5 recency bonus for publication in the last 14 days. A university is enrichment metadata only: it never changes the score or causes an item to appear in Review. Broad one-word areas such as `Reasoning` also require an AI/ML context, avoiding unrelated religious, philosophical, or legal matches. Equivalent paper titles from multiple APIs merge into one Review card, while all source records remain searchable in History. To appear in Review, a paper/news item must match a research question, a research area, or a tracked researcher.

## State and blind spots

`state.db` is local SQLite state, created automatically. It stores every discovery even when it is ignored. Only `automation/state_store.py` accesses it directly. Blind spot windows are per-entry: `min(lookback_days, days_since_date_added)`. An entry added today therefore has a zero-day window and is not shown as a blind spot.

## Weekly Task Scheduler job

1. Open **Task Scheduler** → **Create Basic Task**.
2. Name it `Research OS weekly update`.
3. Choose **Weekly** and choose your preferred day and time.
4. Select **Start a program**.
5. For **Program/script**, enter the full path to `run_weekly_update.bat` in this folder, for example `C:\Users\you\Desktop\UniAuto\run_weekly_update.bat`.
6. Finish the wizard, then use **Run** once in Task Scheduler to verify it. The batch file uses this project’s `.venv` (or the existing `uni_venv`, if present) and runs `automation/weekly_update.py`.

## Notes on Zotero and Obsidian

Zotero receives a `journalArticle` with DOI, metadata, and the configured existing collection. Matched research questions, research areas, universities, and researchers are added as Zotero tags. The collection can be a subcollection anywhere under My Library; its name is matched case-insensitively. When a DOI is present, it remains in the record for Zotero client enrichment; metadata is also supplied as a reliable fallback. Obsidian notes use the same labels as tags and add non-writing wiki-links for questions, areas, universities, and researchers, plus a clickable source link. No source automatically promotes anything.
