# Ingolstadt Mensa

Ingolstadt Mensa surfaces the daily meal plan for the Technische Hochschule Ingolstadt canteens right inside Home Assistant. It uses the open-source GraphQL API provided by Neuland Ingolstadt, letting you pick from multiple cafeterias and price groups while keeping every dish available as its own sensor entity.

## What you get

- One sensor per meal for the current day, including price and rich attributes (name, category, allergens, flags, and all price tiers).
- Coverage for all canteens exposed by the Neuland API: Ingolstadt Mensa, Neuburg Mensa, Reimanns, and Canisius.
- Quick onboarding through a guided config flow and adjustable options later on.

## Installation

1. Add this repository as a **custom repository** in HACS (category: Integration).
2. Install the **Ingolstadt Mensa** integration from HACS.
3. Restart Home Assistant if prompted.
4. Complete the configuration flow by selecting your cafeteria location and price group.

## Configuration

- **Location**: Choose the mensa location supplied by the Neuland API (IngolstadtMensa, NeuburgMensa, Reimanns, or Canisius).
- **Price group**: Decide whether prices should reflect students, employees, or guests.

You can revisit the integration options at any time to switch locations or change the price group. Sensors automatically refresh throughout the day to stay in sync with the published menu.
