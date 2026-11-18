"""THE WORLD TODAY -- front page for Tuesday 17 November 2026.

A self-contained Python 3 program (standard library only) that draws a
1024x1024 newspaper front page summing up the world news of Tuesday
17 November 2026 and writes it to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png).

How it works, in brief:
  * A plain RGB bytearray holds the whole canvas; small helpers paint
    filled rectangles, lines, discs and rings into it.
  * Text is rendered with a 5x7 bitmap font defined below: every glyph
    is seven rows of five bits, typed out by hand for A-Z, 0-9 and a
    handful of punctuation marks, scaled up as needed.
  * The picture is assembled from simple drawn shapes: a masthead band
    with the paper name and the date, a hero panel for the lead story
    (a bridge with a collapsed span over the sea), six story tiles
    each with a small drawn icon, and a ticker band at the bottom.
  * The PNG is encoded by hand: signature, IHDR, one IDAT chunk of
    zlib-compressed scanlines (filter byte 0), and IEND, each chunk
    carrying its CRC32.
  * No network, no input files, no clock, no randomness: two runs
    write byte-identical files.
"""

import binascii
import math
import os
import struct
import zlib

W = 1024
H = 1024

# Palette: dark ink background, cream paper, red / gold / teal accents.
INK = (18, 22, 38)
INK2 = (30, 36, 58)
PAPER = (243, 236, 214)
CREAM = (250, 244, 228)
RED = (196, 38, 38)
RED2 = (150, 26, 26)
GOLD = (214, 164, 62)
TEAL = (42, 148, 138)
BLUE = (52, 96, 158)
SKY = (168, 205, 224)
WHITE = (246, 246, 240)
GREY = (148, 152, 168)
SMOKE = (110, 112, 124)

# The canvas: three bytes per pixel, row-major, top-left origin.
buf = bytearray(W * H * 3)


