import sys
import os
import pytest

# Add project root to sys.path so we can import ai_blocker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ai_blocker

def test_blocklist_integrity():
    """Verify that BLOCKLIST is not empty and is properly formatted."""
    assert isinstance(ai_blocker.BLOCKLIST, dict)
    assert len(ai_blocker.BLOCKLIST) > 0
    
    all_domains = []
    for category, domains in ai_blocker.BLOCKLIST.items():
        assert isinstance(category, str)
        assert isinstance(domains, list)
        assert len(domains) > 0
        
        for domain in domains:
            assert isinstance(domain, str)
            assert "." in domain  # basic domain validation
            assert domain.strip() == domain  # no leading/trailing whitespace
            all_domains.append(domain)

def test_translations_sync():
    """Verify category translations are defined for all supported languages."""
    assert len(ai_blocker.CATEGORY_TRANSLATIONS) > 0
    for lang, translations in ai_blocker.CATEGORY_TRANSLATIONS.items():
        assert len(translations) > 0
        # Check that blocklist categories are translated in this language
        for category in ai_blocker.BLOCKLIST:
            assert category in translations

