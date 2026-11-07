# Bluebird

**Snow odds, time slot by time slot, resort by resort.**

A "bluebird day" is what skiers call the first sunny day after a snowstorm:
deep blue sky, fresh snow everywhere. Bluebird helps you find those days.
Four times a day it tells you, for each ski resort of a mountain range, how
likely it is to snow this morning, at lunchtime, this afternoon, this
evening, tonight and tomorrow, and how likely you are to find fresh powder
on or off the pistes.

Once a season is over, a **Rewind** looks back at it: which resort got the
most snow, the longest snowfall, the snowiest slopes and the snowiest
off-piste terrain around them. The first one is **Rewind 25/26**.

It is built for your phone, in French, English or Spanish.

---

## What you see

At the top, the Bluebird logo sits on the left and, on the right, a button
with the flag of the current language opens a small window to choose
another language. The site starts in your phone's or computer's language
when it is French, English or Spanish, in French otherwise. Below the name, a first row of buttons
lets you choose **where** (see [Places](#places)), and a second row of the
same buttons narrows the page step by step (see [Filters](#filters)). Just
above the tiles, a date tells you which day the data are for (the day of
their last update), with the update time on a small line below it. Each
tile then answers one question for one **time slot** (see [Available
indicators](#available-indicators)) and presents the resorts like the odds of
a match on a betting site.

### Time slots

| Slot | Hours (Paris time) |
|---|---|
| This morning | 06:00 – 12:00 |
| At lunchtime | 12:00 – 14:00 |
| This afternoon | 14:00 – 18:00 |
| This evening | 18:00 – midnight |
| Tonight | midnight – 06:00 |
| Today (whole day) | shown from 06:00 to 18:00 |

Each tile shows its slot on a small **time badge** in its top left corner,
like a ticket with two boxes and short words in each language: the day
("Today", "Tmrw"; in French "Auj.", "Dem.") and the moment ("AM", "Noon",
"PM", "Eve", "Night"). A whole-day tile only shows the day, and tonight's
tiles only say "Tonight". Each day has its own dark colour, and each moment
a light one, from dawn to night, so you recognise them at a glance:

| Day | Colour | | Moment | Colour |
|---|---|---|---|---|
| Today | midnight blue | | Morning | dawn pink |
| Tonight | indigo | | Lunchtime | yellow |
| Tomorrow | dark green | | Afternoon | amber |
| | | | Evening (and sunset) | violet |
| | | | Night | deep indigo |

An icon (sun rising, sun high, sun setting, moon) repeats the colour of the
moment. The title of the tile stays short ("Snow", "Bluebird day") since the
badge already says when, and the back of the tile repeats the badge with the
exact date and hours ("Saturday 16 January, 06:00 to 12:00"). Later, the
week-end and next week will get their own colours too.

Tiles are sorted by time: the slots coming soonest first, then tomorrow's.
**A tile disappears as soon as its slot is over**, even if the page stays
open: after noon you no longer see "this morning", after 18:00 you no longer
see "at lunchtime" or "this afternoon", but "this evening", "tonight" and
tomorrow's slots remain. The day switches at 06:00: at 00:30, "tonight" is
still the night that has just started, and "tomorrow morning" is the coming
morning.

Each tile shows:

- a **banner**: a photo of the
  ski area ranked first when one is available, otherwise an illustration (the
  first tile shows it across the whole card). Tiles lower on the page, such as
  **Off-piste powder**, have no banner and are shorter;
- the **three most likely resorts** as buttons, each with its percentage,
  three **reliability dots** (one: low, two: medium, three: high) and a bar
  below it;
- optionally, betting-style **odds** (1 ÷ probability), if enabled for a tile;
- **See all** to list every other resort, from most to least likely, each
  with its reliability dots. While the list is open, a **See less** button
  also appears above it, so you can close it without scrolling down.

For now, the tiles show the probability only: tapping a resort does
nothing. (A detailed view per resort — expected snow, recent wind and
temperature, time window, elevation — exists and may come back later.)

Tap the **?** in the top-right corner of a tile, or anywhere on the tile
outside the resort buttons, to turn it over. The back explains the indicator:
what it measures, the time window studied, how it is computed, how reliable
it is today, when it was last updated, where the data comes from and who
took the photo. Tap the
**×** (or the back of the card) to turn it again.

Resorts appear under a short name in the tiles (for example "Cauterets" for
"Cauterets – Cirque du Lys"). All tiles have the same size, so the page stays
tidy; switching filter brings the matching tiles in with a short animation.

### Places

The first row of buttons works like the filters, one level at a time:

1. **Mountain range**: the Pyrenees for now (Alps and others later).
2. **Département**, or abroad the region or country, in a single row: in
   the Pyrenees, **Pyrénées-Atlantiques**, **Hautes-Pyrénées**,
   **Haute-Garonne**, **Ariège** and **Pyrénées-Orientales** today. When
   Spanish and Andorran resorts are added, their regions follow the
   départements with a flag: **🇪🇸 Aragon**, **🇪🇸 Catalogne**, **🇪🇸 Navarre**,
   **🇦🇩 Andorre**.
3. **Linked ski area**, when several resorts share one (Les 3 Vallées,
   Portes du Soleil…): it shows all its resorts, even across a border. None
   of the current Pyrenean resorts shares a linked area, so this level does
   not appear yet.

Resorts abroad carry their flag in the tiles (🇪🇸 Baqueira), so a ranking of
the whole massif shows at a glance which side of the border each one is on.
Every tile then ranks the resorts of the chosen place only ("1. Cauterets,
2. Luz Ardiden…" in the Hautes-Pyrénées). Tap the **×** of a place to go
back up; the whole place you chose is remembered on your device.

### Filters

The filters work like those of a music app on the phone, one level at a time:

1. **Home page** (no filter chosen): the most useful tiles of the moment for
   the place you chose, up to 50, always led by the **bluebird day** (today,
   or tomorrow once today's ski day is over). The others are picked and
   ordered automatically: strong values first, at the right time of day,
   when the forecast is reliable (see
   [How the home page is chosen](#how-the-home-page-is-chosen)). The filter row shows
   **Rewind 25/26**, **Mood** (its name and outline shimmer in moving
   colours, see [Moods](#moods)) and the six categories **Snow**, **Snow quality**,
   **Sky**, **Comfort**, **Getting there** and **Safety** (see
   [Categories](#categories)).
2. Tap a category, for example **Snow quality**: its button fills in, moves
   to the left with a small **×**, the other categories disappear, and the
   page shows one tile per indicator **for the whole day**, today and
   tomorrow. Next to it appear its **sub-categories**: **Powder**, **Snow
   condition**, **Beginners**.
3. Tap a sub-category: it joins the row the same way, and **Today** and
   **Tomorrow** appear.
4. Tap **Today**: only today's whole-day tiles remain, and the time slots
   still to come appear: **Morning**, **Lunchtime**, **Afternoon**,
   **Evening**, **Night** (only those the indicators have).
5. Tap a slot: the page shows the tiles of that slot only ("powder on piste
   this morning").

The time-slot tiles only appear at this last level, so the page stays short:
above it, each indicator has a single whole-day tile per day ("today",
"tonight" for the snow cannons, "this evening" for the sunset and the starry
night), and today's tiles give way to tomorrow's once the day is over. Tap a
chosen filter (the one with the **×**) to remove it and the ones after it.
**Safety** has a single sub-category, so it goes straight to Today/Tomorrow,
and stops there (wind-blown snow is computed for the whole day); **Rewind
25/26** has no further level. Your filter is remembered on your device,
down to its last level (for example Mood, On site, Freerider): next time the
site opens straight on it.

### Moods

**Mood** answers the wish of the day, not your skiing level: the same skier
can be a Freerider on a powder day and pick Dolce vita when the sun is out.
Tap **Mood**, then where you are, then your mood:

- **On site**
  - **Freerider**: off-piste powder, snow alert, snow, wind-blown snow,
    white day, bluebird day, lifts in the wind, hard snow.
  - **Carver**: on-piste powder, hard snow, snow, lifts in the wind, white
    day, bluebird day, heavy snow, full sun.
  - **Dolce vita**: a bit of skiing, a lot of terrace: bluebird day, full
    sun, sunset, mild day, spring snow, starry night, wind chill.
  - **Snowplough** (beginners, teenagers or adults): what scares a
    beginner: easy conditions, white day (seeing the slope), hard snow
    (ice), lifts in the wind, heavy snow, mild day, wind chill.
  - **Little ones** (Piou-Piou, children starting out): children feel the
    cold and tire quickly: wind chill, mild day, easy conditions, full sun,
    snow, white day.
- **On the way** (tomorrow only, at any time of day)
  - **Heading up tomorrow**: can you get there, and which resort is best?
    Chains, snow, lifts in the wind, bluebird day, on-piste and off-piste
    powder, white day.
  - **Heading down tomorrow**: the road back, and is the last morning worth
    skiing? Chains, snow, on-piste powder, bluebird day.

A mood shows **all** its indicators, each once, at its best moment: alerts
first, then the strongest values at the right time of day (see
[How the home page is chosen](#how-the-home-page-is-chosen)), then the
others, so a dry day still tells a Freerider "no powder today". Nothing is
pinned, not even the bluebird day.

If an update is late, a line under the date above the tiles says so.

### Service status

At the bottom of the page, the **Service status** link (with a small coloured
dot showing the overall state) opens a full-window page, like the privacy
page. It says whether the last update went well ("All systems running") or
how many items are degraded, with the time of the update, then lists, one
line each, the state of every data source, every data processing step, every
indicator and every tile:

- **Available**: fresh and complete;
- **Partial**: fresh, but some resorts are missing;
- **Outdated**: the values shown come from an earlier update (for example
  "data from 06:00"), because the latest one could not compute them;
- **Unavailable**: no value.

When an indicator cannot be updated, Bluebird keeps showing its last valid
values for the slots still to come, with a "Data from 06:00" badge on the
tile, rather than an empty page. A slot with no value at all says so on its
tile.


### Rewind 25/26

The red **Rewind 25/26** filter, the first of the filter row, replaces the
day's tiles with a review of the 2025/26 season (1 December 2025 to 1 May
2026, in the Pyrenees). The home page never shows these tiles: they are only
under their red filter. Rewind tiles look like the day's tiles (photo of the leading resort
or an illustration, podium, full ranking), dressed in Christmas red and white
with a "REWIND 25/26" badge. Their indicators are listed in
[Available indicators](#available-indicators).

The top three resorts are on the podium; **See all** lists the others with
their value. Snow totals are in metres (for example 4.43 m), the longest
snowfall in hours and the ideal snow cover as a share of the season's days
(its bars go from 0 to 100 %; the other bars are relative to the best resort).
The back of each tile explains the measure, the season dates, how it is
computed and the sources. The line above the tiles reads "Season 2025/2026"
instead of the update time.

## Available indicators

### Categories

Every indicator, available or planned, belongs to one category that answers a
simple question, whatever your level or activity:

| Category | The question it answers | Sub-categories on the site |
|---|---|---|
| ❄️ **Snow** | Will it snow, how much, and is there enough snow on the ground? | Snowfall (snow, snow alert) · Snow cannons |
| 🎿 **Snow quality** | What will the snow be like under your skis or snowshoes: powder, spring snow, ice? | Powder (on piste, off-piste) · Snow condition (spring, hard, heavy) · Beginners (easy conditions) |
| ☀️ **Sky** | What will you see: sun, cloud, a white day, a sunset? | Sun (bluebird day, full sun) · Visibility (white day) · Sky show (sunset, starry night) |
| 🧣 **Comfort** | How will it feel: cold, wind, strong sun, a mild day? | Cold (wind chill) · Mild weather (mild day) |
| 🚗 **Getting there** | Can you drive up, will the lifts run, will it be crowded? | Road (chains) · Lifts (lifts in the wind) |
| ⚠️ **Safety** | Which mountain hazards to watch? (Always read the official avalanche bulletin too.) | Off-piste (avalanche danger, wind-blown snow) |

They are the filters of the site (in French **Neige**, **Glisse**,
**Ciel**, **Confort**, **Accès**, **Sécurité**). They replaced the first topics (Snow,
Powder, Visibility): powder is one kind of snow quality, and a white day is
about light and sky. The season reviews (Rewinds) keep their own filter.

### Every 6 hours (live)

Probabilities for each time slot of today and tomorrow (see [Time
slots](#time-slots)), refreshed every 6 hours, with reliability dots.

Indicators are grouped by **category**, which is also their filter on the
site (see [Categories](#categories)). Each one is shown in the most telling
way:

- **an amount** (centimetres, hours, °C, km/h) when the quantity itself
  speaks: it is the **median** of the 91 scenarios (half give more, half
  less), and the dots say how close the scenarios are. Some come with a word
  that places the value on a scale (the official wind chill risk, light /
  strong wind…);
- **Yes / Possible / No** when you have a decision to take: Yes from a 60 %
  chance, Possible from 25 %;
- **a percentage** for uncertain events or combinations of conditions: the
  share of the 91 scenarios in which it happens.

The word or time next to a value (risk, sunset time) shows in the full list
of resorts ("See all").

| Category | Indicator | Shown as | Slots | Question | How to read it |
|---|---|---|---|---|---|
| ❄️ Snow | **Snow** | cm of snow (median) | whole day, morning, lunchtime, afternoon, evening, night | How much snow will fall during the slot (for the whole day: between 08:00 and 17:00), at mid-mountain? | Bring goggles for flat light; fresh snow may build up. |
| ❄️ Snow | **Snow alert** | cm in 36 h (median), with light / good / alert | today, tomorrow (whole day) | How much snow will fall at mid-mountain within 36 hours from 06:00? "Alert" from 30 cm. | A big dump is coming: plan a powder day, and check the roads. |
| ❄️ Snow | **Snow cannons** | hours of snowmaking weather (median) | tonight, tomorrow night (also as the night slot) | How many hours of the night (20:00–06:00) will be cold and dry enough to make snow at mid-mountain (wet-bulb temperature of −2.5 °C or less)? A useful night has 6 or more. | The resort can make snow overnight: better-covered pistes in the morning, especially early season. |
| 🎿 Snow quality | **Powder on piste** | cm since grooming (median) | whole day (at lift opening), morning, lunchtime, afternoon | How much snow will have fallen on the pistes since the grooming machines finished, by the start of the slot (at lift opening for the morning)? Powder from 5 cm. | The pistes will be covered with fresh, ungroomed snow. |
| 🎿 Snow quality | **Off-piste powder** | % | whole day (at lift opening), morning, lunchtime, afternoon | Has at least 15 cm fallen in the 36 hours before the start of the slot near the summit, without strong wind or a thaw spoiling it? | Good chances of light, untracked powder off-piste. Always check the avalanche bulletin first. |
| 🎿 Snow quality | **Spring snow** | % | whole day (09:00–17:00), morning, lunchtime, afternoon | After a night freeze (−1 °C or less between 00:00 and 08:00), does the snow soften during the slot (+1 °C or more), without 5 cm of fresh snow on top? | Smooth "corn" snow: the best time to ski in spring. |
| 🎿 Snow quality | **Hard snow** | Yes / Possible / No | whole day (09:00–11:00), morning | After a thaw the day before (+2 °C or more) and a night freeze (−2 °C or less), does the snow stay frozen during the slot (0 °C or less), without fresh snow on top? | Hard, icy pistes: sharp edges, and wait for the sun to soften them. |
| 🎿 Snow quality | **Heavy snow** | % | whole day (11:00–17:00), lunchtime, afternoon | Will the slot be warm (+4 °C or more) or bring wet snow (1 cm or more at +0.5 °C or more)? | Heavy, sticky snow: tiring legs, ski earlier in the day. |
| 🎿 Snow quality | **Easy conditions** | % | whole day (09:00–17:00), morning, lunchtime, afternoon | Will the slot stay calm (wind under 25 km/h), not too cold (above −10 °C), visible (at most a quarter of white hours) and without a snowstorm (under 2 cm)? | A good time for beginners and children. |
| ☀️ Sky | **White day** | % | today, tomorrow (whole day) | Will the ski day (09:00–17:00) be a white day at mid-mountain? | Expect no relief and poor contrast: stay near trees and markers, take tinted goggles. |
| ☀️ Sky | **Bluebird day** | % | today, tomorrow (whole day) | Will at least 15 cm of fresh snow have fallen at mid-mountain in the 36 hours before 09:00, followed by a sunny ski day (09:00–17:00)? | The dream day: fresh snow under a deep blue sky. Sunscreen and dark goggles; powder goes fast. |
| ☀️ Sky | **Sunset** | % and the sunset time | tonight, tomorrow evening | Will the sky be mostly clear (40 % of cloud or less) near the summit around sunset, from the hour before to the hour after? The tile gives the sunset time. | A sunset to watch from the top (the time assumes a flat horizon: ridges to the west hide it earlier). |
| ☀️ Sky | **Starry night** | % | this evening, tomorrow evening (18:00–00:00; also as the evening slot) | Will the evening (18:00–00:00) have at least 4 clear hours (20 % of cloud or less) near the summit? | A starry sky for a night walk or stargazing. |
| ☀️ Sky | **Full sun** | hours of sun (median) | whole day (09:00–17:00), morning, lunchtime, afternoon | How many hours of the slot will be sunny at mid-mountain (little cloud, strong sunlight; daylight hours only)? | Sunglasses and sunscreen: the light is at its best. |
| 🧣 Comfort | **Mild day** | % | today, tomorrow (whole day) | Will the ski day (09:00–17:00) reach +5 °C at mid-mountain, with wind under 20 km/h and at least 5 sunny hours? | Picnic weather on the slopes. |
| 🧣 Comfort | **Wind chill** | felt °C (median), with the wind chill risk | whole day (09:00–17:00), morning, lunchtime, afternoon | How cold will it feel near the summit at the coldest of the slot (wind chill: temperature and wind together)? With Environment Canada's risk: moderate from −10 °C, high from −28 °C (frostbite in 10 to 30 minutes)… | Cover every bit of skin: frostbite comes fast in the wind. |
| 🚗 Getting there | **Chains needed** | Yes / Possible / No | today, tomorrow (whole day) | Will at least 2 cm of snow fall on the access road, at the bottom of the resort, from 20:00 the evening before to 10:00? | Fit chains or snow socks; leave earlier. Winter equipment is compulsory in the mountains anyway. |
| 🚗 Getting there | **Lifts in the wind** | km/h of wind (median), with light / strong / closures likely | whole day (09:00–17:00), morning, lunchtime, afternoon | How strong will the mean wind be near the summit at the windiest of the slot? Gusts are often 1.5 to 2 times stronger: closures likely from 45 km/h. | Top lifts may slow down or close: plan for the lower slopes. |
| ⚠️ Safety | **Avalanche danger** | level 1 to 5 of the official bulletin, in its European colour | today, tomorrow (whole day) | What danger level does Météo-France's avalanche bulletin give for the resort's massif, at the elevation of its summit? Relayed as is, never computed by Bluebird: a blue rosette next to the title says so. Before 4 pm, tomorrow shows the trend given the day before, then the new bulletin. | The back of the tile gives the name of each level and what to do, and a link to the full official bulletin (opens in a new tab). Always read it before going off-piste, and carry a transceiver, shovel and probe. |
| ⚠️ Safety | **Wind-blown snow** | Yes / Possible / No | today, tomorrow (whole day) | Has at least 10 cm of snow fallen near the summit in the 48 hours before 09:00, with wind reaching 30 km/h since? | Wind slabs likely off-piste. Always read the avalanche bulletin first. |

A **white day** ("jour blanc") is a day without visible relief. Hour by hour
over the ski day (09:00–17:00), Bluebird counts an hour as white when the
resort is inside the cloud (humidity of at least 98 % and low cloud of at
least 90 %), when at least 0.5 cm of snow falls per hour, or in flat light
(sunlight below 30 % of what a clear sky would give at that hour). A day with
at least 6 white hours out of 8 is a white day.

A **bluebird day** is the opposite: fresh snow and a clear sky. An hour of
the ski day is sunny when clouds cover at most 30 % of the sky and sunlight
reaches at least 60 % of what a clear sky would give at that hour (early and
late hours, when the sun is very low, only need the clear sky). It takes at
least 6 sunny hours out of 8, after at least 15 cm of snow in the 36 hours
before 09:00.

Some indicators work around missing data, so read them as estimates:
**Chains needed** places the road at the bottom of the resort and brings
the mid-mountain temperature down to it (0.65 °C warmer per 100 m lower);
**Lifts in the wind** uses the mean wind, as the scenarios have no gusts;
**Sunset** and **Starry night** use the cloud cover of the whole air column,
so a sea of clouds below the summit counts as cloud.

### Rewind 25/26 (season review)

Values over the 2025/26 season (1 December 2025 to 1 May 2026, Pyrenees),
computed once from archived forecasts, under the red **Rewind 25/26** filter.

| Indicator | Question | Value |
|---|---|---|
| **Most snow** | Which resort got the most snow over the whole season, at mid-mountain? | metres of snow fallen |
| **Longest snowfall** | Which resort had the longest continuous snowfall? A lull of an hour does not interrupt it. | hours |
| **Most snow on the slopes** | Which ski area got the most snow, on average over points spread along its pistes? | metres of snow fallen |
| **Most off-piste snow** | Which resort got the most snow in the terrain around its ski area? | metres of snow fallen |
| **Ideal snow cover** | On what share of the season's days was the snowpack deeper than 70 cm on average over the slopes? That is the ideal cover, smoothing out the bumps of the terrain, and powder paradise when the snow is fresh. | % of the season's days |
| **Fewest white days** | Which resort had the fewest white days on its slopes over the season (same definition as above, on points along the pistes)? The resort with the fewest comes first. | days |

### Future indicators

Ideas under study, not yet on the site, by category. The most likely next
ones are marked ⭐. Each will be checked against the data really available
before it is built.

- **When**: *6 h* = a probability for today and tomorrow, refreshed every 6
  hours; *Season* = a season review (Rewind); *History* = since the data
  exist (weather reanalyses back to 1950, checked against Météo-France snow
  observations; their grid is coarser than the daily model, so they compare
  resorts and decades, they are not measurements).
- **For**: the activities it matters to: alpine skiing, snowshoeing,
  cross-country skiing, village (non-skiers), or everyone.

#### ❄️ Snow

| Indicator | When | For | Question |
|---|---|---|---|
| **Rain at the resort** ⭐ | 6 h | Everyone | Chance of rain up to the summit, making a wet day and heavy snow. |
| **Snow on the ground** ⭐ | 6 h | Everyone | How deep the snow is on the slopes today, and whether it is building up or melting. |
| **Snow in the village** | 6 h | Village | Chance that the resort village wakes up white tomorrow (sledging, postcard views). |
| **Rain-snow line** ⭐ | 6 h | Everyone | At which altitude snow turns to rain today and tomorrow, estimated from the temperatures at mid-altitude and at the summit. |
| **Snow that lasts** | 6 h | Everyone | Will the fresh snow survive the next 24 hours, with no thaw or rain right after it? |
| **Powder days** ⭐ | Season | Alpine skiing, snowshoeing | Days with 20 cm or more of new snow in 24 hours. |
| **Biggest storm** | Season | Everyone | The largest snowfall over 72 hours, with its dates. |
| **Natural snow season** | Season | Everyone | First and last day with at least 30 cm of snow on the ground, and the number of days in between. |
| **Peak snowpack** | Season | Everyone | The deepest snow on the ground and its date. |
| **Rain days at the resort** | Season | Everyone | Days of rain up to the summit in mid-season. |
| **Snow cannon nights** | Season | Alpine skiing | Nights cold and dry enough to make snow. |
| **Slopes vs off-piste gap** | Season | Alpine skiing | Resorts where the terrain around the slopes got much more snow than the slopes. |
| **Best week** | Season | Everyone | The week of the season when you had to be there, per resort. |
| **First and last snow** | Season | Everyone | The dates of the season's first and last snowfall at each resort. |
| **This season in history** ⭐ | History | Everyone | Where the current season ranks since 1950 ("the 12th snowiest"), updated every day. |
| **Climate trend** ⭐ | History | Everyone | How the number of snow days changes per decade at each resort. |
| **Snow reliability** | History | Everyone | Share of seasons with at least 100 days of enough snow: useful to choose a season pass. |
| **When to go?** | History | Everyone | For each week of the season, the historical chance of good conditions at each resort. |
| **Snow at Christmas** | History | Everyone | Historical chance of at least 30 cm of snow on the ground on 25 December. |
| **Records** | History | Everyone | Biggest 24-hour snowfall, biggest storm, coldest season since 1950. |
| **Later openings** | History | Everyone | Average date of the first good snow cover, decade by decade. |
| **Rising rain-snow line** | History | Everyone | Average winter altitude of the 0 °C level, decade by decade. |
| **Our success rate** | History | Everyone | How well Bluebird's past probabilities matched the snow that fell ("when we say 70 %, it snows 68 % of the time"). |

#### 🎿 Snow quality

| Indicator | When | For | Question |
|---|---|---|---|
| **Wax of the day** | 6 h | Cross-country skiing | Snow temperature and humidity on the tracks, to choose the right wax. |
| **Off-piste crust** | 6 h | Off-piste, touring | Rain or a thaw then a refreeze: a breakable crust off-piste ("Hard snow" only covers the groomed slopes). |
| **Supportive snow** | 6 h | Snowshoeing, touring | Snow that carries your weight, or snow you sink into. |
| **Coldest morning and freeze-thaw days** | Season | Everyone | The season's coldest morning and the number of spring-snow days. |

#### ☀️ Sky

| Indicator | When | For | Question |
|---|---|---|---|
| **Sea of clouds** ⭐ | 6 h | Everyone | Chance that the top of the resort is in the sun above a sea of clouds while the valley stays grey. |
| **Best time slot** | 6 h | Everyone | The best hours of the day per resort, combining visibility, sun and wind. |
| **Summit in the clouds** ⭐ | 6 h | Alpine skiing | The top of the ski area is in the cloud while mid-altitude is clear: better stay on the lower slopes. |
| **Full moon night** | 6 h | Snowshoeing, touring | Full moon and a clear sky for a night outing. |
| **Sunrise** | 6 h | Touring, snowshoeing | A visible sunrise from the top, for dawn outings. |
| **Sunniest resort** ⭐ | Season | Everyone | Which resort got the most sunshine over the season (the sunlight is already stored)? |
| **Bluebird days** ⭐ | Season | Everyone | How many bluebird days each resort had. |
| **Sunset evenings** | Season | Everyone | How many evenings offered a visible sunset from the ski area. |
| **Sea-of-clouds days** | Season | Everyone | How many days the resort stood above a sea of clouds. |
| **Longest bluebird streak** | History | Everyone | The record number of sunny days in a row. |

#### 🧣 Comfort

| Indicator | When | For | Question |
|---|---|---|---|
| **UV and sunburn** | 6 h | Everyone | Peak UV at altitude, made stronger by the snow's reflection. |
| **Village weather tonight** | 6 h | Village | Rain, snow and temperature in the resort village this evening. |

#### 🚗 Getting there

| Indicator | When | For | Question |
|---|---|---|---|
| **Expected crowds** | 6 h | Everyone | Crowd index from school holidays by zone, weekends and good weather. |
| **Chains on the way back** | 6 h | Everyone | Snow on the access road at the end of the day, for the drive home ("Chains needed" looks at the morning). |
| **Black ice** ⭐ | 6 h | Everyone | Rain falling on frozen ground: slippery roads and slopes. |
| **Lifts stopped by wind** | Season | Alpine skiing | Days when the wind would have closed the top lifts. |
| **Chain days** | Season | Everyone | Mornings when chains would have been needed on the access road. |
| **Holiday luck** | Season | Everyone | Which school-holiday zone (A, B or C) had the best conditions. |
| **Weekend index** | Season | Everyone | Share of weekends with good conditions: what most skiers actually live. |

#### ⚠️ Safety

Never a replacement for the official avalanche bulletin (BERA).

| Indicator | When | For | Question |
|---|---|---|---|
| **Ski touring and snowshoe start time** | 6 h | Touring, snowshoeing | Best start and return times for an outing (night freeze, warming, avalanche risk). |
| **High avalanche risk days** | Season | Off-piste, touring, snowshoeing | Days with an avalanche danger level of 4 or 5. |

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
**reliability index** for the slot: the average reliability of all resorts
for that indicator (high counts fully, medium half, low not at all).

The high-resolution Météo-France model (AROME) is shown next to it as a
second opinion.

Fixed facts about each resort (position, elevations, grooming and opening
times, pistes and lifts) are stored with the project and refreshed at most
once a season. Only the weather is fetched at each update, with a single
request per weather service for all resorts at once.

**Rewinds** use a different source: the archived hour-by-hour forecasts of
Météo-France's high-resolution model (AROME, 1.5 km grid), via Open-Meteo,
once the season is over. For each resort Bluebird takes the resort point at
mid-mountain, points spread along its pistes (from OpenStreetMap) and points
in a circle around its ski area. The season's hourly data is stored with the
project once and for all, so the rankings never change and new season
indicators can be added later without fetching it again. The snow depth on
the ground comes from the German weather service's ICON model (Météo-France's
archive does not include it), on a coarser grid of about 7 km.

The **avalanche danger** is not a forecast of Bluebird: it is the level of
Météo-France's avalanche risk bulletin (BRA), written by its forecasters with
the observers of the snow and weather network. Météo-France publishes one
bulletin per avalanche massif every day around 4 pm, from early November to
late May, for the next day. Each resort gets the bulletin of the massif it
lies in (checked against Météo-France's official massif outlines), at the
elevation of its summit when the level differs above and below a given
altitude. When the level changes during the day, or differs between the two
sides of the massif, Bluebird keeps the higher one. Out of season there is no
bulletin and no avalanche tile. Source: Météo-France, Licence Ouverte.

### How the home page is chosen

With no filter chosen, Bluebird picks the tiles itself. You never see a
score: the tiles simply come in the right order.

1. **The bluebird day always comes first**, whatever its chance: it is what
   the site is about.
2. **Alerts** come next: an avalanche danger of 4 (high) or 5, lifts in
   strong wind (60 km/h or more), chains needed ("Oui"), wind-blown snow
   ("Oui"), a felt temperature of −28 °C or colder.
3. **Then every other indicator** of today and tomorrow, best first. Each
   one gets a mark from four things:
   - **how much it matters** to a skier: fresh snow and powder before a
     sunset or a starry night;
   - **how strong the values are** among the three best resorts of your
     place: 50 cm of snow beats a 12 % bluebird day. Below a minimum the
     tile is left out (no "Snow 3 cm" on the home page);
   - **the right moment**: the time slot in progress before the later ones,
     the whole day mostly in the morning, the sunset in the afternoon,
     **tomorrow only from 17:00** (when the lifts close), except a road or
     lift alert for tomorrow, shown from noon to plan the trip;
   - **how reliable** the forecast is: scenarios that agree, fresh data, most
     resorts of the place with a value.
4. One tile per indicator (its best moment), no more than two of the same
   category among the first six, and **50 tiles at most**, so the page ends
   and the bottom links stay within reach.
5. If nothing stands out, the page shows the bluebird day, snow, on-piste
   powder and white day.

The order changes when new forecasts arrive and when a time slot ends, never
while you are looking at it.

| Indicator | Shown on the home page from | Full strength at | Alert from |
|---|---|---|---|
| Bluebird day | always (first) | 70 % | — |
| Snow alert | 20 cm in 36 h | 50 cm | — |
| Snow | 5 cm in the day (2 cm in a time slot) | 30 cm (15 cm in a slot) | — |
| On-piste powder | 5 cm since grooming | 20 cm | — |
| Off-piste powder | 30 % | 70 % | — |
| Avalanche danger | level 3 (considerable) | level 4 (high) | level 4 |
| Lifts in the wind | 45 km/h | 70 km/h | 60 km/h |
| Chains needed | Possible | Oui | Oui |
| Wind-blown snow | Possible | Oui | Oui |
| Full sun | 50 % | 90 % | — |
| White day | 40 % | 80 % | — |
| Spring snow | 40 % | 80 % | — |
| Hard snow | Possible | Oui | — |
| Wind chill | −15 °C | −30 °C | −28 °C |
| Heavy snow | 40 % | 80 % | — |
| Easy conditions | 50 % | 90 % | — |
| Mild day | 50 % | 90 % | — |
| Sunset | 50 % | 90 % | — |
| Snow cannons | 3 cold hours | 8 cold hours | — |
| Starry night | 50 % | 90 % | — |

The indicators are listed from the most to the least important. Values are
the mean of the three best resorts of your place.

### Update schedule

- Every 6 hours: around **00:00, 06:00, 12:00 and 18:00** (Paris time), from
  November to May.
- Updates can arrive a few minutes late.

## Features

### Available now

- Pyrenees: 18 French resorts, from La Pierre Saint-Martin to Formiguères.
- 20 indicators in six categories, for each time slot or day of today and
  tomorrow (see [Available indicators](#available-indicators)), each shown
  as an amount (cm, hours, °C, km/h), a Yes / Possible / No, a level of an
  official scale or a percentage: snow, snow alert, snow cannons; powder on
  piste and off-piste, spring snow, hard snow, heavy snow, easy conditions;
  white day, bluebird day, sunset, starry night, full sun; mild day, wind
  chill; chains needed, lifts in the wind; avalanche danger (the official
  Météo-France level), wind-blown snow.
- Updated every 6 hours; tiles of slots that are over disappear on their own.
- A service status page (linked from the footer), and the last valid values kept (and flagged)
  when an update fails.
- Betting-style tiles: top three resorts as odds buttons with their
  reliability dots, full ranking on demand, optional odds, and a coloured
  time badge for the day and moment of each tile.
  Three tile sizes: large tiles whose picture fills the card, tiles with a
  picture band on top, and compact tiles without a picture for the
  indicators lower on the page. The picture is a photo of the leading resort
  when we have one we may publish, otherwise a drawing.
- **Live webcam link**: on the **Bluebird day** tile of today, a red LIVE
  badge appears in the top left corner, under the time badge, when the leading resort has a webcam
  at the top of its ski area and a chance of at least 60 %, while the day is
  in progress. It opens the resort's webcam on its provider's website
  (Skaping) in a new tab, to check the sky with your own eyes. Never for
  tomorrow, since a webcam only shows the present. First resort with
  webcams: Cauterets.
- Two-sided tiles: the back explains the indicator, gives the exact date and hours of its slot, and the reliability for that slot.
- Filters in levels, like a music app: category of indicator (Snow, Snow
  quality, Sky, Comfort, Getting there, Safety) or the Rewind, then sub-category, then day (Today, Tomorrow), then time
  slot (the only level showing time-slot tiles); **Moods** for the wish of
  the day (On site: Freerider, Carver, Dolce vita, Snowplough, Little ones;
  On the way: heading up or down tomorrow); a home page led by the
  bluebird day, then the tiles that matter most right now (big snowfalls,
  alerts, the next time slot, tomorrow from the evening), up to 50.
- **Rewind 25/26**: the review of the 2025/26 season in the Pyrenees (most
  snow, longest snowfall, most snow on the slopes, most off-piste snow, ideal
  snow cover days, fewest white days), behind its own red filter.
- Place buttons above the filters (mountain range, then département, then
  linked ski area when there is one), a flag button for the language
  (French, English or Spanish), and next to it an appearance button: System
  (follows your phone, the default), Light or Dark, its icon showing your
  choice. All are remembered on your device.
- More room for the tiles while you scroll: scrolling down folds the place
  and filter buttons into one line that recalls your choices (the place, and
  the filter if you chose one); scrolling up, or tapping that line, brings
  them back. The logo and the appearance and language buttons stay.
- A clean "starry night" design: midnight blue and electric blue, frosted
  glass cards and odds buttons, one very legible free typeface (Sora) for
  titles, numbers and text, and the sporty italic kept for the logo. The large
  tiles show their picture across the whole card. Light and dark mode follow
  your phone's setting unless you choose one, without background animation.
- A ski goggle logo at the top left whose lens changes colour with the time
  of day in the resorts: peach and lavender at dawn (from 6 am), orange
  during the day (from 9 am), pink and violet at dusk (from 5 pm), deep blue
  at night (from 8 pm). The browser tab icon and the home-screen icon always
  show the daytime orange lens.
- Winter photos of the ski areas under free licences, mostly from Wikimedia
  Commons: 15 of the 18 resorts have two or three; Porté-Puymorens,
  Ascou-Pailhères and Le Mourtis show an illustration until a free winter
  photo is found. Each photo is credited on the back of its tile and in the
  legal notice.
- A short footer: the GitHub logo (link to the project's source code) and
  small links to **About**, **Reading a tile** (an example tile, front and
  back, with numbered marks explaining every part: the time badge and its
  colours, the LIVE badge, the values and reliability dots, the ranking, and
  each section of the back), **Service status**, **Legal notice** and
  **Privacy** (which lists the settings kept on your device and can delete
  them). Each opens as
  a full-screen page over a blurred background, sliding up from the bottom;
  close it with the **×**, the Escape key or your phone's back gesture.
- Works on any modern phone browser; add it to your home screen for an
  app-like experience.
- Respects "reduce motion" and "reduce transparency" accessibility settings.

### Coming next

- New indicators: see [Future indicators](#future-indicators).
- A Rewind for each new season, from the 2026/27 season on.
- **More moods**: **Village side** (On site, for those who stay in the
  village: spa, shops, terraces; it needs the weather down in the village)
  and **Heading up this weekend** (On the way, once weekend forecasts
  exist). Later, a mood could weigh some indicators differently (−8 °C felt
  already matters for a child).
- **Webcam picture in the tile**: the live image of the leading resort's
  webcam as the picture of the tile, today only and for the indicators the
  camera's position suits (the summit camera for a bluebird day first).
  It needs the agreement of the webcam's owner: until then, the tile only
  links to the webcam.
- **A page per resort**: the same tiles for a single resort, with its own
  values instead of a ranking, topped by one sentence summing up its day
  ("Demain, grand beau après 20 cm").
- **Warmer texts**: every indicator explained like a friend would, without
  losing any information: the question it answers ("Demain, neige fraîche
  et grand ciel bleu ?"), a practical tip, a verdict in words next to the
  number ("Foncez", "Ça se tente"), how it is computed in three simple
  steps (the technical details stay one tap away), and how far you can
  trust it ("les prévisions sont d'accord" or "elles hésitent").
- **Tile effects**: a light animation between the picture and the text of
  a tile. Some stay on, like snow falling on the Snow tiles; others play
  once, like a glint of sun across the Bluebird day tile when it comes into
  view. None for people who reduce motion on their phone.
- **Odds that move**: an arrow ↑ or ↓ on each odds button when the
  probability rose or fell since the previous update, like the odds of a
  betting app.
- **Calendar alerts**: subscribe in your calendar app to a resort or an
  indicator, and get an event such as "Journée bluebird probable demain à
  Cauterets (78 %)".
- **My resorts**: a star on your favourite resorts, remembered on your
  device, and a "Mes stations" button in the place line.
- **Share a tile**: send a tile as an image, or a link that reopens the
  same place and filters.
- **Offline mode**: install the site on your phone; it keeps the last update
  for when there is no network in the mountains.
- **Yesterday's verdict**: what we forecast against what really happened
  ("we said 12 cm, 9 cm fell"), resort by resort, kept day after day to
  make the percentages better over time.
- **Around me**: a first button "Autour de moi" at the far left of the place
  line. It keeps the resorts less than one hour away **by road** from where
  you are, the nearest first, and every ranking then covers only them. Road
  time, not distance: in the mountains, 10 minutes as the crow flies is often
  30 minutes by car, and passes closed in winter are taken into account.
  Your position is asked only when you tap the button and never leaves your
  phone.
- A comparator of two resorts and a season calendar for the Rewind.
- A home page that also learns what you open most (stored only on your
  phone) and that highlights what changed since yesterday.
- **Animated banners**: for a resort without a photo we may publish, the
  banner of a tile shows a small animation that matches the indicator
  instead of a still drawing: falling snow, a bright sun, drifting fog,
  twinkling stars, a setting sun, wind in the lift cables… Still images for
  people who reduce motion on their phone.
- **Stories for your place**: a full-screen summary of the day for the place
  you chose (massif, département or ski area), one screen per highlight
  (snow tonight, bluebird day tomorrow, the windiest lifts…) with the leading
  resort, its value and the next two; tap or swipe to go to the next story.
- Days of high avalanche danger (level 4 or 5) in the season reviews, from
  Météo-France's public archive of the bulletins.
- Resort opening status (open lifts and pistes).
- Slope orientation and steepness to refine the powder estimate
  (north-facing slopes keep powder longer).
- Weekend and week-long slots (with a matching filter level).
- **Planned filters**, one level at a time (at most five):
  1. **Activity**: alpine skiing, snowshoeing, cross-country skiing, village
     (non-skiers), next to **Rewind 25/26** (unchanged). Snowshoeing and
     cross-country need their own sites (nordic areas and trails), which
     will be added to the resort list first.
  2. **Category**: Snow, Snow quality, Sky, Comfort, Getting there, Safety
     (see [Categories](#categories); the level-1 filters until the activity
     filter arrives), only those with indicators for the activity.
  3. **Terrain**, for alpine skiing: easy pistes (green and blue), steeper
     pistes (red and black), off-piste.
  4. **Day**: today, tomorrow (and later the weekend).
  5. **Time slot**: morning to night.

  A level with a single choice is applied on its own and skipped. There will
  still be no skier level (beginner to expert): the weather is the same for
  everyone, but it differs by terrain, which the piste map tells apart. The
  **Moods** are not levels but the wish of the day: Snowplough and Little
  ones gather the conditions that matter to beginners and children, not a
  skiing technique.
- A 7-day trend tile and a map of the ski areas (piste and lift data from
  OpenStreetMap is already collected and refreshed once a season).
- More mountain ranges: Northern and Southern Alps, Massif Central, Vosges,
  Jura, with their départements and linked ski areas, and resorts across the
  borders marked with a small flag: first the Spanish and Andorran Pyrenees
  (Baqueira-Beret, Formigal, Cerler, La Molina, Grandvalira…), then
  Switzerland and Italy for the Alps.
  Météo-France's avalanche massifs (Haute-Bigorre, Vanoise…) will be kept as
  data for the avalanche indicator, not as a navigation level.
- Checking past forecasts against observed snow to make the percentages more
  accurate, from a day-to-day history of every forecast, resort by resort
  and indicator by indicator.
- Much later, not a priority: a connector so that AI assistants such as
  Claude can ask Bluebird for its forecasts.

## Limits and safety

- **Bluebird is a planning aid, not an avalanche bulletin.** Before any
  off-piste outing, read the official Météo-France avalanche bulletin (BERA),
  carry avalanche safety equipment and know how to use it. The **Avalanche
  danger** tile relays the bulletin's level only: the bulletin also says
  which slopes and aspects are concerned and how the danger changes during
  the day. The **Wind-blown snow** tile is a warning sign, never a danger
  level.
- **Chains needed** estimates the road from the resort's own forecast; it
  does not know snow clearing nor the road's real elevation. Mountain winter
  equipment rules apply whatever it says.
- Forecasts are uncertain, mountain weather even more so. Local effects
  (wind-loaded slopes, sun, sheltered forests) are not captured.
- White days are estimated from humidity, cloud, snowfall and sunlight: the
  models do not forecast visibility. A local fog patch or a sea of clouds
  below the resort may be missed.
- Rewind figures come from a weather model's archived forecasts, not from
  snow measurements at the resorts. They compare resorts fairly with each
  other but are not official snowfall records. Resorts that share pistes in
  the map data (Peyragudes/Val Louron, Font-Romeu/Les Angles) get similar
  slope values.
- Resort coordinates and elevations are approximate; grooming and opening
  times are typical values, not each resort's daily schedule.
- The LIVE webcam link only shows the present: it is offered for today's
  bluebird day while the day is in progress, never as a forecast. The
  webcam itself belongs to its provider and is not shown on Bluebird.
- Powder on piste assumes grooming ends around 02:00 and lifts open at 09:00
  unless configured otherwise for a resort.

## FAQ

**Why is a resort at 0 % when it's snowing outside?**
The forecast models disagree with reality sometimes, and the tile only counts
snow inside its time window and above its threshold (for example 5 cm since
grooming).

**Why is an indicator missing from the home page?**
Its values are too low to matter today, or it is not the right moment yet
(tomorrow's tiles come from 17:00). Choose its category in the filters to see
it anyway.

**Why don't the tiles agree?**
They answer different questions, at different elevations and time windows.
Heavy snow overnight with strong wind can give a high "powder on piste" and
a low "off-piste powder".

**Is the site free?**
Yes. It uses free, openly licensed data (Open-Meteo, CC BY 4.0;
OpenStreetMap, ODbL) for non-commercial use.

**Does it track me?**
No account, no analytics, no cookies. Your language, appearance, place and
filter are stored only in your browser, never sent anywhere. They have no
expiry date, but Safari clears them after 7 days without a visit (unless the
site is on your home screen). The **Privacy** page (link at the bottom of the
site) explains it and has a button to delete them at once.
