"""
ui/pin_map.py — Arduino Uno Pin Map SVG Renderer
-------------------------------------------------
Renders a pixel-accurate SVG of the Arduino Uno board.
Pins mentioned in the LLM answer are highlighted in amber.

The function extract_pins() parses a free-text answer and returns
a set of pin labels such as {"D2", "D3", "D13", "A0", "PWM~3"}.

The function render_pin_map(active_pins) returns an HTML string with
the SVG diagram embedded inline so Streamlit can display it with
st.components.v1.html().

Pin layout (Arduino Uno R3)
---------------------------
Digital  : D0–D13   (right column, top)
PWM (~)  : D3, D5, D6, D9, D10, D11
Analog   : A0–A5    (right column, bottom)
Power    : 5V, 3.3V, GND, VIN  (left column)
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Pin registry
# ---------------------------------------------------------------------------
#  Each entry: (pin_id, display_label, x, y, is_pwm)
#  Coordinates are for the SVG viewport 480 × 640 px.

_DIGITAL_PINS: list[tuple[str, str, int, int, bool]] = [
    # (id,   label,  cx, cy, pwm?)
    ("D0",  "D0",   390, 115, False),
    ("D1",  "D1",   390, 140, False),
    ("D2",  "D2",   390, 165, False),
    ("D3",  "D3~",  390, 190, True),
    ("D4",  "D4",   390, 215, False),
    ("D5",  "D5~",  390, 240, True),
    ("D6",  "D6~",  390, 265, True),
    ("D7",  "D7",   390, 290, False),
    ("D8",  "D8",   390, 315, False),
    ("D9",  "D9~",  390, 340, True),
    ("D10", "D10~", 390, 365, True),
    ("D11", "D11~", 390, 390, True),
    ("D12", "D12",  390, 415, False),
    ("D13", "D13",  390, 440, False),
]

_ANALOG_PINS: list[tuple[str, str, int, int, bool]] = [
    ("A0", "A0", 390, 480, False),
    ("A1", "A1", 390, 505, False),
    ("A2", "A2", 390, 530, False),
    ("A3", "A3", 390, 555, False),
    ("A4", "A4", 390, 580, False),
    ("A5", "A5", 390, 605, False),
]

_POWER_PINS: list[tuple[str, str, int, int, bool]] = [
    ("VIN",  "VIN",  90, 115, False),
    ("GND",  "GND",  90, 140, False),
    ("GND2", "GND",  90, 165, False),
    ("5V",   "5V",   90, 190, False),
    ("3V3",  "3.3V", 90, 215, False),
]

ALL_PINS = _DIGITAL_PINS + _ANALOG_PINS + _POWER_PINS


# ---------------------------------------------------------------------------
# Pin extractor
# ---------------------------------------------------------------------------

def extract_pins(text: str) -> set[str]:
    """
    Parse answer text and return a set of matching pin IDs.

    Recognises patterns such as:
      - "pin 13", "pin D13", "digital pin 2"
      - "PWM pin 3", "~5", "~6"
      - "A0", "A1", ... "A5"
      - "5V", "GND", "3.3V", "VIN"

    Returns a set like {"D13", "D3", "A0"}.
    """
    found: set[str] = set()

    upper = text.upper()

    # Analog pins:  A0 ... A5
    for m in re.finditer(r'\bA([0-5])\b', upper):
        found.add(f"A{m.group(1)}")

    # Digital / numeric:  "pin 13", "pin D13", "digital 3", "D3", etc.
    for m in re.finditer(r'\b(?:PIN\s*D?|D(?=\d))(\d{1,2})\b', upper):
        n = int(m.group(1))
        if 0 <= n <= 13:
            found.add(f"D{n}")

    # Bare number mention with context word
    for m in re.finditer(
        r'\b(?:DIGITAL|PWM|OUTPUT|INPUT|INTERRUPT|LED|BLINK)\s+(?:PIN\s*)?(\d{1,2})\b',
        upper
    ):
        n = int(m.group(1))
        if 0 <= n <= 13:
            found.add(f"D{n}")

    # Tilde PWM: "~3", "~5", "~6", "~9", "~10", "~11"
    for m in re.finditer(r'~\s*(\d{1,2})', upper):
        n = int(m.group(1))
        if n in (3, 5, 6, 9, 10, 11):
            found.add(f"D{n}")

    # Power pins
    if re.search(r'\b5\s*V\b', upper):
        found.add("5V")
    if re.search(r'\b3\.?3\s*V\b', upper):
        found.add("3V3")
    if re.search(r'\bVIN\b', upper):
        found.add("VIN")
    if re.search(r'\bGND\b', upper):
        found.add("GND")

    return found


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
_COLOR_BODY       = "#1565C0"   # Arduino Uno board — dark blue
_COLOR_BOARD_BG   = "#0D47A1"
_COLOR_PIN_IDLE   = "#90A4AE"   # grey connector
_COLOR_PIN_ACTIVE = "#FFB300"   # amber highlight
_COLOR_PIN_PWM    = "#F57C00"   # orange for PWM
_COLOR_PIN_ANALOG = "#7B1FA2"   # purple for analog
_COLOR_PIN_POWER  = "#C62828"   # red for power
_COLOR_TEXT       = "#FFFFFF"
_COLOR_LABEL_IDLE = "#CFD8DC"
_COLOR_LABEL_ACT  = "#FFB300"


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------

def render_pin_map(active_pins: set[str]) -> str:
    """
    Return an HTML string containing the Arduino Uno SVG pin diagram.

    Active pins (found in `active_pins`) are drawn in amber.
    PWM-capable pins are marked with a tilde (~) in their label.

    Args:
        active_pins : Set of pin IDs returned by extract_pins(), e.g. {"D13", "A0"}.

    Returns:
        HTML string ready for st.components.v1.html().
    """

    def _pin_circle(pid: str, label: str, cx: int, cy: int, is_pwm: bool) -> str:
        active = pid in active_pins
        # Colour logic
        if active:
            fill   = _COLOR_PIN_ACTIVE
            stroke = "#FF6F00"
            r      = 11
        elif pid.startswith("A"):
            fill   = _COLOR_PIN_ANALOG
            stroke = "#6A1B9A"
            r      = 9
        elif pid in ("5V", "3V3", "VIN", "GND", "GND2"):
            fill   = _COLOR_PIN_POWER
            stroke = "#B71C1C"
            r      = 9
        elif is_pwm:
            fill   = "#1976D2"
            stroke = "#0D47A1"
            r      = 9
        else:
            fill   = _COLOR_PIN_IDLE
            stroke = "#546E7A"
            r      = 9

        label_color = _COLOR_LABEL_ACT if active else _COLOR_LABEL_IDLE
        # Place label to the left for power pins (left column), right for others
        if cx < 200:
            lx, anchor = cx - 16, "end"
        else:
            lx, anchor = cx + 16, "start"

        pulse = ""
        if active:
            pulse = (
                f'<circle cx="{cx}" cy="{cy}" r="{r + 4}" '
                f'fill="{fill}" opacity="0.3">'
                f'<animate attributeName="r" values="{r+4};{r+9};{r+4}" '
                f'dur="1.5s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.3;0;0.3" '
                f'dur="1.5s" repeatCount="indefinite"/>'
                f'</circle>'
            )

        return (
            f'{pulse}'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            f'<text x="{lx}" y="{cy + 4}" font-family="monospace" font-size="10" '
            f'fill="{label_color}" text-anchor="{anchor}" font-weight="{"bold" if active else "normal"}">'
            f'{label}</text>'
        )

    # Build all pin circles
    pin_svgs = []
    for pid, label, cx, cy, is_pwm in ALL_PINS:
        pin_svgs.append(_pin_circle(pid, label, cx, cy, is_pwm))

    # Legend
    legend = (
        '<g transform="translate(20, 620)">'
        f'<circle cx="10" cy="8" r="7" fill="{_COLOR_PIN_ACTIVE}"/>'
        f'<text x="22" y="12" font-family="sans-serif" font-size="10" fill="{_COLOR_LABEL_IDLE}">Active pin</text>'
        f'<circle cx="100" cy="8" r="7" fill="#1976D2"/>'
        f'<text x="112" y="12" font-family="sans-serif" font-size="10" fill="{_COLOR_LABEL_IDLE}">PWM pin</text>'
        f'<circle cx="175" cy="8" r="7" fill="{_COLOR_PIN_ANALOG}"/>'
        f'<text x="187" y="12" font-family="sans-serif" font-size="10" fill="{_COLOR_LABEL_IDLE}">Analog pin</text>'
        f'<circle cx="260" cy="8" r="7" fill="{_COLOR_PIN_POWER}"/>'
        f'<text x="272" y="12" font-family="sans-serif" font-size="10" fill="{_COLOR_LABEL_IDLE}">Power pin</text>'
        '</g>'
    )

    # Header labels
    header = (
        '<text x="390" y="90" font-family="sans-serif" font-size="11" '
        'fill="#B0BEC5" text-anchor="middle" font-weight="bold">DIGITAL / PWM</text>'
        '<text x="390" y="463" font-family="sans-serif" font-size="11" '
        'fill="#B0BEC5" text-anchor="middle" font-weight="bold">ANALOG IN</text>'
        '<text x="90" y="90" font-family="sans-serif" font-size="11" '
        'fill="#B0BEC5" text-anchor="middle" font-weight="bold">POWER</text>'
    )

    # Board outline
    board = (
        f'<rect x="30" y="70" width="420" height="590" rx="12" ry="12" '
        f'fill="{_COLOR_BOARD_BG}" stroke="#0A3875" stroke-width="3"/>'
        # Chip
        f'<rect x="170" y="300" width="140" height="90" rx="4" ry="4" '
        f'fill="#212121" stroke="#424242" stroke-width="2"/>'
        f'<text x="240" y="348" font-family="monospace" font-size="10" '
        f'fill="#76FF03" text-anchor="middle">ATmega328P</text>'
        # USB connector
        f'<rect x="30" y="135" width="28" height="50" rx="3" ry="3" '
        f'fill="#37474F" stroke="#546E7A" stroke-width="1"/>'
        f'<text x="44" y="164" font-family="sans-serif" font-size="8" '
        f'fill="#90A4AE" text-anchor="middle">USB</text>'
        # Power jack
        f'<circle cx="44" cy="230" r="13" fill="#37474F" stroke="#546E7A" stroke-width="1"/>'
        f'<text x="44" y="254" font-family="sans-serif" font-size="8" '
        f'fill="#90A4AE" text-anchor="middle">PWR</text>'
        # Crystal
        f'<rect x="195" y="420" width="30" height="14" rx="2" ry="2" '
        f'fill="#37474F" stroke="#546E7A" stroke-width="1"/>'
    )

    # Title
    title = (
        f'<text x="240" y="45" font-family="sans-serif" font-size="14" '
        f'fill="#E3F2FD" text-anchor="middle" font-weight="bold">Arduino Uno R3 — Pin Map</text>'
        f'<text x="240" y="62" font-family="sans-serif" font-size="10" '
        f'fill="#78909C" text-anchor="middle">'
        f'{len(active_pins)} pin(s) highlighted</text>'
    )

    # Divider line between digital and analog
    divider = (
        '<line x1="360" y1="460" x2="430" y2="460" '
        'stroke="#37474F" stroke-width="1" stroke-dasharray="4,2"/>'
    )

    pin_elements = "\n  ".join(pin_svgs)

    svg = f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 650"
     style="width:100%; max-width:480px; background:#0A1929; border-radius:12px;">
  {title}
  {board}
  {header}
  {divider}
  {pin_elements}
  {legend}
</svg>"""

    return f"""
<div style="
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 8px;
  background: #0A1929;
  border-radius: 12px;
">
{svg}
</div>
"""
