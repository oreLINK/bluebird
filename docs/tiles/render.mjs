#!/usr/bin/env node
/**
 * Renders the mockups of TILES.md into docs/tiles/*.svg.
 *
 *   node docs/tiles/render.mjs
 *
 * Every mockup is built from the same parts and the same example data (the
 * bluebird day of a January morning in the Pyrenees), so two pictures differ
 * only by the axis value they illustrate (the `scale` display uses the
 * avalanche danger instead, whose values are levels). Colours are the light-mode tokens
 * of web/src/styles/tokens.css (design "Nuit étoilée", TILES.md §9). The texts
 * are the French UI, as on the site.
 * Generated files: edit this script, never the SVGs.
 */
import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = dirname(fileURLToPath(import.meta.url));

// ------------------------------------------------------------- tokens (light)
const C = {
  page: '#e9eef7',
  surface: '#fbfcfe',
  line: '#d8e0ee',
  ink: '#0a1630',
  inkFaint: '#56688a',
  brand: '#0a1f5c',
  link: '#1d4ed8',
  glassEdge: '#ffffff',
  pillBg: '#e7edfa', // --pill-bg at 62 % over the card
  pillInk: '#0a1f5c',
  pillBorder: '#cfdcf6',
  probHigh: '#1d4ed8',
  track: '#dce4f2',
  rewind: '#c8102e',
  rewindInk: '#b00d27',
  live: '#d0021b',
  staleBg: '#fff1d6',
  staleInk: '#7a4b00',
  planned: '#8a99ad',
  whenToday: '#0b3b66', // --when-today (day cell of the time badge, white text)
  whenTomorrow: '#0f4c45', // --when-tomorrow
  verified: '#1d6ff2', // --verified-bg (certified rosette)
  // --danger-<n>-bg / -ink: European avalanche danger scale (`display: scale`).
  danger: {
    1: ['#3fa34d', '#06200c'],
    2: ['#ffe11a', '#3a2f00'],
    3: ['#ff9317', '#331800'],
    4: ['#dc0712', '#ffffff'],
    5: ['#dc0712', '#ffffff'],
  },
  danger5Alt: '#120a0a', // --danger-5-alt: checkerboard, outline and plate of level 5
};

// ------------------------------------------------------------- example data
const TITLE = 'Journée bluebird'; // the period is on the time badge, never in the title
// A whole day: the time badge shows the day alone, in the colour of the day.
const TODAY = { day: 'AUJ.', color: C.whenToday };
const TOMORROW = { day: 'DEM.', color: C.whenTomorrow };
const LIVE = [
  { name: 'Cauterets', value: '82 %', share: 0.82 },
  { name: 'Gourette', value: '64 %', share: 0.64 },
  { name: 'Peyragudes', value: '41 %', share: 0.41 },
];
// A `scale` display (avalanche danger): the level on the colour of its step.
const AVALANCHE_TITLE = "Risque d'avalanche";
const AVALANCHE = [
  { name: 'Cauterets', value: '5', share: 1, level: 5 },
  { name: 'Gourette', value: '4', share: 0.8, level: 4 },
  { name: 'Peyragudes', value: '3', share: 0.6, level: 3 },
];
const REWIND = [
  { name: 'Cauterets', value: '4,43 m', share: 1 },
  { name: 'Gourette', value: '3,90 m', share: 0.88 },
  { name: 'Peyragudes', value: '3,12 m', share: 0.7 },
];

// ------------------------------------------------------------- geometry
const W = 320;
const H = 340;
const X = 16; // card left
const Y = 16; // card top
const CW = 288; // card width
const R = 24; // card radius (--radius-l)
const RI = 14; // odds button radius (--radius-m, scaled)
const FONT = "Sora, 'Segoe UI', Helvetica, Arial, sans-serif";
const DISPLAY = FONT;

const esc = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** A rectangle with all four corners rounded. */
const rounded = (x, y, w, h, r) =>
  `M${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h - r} Q${x + w},${y + h} ${x + w - r},${y + h} H${x + r} Q${x},${y + h} ${x},${y + h - r} V${y + r} Q${x},${y} ${x + r},${y} Z`;

