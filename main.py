import json
import logging
import traceback

from app.plex import create_plex_collection
from app.parser import get_anime_filler_list
from app.sonarr import get_sonarr_episodes, configure_monitoring
from app.variables import USER_CONFIG

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if USER_CONFIG.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    logger.info("Starting SoFE processing...")
    logger.info(f"AnimeFillerList anime: {USER_CONFIG.afl_anime_name}")
    logger.info(f"Sonarr Series ID: {USER_CONFIG.sonarr_series_id}")

    logger.info("Fetching filler episodes from AnimeFillerList...")
    fillers_from_api = get_anime_filler_list(USER_CONFIG.afl_anime_name)

    if not fillers_from_api:
        logger.warning(
            "AnimeFillerList returned 0 filler episodes. "
            "The anime name may be incorrect or no filler episodes were found."
        )
    else:
        logger.info(f"Found {len(fillers_from_api)} filler episode(s).")

    logger.info("Fetching episodes from Sonarr...")
    sonarr_episodes = get_sonarr_episodes(USER_CONFIG.sonarr_series_id)

    if not sonarr_episodes:
        logger.warning("Sonarr returned 0 episodes.")
    else:
        logger.info(f"Found {len(sonarr_episodes)} episode(s) in Sonarr.")

    nonfillers_episodes = []

    logger.info("Processing episode list...")

    skipped_absolute_number = 0

    for episode in sonarr_episodes:
        absolute_episode = episode.get("absolute_episode_number")

        if absolute_episode is None:
            skipped_absolute_number += 1
            logger.debug(
                f"Skipping '{episode.get('title', 'Unknown')}' because it has no absolute episode number."
            )
            continue

        if absolute_episode not in fillers_from_api:
            nonfillers_episodes.append(
                {
                    "id": episode.get("id"),
                    "season": episode.get("season"),
                    "episode_number": episode.get("episode_number"),
                    "absolute_episode_number": absolute_episode,
                }
            )

    logger.info(
        f"Found {len(nonfillers_episodes)} non-filler episode(s)."
    )

    if skipped_absolute_number:
        logger.info(
            f"Skipped {skipped_absolute_number} episode(s) without an absolute episode number."
        )

    episodes_in_season_episode_format = [
        f"s{episode['season']:02d}e{episode['episode_number']:02d}"
        for episode in nonfillers_episodes
    ]

    episodes_to_monitor = [
        episode["id"]
        for episode in nonfillers_episodes
        if episode.get("id") is not None
    ]

    if USER_CONFIG.create_plex_collection:
        logger.info("Creating/updating Plex collections...")
        create_plex_collection(
            collection_items=episodes_in_season_episode_format
        )
        logger.info("Finished Plex collection processing.")

    logger.debug(
        "Non-Filler Episodes:\n%s",
        json.dumps(nonfillers_episodes, indent=4),
    )

    if USER_CONFIG.monitor_non_filler_sonarr_episodes:
        if episodes_to_monitor:
            logger.info(
                f"Updating monitoring for {len(episodes_to_monitor)} episode(s)..."
            )
            configure_monitoring(monitored_list=episodes_to_monitor)
            logger.info("Sonarr monitoring update completed.")
        else:
            logger.warning("No episodes available to monitor.")
    else:
        logger.info("Monitoring updates are disabled by configuration.")

    logger.info("SoFE completed successfully.")


if __name__ == "__main__":
    logger.info("Initializing SoFE...")

    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
    except Exception:
        logger.exception("Unhandled exception while running SoFE:")
        logger.debug(traceback.format_exc())
        raise