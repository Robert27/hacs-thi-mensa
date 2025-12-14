# Ingolstadt Mensa

Ingolstadt Mensa surfaces the meal plan for the Technische Hochschule Ingolstadt canteens right inside Home Assistant. It uses the open-source GraphQL API provided by Neuland Ingolstadt, letting you pick from multiple cafeterias and price groups while keeping every dish available as its own sensor entity.

## What you get

- **Two days of meals**: Today's and tomorrow's meals, organized in separate device groups
- **Up to 5 sensors per day**: Each day (Today/Tomorrow) has up to 5 meal sensors with stable entity IDs
- **Rich meal information**: Each sensor includes price, name, category, allergens, flags, and all price tiers
- **Coverage for all canteens**: Ingolstadt Mensa, Neuburg Mensa, Reimanns, and Canisius
- **Formatted display names**: Location and price group names are properly formatted in the setup flow
- **Quick onboarding**: Guided config flow with formatted dropdown options and adjustable settings

## Installation

1. Add this repository as a **custom repository** in HACS (category: Integration).
2. Install the **Ingolstadt Mensa** integration from HACS using the custom repository: `https://github.com/Robert27/hacs-thi-mensa`
3. Restart Home Assistant if prompted.
4. Complete the configuration flow by selecting your cafeteria location and price group.

## Configuration

- **Location**: Choose the mensa location supplied by the Neuland API (IngolstadtMensa, NeuburgMensa, Reimanns, or Canisius).
- **Price group**: Decide whether prices should reflect students, employees, or guests.

You can revisit the integration options at any time to switch locations or change the price group. Sensors automatically refresh throughout the day to stay in sync with the published menu.

## Entity Organization

Each restaurant location creates two device groups:
- **Restaurant Name - Today**: Up to 5 sensors for today's meals
- **Restaurant Name - Tomorrow**: Up to 5 sensors for tomorrow's meals

Entity IDs are stable (e.g., `sensor.ingolstadt_mensa_today_1`, `sensor.ingolstadt_mensa_tomorrow_2`) and won't change when meals are updated, ensuring your automations and dashboards remain consistent.