/** Rounded top corners only (for an image band at the top of the card). */
const topRounded = (x, y, w, h, r) =>
  `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;

function text(x, y, s, { size = 11, weight = 500, fill = C.ink, anchor = 'middle', display = false } = {}) {
  const family = display ? DISPLAY : FONT;
  const tracking = display ? ` letter-spacing="${(-0.02 * size).toFixed(2)}"` : '';
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${size}" font-weight="${display ? 700 : weight}"${tracking} fill="${fill}" text-anchor="${anchor}">${esc(s)}</text>`;
}

/** The glass card: near-white surface, light edge, soft shadow (`.card-body`). */
function card(h) {
  return `<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="8" stdDeviation="9" flood-color="#0f172a" flood-opacity=".10"/></filter></defs>
  <rect x="${X}" y="${Y}" width="${CW}" height="${h}" rx="${R}" fill="${C.surface}" stroke="${C.line}" filter="url(#sh)"/>
  <path d="M${X + R},${Y + 1} H${X + CW - R}" stroke="${C.glassEdge}" stroke-width="1.5"/>`;
}

// ------------------------------------------------------------- images
let uid = 0;
/** Illustration (`visual: scene`): flat ridges and snow, like BannerArt.svelte. */
function scene(y, h, clip) {
  const id = `s${++uid}`;
  const b = y + h;
  return `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#123b7a"/><stop offset="1" stop-color="#2f6fc0"/></linearGradient></defs>
  <g clip-path="url(#${clip})">
    <rect x="${X}" y="${y}" width="${CW}" height="${h}" fill="url(#${id})"/>
    <circle cx="${X + 236}" cy="${y + h * 0.42}" r="13" fill="#dbe9fb"/>
    <path d="M${X},${b - h * 0.42} L${X + 40},${b - h * 0.55} L${X + 78},${b - h * 0.46} L${X + 120},${b - h * 0.62} L${X + 150},${b - h * 0.5} L${X + 196},${b - h * 0.66} L${X + 240},${b - h * 0.48} L${X + CW},${b - h * 0.56} V${b} H${X} Z" fill="#8cc4f5"/>
    <path d="M${X},${b - h * 0.2} L${X + 50},${b - h * 0.27} L${X + 100},${b - h * 0.21} L${X + 150},${b - h * 0.3} L${X + 210},${b - h * 0.22} L${X + CW},${b - h * 0.28} V${b} H${X} Z" fill="#eaf3fd"/>
  </g>`;
}

/** Photo (`visual: photo`): a sunny snowy peak, shaded like a picture. */
function photo(y, h, clip) {
  const id = `p${++uid}`;
  const b = y + h;
  return `<defs>
    <linearGradient id="${id}a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1f5fbf"/><stop offset="1" stop-color="#7fb6ec"/></linearGradient>
    <linearGradient id="${id}b" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#e9eef5"/><stop offset="1" stop-color="#9fb2c9"/></linearGradient>
  </defs>
  <g clip-path="url(#${clip})">
    <rect x="${X}" y="${y}" width="${CW}" height="${h}" fill="url(#${id}a)"/>
    <path d="M${X},${b} L${X + 70},${b - h * 0.45} L${X + 150},${y + h * 0.16} L${X + 230},${b - h * 0.5} L${X + CW},${b - h * 0.3} V${b} Z" fill="url(#${id}b)"/>
    <path d="M${X + 150},${y + h * 0.16} L${X + 168},${b - h * 0.48} L${X + 190},${b - h * 0.38} L${X + 230},${b - h * 0.5} L${X + 150},${y + h * 0.16} Z" fill="#7f93ad" opacity=".55"/>
    <path d="M${X + 96},${b - h * 0.3} L${X + 104},${b - h * 0.36} L${X + 112},${b - h * 0.29} M${X + 40},${b - h * 0.12} L${X + 120},${b - h * 0.2} L${X + 200},${b - h * 0.1}" stroke="#5e7088" stroke-width="1.4" fill="none" opacity=".7"/>
    <rect x="${X}" y="${b - h * 0.14}" width="${CW}" height="${h * 0.14}" fill="#f7fafd" opacity=".85"/>
  </g>`;
}

