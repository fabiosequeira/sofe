import logging

import requests
from lxml import html

logger = logging.getLogger(__name__)


def get_anime_filler_list(afl_anime_name: str) -> list[int]:
    """
    Download and parse filler episodes from AnimeFillerList.
    """

    url = f"https://www.animefillerlist.com/shows/{afl_anime_name}/"

    logger.info(f"Downloading AnimeFillerList page: {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        logger.info(
            f"AnimeFillerList responded with HTTP {response.status_code}"
        )

        data = html.fromstring(response.content)

        filler_ranges = data.xpath(
            '//div[@class="filler"]/span[@class="Episodes"]/a/text()'
        )

        if not filler_ranges:
            logger.warning(
                "No filler episode ranges were found. "
                "The anime name may be incorrect or the website layout may have changed."
            )

        logger.debug(f"Raw filler ranges: {filler_ranges}")

        fillers = []

        for text in filler_ranges:
            try:
                text = text.strip()

                if "-" in text:
                    start, end = map(int, text.split("-"))
                    fillers.extend(range(start, end + 1))
                else:
                    fillers.append(int(text))

            except ValueError:
                logger.warning(
                    f"Ignoring invalid filler range: '{text}'"
                )

        fillers = sorted(set(fillers))

        logger.info(
            f"Parsed {len(fillers)} filler episode(s)."
        )

        return fillers

    except requests.exceptions.RequestException:
        logger.exception(
            "Failed to download AnimeFillerList."
        )

    except Exception:
        logger.exception(
            "Unexpected error while parsing AnimeFillerList."
        )

    return []