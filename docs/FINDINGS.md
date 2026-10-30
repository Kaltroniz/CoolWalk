# Findings (filled in from real runs; every number in the article and video comes from here)

## Run details
- Landsat scene id / date / cloud cover: `LC08_L2SP_147040_20260609_02_T1` / `2026-06-09` / `0.0%`
- Sentinel-2 date / tiles: `2026-06-07` / 1 tile (`S2B_43RGM_20260607_0_L2A`, cloud cover 0.03%)
- Street segments / km of network: 35,748 segments / 2,376.9 km (12,687 intersections)
- Missing temperature share, missing NDVI share: 0.0% LST missing, 0.0% NDVI missing (183,616 points sampled)
- Temperature range (5th to 95th percentile, C): 40.3 °C to 46.3 °C

## Leafy vs dense streets
Sample of 10 street segments across central Delhi:

| Street Name | Classification | Surface Temp (LST) | Vegetation (NDVI) | Heat Index (0..1) | Context |
|---|---|---|---|---|---|
| **Akbar Road** | secondary | 40.6–41.9 °C | 0.885–0.961 | 0.042–0.159 | Dense canopy avenue in Lutyens' Delhi |
| **Teen Murti Marg** | secondary | 41.0–42.5 °C | 0.927–0.954 | 0.068–0.217 | Forested boulevard |
| **Janpath Lane** | tertiary | 42.2 °C | 0.935 | 0.192 | Tree-lined lane near Janpath |
| **Janpath** | secondary | 42.5–43.5 °C | 0.365–0.755 | 0.252–0.475 | Wide mixed-use boulevard |
| **Lal Kuan Bazar** | tertiary | 45.4–45.6 °C | 0.229–0.285 | 0.719–0.776 | Dense market street in Old Delhi |
| **Khari Baoli Road** | tertiary | 46.4–46.7 °C | 0.279–0.365 | 0.741–0.814 | Historic wholesale spice market |
| **Chandni Chowk** | tertiary | 46.2–46.5 °C | 0.235–0.349 | 0.754–0.843 | Core commercial thoroughfare, high thermal mass |
| **Nai Sarak** | unclassified | 46.4 °C | 0.188–0.209 | 0.860–0.868 | Narrow book market corridor |
| **Chawri Bazar** | tertiary | 46.1–46.3 °C | 0.169–0.172 | 0.869–0.871 | Narrow, high-density market street |
| **Kinari Bazar** | unclassified | 46.2 °C | 0.115 | 0.914 | High-density alley in Shahjahanabad |

The physical contrast is stark: tree-covered avenues register 40.6–41.9 °C with dense canopy (NDVI > 0.88) and low heat scores (0.04–0.16), running about 4 to 5 °C cooler than unshaded asphalt corridors in Shahjahanabad that register 46.1–46.7 °C with minimal greenery (NDVI < 0.25) and extreme heat scores (0.75–0.93).

## Network
- Share of street length in high-heat zones (heat index >= 0.66): 19.8% (471.4 km of 2,376.9 km)
- Hottest streets: Chipwara Khurd (heat 0.934, LST 46.1 °C), Gali Ahar (0.918, 46.0 °C), Kinari Bazar (0.914, 46.2 °C), Maliwara (0.895, 46.3 °C), Chipwara Kalan (0.892, 46.4 °C), Dariba Kalan (0.886, 46.2 °C)
- Coolest streets: Shaded parkways and estate roads in New Delhi / Lutyens' zone (Akbar Road, Lodhi Estate, Teen Murti Marg, heat index 0.00 to 0.22)

## Demo walks
| Walk | Standard min | CoolWalk min | Standard hot share | CoolWalk hot share | Avoided exposure | Avg Surface Temp (Std vs Cool) | Source of standard route |
|---|---|---|---|---|---|---|---|
| **Jama Masjid to Delhi Gate** | 20.5 min | 23.8 min | 80.0% | 23.5% | 56.5 percentage points (70.6% relative cut) | 44.7 °C vs 44.5 °C | Amazon Location Service |
| **Jama Masjid to Raj Ghat** | 30.2 min | 35.5 min | 59.0% | 9.5% | 49.5 percentage points (83.9% relative cut) | 43.9 °C vs 42.0 °C (-1.9 °C) | Amazon Location Service |
| **Delhi Gate to Lahori Gate** | 40.2 min | 44.8 min | 90.3% | 15.0% | 75.3 percentage points (83.4% relative cut) | 45.3 °C vs 44.9 °C (-0.4 °C) | Amazon Location Service |

## Performance and cost
- Lambda routing compute: ~50 ms (pure A* algorithm over 35k segments)
- Lambda cold start: 3.12 s (decompresses and indexes graph in memory)
- Lambda warm response: 1.03 s (network roundtrip from Delhi client to us-east-1)
- Approximate AWS cost so far: < $0.05 total (Athena queries scanned < 5 MB, S3 requests negligible, Lambda within free tier)