/** Webcam still (`visual: webcam`, planned): a 360° panorama strip with its time stamp. */
function webcam(y, h, clip) {
  const id = `w${++uid}`;
  const b = y + h;
  return `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d63d6"/><stop offset="1" stop-color="#9cc7f0"/></linearGradient></defs>
  <g clip-path="url(#${clip})">
    <rect x="${X}" y="${y}" width="${CW}" height="${h}" fill="url(#${id})"/>
    <circle cx="${X + 222}" cy="${y + 28}" r="9" fill="#fff8d8"/>
    <circle cx="${X + 222}" cy="${y + 28}" r="19" fill="none" stroke="#fff8d8" stroke-opacity=".45"/>
    <path d="M${X},${b - h * 0.36} L${X + 30},${y + h * 0.18} L${X + 58},${b - h * 0.5} L${X + 92},${b - h * 0.42} L${X + 130},${b - h * 0.6} L${X + 176},${b - h * 0.44} L${X + 214},${b - h * 0.5} L${X + 252},${b - h * 0.38} L${X + CW},${b - h * 0.52} V${b} H${X} Z" fill="#c7d3e1"/>
    <path d="M${X},${b - h * 0.18} Q${X + 140},${b - h * 0.34} ${X + CW},${b - h * 0.16} V${b} H${X} Z" fill="#f6f9fc"/>
    <path d="M${X + 70},${b} L${X + 92},${b - h * 0.44} M${X + 92},${b - h * 0.44} L${X + 150},${b - h * 0.28}" stroke="#55606e" stroke-width="2"/>
    <rect x="${X + 10}" y="${b - 22}" width="112" height="16" rx="3" fill="#000" opacity=".45"/>
    ${text(X + 16, b - 10, 'Les Crêtes · 10:00', { size: 9, fill: '#fff', anchor: 'start', weight: 600 })}
  </g>`;
}

const IMAGES = { scene, photo, webcam };

// ------------------------------------------------------------- parts
function helpButton(x, y, onImage) {
  const fill = onImage ? 'rgba(255,255,255,.24)' : C.pillBg;
  const ink = onImage ? '#fff' : C.pillInk;
  return `<circle cx="${x}" cy="${y}" r="13" fill="${fill}" stroke="${onImage ? 'rgba(255,255,255,.6)' : C.pillBorder}"/>${text(x, y + 4, '?', { size: 12, weight: 700, fill: ink })}`;
}

function badge(x, y, label, { bg, ink = '#fff', dot = false, icon = '' }) {
  const w = 18 + label.length * 6.4 + (dot ? 10 : 0) + (icon ? 14 : 0);
  let cx = x + 9;
  let parts = '';
  if (dot) {
    parts += `<circle cx="${cx + 3}" cy="${y + 10}" r="3" fill="${ink}"/>`;
    cx += 10;
  }
  if (icon === 'webcam') {
    parts += `<g fill="none" stroke="${ink}" stroke-width="1.3"><circle cx="${cx + 5}" cy="${y + 9}" r="4"/><circle cx="${cx + 5}" cy="${y + 9}" r="1.4"/><path d="M${cx + 2.5},${y + 13} l-1,3 h7 l-1,-3"/></g>`;
    cx += 14;
  }
  if (icon === 'rewind') {
    parts += `<path d="M${cx + 6},${y + 6} l-4,4 4,4 M${cx + 11},${y + 6} l-4,4 4,4" stroke="${ink}" stroke-width="1.5" fill="none"/>`;
    cx += 14;
  }
  if (icon === 'clock') {
    parts += `<g fill="none" stroke="${ink}" stroke-width="1.3"><circle cx="${cx + 5}" cy="${y + 10}" r="4.5"/><path d="M${cx + 5},${y + 7.5} v2.8 l2,1"/></g>`;
    cx += 14;
  }
  return `<g><rect x="${x}" y="${y}" width="${w}" height="20" rx="10" fill="${bg}"/>${parts}${text(cx, y + 14, label, { size: 9, weight: 800, fill: ink, anchor: 'start' })}</g>`;
}

/**
 * Time badge (TimeBadge.svelte) of a whole-day tile: the short day label in
 * the dark colour of the day (88 % over the card, 80 % on an image), white
 * text. Moments ("Dem. | Matin") add a soft second cell, not drawn here.
 */
function ticket(x, y, { day, color }, onImage) {
  const w = 12 + day.length * 6;
  return `<g><rect x="${x}" y="${y}" width="${w}" height="17" rx="4" fill="${color}" opacity="${onImage ? 0.8 : 0.88}"/>
  ${text(x + 6, y + 12, day, { size: 8.5, weight: 800, fill: '#fff', anchor: 'start' })}</g>`;
}

