"""
Dynamic SVG Quality Badge Generator.
Produces high-resolution SVG status badges for repository READMEs and CI/CD dashboards.
"""

from typing import Optional


class BadgeGenerator:
    """Renders accessible, shields.io-compatible flat SVG badges."""

    COLOR_GREEN = "#2ea44f"
    COLOR_YELLOW = "#dfb317"
    COLOR_ORANGE = "#fe7d37"
    COLOR_RED = "#e05d44"
    COLOR_BLUE = "#0366d6"
    COLOR_GREY = "#555"

    @classmethod
    def get_color_for_score(cls, score: float) -> str:
        if score >= 80:
            return cls.COLOR_GREEN
        elif score >= 65:
            return cls.COLOR_YELLOW
        elif score >= 50:
            return cls.COLOR_ORANGE
        return cls.COLOR_RED

    @classmethod
    def get_color_for_verdict(cls, verdict: str) -> str:
        norm = verdict.upper()
        if "APPROVED_WITH" in norm:
            return cls.COLOR_YELLOW
        elif "APPROV" in norm:
            return cls.COLOR_GREEN
        return cls.COLOR_RED

    @classmethod
    def generate_svg(
        cls,
        label: str = "PanelReview",
        value: str = "PASS",
        color: Optional[str] = None,
        label_color: str = "#555",
    ) -> str:
        """Generates standard flat SVG markup."""
        # Calculate dynamic text width approximations
        label_width = max(35, len(label) * 7 + 14)
        value_width = max(35, len(value) * 7 + 14)
        total_width = label_width + value_width

        label_x = label_width / 2.0
        value_x = label_width + (value_width / 2.0)

        bg_color = color or cls.COLOR_GREEN

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{total_width}" height="20" role="img" aria-label="{label}: {value}">
  <title>{label}: {value}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="{label_color}"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{bg_color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110">
    <text aria-hidden="true" x="{label_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{label}</text>
    <text x="{label_x * 10}" y="140" transform="scale(.1)" fill="#fff">{label}</text>
    <text aria-hidden="true" x="{value_x * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)">{value}</text>
    <text x="{value_x * 10}" y="140" transform="scale(.1)" fill="#fff">{value}</text>
  </g>
</svg>"""
        return svg

    @classmethod
    def generate_score_badge(cls, score: float, label: str = "PanelReview", output_path: Optional[str] = None) -> str:
        """Creates a score badge (e.g. 85/100) and optionally writes to file."""
        val = f"{int(round(score))}/100"
        color = cls.get_color_for_score(score)
        svg = cls.generate_svg(label=label, value=val, color=color)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(svg)

        return svg
