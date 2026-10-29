# Findings (filled in from real runs; every number in the article and video comes from here)

## Run details
- Landsat scene id / date / cloud cover: `LC08_L2SP_147040_20260609_02_T1` / `2026-06-09` / `0.0%`
- Sentinel-2 date / tiles: `2026-06-07` / 1 tile (`S2B_43RGM_20260607_0_L2A`, cloud cover 0.03%)
- Street segments / km of network: 35,748 segments / 2,376.9 km (12,687 intersections)
- Missing temperature share, missing NDVI share: 0.0% LST missing, 0.0% NDVI missing (183,616 points sampled)
- Temperature range (5th to 95th percentile, C): 40.3 °C to 46.3 °C

## Sanity check: leafy vs dense streets
Sample of 10 street segments across central Delhi:

| Street Name | Classification | Surface Temp (LST) | Vegetation (NDVI) | Heat Index (0..1) | Context |
|---|---|---|---|---|---|
| **Janpath Lane** | tertiary | 41.6 °C | 1.000 | 0.132 | Tree-lined lane near Janpath |
| **Akbar Road** | secondary | 41.9 °C | 0.885 | 0.159 | Dense canopy avenue in Lutyens' Delhi |
| **Teen Murti Haifa Chowk** | secondary | 42.0 °C | 0.861 | 0.170 | Landscaped roundabout near Teen Murti Bhavan |
| **Teen Murti Marg** | secondary | 42.5 °C | 0.927 | 0.217 | Forested boulevard |
| **Janpath** | secondary | 43.5 °C | 0.365 | 0.475 | Wide mixed-use boulevard |
| **Lal Kuan Bazar** | tertiary | 45.4 °C | 0.285 | 0.719 | Dense market street in Old Delhi |
| **Khari Baoli Road** | tertiary | 46.7 °C | 0.279 | 0.814 | Historic wholesale spice market |
| **Chandni Chowk** | tertiary | 46.5 °C | 0.235 | 0.843 | Core commercial thoroughfare, high thermal mass |
| **Nai Sarak** | unclassified | 46.4 °C | 0.209 | 0.860 | Narrow book market corridor |
| **Chawri Bazar** | tertiary | 46.1 °C | 0.172 | 0.869 | Narrow, high-density metal market street |

The sanity check confirms the expected physical pattern: tree-covered avenues register 41–42 °C with high NDVI and low heat scores (0.13–0.22), whereas dense bazaar corridors in Shahjahanabad register 46–47 °C with minimal greenery and extreme heat scores (0.72–0.87).

## Network
- Share of street length in high-heat zones (heat index >= 0.66): 19.8% (471.4 km of 2,376.9 km)
- Hottest streets: Chipwara Khurd (0.934), Gali Ahar (0.918), Kinari Bazar (0.914), Maliwara (0.895), Chipwara Kalan (0.892), Dariba Kalan (0.886), Haidar Quli (0.886)
- Coolest streets: Shaded parkways and estate roads in New Delhi / Lutyens' zone (Akbar Road, Lodhi Estate, Teen Murti Marg, heat index 0.00 to 0.22)

## Demo walks
| Walk | Standard min | CoolWalk min | Standard hot share | CoolWalk hot share | Source of standard route | Heat avoided |
|---|---|---|---|---|---|---|
| **Jama Masjid to Delhi Gate** | 20.5 min | 23.8 min | 80.0% | 23.5% | Amazon Location Service | -56.5% exposure (+3.3 min) |
| **Jama Masjid to Raj Ghat** | 30.2 min | 35.5 min | 59.0% | 9.5% | Amazon Location Service | -49.5% exposure (+5.3 min) |
| **Chandni Chowk to Connaught Place** | 47.2 min | 44.7 min | 54.8% | 50.2% | Amazon Location Service | -4.6% exposure (-2.5 min faster) |

*(Note: for Chandni Chowk to Connaught Place, when compared against the pure shortest graph path of 44.3 min with 61.2% hot share, CoolWalk at 44.7 min avoids 11.0% hot exposure for +0.4 min).*

## Performance and cost
- Lambda Cold start: 3.12 s
- Lambda Warm response: 1.03 s (route computation alone is ~50 ms)
- Approximate AWS cost so far: < $0.05 total (Athena queries scanned < 5 MB, S3 requests negligible, Lambda within free tier)
