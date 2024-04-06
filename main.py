from app.time_lapse_creator import Source, TimeLapseCreator


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

bulgaria_webcams = TimeLapseCreator(sources_list)

bulgaria_webcams.execute()
