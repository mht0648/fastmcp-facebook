"""Unit and edge-case tests for copy_templates.py."""

import unittest
from copy_templates import format_marketing_copy, TEMPLATES, DEFAULT_HASHTAGS


class TestCopyTemplates(unittest.TestCase):
    """Test suite for marketing copy generation and formatting."""

    def setUp(self):
        self.sample_args = {
            "product_name": "Ergonomic Office Chair",
            "price": "$199.99",
            "product_url": "https://example.com/chair",
            "description": "High back mesh chair with lumbar support and 3D armrests."
        }

    def test_all_supported_styles(self):
        """Verify that all predefined template styles render the required variables."""
        for style_name in TEMPLATES.keys():
            result = format_marketing_copy(**self.sample_args, style=style_name)
            self.assertIn("Ergonomic Office Chair", result)
            self.assertIn("$199.99", result)
            self.assertIn("https://example.com/chair", result)
            self.assertIn("High back mesh chair", result)
            self.assertIn("#BabuJeeStore", result)

    def test_unknown_style_fallback(self):
        """An unrecognized style should fall back safely to 'promotional'."""
        result = format_marketing_copy(**self.sample_args, style="non_existent_style")
        self.assertIn("SPECIAL OFFER: Ergonomic Office Chair", result)

    def test_discount_percent_formatting(self):
        """Test with discount provided vs no discount provided."""
        with_discount = format_marketing_copy(**self.sample_args, discount_percent=25)
        self.assertIn("(25% OFF!)", with_discount)

        without_discount = format_marketing_copy(**self.sample_args, discount_percent=None)
        self.assertNotIn("% OFF!", without_discount)

        zero_discount = format_marketing_copy(**self.sample_args, discount_percent=0)
        self.assertNotIn("% OFF!", zero_discount)

    def test_custom_hashtags_formatting_and_deduplication(self):
        """Test hashtags with missing hash signs, whitespace, and duplicates."""
        custom_tags = ["office", "  furniture  ", "#BabuJeeStore"]
        result = format_marketing_copy(**self.sample_args, custom_hashtags=custom_tags)

        # Tags should have '#' prepended and whitespace stripped
        self.assertIn("#office", result)
        self.assertIn("#furniture", result)

        # Deduplication check: #BabuJeeStore is already in defaults, shouldn't appear twice
        words = result.split()
        self.assertEqual(words.count("#BabuJeeStore"), 1)

    def test_hashtag_cap_at_eight(self):
        """Ensure hashtags are capped at a maximum of 8 tags for Facebook best practices."""
        many_tags = [f"tag{i}" for i in range(20)]
        result = format_marketing_copy(**self.sample_args, custom_hashtags=many_tags)
        tag_line = [line for line in result.split("\n") if line.startswith("#")][-1]
        tags = tag_line.split()
        self.assertLessEqual(len(tags), 8)

    def test_empty_and_whitespace_description(self):
        """Edge case: empty or whitespace-padded product description."""
        result = format_marketing_copy(
            product_name="Minimal Widget",
            price="$9.99",
            product_url="https://example.com/widget",
            description="   \n  Compact and sleek.  \n\n  "
        )
        self.assertIn("Compact and sleek.", result)
        # Should not have excessive raw trailing whitespace
        self.assertNotIn("\n  Compact and sleek.  \n", result)

    def test_unicode_and_emojis(self):
        """Ensure non-ASCII unicode characters and complex emojis do not cause errors."""
        result = format_marketing_copy(
            product_name="Premium 🎧 Headphones & ⚡ Charger",
            price="€89,50",
            product_url="https://example.com/headphones?ref=fb&tag=ünîcødé",
            description="Audio haute-fidélité avec réduction de bruit active. 🌟"
        )
        self.assertIn("Premium 🎧 Headphones & ⚡ Charger", result)
        self.assertIn("€89,50", result)
        self.assertIn("Audio haute-fidélité", result)


if __name__ == "__main__":
    unittest.main()
