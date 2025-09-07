import pytest
from typing import TYPE_CHECKING, Optional, List

from ..house import House

if TYPE_CHECKING:
    from message import Message, DialogueMessage, SoundMessage, ServerMessage
    from coord import Coord
    from Player import HumanPlayer


class TestHouse:
    """
    House enum test module.
    This module contains comprehensive unit tests for the House enumeration in Dumbledore's Office.
    Tests verify enum properties, behavior, and operations.
    """

    @pytest.fixture
    def all_houses(self) -> List[House]:
        """Fixture providing a list of all House enum values."""
        return [House.GRYFFINDOR, House.HUFFLEPUFF, House.RAVENCLAW, House.SLYTHERIN]

    @pytest.fixture
    def house_names(self) -> List[str]:
        """Fixture providing a list of all House enum names."""
        return ["GRYFFINDOR", "HUFFLEPUFF", "RAVENCLAW", "SLYTHERIN"]

    @pytest.fixture
    def house_values(self) -> List[int]:
        """Fixture providing a list of all House enum values (integers)."""
        return [1, 2, 3, 4]

    def test_house_enum_count(self, all_houses):
        """Test that the House enum has exactly 4 values."""
        assert len(House) == 4, "House enum should have exactly 4 values"
        
        assert len(all_houses) == 4, "Should be exactly 4 houses"

    def test_house_enum_members(self, all_houses):
        """Test that the House enum has the expected members."""
        for house in all_houses:
            assert house in House, f"{house.name} should be a House enum value"

    def test_house_enum_uniqueness(self, all_houses):
        """Test that each House enum value is unique."""
        # Check all pairs of houses for uniqueness
        for i, house1 in enumerate(all_houses):
            for house2 in all_houses[i+1:]:
                assert house1 != house2, f"{house1.name} and {house2.name} should have different values"

    def test_house_enum_names(self, all_houses, house_names):
        """Test that the House enum names match the expected values."""
        for i, house in enumerate(all_houses):
            assert house.name == house_names[i], f"{house} enum should have name '{house_names[i]}'"

    def test_house_enum_values_auto_assigned(self, all_houses, house_values):
        """Test that the House enum values are automatically assigned and sequential."""
        for i, house in enumerate(all_houses):
            assert house.value == house_values[i], f"{house.name} should have value {house_values[i]}"

    def test_house_enum_iterable(self, all_houses):
        """Test that the House enum is iterable."""
        houses_list = list(House)
        assert len(houses_list) == 4, "House enum should have 4 values when iterated"
        
        for house in all_houses:
            assert house in houses_list, f"{house.name} should be in iterated houses"

    def test_house_enum_comparison(self, all_houses):
        """Test that House enum values can be compared and used in conditions."""
        for house in all_houses:
            # Test identity comparison
            assert house is house, f"{house.name} should be identical to itself"
            
            # Test equality comparison
            assert house == house, f"{house.name} should be equal to itself"
            
            # Test non-identity with other houses
            other_houses = [h for h in all_houses if h != house]
            for other in other_houses:
                assert house is not other, f"{house.name} should not be identical to {other.name}"
                assert house != other, f"{house.name} should not be equal to {other.name}"

    def test_house_enum_conversion_to_string(self, all_houses):
        """Test that House enum values can be converted to strings."""
        for house in all_houses:
            expected_str = f"House.{house.name}"
            assert str(house) == expected_str, f"String representation should be '{expected_str}'"

    def test_house_enum_from_string(self, all_houses, house_names):
        """Test that House enum values can be retrieved from strings."""
        for i, name in enumerate(house_names):
            assert House[name] == all_houses[i], f"House['{name}'] should return {all_houses[i].name} enum value"

    def test_house_enum_invalid_name(self):
        """Test that attempting to access a non-existent House enum name raises an error."""
        with pytest.raises(KeyError, match="'INVALID_HOUSE'"):
            House["INVALID_HOUSE"]

    def test_house_enum_by_value(self, all_houses, house_values):
        """Test that House enum members can be looked up by value."""
        for i, value in enumerate(house_values):
            assert House(value) == all_houses[i], f"House({value}) should return {all_houses[i].name} enum value"

    def test_house_enum_invalid_value(self):
        """Test that attempting to look up a non-existent House enum value raises an error."""
        with pytest.raises(ValueError):
            House(999)  # A value that doesn't exist in the enum

    def test_house_enum_hashable(self, all_houses):
        """Test that House enum values are hashable and can be used in dictionaries and sets."""
        # Create a dictionary with houses as keys
        house_dict = {house: house.name.lower() for house in all_houses}
        
        # Check that we can retrieve values by house key
        for house in all_houses:
            assert house_dict[house] == house.name.lower(), f"House enum values should work as dictionary keys"
        
        # Create a set with houses
        house_set = set(all_houses)
        assert len(house_set) == 4, "Should be able to create a set of House enum values"
