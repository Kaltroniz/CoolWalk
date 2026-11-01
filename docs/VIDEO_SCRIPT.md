# Video script (target 2:40, hard limit 3:00)

Record the screen with a voice-over. No copyrighted music, or royalty-free music you have rights to. No third-party logos beyond the app itself. The live demo URL must be visible on screen.

| Time | On screen | Voice-over |
|---|---|---|
| **0:00 to 0:25** | The live site, heat layer visible. Slow zoom on central Delhi. | "In a Delhi summer, surface temperatures across the city frequently exceed 45 °C. Standard navigation apps only optimize for distance, routing people down unshaded, baking asphalt corridors. CoolWalk maps microclimates to give pedestrians the cooler choice. On heat-exposed walks (where the standard route spends more than half the way in high-heat zones, about 1 in 7 random walks here), CoolWalk avoids 9 minutes of intense heat for just one extra minute of walking time." |
| **0:25 to 0:55** | Preset "Jama Masjid to Raj Ghat". Hover scrub along heat strip. Point out independent check. | "Take Jama Masjid to Raj Ghat. The standard walk from Amazon Location Service puts pedestrians in high-heat zones for 59% of the walk, averaging 43.9 °C surface temperature. CoolWalk trades 5 minutes for a greener route that cuts high-heat exposure down to just 9.5% and drops surface temperature by 1.9 °C. Scrubbing across the heat strip tracks our exact position on the map. Underneath, an independent check against held-out satellite scenes corroborates that the cooler route holds across multiple dates." |
| **0:55 to 1:20** | Click 'Where can I cool down?'. Refuge options appear (park, water point, metro). Click 'Show route'. | "Need immediate relief? The 'Where can I cool down' refuge finder routes pedestrians from any point to their nearest park, drinking water fountain, or metro station along the coolest path. In seconds, it compares the fastest rush against a heat-minimized walk to safe shelter." |
| **1:20 to 1:45** | Toggle 'Show places in the heat', open 'Where shade matters most' civic planner view. | "By querying Apache Iceberg tables in Amazon Athena, we found that a third of hospitals and clinics and 20% of schools sit in high-heat zones. The Civic Planner View ranks 20 priority corridors where pedestrians have no choice but to endure extreme heat, complete with an instant CSV export for municipal shade planning." |
| **1:45 to 2:15** | Architecture diagram. | "Under the hood, open Landsat 8/9 thermal infrared and Sentinel-2 vegetation bands score about 36,000 directed street segments (about 1,190 km of street). The data is stored in Apache Iceberg tables on Amazon S3 and queried with Athena. An AWS Lambda router executes heat-weighted A* routing in 50 milliseconds. Amazon Location Service powers the basemap, place search, and standard pedestrian routing, while AWS Amplify serves the secure HTTPS frontend." |
| **2:15 to 2:35** | App footer, then full screen showing live URL and GitHub link. | "CoolWalk is open data, MIT licensed, and runs live at the URL on your screen. You can download the dataset directly or adapt the pipeline to your own city. Try it live today." |

### Checklist before upload
- [ ] Duration is under 2 minutes 45 seconds (hard limit 3:00).
- [ ] No copyrighted music or third-party logos.
- [ ] YouTube or Vimeo set to Public or Unlisted.
- [ ] Live URL (`https://main.d3miw0zrayytbj.amplifyapp.com`) clearly displayed.
- [ ] Video URL inserted into AWS Builder Center submission "demo" field.
