# CoolWalk plan

## Why this can win (mapped to the judging criteria, 25% each)

| Criterion | What we show |
|---|---|
| Technical innovation and originality | Satellite heat and vegetation turned into a routing cost, a bounded-detour heat-aware A*, and an Amazon Location route scored against the same heat data. |
| Craft and execution | Public CloudFront site, real data, tested router, graceful fallbacks, phone layout, one-command deploy. |
| Usefulness and impact | A daily-life problem (walking in Delhi's summer heat). Reusable pipeline: change the bounding box and dates for another city. |
| Creativity and storytelling | The heat strip under each route, and a 3-minute video that starts with a real walk and a real number. |

Entries on common themes lose when they are generic. CoolWalk wins on specificity: real dated scenes, three real walks between places people know, and honest limits.

## Timeline (IST). Window opens Fri Oct 30 about 12:30 pm, closes Tue Nov 3 about 2:30 am. Confirm on the Builder Center page.

| When | Goal | Done when |
|---|---|---|
| Thu Oct 29 (today) | Step 0 checks only. AWS account, budget alert, Builder profile. | Pedestrian route test, scene found, segment count known. |
| Fri Oct 30 | Deploy stack, run pipeline steps 1 to 4. | Heat grid on the map, Iceberg table exists, sanity check of leafy vs dense streets written up. |
| Sat Oct 31 | Router live, UI works end to end, pick demo walks. | Three preset walks return both routes with believable numbers. |
| Sun Nov 1 | Polish, phone layout, errors, screenshots. Feature freeze Sunday night. | Checklist below passes on the CloudFront URL. |
| Mon Nov 2 | Record video, publish article, push repo, submit by about 8 pm IST. | Submission confirmed. Leave the night as buffer. |

## Cut order if time runs short
1. Findings panel. 2. Heat layer polish. 3. Marker dragging. 4. Amazon Location baseline (fall back to graph shortest path).
Never cut: public URL, written article, video.

## Risks and fixes

| Risk | Likelihood | Fix |
|---|---|---|
| Pedestrian routing weak or missing in India | Medium | Frontend already falls back to our own shortest path and labels it honestly. |
| Landsat bucket is requester-pays | Certain | Pipeline uses a requester-pays session. Costs are small. Watch the budget alert. |
| Few clear scenes | Medium | Widen dates or pick the best remaining scene. State the date in the app. |
| Thermal data too coarse for street contrast | Medium | Heat index blends 10 m vegetation. Check the sanity step. |
| Lambda cold start with a big graph | Medium | Shrink bbox, or provisioned concurrency for the demo. |
| API key referer or CORS errors | High (first deploy) | Add the CloudFront URL to the key's referers. Test on the live URL early. |
| Iceberg CTAS fails when the target location is not empty | Low | Step 3 clears the prefix before each run. |
| Sentinel-2 tile edge or cloud gaps | Medium | Pipeline mosaics same-day tiles and fills gaps with the median, and prints the missing share. |

## Submission checklist (pass/fail first)

- [ ] Live URL opens without login, on a laptop and a phone.
- [ ] Map shows data (heat layer and both routes).
- [ ] Runs on AWS (CloudFront, S3, Lambda, Location Service, Athena/Iceberg).
- [ ] Builder Center article published: dataset, how it got on the map, AWS services, live link.
- [ ] Video under 3 minutes, public on YouTube or Vimeo, no copyrighted music or third-party logos, link put in the "demo" field.
- [ ] Repo public with MIT license and no secrets.
- [ ] Data credits shown.
- [ ] Every number in the article and video comes from `docs/FINDINGS.md`.
- [ ] Eligibility: 18 or older, Builder Center profile, one entry only.
