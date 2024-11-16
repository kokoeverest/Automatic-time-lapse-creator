from src.automatic_time_lapse_creator_kokoeverest.time_lapse_creator import Source, TimeLapseCreator


aleko_source = Source(
    "aleko", "https://home-solutions.bg/cams/aleko2.jpg?1705293967111"
)
borovets_source = Source(
    "markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"
)
pleven_hut_source = Source(
    "plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"
)

sample_source_with_empty_url = Source("fake", "https://empty.url")

sources_list: list[Source] = [aleko_source, borovets_source, pleven_hut_source]
invalid_source_list = [sample_source_with_empty_url]

# bulgaria_webcams = TimeLapseCreator(sources_list)

bulgaria_webcams = TimeLapseCreator(invalid_source_list)
# print(f"Sources before: {len(bulgaria_webcams.sources)}")

# bulgaria_webcams.remove_sources({aleko_source})
# print(f"Sources after: {len(bulgaria_webcams.sources)}")

if __name__ == "__main__":
    bulgaria_webcams.execute()
