from src.automatic_time_lapse_creator_kokoeverest.source import Source


default_city_name = "Sofia"
invalid_city_name = "Logator"
valid_source_name = "aleko"
valid_url = "https://home-solutions.bg/cams/aleko2.jpg?1705293967111"

sample_source1 = Source(valid_source_name, valid_url)
duplicate_source = Source(valid_source_name, valid_url)

sample_source2 = Source(
    "markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"
)
sample_source3 = Source(
    "plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
)
sample_source_with_empty_url = Source("fake", "empty url")
empty_dict = {}