/** The three best stations as odds buttons, with their bars. */
function odds(y, items, { compact = false, rewind = false, overlay = false } = {}) {
  const boxH = compact ? 40 : 54;
  // Glass buttons; white glass on an image (full tiles); solid red for a Rewind.
  const bg = rewind ? C.rewind : overlay ? 'rgba(255,255,255,.2)' : C.pillBg;
  const border = rewind ? C.rewind : overlay ? 'rgba(255,255,255,.45)' : C.glassEdge;
  const ink = rewind || overlay ? '#fff' : C.pillInk;
  const bar = rewind ? C.rewind : C.probHigh;
  return items
    .map((it, i) => {
      const x = X + 16 + i * 88;
      if (it.level) return scaleOdds(x, y, it, boxH, compact);
      const dots = rewind
        ? ''
        : [0, 1, 2]
            .map((d) => `<circle cx="${x + 34 + d * 6}" cy="${y + boxH - 7}" r="2" fill="${d < 2 || i === 0 ? ink : overlay ? 'rgba(255,255,255,.35)' : '#9fb6d3'}"/>`)
            .join('');
      const name = text(x + 40, y + (compact ? 13 : 16), it.name, { size: 9.5, weight: 500, fill: ink });
      const value = text(x + 40, y + (compact ? 29 : 36), it.value, { size: compact ? 14 : 17, fill: ink, display: true });
      const trackFill = overlay ? 'rgba(255,255,255,.35)' : C.track;
      return `<rect x="${x}" y="${y}" width="80" height="${boxH}" rx="${RI}" fill="${bg}" stroke="${border}"/>${name}${value}${dots}
      <rect x="${x + 6}" y="${y + boxH + 7}" width="68" height="3" rx="1.5" fill="${trackFill}"/>
      <rect x="${x + 6}" y="${y + boxH + 7}" width="${68 * it.share}" height="3" rx="1.5" fill="${overlay ? '#fff' : bar}"/>`;
    })
    .join('');
}

/**
 * One odds button of a `scale` display: filled with the colour of the level
 * (`data-scale`), level 5 a red and black checkerboard with the number
 * outlined and the name and dots on a dark plate.
 */
function scaleOdds(x, y, it, boxH, compact) {
  const [bg, ink] = C.danger[it.level];
  const five = it.level === 5;
  const id = `k${++uid}`;
  const fill = five ? `url(#${id})` : bg;
  const pattern = five
    ? `<defs><pattern id="${id}" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="${bg}"/><rect width="6" height="6" fill="${C.danger5Alt}"/><rect x="6" y="6" width="6" height="6" fill="${C.danger5Alt}"/></pattern></defs>`
    : '';
  const nameY = y + (compact ? 13 : 16);
  const valueY = y + (compact ? 27 : 36);
  const plate = five
    ? `<rect x="${x + 12}" y="${nameY - 10}" width="56" height="13" rx="4" fill="${C.danger5Alt}" opacity=".84"/>${compact ? '' : `<rect x="${x + 27}" y="${y + boxH - 12}" width="26" height="10" rx="5" fill="${C.danger5Alt}" opacity=".84"/>`}`
    : '';
  const outline = five ? ` stroke="${C.danger5Alt}" stroke-width="3" paint-order="stroke"` : '';
  const value = `<text x="${x + 40}" y="${valueY}" font-family="${DISPLAY}" font-size="${compact ? 14 : 18}" font-weight="700" fill="${ink}" text-anchor="middle"${outline}>${esc(it.value)}</text>`;
  const dots = [0, 1, 2].map((d) => `<circle cx="${x + 34 + d * 6}" cy="${y + boxH - 7}" r="2" fill="${ink}"/>`).join('');
  return `${pattern}<rect x="${x}" y="${y}" width="80" height="${boxH}" rx="${RI}" fill="${fill}" stroke="${five ? C.danger5Alt : bg}"/>${plate}
  ${text(x + 40, nameY, it.name, { size: 9.5, weight: 600, fill: ink })}${value}${dots}
  <rect x="${x + 6}" y="${y + boxH + 7}" width="68" height="3" rx="1.5" fill="rgba(255,255,255,.35)"/>
  <rect x="${x + 6}" y="${y + boxH + 7}" width="${68 * it.share}" height="3" rx="1.5" fill="${bg}"/>`;
}

