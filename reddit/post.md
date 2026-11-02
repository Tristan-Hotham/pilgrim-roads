## Title

[OC] Every waymarked pilgrim route in OpenStreetMap: 77,804 km. More than half lead to Santiago de Compostela, and there is more of the Way of St James in Germany (14,814 km) than in Spain (9,922 km)

## Body

I took 1,906 OpenStreetMap route relations tagged as pilgrimage routes and measured them without counting any stretch twice (stages, super-routes and cycling versions overlap a lot: the naive total is 83,037 km). 41,674 km are signed for Santiago, in 22 countries, and only 13% of that lies within 500 km of the cathedral: half is more than 1,659 km away, mostly in Germany, Poland and Austria, and the farthest stretch is in Ukraine, 2,911 km away. Also mapped: the Via Francigena to Rome (5,120 km), the St Olav Ways to Trondheim (3,011 km), the Marian ways of Hungary (6,750 km) and 1,330 pilgrimage sites from Wikidata. Caveats: this is what volunteers have mapped, not where pilgrims walk; it is 99% European (the Hajj, Arba'een and Kumbh Mela do not appear as routes); and some famous routes, including the last stretch of the Camino Francés and most French routes, are missing from the download, so every total is a lower bound. Interactive map with search and distance rings: https://maps.tristanhotham.com/pilgrim-roads/

## Source comment

Sources: OpenStreetMap route relations tagged pilgrimage, via the Overpass API (© OpenStreetMap contributors, ODbL); Wikidata pilgrimage sites (CC0); Compostela certificate counts and historical facts from Wikipedia (CC BY-SA); outlines from Natural Earth. Kilometres = unique way segments (coordinates to about 10 m), each counted once; families from route names, Wikidata links and the scallop shell symbol; distances from Santiago are straight lines.

Tools: Python (pandas, shapely, pyproj, scipy, matplotlib); MapLibre for the interactive map.

Interactive version: https://maps.tristanhotham.com/pilgrim-roads/
Paper: https://doi.org/10.5281/zenodo.23878608
Blog post: https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/
