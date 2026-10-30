# Video script (target 2:45, hard limit 3:00)

Record the screen with a voice-over. No copyrighted music, or royalty-free music you have rights to. No third-party logos beyond the app itself. The live demo URL must be visible on screen.

| Time | On screen | Voice-over |
|---|---|---|
| **0:00 to 0:20** | The live site, heat layer visible. Slow zoom on Old Delhi. | "In Delhi's summer, streets can reach surface temperatures well over 45 °C. Standard map apps always give you the shortest path. They don't tell you which roads bake in direct sun and which ones have tree shade." |
| **0:20 to 0:35** | CoolWalk interface. Click preset 1: "Jama Masjid to Delhi Gate". | "CoolWalk is a public web map for central Delhi that trades a few minutes of walking for far less time in dangerous heat." |
| **0:35 to 1:15** | Both routes appear. Point at the heat strip and surface temperature under each. | "Here is Jama Masjid to Delhi Gate. The standard walk from Amazon Location Service takes 20.5 minutes and spends 80% of the journey in high-heat zones. CoolWalk takes 23.8 minutes — just 3.3 minutes more — and slashes high-heat exposure down to 23.5%, avoiding 56.5 percentage points of high heat. The heat strip under each route compares thermal exposure block by block." |
| **1:15 to 1:40** | Click preset 2: "Jama Masjid to Raj Ghat", then preset 3: "Delhi Gate to Lahori Gate". Drag slider from Fastest to Coolest. | "On walks like Jama Masjid to Raj Ghat, CoolWalk cuts high heat from 59% to under 10% and drops mean surface temperature from 43.9 to 42.0 °C. Or Delhi Gate to Lahori Gate, where standard pedestrian routing puts you in high heat for 90% of the walk, and CoolWalk cuts that to 15%. With the tradeoff slider, you can tune how aggressively to avoid heat: at Fastest, you get the shortest route; sliding toward Coolest, the router shifts to leafy, shaded corridors." |
| **1:40 to 2:00** | Type "Chandni Chowk" into place search, click suggestions, drag pin B. | "You can search any landmark with Amazon Location autocomplete, click any point on the map, or drag pins A and B to recalculate instantly. Every walk also has a direct shareable link." |
| **2:00 to 2:25** | Architecture diagram. | "Under the hood, open Landsat 8 surface temperature and Sentinel-2 vegetation bands score 35,748 street segments. The scored dataset is stored in an Apache Iceberg table on Amazon S3 and queried with Amazon Athena. An AWS Lambda function computes heat-weighted A* routes in about 50 milliseconds of routing compute, returning both heat exposure and physical surface temperature. Amazon Location Service provides the vector map, place search, and standard pedestrian routing." |
| **2:25 to 2:40** | Open 'What the data shows' details panel. | "Across 2,377 km of walkable streets, 19.8% sit in high-heat zones. Narrow bazaar corridors like Chipwara Khurd and Kinari Bazar reach 46 °C, while shaded avenues like Akbar Road run about 4 to 5 °C cooler at the surface." |
| **2:40 to 2:50** | App footer, then full screen showing live URL and repo link. | "Heat data comes from June 2026 satellite observations as an objective proxy for surface heat retention. The entire stack is open-source under MIT, deployed securely with HTTPS on AWS Amplify Hosting, and can be adapted to any city by changing a bounding box. Try it live at the URL on screen." |

### Checklist before upload
- [ ] Duration is under 2 minutes 50 seconds (hard limit 3:00).
- [ ] No copyrighted music or third-party logos.
- [ ] YouTube or Vimeo set to Public or Unlisted.
- [ ] Live URL (`https://main.d3miw0zrayytbj.amplifyapp.com`) clearly displayed.
- [ ] Video URL inserted into AWS Builder Center submission "demo" field.
