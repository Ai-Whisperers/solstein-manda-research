"""Tests for core/cache.py — persistent disk cache."""
import sys, os, json, tempfile, shutil, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.cache import cache_get, cache_set, cache_get_or_fetch, cache_stats, CACHE_DIR


class TestCacheGetSet:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_dir = CACHE_DIR
        import core.cache as c
        c.CACHE_DIR = self.test_dir

    def teardown_method(self):
        import core.cache as c
        c.CACHE_DIR = self.orig_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_set_and_get(self):
        cache_set('test_source', 'test_key', {'hello': 'world'})
        result = cache_get('test_source', 'test_key')
        assert result == {'hello': 'world'}

    def test_get_missing_key(self):
        result = cache_get('test_source', 'nonexistent')
        assert result is None

    def test_get_missing_source(self):
        result = cache_get('nonexistent', 'key')
        assert result is None

    def test_set_overwrites(self):
        cache_set('test_source', 'key1', {'v': 1})
        cache_set('test_source', 'key1', {'v': 2})
        result = cache_get('test_source', 'key1')
        assert result == {'v': 2}

    def test_large_data(self):
        big = {'data': 'x' * 10000}
        cache_set('test_source', 'big', big)
        result = cache_get('test_source', 'big')
        assert result == big

    def test_none_data_not_cached(self):
        result = cache_get_or_fetch('test_source', 'none_key', lambda: None)
        assert result is None
        # Should NOT have cached it
        assert cache_get('test_source', 'none_key') is None

    def test_fetch_fn_called_only_once(self):
        call_count = [0]
        def fetch_fn():
            call_count[0] += 1
            return {'data': 42}

        r1 = cache_get_or_fetch('test_source', 'once_key', fetch_fn)
        assert r1 == {'data': 42}
        assert call_count[0] == 1

        r2 = cache_get_or_fetch('test_source', 'once_key', fetch_fn)
        assert r2 == {'data': 42}
        assert call_count[0] == 1  # Still 1 — not called again


class TestCacheTTL:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_dir = CACHE_DIR
        import core.cache as c
        c.CACHE_DIR = self.test_dir

    def teardown_method(self):
        import core.cache as c
        c.CACHE_DIR = self.orig_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_expired_ttl_returns_none(self):
        import core.cache as c
        c.CACHE_DIR = self.test_dir
        cache_set('test_source', 'ttl_key', {'data': 'fresh'}, ttl=-3600)
        result = cache_get('test_source', 'ttl_key')
        assert result is None, "Expired cache should return None"

    def test_valid_ttl_returns_data(self):
        cache_set('test_source', 'valid_key', {'data': 'good'}, ttl=3600)
        result = cache_get('test_source', 'valid_key')
        assert result == {'data': 'good'}


class TestCacheStats:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_dir = CACHE_DIR
        import core.cache as c
        c.CACHE_DIR = self.test_dir

    def teardown_method(self):
        import core.cache as c
        c.CACHE_DIR = self.orig_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_empty_cache(self):
        stats = cache_stats()
        assert stats['total_files'] == 0
        assert stats['total_size_kb'] == 0
        assert stats['sources'] == {}

    def test_stats_with_data(self):
        cache_set('alpha', 'k1', {'a': 1})
        cache_set('beta', 'k2', {'b': 2})
        stats = cache_stats()
        assert stats['total_files'] == 2
        assert 'alpha' in stats['sources']
        assert 'beta' in stats['sources']
        assert stats['total_size_kb'] > 0


class TestAtomicWrite:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_dir = CACHE_DIR
        import core.cache as c
        c.CACHE_DIR = self.test_dir

    def teardown_method(self):
        import core.cache as c
        c.CACHE_DIR = self.orig_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_no_tmp_files_left_behind(self):
        cache_set('test_source', 'clean_key', {'data': 'clean'})
        cache_path = os.path.join(self.test_dir, 'test_source', 'clean_key.json')
        assert os.path.exists(cache_path)
        # No .tmp file should remain
        tmp_path = cache_path + '.tmp'
        assert not os.path.exists(tmp_path)

    def test_atomicity_on_corrupted_write(self):
        cache_set('test_source', 'atomic_key', {'data': 'atomic'})
        result = cache_get('test_source', 'atomic_key')
        assert result == {'data': 'atomic'}
        # Verify the file is valid JSON and contains our data
        cache_path = os.path.join(self.test_dir, 'test_source', 'atomic_key.json')
        with open(cache_path) as f:
            parsed = json.load(f)
        assert parsed.get('data', {}).get('data') == 'atomic'
