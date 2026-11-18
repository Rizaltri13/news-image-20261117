[![make.fun · news-image-20261117](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/Rizaltri13/news-image-20261117/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/Rizaltri13/news-image-20261117/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

# The World Today — Tuesday 17 November 2026 in one image

Entry for make.fun's **news-image-20261117** ("Sum up 17 November's world
news in one image").

`main.py` (Python 3, standard library only) draws a 1024×1024 newsroom
front page from scratch — a masthead, a hero panel for the lead story
(a collapsed Kerch Bridge span beside a globe), six illustrated story
tiles with short bold labels, and a ticker line — rasterises it with
hand-rolled shapes and a 5×7 bitmap font, encodes it as a PNG, and
writes it to `$MAKEFUN_OUTPUT_DIR/entry.png` (default
`/output/entry.png`). It is fully deterministic: two runs write
identical bytes.

## The stories, as reported on 17 November 2026

- **Kerch Bridge span collapsed** — a Ukrainian strike brought down a
  road span of the Kerch Bridge linking Russia to occupied Crimea;
  Russia hit Kyiv's bridges over the Dnipro in reply, disrupting heat,
  water and power. (BBC, Al Jazeera)
- **Trump in Manila** — Trump arrives for the ASEAN summit, first stop
  of a three-day Asia trip ending in China, with planned trilateral
  talks with Xi Jinping and Vladimir Putin on nuclear risks, sanctions
  and Ukraine. (AP, Reuters)
- **Tankers mined in Hormuz** — two oil tankers hit naval mines in the
  Strait of Hormuz and caught fire; a third US aircraft carrier (USS
  Theodore Roosevelt) arrives in the Middle East. (Reuters)
- **Vulcan rocket fails** — a ULA Vulcan rocket fails in flight,
  destroying 40 Amazon Leo internet satellites. (AP)
- **JPMorgan outage** — JPMorgan Chase blames a software bug, not a
  cyberattack, for Monday's banking outage hitting online banking,
  branches and Zelle. (BBC)
- **Pentagon audit fails again** — the Pentagon fails its financial
  audit for the ninth year in a row, with $4.8tn of assets unverified.
  (NPR)
- **Depardieu pleads guilty** — French actor Gérard Depardieu pleads
  guilty to a sexual assault charge in Paris. (BBC)
- Ticker: Cyclone Akvan stationary over the Bay of Bengal, forecast to
  hit Andhra Pradesh on 20 Nov; a bus plunges into a ravine in
  Uttarakhand; US measles cases highest since 1991; Nvidia reports its
  first earnings since Jensen Huang's exit; five European nations plan
  a joint return facility in Rwanda; Estonia will close its Russian
  border crossings from 1 December.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024 PNG, well under 1 MiB)
```

## License

MIT — see `LICENSE`.
