# Bluebird

**Morning snow odds, resort by resort.**

A "bluebird day" is what skiers call the first sunny day after a snowstorm:
deep blue sky, fresh snow everywhere. Bluebird helps you find those days. Every
morning it tells you, for each ski resort of a mountain range, how likely it
is to snow today and how likely you are to find fresh powder on or off the
pistes.

It is built for your phone, in French or English.

---

## What you see

At the top, choose a mountain range (the Pyrenees for now) and your language.
Below, each tile answers one question and ranks the resorts from most to least
likely, like the odds on a betting site.

| Tile | Question | How to read a high percentage |
|---|---|---|
| **Snow today** | Will it snow during the ski day (08:00–17:00)? | Bring goggles for flat light; fresh snow may build up during the day. |
| **Powder on piste** | Did at least 5 cm fall after the grooming machines finished, before the lifts open? | First runs on the pistes will be in fresh, ungroomed snow. |
| **Off-piste powder** | Did at least 15 cm fall in the last 36 hours near the summit, without strong wind or a thaw spoiling it? | Good chances of light, untracked powder off-piste. Always check the avalanche bulletin first. |

Each row shows:

- the **rank** and the **resort name** ("Favourite" marks a clear number one);
- a **bar** and a **percentage** coloured from slate grey (unlikely) to
  glacier blue (likely);
- optionally, betting-style **odds** (1 ÷ probability), if enabled for a tile.

Tap a row to see why: expected snow (median and high scenario), recent wind
and temperature, the time window studied, the resort's elevation, and how
reliable the figure is.

The header line tells you which day the forecast is for and when it was last
updated. If today's update is not available yet, a notice says so.

## Where the numbers come from

Bluebird does not invent its own weather forecast. It reads **ensemble
forecasts**: weather centres run their model dozens of times with slightly
different starting conditions to see how uncertain the forecast is.

- 51 scenarios from the European centre (ECMWF) and 40 from the German
  weather service (DWD ICON), via [Open-Meteo](https://open-meteo.com/).
- For each resort, at mid-mountain and near the summit.

A probability is simply **the share of scenarios in which the condition comes
true**. "72 %" means 72 out of 100 scenarios give enough snow.

**Reliability** ("Confidence") reflects how much the scenarios agree: when
almost all agree (very likely or very unlikely), reliability is high; when
they split half and half, it is low.

The high-resolution Météo-France model (AROME) is shown next to it as a
second opinion.

### Update schedule

- Twice each morning, around **04:30 and 06:30** (Paris time), from November
  to May.
- Updates can arrive a few minutes late.

## Features

### Available now

- Pyrenees: 18 French resorts, from La Pierre Saint-Martin to Formiguères.
- Three probabilities: snow today, powder on piste, powder off-piste.
- Ranking tiles with details on tap, reliability indicator, optional odds.
- French and English, remembered on your device.
- Light "bluebird day" theme and dark "alpine night" theme, following your
  phone's setting.
- Works on any modern phone browser; add it to your home screen for an
  app-like experience.
- Respects "reduce motion" and "reduce transparency" accessibility settings.

### Coming next

- Avalanche risk level from the Météo-France bulletin (BERA), next to each resort.
- Resort opening status (open lifts and pistes).
- Slope orientation and steepness to refine the powder estimate
  (north-facing slopes keep powder longer).
- A 7-day trend tile and a map of the ski areas.
- More mountain ranges: Northern and Southern Alps, Massif Central, Vosges, Jura.
- Checking past forecasts against observed snow to make the percentages more accurate.

## Limits and safety

- **Bluebird is a planning aid, not an avalanche bulletin.** Before any
  off-piste outing, read the official Météo-France avalanche bulletin (BERA),
  carry avalanche safety equipment and know how to use it.
- Forecasts are uncertain, mountain weather even more so. Local effects
  (wind-loaded slopes, sun, sheltered forests) are not captured.
- Resort coordinates and elevations are approximate; grooming and opening
  times are typical values, not each resort's daily schedule.
- Powder on piste assumes grooming ends around 02:00 and lifts open at 09:00
  unless configured otherwise for a resort.

## FAQ

**Why is a resort at 0 % when it's snowing outside?**
The forecast models disagree with reality sometimes, and the tile only counts
snow inside its time window and above its threshold (for example 5 cm since
grooming).

**Why don't the three tiles agree?**
They answer different questions, at different elevations and time windows.
Heavy snow overnight with strong wind can give a high "powder on piste" and
a low "off-piste powder".

**Is the site free?**
Yes. It uses free, openly licensed data (Open-Meteo, CC BY 4.0;
OpenStreetMap, ODbL) for non-commercial use.

**Does it track me?**
No account, no analytics, no cookies. Your language and last mountain range
are stored only in your browser.
