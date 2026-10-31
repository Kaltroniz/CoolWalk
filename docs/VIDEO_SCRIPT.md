# Video script (target 2:40, hard limit 3:00)

Record the screen with a voice-over. No copyrighted music, or royalty-free music you have rights to. No third-party logos beyond the app itself. The live demo URL must be visible on screen.

| Time | On screen | Voice-over |
|---|---|---|
| **0:00 to 0:25** | The live site, heat layer visible. Slow zoom on central Delhi. | "In a Delhi summer, surface temperatures across the city frequently exceed 45 °C. Standard navigation apps only optimize for distance. They don't know which streets bake in direct sun and which corridors have tree canopy. CoolWalk gives pedestrians the cooler choice." |
| **0:25 to 1:10** | Click preset: "Jama Masjid to Raj Ghat". Both routes appear. Scrub mouse across heat strip bars. | "Take Jama Masjid to Raj Ghat. The standard pedestrian route from Amazon Location Service takes 30.2 minutes, with 59% of the walk through high-heat, low-canopy streets, averaging 43.9 °C surface temperature. CoolWalk trades just 5 minutes for a leafy route that cuts high-heat exposure down to 9.5% and drops average surface temperature to 42.0 °C — a full 1.9 °C reduction. Scrubbing across the heat strip projects our location block by block on the map." |
| **1:10 to 1:35** | Click "Delhi Gate to Lahori Gate". Drag tradeoff slider between Fastest and Coolest. | "On Delhi Gate to Lahori Gate, standard routing puts pedestrians in high-heat zones for 90% of the walk. CoolWalk routes through lower-heat streets, cutting that down to 15%. With the tradeoff slider, you choose: fastest route at the left, or coolest leafy corridors at the right." |
| **1:35 to 1:55** | Search a landmark with autocomplete, then expand 'What the data shows' and click a street name. | "You can search any landmark with Amazon Location autocomplete, drop custom pins anywhere on the map, or share walks directly via URL. Under 'What the data shows', clicking any hot or cool street flies the camera straight to that corridor with its measured surface temperature." |
| **1:55 to 2:20** | Architecture diagram. | "Under the hood, open Landsat 8 thermal infrared and Sentinel-2 vegetation bands score 35,748 street segments. The scored dataset is stored in an Apache Iceberg table on Amazon S3 and queried with Amazon Athena. AWS Lambda runs heat-weighted A* routing in about 50 milliseconds of routing compute, returning both the heat index and physical surface temperature. Amazon Location Service powers the vector basemap, place search, and standard pedestrian routing." |
| **2:20 to 2:40** | App footer, then full screen showing live URL and GitHub link. | "Heat data comes from June 2026 satellite observations combining surface temperature and vegetation. The entire stack is MIT licensed, deployed securely with HTTPS on AWS Amplify Hosting, and can be adapted to any city by updating a bounding box. Try it live at the URL on screen." |

### Checklist before upload
- [ ] Duration is under 2 minutes 45 seconds (hard limit 3:00).
- [ ] No copyrighted music or third-party logos.
- [ ] YouTube or Vimeo set to Public or Unlisted.
- [ ] Live URL (`https://main.d3miw0zrayytbj.amplifyapp.com`) clearly displayed.
- [ ] Video URL inserted into AWS Builder Center submission "demo" field.
