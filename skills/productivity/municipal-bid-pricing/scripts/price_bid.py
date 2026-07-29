#!/usr/bin/env python3
"""
Pricing engine for municipal tree-care bids.

Reads competitor bids + TRIM IT signals, applies discount strategy with strict
cost-floor enforcement, outputs priced JSON ready for the spreadsheet generator.

Usage:
  /opt/data/.venv/bin/python price_bid.py \
    --competitor-bids /path/to/competitor_bids.json \
    --signals /path/to/signals.json \
    --output /path/to/priced.json \
    [--escalation-rate 0.035] [--years 5]

Strategy:
  1. Escalate competitor's prior bid → current estimate (default 3.5%/yr × 5yr)
  2. Apply volume-weighted discounts (see VOLUME_BAND_DISCOUNTS):
     - 10% on high-volume bands (13-18, 19-24, 24-30) — drive 80%+ of revenue
     - 8% standard on mid-volume (7-12) and most other categories
     - 5% on low-volume bands (0-6, 31+) — protect margin
     - 10% on removals, 8% on stumps
     - Fan Palm trunk clean: 40% under (WCA overcharges — it's fast work)
     - Date Palm trunk clean: 8% under (premium work)
  3. Enforce cost floors — NEVER below $130/hr or Price Buddy per-tree floors
  4. If target < floor: price AT floor, flag as floor-enforced (expected on some items)
"""
import argparse, json

# ---- Discount strategy by category ----
# Variable discounts per Skipper-confirmed rules:
#   - Volume bands (13-18, 19-24, 24-30) get aggressive 10% (drive 80%+ of revenue)
#   - Low-volume bands (0-6, 31+) get 5% (protect margin, won't hurt bid score)
#   - Mid-volume 7-12 gets standard 8%
#   - Palm trunk: Date = premium work (8% under), Fan = easier (40% under, WCA overcharges)
DISCOUNTS = {
    'full_prune': 0.08,
    'raise_clear': 0.05,
    'palm_date': 0.08, 'palm_fan': 0.08, 'palm_other': 0.08,
    'trunk_date': 0.08, 'trunk_fan': 0.40,
    'single_tree': 0.08,
    'removal': 0.10,
    'stump': 0.08,
    'plant_15g': 0.08, 'plant_24': 0.08, 'plant_36': 0.08, 'plant_48': 0.08,
    'plant_palm_ft': 0.08, 'plant_palm_ea': 0.08,
    'watering': 0.08,
    'arborist': 0.08, 'pca': 0.08, 'qa': 0.08,
}

# ---- Volume-band overrides (applied for full_prune + raise_clear) ----
# Bands driving >15% of revenue → aggressive 10%; low-volume bands → 5%
VOLUME_BAND_DISCOUNTS = {
    'full_prune': {'0-6': 0.05, '7-12': 0.08, '13-18': 0.10, '19-24': 0.10, '24-30': 0.10, '31+': 0.05},
    'raise_clear': {'0-6': 0.05, '7-12': 0.05, '13-18': 0.08, '19-24': 0.08, '24-30': 0.08, '31+': 0.05},
}

# ---- Fixed cost floors ----
TPH_FLOOR = 130
DAY_RATE_FLOOR = 3120       # 3p × 8hr × $130
EMERG_DAY_FLOOR = 390       # 3p × $130
EMERG_NIGHT_FLOOR = 488     # 3p × $130 × 1.25

# ---- Ratios ----
RAISE_RATIO = 0.35          # raise/clearance = 35% of full prune
REMOVAL_RATIO = 2.5         # removal = 2.5× prune
STUMP_RATIO = 0.35          # stump = 35% of removal


def categorize(desc):
    """Map a line-item description to (category, dbh_band)."""
    d = desc.upper()
    cat = 'standard'
    if 'FULL PRUNE' in d and 'DSH' in d: cat = 'full_prune'
    elif 'RAISE' in d or 'CLEARANCE' in d: cat = 'raise_clear'
    elif 'DATE PALM PRUNE' in d: cat = 'palm_date'
    elif 'FAN PALM PRUNE' in d: cat = 'palm_fan'
    elif 'PALM PRUNE' in d: cat = 'palm_other'
    elif 'TRUNK CLEAN' in d and 'DATE' in d: cat = 'trunk_date'
    elif 'TRUNK CLEAN' in d and 'FAN' in d: cat = 'trunk_fan'
    elif 'SERVICE REQUEST' in d: cat = 'single_tree'
    elif 'REMOVAL' in d: cat = 'removal'
    elif 'STUMP' in d: cat = 'stump'
    elif 'GROUND PERSON' in d: cat = 'labor_ground'
    elif 'EQUIPMENT OPERATOR' in d: cat = 'labor_operator'
    elif 'TREE TRIMMER' in d: cat = 'labor_trimmer'
    elif 'DAY RATE' in d: cat = 'day_rate'
    elif 'PLANT' in d and '15 GALLON' in d: cat = 'plant_15g'
    elif 'PLANT' in d and '24' in d: cat = 'plant_24'
    elif 'PLANT' in d and '36' in d: cat = 'plant_36'
    elif 'PLANT' in d and '48' in d: cat = 'plant_48'
    elif 'PLANT' in d and 'PER FT' in d: cat = 'plant_palm_ft'
    elif 'PLANT' in d and '10-30' in d: cat = 'plant_palm_ea'
    elif 'WATERING' in d: cat = 'watering'
    elif 'EMERGENCY' in d and 'NORMAL' in d: cat = 'emerg_day'
    elif 'EMERGENCY' in d: cat = 'emerg_night'
    elif 'ARBORIST' in d: cat = 'arborist'
    elif 'PEST CONTROL' in d: cat = 'pca'
    elif 'QUALIFIED' in d or 'APPLICATOR' in d: cat = 'qa'

    band = None
    if '0-6' in d or '0-4' in d: band = '0-6'
    elif '7-12' in d: band = '7-12'
    elif '13-18' in d: band = '13-18'
    elif '19-24' in d: band = '19-24'
    elif '24-30' in d or '25-30' in d: band = '24-30'
    elif '31' in d: band = '31+'
    return cat, band


