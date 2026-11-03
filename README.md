# Hits by Design

**A DMAIC study of Omar Courtz's album streams**
By **Fernando Zegrí** · University of Puerto Rico

🔗 **Live site:** https://fzegri.github.io/hits-by-design/

## What it is

A Six Sigma Yellow Belt DMAIC project that asks one question: **how should Omar Courtz build and time his third album**, based on how the songs on his first two albums performed? It treats an album as a product line. Each song is a product, and its daily Spotify streams are the quality measure.

- **Scope:** 35 songs from *PRIMERA MUSA* (2024) and *POR SI MAÑANA NO ESTOY* (2026)
- **Tools:** project charter, SIPOC, process map, Pareto/ABC, fishbone diagram, median comparisons, 5 Whys, run charts, control plan
- **Output:** an Album 3 brief, a tracklist calculator, and a recommended release calendar

## Key findings

1. Streams are concentrated: 18 of 35 songs earn 80% of streams.
2. Intro/interlude/outro tracks underperform on both albums.
3. Songs in the second half of the tracklist outstream the first half on both albums.
4. Features, pre-release singles and song length aren't reliable levers. The two albums disagree on all three.
5. Recommended Album 3 release: **Friday, July 23, 2027**, with the lead single around May 21, 2027.

## How it stays up to date

A GitHub Actions workflow (`.github/workflows/weekly-update.yml`) runs every Saturday:

1. Downloads the latest stream counts from [kworb.net](https://kworb.net/spotify/artist/3E12tRURRvPfHz0hAMCFYc_songs.html)
2. Checks every number (totals can't drop, daily streams can't jump unrealistically). If anything fails, nothing changes that week.
3. Adds a weekly snapshot to `history.js`, which feeds the run charts in the Control phase
4. Commits the update, and GitHub Pages republishes the site

Weekly updates continue until Omar Courtz releases his third studio album.

## Files

| File | What it holds |
|---|---|
| `index.html` | The site (D3.js charts, three tabs: About, Dashboard, DMAIC) |
| `data.js` | Latest numbers for the 35 songs |
| `history.js` | One snapshot per week |
| `status.js` | Marks the final update once Album 3 is out |
| `scripts/weekly_update.py` | The weekly updater |

## Data sources

kworb.net (Spotify streams), Wikipedia, Deezer, Apple Music, artist credit pages. Patterns come from 2 albums and 35 songs. They're associations, not proven causes.
