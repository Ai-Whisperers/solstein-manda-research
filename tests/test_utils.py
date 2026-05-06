"""Tests for core/utils.py — safe JSON, folder names, config."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.utils import safe_json_loads, safe_json_load, folder_from


class TestSafeJsonLoads:
    def test_valid_json(self):
        assert safe_json_loads('{"a": 1}') == {'a': 1}

    def test_valid_list(self):
        assert safe_json_loads('[1, 2, 3]') == [1, 2, 3]

    def test_none_input(self):
        assert safe_json_loads(None) is None

    def test_empty_string(self):
        assert safe_json_loads('') is None

    def test_invalid_json(self):
        assert safe_json_loads('{invalid') is None

    def test_default_on_invalid(self):
        assert safe_json_loads('{invalid', default=[]) == []

    def test_html_instead_of_json(self):
        assert safe_json_loads('<html>404</html>') is None


class TestSafeJsonLoad:
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'key': 'value'}, f)
            path = f.name
        try:
            result = safe_json_load(path)
            assert result == {'key': 'value'}
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        result = safe_json_load('/nonexistent/path.json')
        assert result is None

    def test_default_on_not_found(self):
        result = safe_json_load('/nonexistent/path.json', default={})
        assert result == {}

    def test_corrupt_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{corrupt')
            path = f.name
        try:
            result = safe_json_load(path)
            assert result is None
        finally:
            os.unlink(path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        try:
            result = safe_json_load(path)
            assert result is None
        finally:
            os.unlink(path)


class TestFolderFrom:
    def test_simple_name(self):
        assert folder_from('Booking Experts') == 'booking-experts'

    def test_name_with_special_chars(self):
        assert folder_from("Dentist's Office") == 'dentists-office'

    def test_name_with_parentheses(self):
        assert folder_from('Mews (Systems)') == 'mews-systems'

    def test_name_with_slashes(self):
        assert folder_from('A/B Testing Co') == 'a-b-testing-co'

    def test_name_with_ampersand(self):
        assert folder_from('Fish & Chips') == 'fish-and-chips'

    def test_double_hyphens_collapsed(self):
        assert folder_from('Foo -- Bar') == 'foo-bar'

    def test_already_kebab(self):
        assert folder_from('my-company') == 'my-company'
