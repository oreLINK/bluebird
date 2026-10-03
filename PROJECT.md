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

At the top, the menu button (on the right) lets you choose the mountain range
(the Pyrenees for now) and your language. Below it, filters narrow the page
to one kind of indicator: **All**, **Snow** or **Powder**. A dark-blue strip
tells you which mountain range and day the forecast is for, and when it was
last updated. Each tile then answers one question and presents the resorts
like the odds of a match on a betting site.

| Tile | Question | How to read a high percentage |
|---|---|---|
| **Snow today** | Will it snow during the ski day (08:00–17:00)? | Bring goggles for flat light; fresh snow may build up during the day. |
| **Powder on piste** | Did at least 5 cm fall after the grooming machines finished, before the lifts open? | First runs on the pistes will be in fresh, ungroomed snow. |
| **Off-piste powder** | Did at least 15 cm fall in the last 36 hours near the summit, without strong wind or a thaw spoiling it? | Good chances of light, untracked powder off-piste. Always check the avalanche bulletin first. |

Each tile shows:

- a **banner**: a photo of the
  ski area ranked first when one is available, otherwise an illustration (the
  first tile shows it across the whole card);
- the **three most likely resorts** as buttons, each with its percentage and
  a bar below it;
- optionally, betting-style **odds** (1 ÷ probability), if enabled for a tile;
- **See all** to list every other resort, from most to least likely.

Tap a resort to see why: expected snow (median and high scenario), recent
wind and temperature, the time window studied, the resort's elevation, and
how reliable the figure is.

Tap the **?** in the top-right corner of a tile, or anywhere on the tile
outside the resort buttons, to turn it over. The back explains the indicator:
what it measures, the time window studied, how it is computed, how reliable
it is today, when it was last updated and where the data comes from. Tap the
**×** (or the back of the card) to turn it again.

Resorts appear under a short name in the tiles (for example "Cauterets" for
"Cauterets – Cirque du Lys"). All tiles have the same size, so the page stays
tidy; switching filter brings the matching tiles in with a short animation.

If today's update is not available yet, the dark-blue strip says so.

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
they split half and half, it is low. The back of each tile also gives a
**reliability index** for the day: the average reliability of all resorts
for that indicator (high counts fully, medium half, low not at all).

The high-resolution Météo-France model (AROME) is shown next to it as a
second opinion.

Fixed facts about each resort (position, elevations, grooming and opening
times, pistes and lifts) are stored with the project and refreshed at most
once a season. Only the weather is fetched every morning.

### Update schedule

- Twice each morning, around **04:30 and 06:30** (Paris time), from November
  to May.
- Updates can arrive a few minutes late.

## Features

### Available now

- Pyrenees: 18 French resorts, from La Pierre Saint-Martin to Formiguères.
- Three probabilities: snow today, powder on piste, powder off-piste.
- Betting-style tiles: top three resorts as odds buttons, full ranking on
  demand, details on tap, reliability indicator, optional odds.
- Two-sided tiles: the back explains the indicator and today's reliability.
- Filters by kind of indicator (All, Snow, Powder), remembered on your device.
- Menu with the mountain range and language (French or English), remembered
  on your device.
- Clean dark-blue, light-blue and white design with a sporty typeface, in
  light and dark mode following your phone's setting, without background
  animation.
- Banner photos of the ski areas, credited to their authors (photos are
  added progressively; an illustration is shown until then).
- Works on any modern phone browser; add it to your home screen for an
  app-like experience.
- Respects "reduce motion" and "reduce transparency" accessibility settings.

### Coming next

- Avalanche risk level from the Météo-France bulletin (BERA), next to each resort.
- Resort opening status (open lifts and pistes).
- Slope orientation and steepness to refine the powder estimate
  (north-facing slopes keep powder longer).
- A 7-day trend tile and a map of the ski areas (piste and lift data from
  OpenStreetMap is already collected and refreshed once a season).
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
