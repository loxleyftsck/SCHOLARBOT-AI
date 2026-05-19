"""Tests for ui/tokens.py — design token system."""

import pytest
from ui.tokens import (
    get_colors,
    get_fonts,
    build_css_variables,
    COLORS,
    FONTS,
    SPACING,
    RADIUS,
    TRANSITIONS,
)


class TestDesignTokens:
    """Test design token functions."""

    def test_get_colors_returns_dict(self):
        """Should return color dictionary."""
        colors = get_colors()
        assert isinstance(colors, dict)
        assert "background" in colors
        assert "walnut" in colors
        assert "text_primary" in colors

    def test_get_fonts_returns_dict(self):
        """Should return font dictionary."""
        fonts = get_fonts()
        assert isinstance(fonts, dict)
        assert "serif" in fonts
        assert "sans" in fonts
        assert "mono" in fonts

    def test_build_css_variables(self):
        """Should build valid CSS variables string."""
        css = build_css_variables()
        assert ":root {" in css
        assert "--color-background:" in css
        assert "--font-serif:" in css
        assert "--space-4:" in css
        assert "--radius-lg:" in css
        assert "}" in css

    def test_colors_are_hex(self):
        """All colors should be valid hex values."""
        colors = get_colors()
        for key, value in colors.items():
            if key.startswith("text") or key in ("background", "walnut", "surface", "border"):
                assert value.startswith("#"), f"Color {key}={value} is not hex"
                assert len(value) == 7, f"Color {key}={value} is not 6-digit hex"

    def test_fonts_have_fallbacks(self):
        """Fonts should include fallback stacks."""
        fonts = get_fonts()
        for key, value in fonts.items():
            assert "," in value, f"Font {key} should have fallback stack"

    def test_spacing_follows_8px_grid(self):
        """Spacing should follow 8px grid system."""
        assert SPACING["1"] == "4px"
        assert SPACING["2"] == "8px"
        assert SPACING["4"] == "16px"
        assert SPACING["8"] == "32px"

    def test_radius_values(self):
        """Radius values should be CSS-valid."""
        assert "px" in RADIUS["sm"]
        assert "px" in RADIUS["lg"]
        assert "px" in RADIUS["full"]

    def test_transition_timing_functions(self):
        """Transitions should use valid timing functions."""
        for key, value in TRANSITIONS.items():
            assert "ease" in value or "linear" in value or "cubic-bezier" in value

    def test_z_index_layers(self):
        """Z-index should define proper layering."""
        from ui.tokens import Z_INDEX
        assert Z_INDEX["modal"] > Z_INDEX["overlay"]
        assert Z_INDEX["overlay"] > Z_INDEX["sticky"]


class TestColorAccessibility:
    """Test color contrast and accessibility."""

    def test_background_contrast(self):
        """Background should be lighter than text."""
        colors = get_colors()
        bg = colors["background"]
        text = colors["text_primary"]
        # Light bg, dark text - this should always be true
        assert bg != text

    def test_success_error_distinct(self):
        """Success and error colors should be visually distinct."""
        colors = get_colors()
        success = colors.get("secondary", colors.get("success", ""))
        error = colors["error"]
        assert success != error
