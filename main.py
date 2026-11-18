#!/usr/bin/env python3
"""news-image-20261117 entry: draw one 1024x1024 PNG that sums up the world
news of Tuesday 17 November 2026, and write it to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png).

Pure Python 3 standard library. The picture is rasterised into an RGB
buffer with hand-rolled shapes and a 5x7 bitmap font, then encoded as a
PNG with zlib. No network, no inputs, no randomness: two runs write the
same bytes.

Layout: a newsroom front page. A masthead and date band, a hero panel for
the lead story -- a collapsed Kerch Bridge span beside a globe -- six
story tiles with icons and short bold labels, and a ticker line of
further stories along the bottom.

The day, as reported on 17 November 2026 (BBC, Al Jazeera, AP, Reuters):
  * LEAD: a Ukrainian strike collapses a road span of the Kerch Bridge
    linking Russia to occupied Crimea; Russia hits Kyiv's bridges over
    the Dnipro in reply, disrupting heat, water and power.
  * Trump arrives in Manila for the ASEAN summit, first stop of a
    three-day Asia trip ending in China, with planned trilateral talks
    with Xi Jinping and Vladimir Putin on nuclear risks, sanctions and
    Ukraine.
  * Two oil tankers hit naval mines in the Strait of Hormuz and catch
    fire; a third US aircraft carrier (USS Theodore Roosevelt) arrives
    in the Middle East.
  * A ULA Vulcan rocket fails in flight, destroying 40 Amazon Leo
    internet satellites.
  * JPMorgan Chase blames a software bug (not a cyberattack) for
    Monday's banking outage hitting online banking, branches and Zelle.
  * The Pentagon fails its financial audit for the ninth year in a row
    ($4.8tn of assets unverified).
  * French actor Gerard Depardieu pleads guilty to a sexual assault
    charge in Paris.
  Ticker: Cyclone Akvan stationary over the Bay of Bengal, forecast to
  hit Andhra Pradesh on 20 Nov; a bus plunges into a ravine in
  Uttarakhand; US measles cases highest since 1991; Nvidia reports its
  first earnings since Jensen Huang's exit; five European nations plan
  a joint return facility in Rwanda; Estonia will close its Russian
  border crossings from 1 December.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
INK = (13, 27, 38)        # page background
PANEL = (23, 44, 59)      # tile background
PANEL2 = (17, 34, 46)     # hero background
EDGE = (62, 94, 112)      # panel borders
CREAM = (245, 239, 224)   # headline text
MUTED = (158, 182, 196)   # secondary text
RED = (216, 72, 66)       # lead accent
GOLD = (232, 182, 76)
TEAL = (63, 167, 160)
SKY = (127, 178, 217)
SAND = (217, 201, 163)
GREEN = (87, 167, 115)
GREY = (148, 163, 173)
STEEL = (96, 116, 128)
DARK = (9, 16, 22)

buf = bytearray(W * H * 3)

# ---------------------------------------------------------------- canvas
def rect(x, y, w, h, c):
    """Filled rectangle, clipped to the canvas."""
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    n = len(row)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        buf[i:i + n] = row


def disc(cx, cy, r, c):
    """Filled circle."""
    r2 = r * r
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        rect(cx - dx, yy, 2 * dx + 1, 1, c)


def ring(cx, cy, r, c, t=2):
    """Circle outline of thickness t."""
    ro = r + t
    ri = max(0, r - t)
    for yy in range(cy - ro, cy + ro + 1):
        dy = yy - cy
        dxo = int(math.sqrt(max(0, ro * ro - dy * dy)))
        if abs(dy) <= ri:
            dxi = int(math.sqrt(ri * ri - dy * dy))
            rect(cx - dxo, yy, dxo - dxi, 1, c)
            rect(cx + dxi + 1, yy, dxo - dxi, 1, c)
        else:
            rect(cx - dxo, yy, 2 * dxo + 1, 1, c)


def ellipse(cx, cy, rx, ry, c, t=3):
    """Ellipse outline drawn as short line segments."""
    steps = 72
    prev = None
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        p = (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
        if prev is not None:
            line(prev[0], prev[1], p[0], p[1], c, t)
        prev = p


def line(x1, y1, x2, y2, c, t=3):
    """Thick line: a chain of small discs."""
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    r = max(1, t // 2)
    for i in range(steps + 1):
        x = x1 + (x2 - x1) * i // steps
        y = y1 + (y2 - y1) * i // steps
        disc(x, y, r, c)


def poly(points, c):
    """Filled polygon by scanline."""
    ys = [p[1] for p in points]
    n = len(points)
    for yy in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if (y1 <= yy < y2) or (y2 <= yy < y1):
                xs.append(int(x1 + (yy - y1) * (x2 - x1) / (y2 - y1)))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            rect(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, c)


def panel(x, y, w, h, fill):
    rect(x, y, w, h, fill)
    rect(x, y, w, 2, EDGE)
    rect(x, y + h - 2, w, 2, EDGE)
    rect(x, y, 2, h, EDGE)
    rect(x + w - 2, y, 2, h, EDGE)


# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, rows top to bottom, '#' is ink.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'X': ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
}


def textw(s, scale):
    return len(s) * 6 * scale - scale


def text(x, y, s, scale, c, bold=False):
    """Draw text with its top-left at (x, y); return the end x."""
    off = max(1, scale // 2) if bold else 0
    for ch in s.upper():
        rows = FONT.get(ch, FONT[' '])
        for gy, row in enumerate(rows):
            for gx, bit in enumerate(row):
                if bit == '#':
                    rect(x + gx * scale, y + gy * scale, scale, scale, c)
                    if bold:
                        rect(x + gx * scale + off, y + gy * scale,
                             scale, scale, c)
        x += 6 * scale
    return x


def textc(cx, y, s, scale, c, bold=False):
    """Draw text centred on cx."""
    return text(cx - textw(s, scale) // 2, y, s, scale, c, bold)


# ---------------------------------------------------------------- icons
def globe(cx, cy, r):
    """A simple world globe: ocean disc, land blobs, graticule."""
    disc(cx, cy, r, (36, 88, 107))
    land = (87, 167, 115)
    # North America, South America, Africa/Eurasia hints, Australia.
    disc(cx - r // 2, cy - r // 3, r // 4, land)
    disc(cx - r // 4, cy + r // 4, r // 6, land)
    disc(cx + r // 4, cy - r // 4, r // 3, land)
    disc(cx + r // 3, cy + r // 5, r // 5, land)
    disc(cx + r // 2, cy + r // 2, r // 7, land)
    # Graticule: meridian and latitude ellipses over the land.
    for f in (0.33, 0.66, 1.0):
        ellipse(cx, cy, int(r * f), r, (70, 130, 145), 2)
    for f in (-0.55, 0.0, 0.55):
        ellipse(cx, cy + int(r * f), r, int(r * 0.32), (70, 130, 145), 2)
    # The offset latitude ellipses poke past the limb near the edges, so
    # wipe anything drawn outside the disc back to the hero panel colour.
    rr = r + 2
    for yy in range(cy - rr, cy + rr + 1):
        for xx in range(cx - rr, cx + rr + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 > rr * rr:
                i = (yy * W + xx) * 3
                if tuple(buf[i:i + 3]) != PANEL2:
                    buf[i:i + 3] = bytes(PANEL2)
    ring(cx, cy, r, SKY, 3)


def icon_bridge(x, y):
    """A suspension bridge with its middle span collapsed into the strait."""
    # smoke rising from the broken span
    disc(x + 126, y + 78, 9, GREY)
    disc(x + 138, y + 62, 12, GREY)
    disc(x + 116, y + 58, 8, (120, 134, 144))
    # towers
    poly([(x + 34, y + 28), (x + 46, y + 28), (x + 46, y + 126),
          (x + 34, y + 126)], STEEL)
    poly([(x + 206, y + 28), (x + 218, y + 28), (x + 218, y + 126),
          (x + 206, y + 126)], STEEL)
    # suspension cables from the tower tops to the deck
    line(x + 40, y + 32, x + 100, y + 118, GREY, 3)
    line(x + 40, y + 32, x + 8, y + 118, GREY, 3)
    line(x + 212, y + 32, x + 152, y + 118, GREY, 3)
    line(x + 212, y + 32, x + 244, y + 118, GREY, 3)
    # deck: two standing ends, one span fallen into the water
    rect(x + 8, y + 118, 92, 9, STEEL)
    rect(x + 152, y + 118, 92, 9, STEEL)
    line(x + 102, y + 122, x + 148, y + 160, STEEL, 8)
    disc(x + 126, y + 120, 7, RED)   # the break point
    # water
    line(x + 4, y + 176, x + 248, y + 176, SKY, 3)
    line(x + 4, y + 188, x + 248, y + 188, TEAL, 3)


def icon_plane(x, y):
    """An airliner climbing past a rising sun: Trump lands in Manila."""
    disc(x + 142, y + 16, 11, GOLD)                # sun
    # fuselage, nose right
    line(x + 18, y + 52, x + 150, y + 44, SAND, 9)
    disc(x + 150, y + 44, 6, SAND)
    # main wing
    poly([(x + 70, y + 48), (x + 96, y + 86), (x + 108, y + 86),
          (x + 88, y + 46)], SAND)
    # tail fin
    line(x + 22, y + 50, x + 12, y + 28, SAND, 6)
    # windows
    for wx in range(48, 138, 14):
        disc(wx, y + 46, 2, DARK)
    # contrail
    line(x + 6, y + 58, x + 58, y + 62, SKY, 2)


def icon_tanker(x, y):
    """An oil tanker on fire after a mine strike, in the Strait of Hormuz."""
    # flames above the middle tank
    poly([(x + 76, y + 52), (x + 84, y + 22), (x + 92, y + 40),
          (x + 100, y + 16), (x + 108, y + 52)], GOLD)
    poly([(x + 84, y + 52), (x + 90, y + 32), (x + 96, y + 52)], RED)
    # smoke
    disc(x + 92, y + 12, 8, GREY)
    disc(x + 104, y + 4, 6, GREY)
    # deck tanks and bridge tower
    rect(x + 28, y + 52, 30, 18, GREY)
    rect(x + 66, y + 52, 30, 18, GREY)
    rect(x + 110, y + 52, 30, 18, GREY)
    rect(x + 140, y + 38, 14, 32, CREAM)
    # hull
    poly([(x + 8, y + 70), (x + 164, y + 70), (x + 150, y + 92),
          (x + 22, y + 92)], STEEL)
    # sea, and a spiked mine drifting by
    line(x + 6, y + 100, x + 166, y + 100, SKY, 3)
    line(x + 6, y + 108, x + 166, y + 108, TEAL, 3)
    disc(x + 146, y + 104, 5, DARK)
    line(x + 141, y + 99, x + 151, y + 109, DARK, 2)
    line(x + 141, y + 109, x + 151, y + 99, DARK, 2)


def icon_rocket(x, y):
    """A Vulcan rocket breaking apart: flame, smoke, falling satellites."""
    # stars
    disc(x + 20, y + 18, 3, GOLD)
    disc(x + 148, y + 26, 3, GOLD)
    disc(x + 156, y + 66, 2, GOLD)
    # falling satellite debris, tumbling
    rect(x + 118, y + 14, 18, 9, GREY)
    line(x + 118, y + 18, x + 106, y + 12, GREY, 3)
    line(x + 136, y + 18, x + 148, y + 12, GREY, 3)
    rect(x + 22, y + 60, 14, 7, GREY)
    # rocket body, nose up
    rect(x + 76, y + 28, 20, 52, CREAM)
    poly([(x + 76, y + 28), (x + 86, y + 6), (x + 96, y + 28)], RED)
    poly([(x + 76, y + 64), (x + 58, y + 86), (x + 76, y + 80)], RED)
    poly([(x + 96, y + 64), (x + 114, y + 86), (x + 96, y + 80)], RED)
    disc(x + 86, y + 44, 6, SKY)
    # flame and smoke below
    poly([(x + 78, y + 80), (x + 86, y + 106), (x + 94, y + 80)], GOLD)
    poly([(x + 82, y + 80), (x + 86, y + 96), (x + 90, y + 80)], RED)
    disc(x + 60, y + 96, 8, GREY)
    disc(x + 112, y + 100, 9, GREY)


def icon_bank(x, y):
    """A bank building struck by a red lightning bolt: a software bug."""
    # pediment, columns, base
    poly([(x + 16, y + 30), (x + 86, y + 8), (x + 156, y + 30)], SAND)
    for cx in (26, 56, 86, 116, 146):
        rect(x + cx, y + 34, 12, 52, SAND)
    rect(x + 16, y + 86, 140, 8, SAND)
    rect(x + 10, y + 94, 152, 6, (170, 150, 110))
    # the bug: a red lightning bolt across the facade
    poly([(x + 96, y + 36), (x + 78, y + 60), (x + 90, y + 60),
          (x + 72, y + 88), (x + 100, y + 58), (x + 88, y + 58)], RED)


def icon_audit(x, y):
    """A ledger crossed out in red: the Pentagon's ninth failed audit."""
    rect(x + 52, y + 8, 68, 92, CREAM)
    rect(x + 52, y + 8, 68, 10, STEEL)
    for ly in (28, 40, 52, 64):
        rect(x + 60, y + ly, 52, 4, MUTED)
    rect(x + 60, y + 76, 36, 4, MUTED)
    # big red X over the whole ledger
    line(x + 44, y + 14, x + 128, y + 96, RED, 7)
    line(x + 128, y + 14, x + 44, y + 96, RED, 7)