/** The "certified" rosette (CertifiedBadge.svelte): ten scallops, white check mark. */
function rosette(cx, cy, size = 18) {
  const k = size / 24;
  const points = [];
  for (let i = 0; i < 120; i++) {
    const a = (i / 120) * 2 * Math.PI;
    const r = 9.3 + 1.2 * Math.cos(10 * a);
    points.push(`${(cx + (r * Math.sin(a)) * k).toFixed(1)} ${(cy - (r * Math.cos(a)) * k).toFixed(1)}`);
  }
  const p = (dx, dy) => `${(cx + (dx - 12) * k).toFixed(1)} ${(cy + (dy - 12) * k).toFixed(1)}`;
  return `<path d="M${points.join('L')}Z" fill="${C.verified}"/><path d="M${p(7.7, 12.3)} L${p(10.6, 15.1)} L${p(16.3, 9.3)}" fill="none" stroke="#fff" stroke-width="${(2.3 * k).toFixed(2)}" stroke-linecap="round" stroke-linejoin="round"/>`;
}

/** Title centred with the rosette right after it (`.title-row`). */
function certifiedTitle(y, title, size, fill) {
  const width = title.length * size * 0.5; // Sora 700, approximate
  const start = X + CW / 2 - (width + 6 + size) / 2;
  return `${text(start, y, title, { size, fill, anchor: 'start', display: true })}${rosette(start + width + 6 + size / 2, y - size * 0.35, size)}`;
}

function seeAll(y, onImage = false) {
  const line = onImage ? 'rgba(255,255,255,.3)' : C.line;
  return `<line x1="${X + 14}" y1="${y}" x2="${X + CW - 14}" y2="${y}" stroke="${line}"/>
  ${text(X + CW / 2, y + 21, 'Voir les 18 stations  ⌄', { size: 11, weight: 700, fill: onImage ? '#fff' : C.link })}`;
}

function caption(s, planned) {
  const tag = planned ? `  ·  PLANNED` : '';
  return text(W / 2, H - 10, s + tag, {
    size: 10,
    weight: 600,
    fill: planned ? C.planned : C.inkFaint,
  });
}

