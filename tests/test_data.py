from src.automatic_time_lapse_creator_kokoeverest.time_lapse_creator import Source


sample_source1 = Source(
    "aleko", "https://home-solutions.bg/cams/aleko2.jpg?1705293967111"
)

sample_source2 = Source(
    "markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"
)
sample_source3 = Source(
    "plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
)

sample_source_with_empty_url = Source(
    "fake", "empty url"
)