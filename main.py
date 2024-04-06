from time_lapse_creator import Source, TimeLapseCreator

sources_list: list[Source] = [
    Source("aleko", "https://home-solutions.bg/cams/aleko2.jpg?1705293967111"),
    Source("markudjik", "https://media.borovets-bg.com/cams/channel?channel=31"),
    Source("plevenhut", "https://meter.ac/gs/nodes/N160/snap.jpg?1705436803718"),
]

bulgaria_webcams = TimeLapseCreator(sources_list)

bulgaria_webcams.execute()