function svg(body, label) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
<rect width="${W}" height="${H}" rx="14" fill="${C.page}"/>
${body}
</svg>
`;
}

// ------------------------------------------------------------- tiles
/**
 * One mockup. `format`: full | banner | compact; `scope`: ranking | station;
 * `visual`: scene | photo | webcam; `kind`: live | historical; `badge`:
 * webcam | stale | undefined; `planned`: grey caption tag.
 */
function tile({ format = 'banner', scope = 'ranking', visual = 'scene', kind = 'live', badge: corner, time = TODAY, planned = false, display = 'percent' }) {
  const rewind = kind === 'historical';
  const scale = display === 'scale'; // avalanche danger: certified, levels in colour
  const items = rewind ? REWIND : scale ? AVALANCHE : LIVE;
  const title = rewind ? 'Le plus de neige' : scale ? AVALANCHE_TITLE : TITLE;
  const titleInk = rewind ? C.rewindInk : C.ink;
  const clip = `c${++uid}`;
  // Same proportions as the site: image 13rem of a 23rem front (+ "see all"),
  // and one compact tile = half a banner tile minus half the gap.
  const cardH = format === 'compact' ? 140 : 292;
  const imageH = 150;
  let body = card(cardH);
  const clipPath = format === 'full' ? rounded(X, Y, CW, cardH, R) : topRounded(X, Y, CW, imageH, R);
  body += `<defs><clipPath id="${clip}"><path d="${clipPath}"/></clipPath></defs>`;

  /** Corner stack: time badge first (live tiles), then LIVE, Rewind or stale under it. */
  const corners = (onImage) => {
    const out = [];
    const x = X + 12;
    let y = Y + 12;
    if (!rewind) {
      out.push(ticket(x, y, time, onImage));
      y += 23;
    }
    if (rewind) out.push(badge(x, y, 'REWIND 25/26', { bg: C.rewind, icon: 'rewind' }));
    if (corner === 'webcam') out.push(badge(x, y, 'LIVE', { bg: C.live, dot: true, icon: 'webcam' }));
    if (corner === 'stale') out.push(badge(x, y, 'Données de 06:00', { bg: C.staleBg, ink: C.staleInk, icon: 'clock' }));
    return out.join('');
  };

  if (format === 'compact') {
    // A badge row level with the "?" button, then the title, then the odds.
    body += rewind ? badge(X + 12, Y + 13, 'REWIND 25/26', { bg: C.rewind, icon: 'rewind' }) : ticket(X + 12, Y + 15, time, false);
    body += helpButton(X + CW - 22, Y + 23, false);
    body += text(X + 14, Y + 54, title, { size: 15, fill: titleInk, anchor: 'start', display: true });
    if (scale) body += rosette(X + 14 + title.length * 15 * 0.5 + 12, Y + 49, 15);
    body += odds(Y + 62, items, { compact: true, rewind });
    body += seeAll(Y + 114);
  } else if (format === 'full') {
    // The image runs down to the bottom of the card, under the "see all" bar.
    body += IMAGES[visual](Y, cardH, clip);
    body += `<defs><linearGradient id="${clip}g" x1="0" y1="0" x2="0" y2="1"><stop offset=".28" stop-color="#050b1e" stop-opacity="0"/><stop offset=".68" stop-color="#050b1e" stop-opacity=".62"/><stop offset="1" stop-color="#050b1e" stop-opacity=".88"/></linearGradient></defs>`;
    body += `<path d="${rounded(X, Y, CW, cardH, R)}" fill="url(#${clip}g)"/>`;
    body += helpButton(X + CW - 24, Y + 24, true) + corners(true);
    body += scale ? certifiedTitle(Y + 162, title, 17, '#fff') : text(X + CW / 2, Y + 162, title, { size: 17, fill: '#fff', display: true });
    body += odds(Y + 176, items, { rewind, overlay: true });
    body += seeAll(Y + 258, true);
  } else {
    body += IMAGES[visual](Y, imageH, clip);
    body += helpButton(X + CW - 24, Y + 24, true) + corners(true);
    body += scale ? certifiedTitle(Y + 178, title, 16, titleInk) : text(X + CW / 2, Y + 178, title, { size: 16, fill: titleInk, display: true });
    if (scope === 'station') {
      body += text(X + CW / 2, Y + 200, 'Cauterets', { size: 12, weight: 600, fill: C.ink });
      body += text(X + CW / 2, Y + 234, '82 %', { size: 32, fill: C.brand, display: true });
      body += [0, 1, 2].map((d) => `<circle cx="${X + CW / 2 - 6 + d * 6}" cy="${Y + 246}" r="2.2" fill="${C.brand}"/>`).join('');
      body += `<line x1="${X}" y1="${Y + 258}" x2="${X + CW}" y2="${Y + 258}" stroke="${C.line}"/>`;
      body += text(X + CW / 2, Y + 279, 'Ce matin 82 % · Demain 71 %', { size: 11, weight: 600, fill: C.inkFaint });
    } else {
      body += odds(Y + 188, items, { rewind });
      body += seeAll(Y + 258);
    }
  }
  return body;
}

// ------------------------------------------------------------- files
const FILES = {
  banner: [{}, 'format: banner · visual: scene · kind: live'],
  full: [{ format: 'full', visual: 'photo' }, 'format: full · visual: photo'],
  compact: [{ format: 'compact' }, 'format: compact (no image)'],
  'visual-photo': [{ visual: 'photo' }, 'visual: photo'],
  'visual-webcam': [{ visual: 'webcam', planned: true }, 'visual: webcam', true],
  'scope-station': [{ scope: 'station', planned: true }, 'scope: station', true],
  rewind: [{ kind: 'historical' }, 'kind: historical (Rewind)'],
  'badge-time': [{ time: TOMORROW }, 'time badge: tomorrow (its colour)'],
  'badge-webcam': [{ visual: 'photo', badge: 'webcam' }, 'webcam rule: LIVE badge'],
  'badge-stale': [{ badge: 'stale' }, 'stale values: "data from" badge'],
  'display-scale': [{ format: 'full', display: 'scale' }, 'display: scale · certified (full)'],
  'display-scale-compact': [{ format: 'compact', display: 'scale' }, 'display: scale · certified (compact)'],
};

for (const [name, [options, label, planned]] of Object.entries(FILES)) {
  uid = 0;
  const body = tile(options) + caption(label, planned);
  writeFileSync(join(OUT, `${name}.svg`), svg(body, label));
}
console.log(`wrote ${Object.keys(FILES).length} mockups to ${OUT}`);