def px(x, y, c):
    """Paint one pixel, silently ignoring out-of-canvas coordinates."""
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def rect(x, y, w, h, c):
    """Paint a filled rectangle."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, c)


def hline(x, y, w, c):
    for xx in range(x, x + w):
        px(xx, y, c)


def vline(x, y, h, c):
    for yy in range(y, y + h):
        px(x, yy, c)


def line(x0, y0, x1, y1, c):
    """Bresenham line between two points."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        px(x, y, c)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def thick_line(x0, y0, x1, y1, c, t=3):
    """A line drawn t pixels wide by stamping discs along it."""
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        disc(x, y, t // 2, c)


def disc(cx, cy, r, c):
    """Paint a filled disc."""
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                px(xx, yy, c)


def ring(cx, cy, r, c):
    """Paint a thin circle outline by sampling angles."""
    for deg in range(360):
        a = math.radians(deg)
        px(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)


def frame(x, y, w, h, c, t=2):
    """Paint a rectangular outline t pixels thick."""
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is seven rows of five bits, written out by
# hand as "1" for an inked cell and "0" for an empty one. Only the
# characters the page actually uses are defined.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00000", "00100"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ":": ("00000", "00100", "00000", "00000", "00100", "00000", "00000"),
    "'": ("00100", "00100", "00100", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("10001", "10010", "00100", "01000", "10010", "01001", "10001"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "00100", "00100", "00100", "00100", "00010"),
    ")": ("01000", "00100", "00100", "00100", "00100", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


# ---------------------------------------------------------------------------
# Text helpers. A glyph is 5 cells wide with 1 cell of spacing, so a
# character cell is 6*scale pixels wide and 7*scale tall.
# ---------------------------------------------------------------------------

def text_w(s, scale):
    """Pixel width of a string at a given scale."""
    if not s:
        return 0
    return len(s) * 6 * scale - scale


def draw_char(x, y, ch, scale, c):
    """Draw one glyph with its top-left corner at (x, y)."""
    g = FONT.get(ch)
    if g is None:
        return
    for r, row in enumerate(g):
        for col, bit in enumerate(row):
            if bit == "1":
                rect(x + col * scale, y + r * scale, scale, scale, c)


def draw_text(x, y, s, scale, c):
    """Draw a string left-aligned from (x, y)."""
    for ch in s:
        draw_char(x, y, ch, scale, c)
        x += 6 * scale


def center_text(y, s, scale, c, x0=0, x1=W):
    """Draw a string centred between x0 and x1."""
    draw_text(x0 + (x1 - x0 - text_w(s, scale)) // 2, y, s, scale, c)


def wrap(s, scale, maxw):
    """Greedy word wrap: split a string into lines fitting maxw pixels."""
    lines = []
    cur = ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(x, y, s, scale, c, maxw, gap=4):
    """Draw a wrapped paragraph; returns the y just below the last line."""
    for ln in wrap(s, scale, maxw):
        draw_text(x, y, ln, scale, c)
        y += 7 * scale + gap
    return y


# ---------------------------------------------------------------------------
# Small drawn icons. Each takes the top-left corner of a ~48x48 box and
# draws a simple pictogram in one accent colour.
# ---------------------------------------------------------------------------

def icon_plane(x, y, c):
    """A jet in profile, nose to the right."""
    thick_line(x + 4, y + 24, x + 40, y + 24, c, 5)
    thick_line(x + 30, y + 10, x + 36, y + 24, c, 4)
    thick_line(x + 14, y + 34, x + 22, y + 24, c, 4)
    thick_line(x + 34, y + 14, x + 40, y + 24, c, 3)
    disc(x + 42, y + 24, 3, c)


def icon_ship(x, y, c):
    """A tanker hull with a smokestack and a wisp of smoke."""
    line(x + 4, y + 30, x + 44, y + 30, c)
    line(x + 8, y + 30, x + 12, y + 42, c)
    line(x + 40, y + 30, x + 36, y + 42, c)
    hline(x + 12, y + 42, 24, c)
    rect(x + 14, y + 18, 6, 12, c)
    disc(x + 17, y + 12, 4, SMOKE)
    disc(x + 22, y + 8, 3, SMOKE)
    hline(x + 2, y + 46, 44, c)


def icon_rocket(x, y, c):
    """A rocket climbing, flame below."""
    rect(x + 20, y + 4, 8, 24, c)
    line(x + 20, y + 4, x + 24, y - 2, c)
    line(x + 28, y + 4, x + 24, y - 2, c)
    line(x + 20, y + 28, x + 12, y + 38, c)
    line(x + 28, y + 28, x + 36, y + 38, c)
    disc(x + 24, y + 42, 5, GOLD)
    disc(x + 24, y + 36, 3, RED)


def icon_bank(x, y, c):
    """A bank front: triangular roof, three columns, steps."""
    line(x + 4, y + 14, x + 24, y + 2, c)
    line(x + 44, y + 14, x + 24, y + 2, c)
    hline(x + 4, y + 14, 40, c)
    vline(x + 8, y + 18, 20, c)
    vline(x + 22, y + 18, 20, c)
    vline(x + 36, y + 18, 20, c)
    hline(x + 4, y + 40, 40, c)
    hline(x + 2, y + 44, 44, c)


def icon_doc(x, y, c):
    """A document sheet with a big check mark."""
    frame(x + 8, y + 2, 30, 40, c, 2)
    hline(x + 13, y + 10, 20, c)
    hline(x + 13, y + 16, 20, c)
    hline(x + 13, y + 22, 14, c)
    thick_line(x + 14, y + 32, x + 20, y + 38, c, 3)
    thick_line(x + 20, y + 38, x + 34, y + 26, c, 3)


def icon_gavel(x, y, c):
    """A judge's gavel, head at top left, handle diagonal."""
    rect(x + 6, y + 6, 18, 10, c)
    rect(x + 4, y + 4, 22, 3, c)
    thick_line(x + 22, y + 14, x + 40, y + 40, c, 4)
    hline(x + 8, y + 42, 32, c)
    disc(x + 42, y + 42, 3, c)


def icon_globe(x, y, c):
    """A globe: circle, equator and a meridian."""
    ring(x + 24, y + 24, 20, c)
    hline(x + 5, y + 24, 38, c)
    line(x + 10, y + 10, x + 38, y + 38, c)
    line(x + 38, y + 10, x + 10, y + 38, c)
    disc(x + 24, y + 24, 3, c)


# ---------------------------------------------------------------------------
# Page layout. The 1024x1024 canvas is divided top to bottom into:
#   masthead (paper name + red date band)  -> y 0..192
#   hero panel (lead story: Kerch Bridge)  -> y 196..496
#   six story tiles, 3 columns x 2 rows   -> y 508..880
#   ticker band (four more stories)        -> y 892..980
#   footer line                            -> y 988..1000
# ---------------------------------------------------------------------------

def draw_masthead():
    """Paper name, tag line, and the red date band."""
    rect(16, 14, 992, 2, GOLD)
    center_text(30, "THE WORLD TODAY", 8, CREAM)
    center_text(100, "WORLD NEWS IN BRIEF - FRONT PAGE", 2, GOLD)
    rect(16, 128, 992, 44, RED)
    center_text(140, "TUESDAY 17 NOVEMBER 2026", 3, WHITE)
    rect(16, 180, 992, 2, GOLD)


def draw_hero_picture(x0, y0, w, h):
    """The Kerch Bridge after the strike: sky, sea, and a deck with a
    span dropped into the water, smoke rising from the gap."""
    rect(x0, y0, w, 150, SKY)
    disc(x0 + w - 54, y0 + 34, 18, GOLD)
    disc(x0 + 60, y0 + 40, 10, WHITE)
    disc(x0 + 84, y0 + 46, 12, WHITE)
    disc(x0 + 108, y0 + 40, 9, WHITE)
    rect(x0, y0 + 150, w, h - 150, BLUE)
    # The standing deck, left and right of the gap.
    rect(x0, y0 + 114, 150, 10, INK)
    rect(x0 + 234, y0 + 114, 150, 10, INK)
    # Piers holding the deck up.
    rect(x0 + 40, y0 + 124, 12, 46, INK)
    rect(x0 + 320, y0 + 124, 12, 46, INK)
    # The fallen span, tilted down into the water.
    thick_line(x0 + 150, y0 + 114, x0 + 200, y0 + 184, INK, 9)
    thick_line(x0 + 156, y0 + 122, x0 + 206, y0 + 192, INK, 5)
    # Smoke curling up from the gap.
    disc(x0 + 178, y0 + 96, 13, SMOKE)
    disc(x0 + 196, y0 + 80, 10, SMOKE)
    disc(x0 + 212, y0 + 66, 7, SMOKE)
    # Wave marks on the water.
    hline(x0 + 20, y0 + 200, 60, SKY)
    hline(x0 + 260, y0 + 210, 80, SKY)
    hline(x0 + 90, y0 + 224, 50, SKY)
    hline(x0 + 290, y0 + 228, 60, SKY)


def draw_hero():
    """Lead story panel: headline and body on the left, picture right."""
    rect(16, 196, 992, 300, PAPER)
    rect(16, 196, 992, 6, RED)
    draw_text(40, 216, "LEAD STORY - UKRAINE", 2, RED)
    draw_text(40, 244, "KERCH BRIDGE", 4, INK)
    draw_text(40, 276, "SPAN FALLS IN", 4, INK)
    draw_text(40, 308, "UKRAINE STRIKE", 4, INK)
    rect(40, 344, 520, 2, RED)
    para(40, 360, "A UKRAINIAN STRIKE BROUGHT DOWN A ROAD SPAN OF "
        "THE KERCH BRIDGE LINKING RUSSIA TO OCCUPIED CRIMEA. RUSSIA "
        "HIT BRIDGES OVER THE DNIPRO IN KYIV IN REPLY, CUTTING HEAT, "
        "WATER AND POWER.", 2, INK, 520)
    draw_hero_picture(600, 216, 384, 240)
    draw_text(600, 470, "THE KERCH BRIDGE AFTER THE STRIKE", 1, INK)


def draw_tile(x, y, w, h, accent, icon, title, body):
    """One story tile: coloured top bar, icon, bold title, short body."""
    rect(x, y, w, h, INK2)
    rect(x, y, w, 6, accent)
    icon(x + 16, y + 18, accent)
    draw_text(x + 16, y + 74, title, 3, CREAM)
    para(x + 16, y + 104, body, 2, WHITE, w - 32)


def draw_tiles():
    """Six tiles: Trump, Hormuz tankers, Vulcan, JPMorgan, Pentagon,
    Depardieu."""
    tw = 322
    th = 180
    gap = 12
    x0 = 16
    rows = (508, 700)
    tiles = [
        (GOLD, icon_plane, "TRUMP IN MANILA",
         "ASEAN SUMMIT OPENS THREE DAY ASIA TRIP TO CHINA"),
        (RED, icon_ship, "MINES HIT TANKERS",
         "TWO SHIPS ABLAZE IN HORMUZ AS US CARRIER ARRIVES"),
        (TEAL, icon_rocket, "VULCAN FAILS",
         "40 AMAZON LEO SATELLITES LOST IN FLIGHT"),
        (GOLD, icon_bank, "JPMORGAN OUTAGE",
         "SOFTWARE BUG, NOT CYBERATTACK, BLAMED"),
        (RED, icon_doc, "PENTAGON AUDIT",
         "FAILS FOR NINTH YEAR IN A ROW"),
        (TEAL, icon_gavel, "DEPARDIEU GUILTY",
         "ACTOR PLEADS GUILTY IN PARIS COURT"),
    ]
    for i, (accent, icon, title, body) in enumerate(tiles):
        col = i % 3
        row = i // 3
        draw_tile(x0 + col * (tw + gap), rows[row], tw, th,
                  accent, icon, title, body)


def draw_ticker():
    """Red ticker band with the remaining stories of the day."""
    rect(16, 892, 992, 88, RED)
    para(32, 902,
         "ALSO TODAY: ESTONIA TO CLOSE RUSSIAN BORDER CROSSINGS FROM "
         "1 DECEMBER AFTER FOILED SABOTAGE PLOT. NVIDIA REPORTS FIRST "
         "EARNINGS SINCE JENSEN HUANG EXIT. CYCLONE AKVAN OVER BAY OF "
         "BENGAL. US MEASLES CASES HIGHEST SINCE 1991.",
         2, WHITE, 960)


def draw_page():
    """Paint the whole front page onto the canvas."""
    rect(0, 0, W, H, INK)
    frame(0, 0, W, H, GOLD, 4)
    draw_masthead()
    draw_hero()
    draw_tiles()
    draw_ticker()
    center_text(990, "THE WORLD TODAY - TUESDAY 17 NOVEMBER 2026", 1, GOLD)


# ---------------------------------------------------------------------------
# PNG encoding by hand: signature, IHDR, IDAT (zlib scanlines, filter 0),
# IEND, each chunk with its CRC32.
# ---------------------------------------------------------------------------

def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    draw_page()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
