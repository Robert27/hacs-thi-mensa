"""Tests for constants and utility functions."""

from custom_components.thi_mensa.const import (
    format_location_name,
    format_price_group_name,
)


def test_format_location_name():
    """Test location name formatting."""
    assert format_location_name("IngolstadtMensa") == "Ingolstadt Mensa"
    assert format_location_name("NeuburgMensa") == "Neuburg Mensa"
    assert format_location_name("Reimanns") == "Reimanns"
    assert format_location_name("Canisius") == "Canisius"
    assert format_location_name("") == "Ingolstadt Mensa"


def test_format_price_group_name():
    """Test price group name formatting."""
    assert format_price_group_name("student") == "Student"
    assert format_price_group_name("employee") == "Employee"
    assert format_price_group_name("guest") == "Guest"
    assert format_price_group_name("") == ""