def price_item(desc, unit, comp_price, price_buddy, esc_factor):
    """Price a single line item with floor enforcement."""
    cat, band = categorize(desc)
    wca_2021 = comp_price
    wca_2026_est = round(wca_2021 * esc_factor)

    # Use volume-band discount where defined, else fall back to category default
    if cat in VOLUME_BAND_DISCOUNTS and band in VOLUME_BAND_DISCOUNTS[cat]:
        discount = VOLUME_BAND_DISCOUNTS[cat][band]
    else:
        discount = DISCOUNTS.get(cat, 0.08)
    target = wca_2026_est * (1 - discount)

    floor = 0
    floor_label = ""
    rationale = ""

    # Labor rates: $130/hr floor
    if cat in ('labor_ground', 'labor_operator', 'labor_trimmer', 'arborist', 'pca', 'qa'):
        floor = TPH_FLOOR
        floor_label = "$130/hr TPH floor"
    elif cat == 'day_rate':
        floor = DAY_RATE_FLOOR
        floor_label = "$3,120/day floor"
    elif cat == 'emerg_day':
        floor = EMERG_DAY_FLOOR
        floor_label = "$390/hr emergency floor"
    elif cat == 'emerg_night':
        floor = EMERG_NIGHT_FLOOR
        floor_label = "$488/hr night floor"
    elif band and cat == 'full_prune':
        floor = price_buddy.get(band, {}).get('blended_floor', 0)
        floor_label = f"Price Buddy floor ({band})"
    elif band and cat == 'raise_clear':
        floor = price_buddy.get(band, {}).get('blended_floor', 0) * RAISE_RATIO
        floor_label = f"Raise floor ({band}, {RAISE_RATIO:.0%} of prune)"
    elif band and cat == 'removal':
        floor = price_buddy.get(band, {}).get('blended_floor', 0) * REMOVAL_RATIO
        floor_label = f"Removal floor ({band}, {REMOVAL_RATIO}× prune)"
    elif band and cat == 'stump':
        prune_floor = price_buddy.get(band, {}).get('blended_floor', 0)
        floor = prune_floor * REMOVAL_RATIO * STUMP_RATIO
        floor_label = f"Stump floor ({band})"

    below_floor = target < floor if floor > 0 else False
    if below_floor:
        gsts_price = round(floor)
        rationale = f"FLOOR-ENFORCED: target ${target:.0f} below {floor_label} ${floor:.0f}."
    else:
        gsts_price = round(target)
        rationale = f"Undercut ${wca_2026_est} by {discount*100:.0f}%"

    savings = wca_2026_est - gsts_price
    savings_pct = (savings / wca_2026_est * 100) if wca_2026_est else 0

    return {
        'description': desc, 'category': cat, 'band': band, 'unit': unit,
        'wca_2021': wca_2021, 'wca_2026_est': wca_2026_est,
        'gsts_recommended': gsts_price,
        'savings_vs_wca': savings, 'savings_pct': round(savings_pct, 1),
        'floor_applied': floor, 'floor_label': floor_label,
        'rationale': rationale, 'below_floor_flag': below_floor,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Price municipal bid line items')
    parser.add_argument('--competitor-bids', required=True)
    parser.add_argument('--signals', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--escalation-rate', type=float, default=0.035)
    parser.add_argument('--years', type=int, default=5)
    args = parser.parse_args()

    with open(args.competitor_bids) as f:
        comp_raw = json.load(f)
    with open(args.signals) as f:
        signals = json.load(f)

    # Flatten competitor bids (may be {folder: [items]} or [items])
    comp_items = []
    if isinstance(comp_raw, dict):
        for items in comp_raw.values():
            comp_items = items
            break
    else:
        comp_items = comp_raw

    price_buddy = signals.get('price_buddy', {})
    esc_factor = (1 + args.escalation_rate) ** args.years

    priced = []
    for item in comp_items:
        priced.append(price_item(
            item['description'], item['unit'],
            item.get('bidder1_price', item.get('price', 0)),
            price_buddy, esc_factor
        ))

    with open(args.output, 'w') as f:
        json.dump(priced, f, indent=2)

    under = sum(1 for p in priced if p['savings_vs_wca'] > 0)
    floor_ct = sum(1 for p in priced if p['below_floor_flag'])
    print(f"Priced {len(priced)} items: {under} under competitor, {floor_ct} floor-enforced")
    print(f"Saved: {args.output}")
