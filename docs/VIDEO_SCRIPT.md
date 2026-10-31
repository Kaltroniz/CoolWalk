# Video script (target 2:40, hard limit 3:00)

Record the screen with a voice-over. No copyrighted music, or royalty-free music you have rights to. No third-party logos beyond the app itself. The live demo URL must be visible on screen.

| Time | On screen | Voice-over |
|---|---|---|
| **0:00 to 0:25** | The live site, heat layer visible. Slow zoom on central Delhi. | "In a Delhi summer, surface temperatures across the city frequently exceed 45 °C. Standard navigation apps only optimize for distance, routing people down unshaded, baking asphalt corridors. CoolWalk maps microclimates to give pedestrians the cooler choice. Across 500 random walking trips in Delhi, CoolWalk shows that a median detour of just one extra minute avoids a minute of high-heat exposure." |
| **0:25 to 0:55** | Preset "Jama Masjid to Raj Ghat". Hover scrub along heat strip. Point out independent check. | "Take Jama Masjid to Raj Ghat. The standard walk from Amazon Location Service puts pedestrians in high-heat zones for 59% of the walk, averaging 43.9 °C surface temperature. CoolWalk trades 5 minutes for a leafy route that cuts high-heat exposure down to just 9.5% and drops surface temperature by 1.9 °C. Scrubbing across the heat strip tracks our exact position on the map. Underneath, an independent check against held-out satellite scenes confirms the cooler route holds across multiple dates." |
| **0:55 to 1:20** | Click 'Where can I cool down?'. Refuge options appear (park, water point, metro). Click 'Show route'. | "Need immediate relief? The 'Where can I cool down' refuge finder routes pedestrians from any point to their nearest park, drinking water fountain, or air-conditioned metro station along the coolest path. In seconds, it compares the fastest rush against a heat-minimized walk to safe shelter." |
| **1:20 to 1:45** | Toggle 'Show places in the heat', showing hospitals/schools/bus stops. Drag tradeoff slider. | "By querying Apache Iceberg tables in Amazon Athena, we found that nearly a third of central Delhi hospitals and 20% of schools sit on streets in high-heat zones. With the tradeoff slider, users can tune their preferences from fastest direct paths to maximum shade." |
| **1:45 to 2:15** | Architecture diagram. | "Under the hood, open Landsat 8/9 thermal infrared and Sentinel-2 vegetation bands score 35,748 street segments. The data is stored in Apache Iceberg tables on Amazon S3 and queried with Athena. An AWS Lambda router executes heat-weighted A* routing in 50 milliseconds. Amazon Location Service powers the basemap, place search, and standard pedestrian routing, while AWS Amplify serves the secure HTTPS frontend." |
| **2:15 to 2:35** | App footer, then full screen showing live URL and GitHub link. | "CoolWalk is open data, MIT licensed, and runs live at the URL on your screen. You can download the dataset directly or adapt the pipeline to your own city. Try it live today." |

### Checklist before upload
- [ ] Duration is under 2 minutes 45 seconds (hard limit 3:00).
- [ ] No copyrighted music or third-party logos.
- [ ] YouTube or Vimeo set to Public or Unlisted.
- [ ] Live URL (`https://main.d3miw0zrayytbj.amplifyapp.com`) clearly displayed.
- [ ] Video URL inserted into AWS Builder Center submission "demo" field.