def icon_gavel(x, y):
    """A judge's gavel coming down: Depardieu pleads guilty in Paris."""
    # sound block
    rect(x + 56, y + 84, 60, 10, SAND)
    rect(x + 50, y + 94, 72, 5, (170, 150, 110))
    # handle and head
    line(x + 56, y + 78, x + 118, y + 30, SAND, 8)
    line(x + 100, y + 22, x + 132, y + 46, SAND, 16)
    line(x + 106, y + 30, x + 126, y + 46, DARK, 3)
    # strike marks
    line(x + 140, y + 18, x + 152, y + 8, GOLD, 3)
    line(x + 148, y + 34, x + 160, y + 26, GOLD, 3)


# ---------------------------------------------------------------- compose
def tile(x, y, w, h, icon, label1, label2, sub1, sub2=None):
    panel(x, y, w, h, PANEL)
    icon(x + (w - 172) // 2, y + 12)
    textc(x + w // 2, y + 128, label1, 3, CREAM, True)
    textc(x + w // 2, y + 156, label2, 3, CREAM, True)
    textc(x + w // 2, y + 194, sub1, 2, MUTED)
    if sub2:
        textc(x + w // 2, y + 214, sub2, 2, MUTED)


def compose():
    rect(0, 0, W, H, INK)
    # outer frame
    rect(8, 8, W - 16, 3, EDGE)
    rect(8, H - 11, W - 16, 3, EDGE)
    rect(8, 8, 3, H - 16, EDGE)
    rect(W - 11, 8, 3, H - 16, EDGE)

    # masthead
    textc(W // 2, 30, "THE DAY IN ONE PICTURE", 3, MUTED)
    textc(W // 2, 60, "THE WORLD TODAY", 10, CREAM, True)
    rect(212, 146, 600, 46, RED)
    textc(W // 2, 155, "TUESDAY 17 NOVEMBER 2026", 4, CREAM, True)

    # hero: collapsed bridge beside the globe, lead story between them
    panel(24, 212, 976, 240, PANEL2)
    icon_bridge(44, 232)
    globe(872, 332, 88)
    lx = 316
    text(lx, 232, "LEAD STORY", 3, RED, True)
    text(lx, 260, "KERCH BRIDGE", 5, CREAM, True)
    text(lx, 302, "SPAN COLLAPSED", 5, CREAM, True)
    rect(lx, 350, 440, 3, GOLD)
    text(lx, 366, "UKRAINE STRIKE HITS SPAN", 3, SAND)
    text(lx, 394, "RUSSIA HITS KYIV BRIDGES", 3, SAND)
    text(lx, 422, "HEAT, WATER, POWER CUT", 3, SAND)

    # six tiles, 3 x 2
    tw, th = 314, 244
    xs = (24, 355, 686)
    ys = (468, 728)
    tiles = [
        (icon_plane, "TRUMP IN MANILA", "ASEAN SUMMIT",
         "ASIA TRIP TO CHINA", "XI + PUTIN TALKS"),
        (icon_tanker, "TANKERS MINED", "IN HORMUZ",
         "2 TANKERS ON FIRE", "3RD US CARRIER IN"),
        (icon_rocket, "VULCAN ROCKET", "FAILS IN FLIGHT",
         "40 LEO SATELLITES", "LOST"),
        (icon_bank, "JPMORGAN OUTAGE", "SOFTWARE BUG",
         "NOT A CYBERATTACK", "ZELLE + BRANCHES HIT"),
        (icon_audit, "PENTAGON AUDIT", "FAILS AGAIN",
         "$4.8TN UNVERIFIED", "9TH YEAR IN A ROW"),
        (icon_gavel, "DEPARDIEU PLEADS", "GUILTY",
         "SEXUAL ASSAULT", "CASE IN PARIS"),
    ]
    for i, (icon, l1, l2, s1, s2) in enumerate(tiles):
        tile(xs[i % 3], ys[i // 3], tw, th, icon, l1, l2, s1, s2)

    # ticker: two lines of further stories
    textc(W // 2, 978,
          "CYCLONE AKVAN NEARS INDIA - BUS CRASH IN UTTARAKHAND - MEASLES HIGH SINCE 1991",
          2, MUTED)
    textc(W // 2, 996,
          "NVIDIA EARNINGS - EU RWANDA RETURNS PLAN - ESTONIA CLOSES RUSSIAN BORDER",
          2, MUTED)


# ---------------------------------------------------------------- png out
def png_bytes():
    raw = bytearray()
    row = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * row:(y + 1) * row]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    compose()
    data = png_bytes()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
