import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ai_blocker


def test_detect_system_language_env():
    """Verify that env var LANGUAGE takes priority and returns matching supported language."""
    # Test valid environment variable 'es'
    with patch.dict(os.environ, {"LANGUAGE": "es_AR.UTF-8"}):
        lang = ai_blocker.detect_system_language()
        assert lang == "es"

    # Test valid environment variable 'ja'
    with patch.dict(os.environ, {"LANGUAGE": "ja_JP.UTF-8"}):
        lang = ai_blocker.detect_system_language()
        assert lang == "ja"

    # Test unsupported language falling back to other variables or default
    with patch.dict(os.environ, {"LANGUAGE": "xyz_XYZ"}):
        # Should check others or fallback to default
        lang = ai_blocker.detect_system_language()
        assert lang in ai_blocker.STRINGS

def test_detect_system_language_fallback():
    """Verify that default fallback is 'en' if no env vars or locale settings match."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("locale.getlocale", return_value=(None, None)):
            with patch("platform.system", return_value="Linux"):
                with patch("ai_blocker.i18n.CURRENT_OS", "Linux"):
                    lang = ai_blocker.detect_system_language()
                    assert lang == "en"
