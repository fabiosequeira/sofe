import logging
from typing import Any

try:
    from plexapi.video import Episode
    from plexapi.server import PlexServer
    from plexapi.base import MediaContainer
    from plexapi.library import ShowSection
except ModuleNotFoundError:
    Episode = Any
    PlexServer = None
    MediaContainer = Any
    ShowSection = Any

from app.variables import USER_CONFIG

logger = logging.getLogger(__name__)


def _get_plex_server():
    """
    Return a PlexServer instance if Plex is configured and available.
    """

    if PlexServer is None:
        logger.warning("Plex support disabled (plexapi not installed).")
        return None

    if not USER_CONFIG.plex_url or not USER_CONFIG.plex_token:
        logger.info("Plex support disabled (PLEX_URL or PLEX_TOKEN not configured).")
        return None

    try:
        logger.info(f"Connecting to Plex ({USER_CONFIG.plex_url})...")
        plex = PlexServer(
            baseurl=USER_CONFIG.plex_url,
            token=USER_CONFIG.plex_token,
        )
        logger.info("Successfully connected to Plex.")
        return plex

    except Exception:
        logger.exception("Failed to connect to Plex.")
        return None


def create_plex_collection(collection_items: list[str] | None = None):
    """
    Create filler and non-filler Plex collections.
    """

    if collection_items is None:
        collection_items = []

    logger.info(
        f"Preparing Plex collections ({len(collection_items)} non-filler episodes)."
    )

    plex = _get_plex_server()

    if plex is None:
        return

    if (
        not USER_CONFIG.plex_anime_library
        or not USER_CONFIG.plex_anime_name
    ):
        logger.warning(
            "PLEX_ANIME_LIBRARY or PLEX_ANIME_NAME not configured."
        )
        return

    try:
        logger.info(
            f"Opening Plex library '{USER_CONFIG.plex_anime_library}'."
        )

        media: ShowSection = plex.library.section(
            title=USER_CONFIG.plex_anime_library
        )

    except Exception:
        logger.exception(
            f"Unable to open Plex library '{USER_CONFIG.plex_anime_library}'."
        )
        return

    try:
        shows: MediaContainer = media.search(
            title=USER_CONFIG.plex_anime_name
        )

    except Exception:
        logger.exception("Failed while searching Plex.")
        return

    if not shows:
        logger.warning(
            f"No Plex show found matching '{USER_CONFIG.plex_anime_name}'."
        )
        return

    for show in shows:

        logger.info(f"Processing '{show.title}'.")

        nonfillers_items: list[Episode] = []
        fillers_items: list[Episode] = []

        try:
            plex_episodes = show.episodes()
        except Exception:
            logger.exception(
                f"Failed to fetch episodes for '{show.title}'."
            )
            continue

        logger.info(
            f"Plex returned {len(plex_episodes)} episode(s)."
        )

        for episode in plex_episodes:
            try:
                if episode.seasonEpisode in collection_items:
                    nonfillers_items.append(episode)
                else:
                    fillers_items.append(episode)
            except Exception:
                logger.exception(
                    f"Failed processing episode '{episode.title}'."
                )

        logger.info(
            f"Non-filler: {len(nonfillers_items)} | "
            f"Filler: {len(fillers_items)}"
        )

        collections = [
            (
                nonfillers_items,
                f"{show.title} - Non-Filler Episodes",
            ),
            (
                fillers_items,
                f"{show.title} - Filler Episodes",
            ),
        ]

        for items, collection_name in collections:

            try:
                if plex.library.search(title=collection_name):
                    logger.info(
                        f"Collection '{collection_name}' already exists."
                    )
                    continue

                if not items:
                    logger.info(
                        f"Skipping empty collection '{collection_name}'."
                    )
                    continue

                logger.info(
                    f"Creating collection '{collection_name}'."
                )

                plex.createCollection(
                    title=collection_name,
                    section=USER_CONFIG.plex_anime_library,
                    items=items,
                )

                logger.info(
                    f"Created '{collection_name}'."
                )

            except Exception:
                logger.exception(
                    f"Failed creating collection '{collection_name}'."
                )