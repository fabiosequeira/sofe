import logging

import sonarr

from app.variables import USER_CONFIG

logger = logging.getLogger(__name__)

CONFIGURATION = sonarr.Configuration(host=USER_CONFIG.sonarr_url)
CONFIGURATION.api_key["X-Api-Key"] = USER_CONFIG.sonarr_api_key


def get_sonarr_episodes(series_id: int) -> list[dict]:
    """
    Fetch all non-special episodes from Sonarr.
    """

    logger.info(f"Connecting to Sonarr ({USER_CONFIG.sonarr_url})...")
    logger.info(f"Fetching episodes for series ID {series_id}...")

    episodes = []

    with sonarr.ApiClient(configuration=CONFIGURATION) as api_client:
        api_instance = sonarr.EpisodeApi(api_client)

        try:
            api_response = api_instance.list_episode(series_id=series_id)

            logger.info(f"Sonarr returned {len(api_response)} episode(s).")

            skipped_specials = 0

            for item in api_response:
                if item.season_number == 0:
                    skipped_specials += 1
                    continue

                episodes.append(
                    {
                        "id": item.id,
                        "title": item.title,
                        "season": item.season_number,
                        "monitored": item.monitored,
                        "episode_number": item.episode_number,
                        "absolute_episode_number": item.absolute_episode_number,
                    }
                )

            logger.info(
                f"Loaded {len(episodes)} regular episode(s)."
            )

            if skipped_specials:
                logger.info(
                    f"Skipped {skipped_specials} special episode(s)."
                )

        except Exception:
            logger.exception(
                "Failed while requesting episodes from Sonarr."
            )

    return episodes


def configure_monitoring(monitored_list: list[int]) -> None:
    """
    Enable monitoring for the supplied Sonarr episode IDs.
    """

    if not monitored_list:
        logger.warning("No episodes supplied for monitoring update.")
        return

    logger.info(
        f"Updating monitoring status for {len(monitored_list)} episode(s)..."
    )

    with sonarr.ApiClient(configuration=CONFIGURATION) as api_client:
        api_instance = sonarr.EpisodeApi(api_client)

        episodes_monitored_resource = sonarr.EpisodesMonitoredResource(
            episodeIds=monitored_list,
            monitored=True,
        )

        try:
            api_instance.put_episode_monitor(
                episodes_monitored_resource=episodes_monitored_resource
            )

            logger.info("Successfully updated Sonarr monitoring.")

        except Exception:
            logger.exception(
                "Failed while updating Sonarr monitoring."
            )