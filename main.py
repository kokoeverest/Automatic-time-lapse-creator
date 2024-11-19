from src.automatic_time_lapse_creator_kokoeverest.time_lapse_creator import TimeLapseCreator
from src.automatic_time_lapse_creator_kokoeverest.source import Source
import os

# Valid sources
aleko_source = Source(
    "aleko", "https://home-solutions.bg/cams/aleko2.jpg?1705293967111"
)
borovets_source = Source(
    "markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"
)
pleven_hut_source = Source(
    "plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
)

sources_list: list[Source] = [aleko_source, borovets_source, pleven_hut_source]
# or
# bulgaria_webcams = TimeLapseCreator(sources_list)

bulgaria_webcams = TimeLapseCreator()
bulgaria_webcams.add_sources(sources_list)

# Invalid source 
sample_source_with_empty_url = Source("fake", "https://empty.url")
invalid_source_list = [sample_source_with_empty_url]

invalid_url_creator = TimeLapseCreator(invalid_source_list)


if __name__ == "__main__":
    # invalid_url_creator.execute()
    bulgaria_webcams.execute()
