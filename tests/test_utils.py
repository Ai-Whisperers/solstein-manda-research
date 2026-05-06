"""Tests for core/utils.py — safe JSON, folder names, config, atomic writes, utilities."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.utils import safe_json_loads, safe_json_load, folder_from, atomic_json_dump, triangulate_employees, check_freshness


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


class TestAtomicJsonDump:
    def test_writes_atomically(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        try:
            atomic_json_dump({'test': True}, path)
            with open(path) as f:
                assert json.load(f) == {'test': True}
            assert not os.path.exists(path + '.tmp')
        finally:
            if os.path.exists(path): os.remove(path)

    def test_overwrites_safely(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        try:
            atomic_json_dump({'v1': 1}, path)
            atomic_json_dump({'v2': 2}, path)
            with open(path) as f:
                assert json.load(f) == {'v2': 2}
        finally:
            if os.path.exists(path): os.remove(path)


class TestTriangulateEmployees:
    def test_no_sources(self):
        assert triangulate_employees({})['consensus'] is None
        assert triangulate_employees({'a': None, 'b': None})['consensus'] is None

    def test_single_source(self):
        r = triangulate_employees({'linkedin': 150})
        assert r['consensus'] == 150
        assert r['confidence'] == 'low'

    def test_two_sources_agree(self):
        r = triangulate_employees({'linkedin': 100, 'github': 110})
        assert r['consensus'] == 105
        assert r['confidence'] == 'high'

    def test_two_sources_disagree(self):
        r = triangulate_employees({'linkedin': 100, 'wikipedia': 1000})
        assert r['confidence'] == 'low'
        assert 'Disagreement' in r['note']

    def test_three_sources_consensus(self):
        r = triangulate_employees({'a': 200, 'b': 210, 'c': 190})
        assert r['consensus'] == 200
        assert r['confidence'] == 'high'


class TestCheckFreshness:
    def test_no_date(self):
        r = check_freshness(None)
        assert r['fresh'] is False

    def test_empty_date(self):
        r = check_freshness('')
        assert r['fresh'] is False

    def test_fresh_date(self):
        from datetime import datetime, timedelta
        fresh = (datetime.now() - timedelta(days=1)).isoformat()
        r = check_freshness(fresh)
        assert r['fresh'] is True

    def test_aging_date(self):
        from datetime import datetime, timedelta
        aging = (datetime.now() - timedelta(days=180)).isoformat()
        r = check_freshness(aging)
        assert r['fresh'] is False
        assert 'Aging' in r['note']

    def test_stale_date(self):
        from datetime import datetime, timedelta
        stale = (datetime.now() - timedelta(days=400)).isoformat()
        r = check_freshness(stale)
        assert r['fresh'] is False
        assert 'Stale' in r['note']

    def test_invalid_date(self):
        r = check_freshness('not-a-date')
        assert r['fresh'] is False
        assert 'Invalid' in r['note']
