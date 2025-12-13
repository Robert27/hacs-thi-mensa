# THI Mensa

Home Assistant custom integration that exposes each of today's meals at the THI mensa as individual sensor entities. Select your campus location and preferred price group during onboarding, and the integration will always show the current day's dishes with pricing.

## Installation

1. Add this repository to HACS as a custom repository.
2. Install the **THI Mensa** integration.
3. Complete the configuration flow by choosing your location and price group.

## Configuration

- **Location**: Mensa location provided by the Neuland API (IngolstadtMensa, NeuburgMensa, Reimanns, or Canisius).
- **Price group**: Whether prices should reflect students, employees, or guests.

The integration creates one sensor per meal found for the current day. Each sensor's state is the meal price for the selected group, with attributes for names, category, allergens, flags, and all price tiers.
