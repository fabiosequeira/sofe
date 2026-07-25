<p align="center">
  <img src="metadata/logo.png?raw=true" alt="Sofe's Logo"/>
</p>
<p align="center" >
  <picture><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/fabiosequeira/sofe?style=flat&logo=github&logoColor=white&label=Stars"></picture>
  <picture><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/fabiosequeira/sofe?style=flat&logo=github&logoColor=white&label=COMMITS"></picture>
  <picture><img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues-closed/fabiosequeira/sofe?style=flat&logo=github&logoColor=white"></picture>
  <picture><img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/fabiosequeira/sofe?style=flat&logo=github&logoColor=white"></picture>
  <picture><img alt="GitHub License" src="https://img.shields.io/github/license/fabiosequeira/sofe?style=flat"></picture>
</p>

SoFE (Sonarr Anime Filler Excluder) is a Python application that configures Sonarr to monitor only non-filler anime episodes sourced from [Anime Filler List](https://www.animefillerlist.com). It also creates separate Plex collections for non-filler and filler episodes, depending on the download status.

> [!Note]
> This is a fork of [chkpwd/sofe](https://github.com/chkpwd/sofe) with reliability fixes on top: logging throughout the app, added timeouts and small fixes to prevent the app from hanging or failing silently, and tagged releases (the upstream repo has no tags, so `:latest` can resolve to an unexpected build).

## Features

- Parses filler episodes from AnimeFillerList
- Monitors non-filler episodes in Sonarr
- Creates Plex Collections for non-filler and filler episodes

## Changes in this fork

- **Logging** — the app now logs its steps (fetching filler data, calling Sonarr/Plex, results) instead of running silently, making it much easier to tell what happened or went wrong.
- **Timeouts & stability fixes** — outbound requests now have timeouts and a few edge cases that could hang or crash the app have been patched.
- **Tagged releases** — proper version tags are published, so `docker pull` gives you a pinned, reproducible image instead of always resolving to whatever `main` currently is.

## Prerequisites

- Sonarr
- Plex
- Docker / Docker Compose

> [!Note]
> Make sure to obtain the anime name from the [Anime Filler List](https://www.animefillerlist.com/) URL — e.g. for `animefillerlist.com/shows/one-piece`, the value is `one-piece`.

![alt text](./metadata/image.png)

## Installation

SoFE can be easily run as a container. This section covers pulling the image from the GitHub Container Registry and running it.

### Pulling the Container Image

Pull a specific, tagged version (recommended, now that releases are tagged):

```sh
docker pull ghcr.io/fabiosequeira/sofe:<version>
```

Or pull the latest build:

```sh
docker pull ghcr.io/fabiosequeira/sofe:latest
```

Check the [Releases](https://github.com/fabiosequeira/sofe/releases) page for available version tags.

### Running the Container

```sh
docker run --rm -p 7979:7979 \
  -e SONARR_URL="https://sonarr.local" \
  -e SONARR_API_KEY="<your_api_key>" \
  -e SONARR_SERIES_ID="187" \
  -e AFL_ANIME_NAME="one-piece" \
  -e PLEX_URL="http://127.0.0.1:32400" \
  -e PLEX_TOKEN="<your_plex_token>" \
  -e CREATE_PLEX_COLLECTION="True" \
  -e MONITOR_NON_FILLER_SONARR_EPISODES="True" \
  -e PLEX_ANIME_LIBRARY="<your_plex_anime_library>" \
  ghcr.io/fabiosequeira/sofe:<version>
```

## Usage

1. **Find the Sonarr series ID** — the easiest way is to query the Sonarr API for the full series list and search the output for your show:

   ```sh
   curl "https://sonarr.local/api/v3/series" -H "X-Api-Key: <your_api_key>" -o series.txt
   ```

   Open `series.txt` and search (Ctrl+F) for the show's name. Near the bottom of that show's entry, after the `statistics` block, you'll find its `id` (shows with more seasons will have a longer entry to scroll through):

   ```json
   "statistics": {
     "seasonCount": 17,
     ...
   },
   "languageProfileId": 1,
   "id": 481
   ```

   That `id` (`481` in this example, for Bleach) is the value to use for `SONARR_SERIES_ID`; Note that the id value is internal to yout sonarr instance, hence the id for your Bleach WILL be different from this one.
2. **Find the AniFillerList slug** — go to [animefillerlist.com](https://www.animefillerlist.com/), search for the show, and copy the last part of the URL (e.g. `one-piece`) into `AFL_ANIME_NAME`.
3. **Get your Plex token (optional)** — only needed if you want Plex collections created; see [Plex's guide on finding your token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/). If you don't use Plex, set `CREATE_PLEX_COLLECTION=False` and you can leave `PLEX_URL`, `PLEX_TOKEN`, and `PLEX_ANIME_LIBRARY` unset.
4. **Set the environment variables** shown above and run the container. On a successful run, SoFE will:
   - fetch the current filler episode list for the configured show from Anime Filler List,
   - update episode monitoring in Sonarr so only non-filler episodes are monitored (if `MONITOR_NON_FILLER_SONARR_EPISODES=True`),
   - create/update Plex collections for filler vs. non-filler episodes (if `CREATE_PLEX_COLLECTION=True`).
5. **Check the logs** — with logging now in place, `docker logs <container>` will show each step and flag any failures (e.g. bad API key, unreachable Sonarr/Plex, unknown anime slug).
6. **Re-run periodically** — SoFE performs a single sync per run rather than watching continuously, so schedule it to re-run on whatever cadence suits you (e.g. a cron job, a systemd timer, or a scheduled task in your container orchestrator) to pick up newly aired episodes.

**Note**: Each run only scans the specific anime configured in your environment variables. If you want to process a different anime, update `SONARR_SERIES_ID` and `AFL_ANIME_NAME` in your configuration and restart the container.

### Environment variables

| Variable | Description |
|---|---|
| `SONARR_URL` | Base URL of your Sonarr instance |
| `SONARR_API_KEY` | Sonarr API key (Settings → General) |
| `SONARR_SERIES_ID` | ID of the target series in Sonarr |
| `AFL_ANIME_NAME` | Show slug from the Anime Filler List URL |
| `CREATE_PLEX_COLLECTION` | **Required.** `True`/`False` — whether to create Plex collections for filler/non-filler episodes. Recommended to set `False` if you don't use Plex. |
| `PLEX_URL` | Optional — only needed if `CREATE_PLEX_COLLECTION=True`. Base URL of your Plex server |
| `PLEX_TOKEN` | Optional — only needed if `CREATE_PLEX_COLLECTION=True`. Plex authentication token |
| `PLEX_ANIME_LIBRARY` | Optional — only needed if `CREATE_PLEX_COLLECTION=True`. Name of the Plex library containing the anime |
| `MONITOR_NON_FILLER_SONARR_EPISODES` | `True`/`False` — set Sonarr to monitor only non-filler episodes |
