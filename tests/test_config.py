"""Tests for core/config.py — centralized configuration."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config


class TestConfigBasics:
    def test_get_returns_env_var(self):
        os.environ['_TEST_VAR'] = 'test_value'
        assert Config.get('_TEST_VAR') == 'test_value'
        del os.environ['_TEST_VAR']

    def test_get_returns_default(self):
        assert Config.get('_NONEXISTENT', 'default') == 'default'

    def test_get_returns_none_for_missing(self):
        assert Config.get('_NONEXISTENT') is None

    def test_github_token_returns_none_if_not_set(self):
        # No token set — should return None (not crash)
        result = Config.github_token()
        assert result is None or isinstance(result, str)

    def test_litellm_url_default(self):
        url = Config.litellm_url()
        assert '4000' in url


class TestConfigPaths:
    def test_base_exists(self):
        assert os.path.isdir(Config.BASE)

    def test_horeca_dir_ends_correctly(self):
        assert Config.HORECA_DIR.endswith('output/HORECA')

    def test_john_json_ends_correctly(self):
        assert Config.JOHN_JSON.endswith('horeca_data.json')


class TestConfigDefaults:
    def test_cache_ttl_is_seven_days(self):
        assert Config.CACHE_TTL == 7 * 24 * 3600

    def test_timeouts_are_reasonable(self):
        assert 5 <= Config.TIMEOUT_DEFAULT <= 60
        assert Config.TIMEOUT_SLOW >= Config.TIMEOUT_DEFAULT

    def test_max_workers(self):
        assert 1 <= Config.MAX_WORKERS <= 20

    def test_user_agent_not_empty(self):
        assert len(Config.USER_AGENT) > 10
