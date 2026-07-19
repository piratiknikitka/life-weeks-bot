"""
Core "life in weeks" logic:
- weeks_lived(): how many full weeks have passed since birth
- draw_life_grid(): renders a 90-years x 52-weeks grid, red = lived, white = remaining
"""

from datetime import date
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

YEARS = 90
WEEKS_PER_YEAR = 52
TOTAL_WEEKS = YEARS * WEEKS_PER_YEAR  # 4680

# --- visual settings ---
CELL = 10          # cell size in px
GAP = 2             # gap between cells in px
MARGIN_LEFT = 75
MARGIN_TOP = 95
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 45

ARROW_COLOR = (60, 60, 160)

COLOR_LIVED = (196, 30, 30)
COLOR_LEFT = (255, 255, 255)
COLOR_BORDER = (190, 190, 190)
COLOR_BG = (255, 255, 255)
COLOR_TEXT = (25, 25, 25)


def _draw_arrow(draw, x0, y0, x1, y1, color=ARROW_COLOR, width=2, head=6):
    draw.line([x0, y0, x1, y1], fill=color, width=width)
    if x1 == x0:  # vertical arrow, pointing down
        draw.polygon(
            [(x1 - head, y1 - head), (x1 + head, y1 - head), (x1, y1 + head)],
            fill=color,
        )
    else:  # horizontal arrow, pointing right
        draw.polygon(
            [(x1 - head, y1 - head), (x1 - head, y1 + head), (x1 + head, y1)],
            fill=color,
        )


def weeks_lived(birth_date: date, as_of: date = None) -> int:
    """Full weeks passed since birth_date (0 if birth_date is in the future)."""
    as_of = as_of or date.today()
    days = (as_of - birth_date).days
    if days < 0:
        return 0
    return days // 7


def _load_fonts():
    # DejaVu is preinstalled in most Linux base images (incl. Render's).
    # Falls back to PIL's built-in bitmap font if not found.
    try:
        title = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        axis = ImageFont.truetype("DejaVuSans.ttf", 11)
        footer = ImageFont.truetype("DejaVuSans.ttf", 13)
    except IOError:
        title = axis = footer = ImageFont.load_default()
    return title, axis, footer


def draw_life_grid(birth_date: date, as_of: date = None) -> bytes:
    """Returns PNG bytes of the life-in-weeks grid."""
    as_of = as_of or date.today()
    lived = min(weeks_lived(birth_date, as_of), TOTAL_WEEKS)
    remaining = TOTAL_WEEKS - lived

    grid_w = YEARS * (CELL + GAP) - GAP
    grid_h = WEEKS_PER_YEAR * (CELL + GAP) - GAP

    width = MARGIN_LEFT + grid_w + MARGIN_RIGHT
    height = MARGIN_TOP + grid_h + MARGIN_BOTTOM

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)
    font_title, font_axis, font_footer = _load_fonts()

    years_lived = lived // WEEKS_PER_YEAR
    weeks_into_year = lived % WEEKS_PER_YEAR
    title = f"Lived {lived} of {TOTAL_WEEKS} weeks  ({years_lived}y {weeks_into_year}w)"
    draw.text((MARGIN_LEFT, 15), title, fill=COLOR_TEXT, font=font_title)

    # year axis labels every 10 years
    for y in range(0, YEARS + 1, 10):
        x = MARGIN_LEFT + y * (CELL + GAP)
        draw.text((x, MARGIN_TOP - 20), str(y), fill=COLOR_TEXT, font=font_axis)

    # "years" direction arrow, above the year numbers, pointing right
    draw.text((MARGIN_LEFT, MARGIN_TOP - 45), "years", fill=COLOR_TEXT, font=font_axis)
    _draw_arrow(
        draw,
        MARGIN_LEFT + 45, MARGIN_TOP - 40,
        MARGIN_LEFT + grid_w, MARGIN_TOP - 40,
    )

    # "weeks" direction arrow, to the left of the grid, pointing down
    draw.text((10, MARGIN_TOP), "weeks", fill=COLOR_TEXT, font=font_axis)
    _draw_arrow(
        draw,
        40, MARGIN_TOP + 25,
        40, MARGIN_TOP + grid_h,
    )

    # the grid itself: columns = years, rows = weeks within a year
    for col in range(YEARS):
        for row in range(WEEKS_PER_YEAR):
            week_index = col * WEEKS_PER_YEAR + row
            x0 = MARGIN_LEFT + col * (CELL + GAP)
            y0 = MARGIN_TOP + row * (CELL + GAP)
            x1 = x0 + CELL
            y1 = y0 + CELL
            fill = COLOR_LIVED if week_index < lived else COLOR_LEFT
            draw.rectangle([x0, y0, x1, y1], fill=fill, outline=COLOR_BORDER)

    footer = f"Lived: {lived}   |   Remaining: {remaining}   |   as of {as_of.isoformat()}"
    draw.text((MARGIN_LEFT, height - 25), footer, fill=COLOR_TEXT, font=font_footer)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
