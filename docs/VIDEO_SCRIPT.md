# Video script (target 2:45, hard limit 3:00)

Record the screen with a voice-over. No music, or royalty-free music you have rights to. No third-party logos beyond the app itself. Replace `{{...}}` with numbers from `docs/FINDINGS.md`. Do not say anything you cannot show.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00 to 0:20 | The live site, heat layer visible. Slow zoom on Old Delhi. | "In May, central Delhi's streets get very hot. A normal map gives you the shortest walk. It does not tell you which streets hold the heat." |
| 0:20 to 0:35 | Title: CoolWalk. Pick walk 1 from the examples. | "CoolWalk is a walking map that trades a few minutes for much less time in the heat." |
| 0:35 to 1:15 | Routes appear. Point at the heat strip under each. | "Here is {{start}} to {{end}}. The standard walk takes {{N}} minutes and spends {{X}} percent of the way in high-heat zones. CoolWalk takes {{M}} minutes and cuts that to {{Y}} percent. The strip shows each stretch of the walk." |
| 1:15 to 1:40 | Drag the slider from Fastest to Coolest. | "You choose the tradeoff. At the fast end it is the shortest walk. As I move toward cooler, the route moves onto leafier streets." |
| 1:40 to 2:00 | Search a place, click the map, drag a marker. | "You can search any place, click the map, or drag a pin." |
| 2:00 to 2:25 | Architecture diagram from the README. | "Landsat surface temperature and Sentinel-2 vegetation score every street. The scores live in an Apache Iceberg table on S3, queried with Athena. A Lambda routes with heat as a cost, and Amazon Location Service provides the map, place search and the standard pedestrian route." |
| 2:25 to 2:40 | Findings panel. | "Across {{km}} kilometres of streets, {{share}} percent are in high-heat zones. {{Street}} runs hottest, {{Street}} runs coolest." |
| 2:40 to 2:50 | Footer, then the live URL and repo link. | "The heat map comes from one dated satellite scene, so it shows where streets hold heat, not the air temperature. Change the bounding box and you can map another city. Try it at the link." |

Checklist before upload: under 3 minutes, public visibility, link in the "demo" field, the live URL visible on screen at the end.
