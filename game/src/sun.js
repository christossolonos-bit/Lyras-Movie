// Real sun (and moon) position over Death Valley for any moment, after the NOAA solar
// calculator and a low-precision lunar ephemeris. Accurate to a fraction of a degree,
// which is far better than anyone can see in the sky.

export const DEATH_VALLEY = { lat: 36.4615, lon: -116.8667, tz: 'America/Los_Angeles', name: 'Furnace Creek' };

const rad = Math.PI / 180, deg = 180 / Math.PI;

function julianDay(date) { return date.getTime() / 86400000 + 2440587.5; }

// Elevation and azimuth (degrees; azimuth clockwise from true north) for a sky position
// given as right ascension / declination (degrees).
function toHorizon(raDeg, decDeg, date, lat, lon) {
  const jd = julianDay(date), d = jd - 2451545.0;
  const gmst = (280.46061837 + 360.98564736629 * d) % 360;
  const ha = ((gmst + lon - raDeg) % 360 + 540) % 360 - 180;
  const H = ha * rad, dec = decDeg * rad, phi = lat * rad;
  const sinAlt = Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H);
  const alt = Math.asin(sinAlt);
  const az = Math.atan2(-Math.sin(H) * Math.cos(dec), Math.cos(phi) * Math.sin(dec) - Math.sin(phi) * Math.cos(dec) * Math.cos(H));
  let elev = alt * deg;
  // atmospheric refraction near the horizon (lifts the sun about half a degree at sunset)
  if (elev > -1) elev += 1.02 / Math.tan((elev + 10.3 / (elev + 5.11)) * rad) / 60;
  return { elev, azim: (az * deg + 360) % 360 };
}

export function sunPosition(date, lat = DEATH_VALLEY.lat, lon = DEATH_VALLEY.lon) {
  const n = julianDay(date) - 2451545.0;
  const L = (280.46 + 0.9856474 * n) % 360;
  const g = ((357.528 + 0.9856003 * n) % 360) * rad;
  const lambda = (L + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * rad;
  const eps = (23.439 - 0.0000004 * n) * rad;
  const ra = Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda)) * deg;
  const dec = Math.asin(Math.sin(eps) * Math.sin(lambda)) * deg;
  return toHorizon(ra, dec, date, lat, lon);
}

export function moonPosition(date, lat = DEATH_VALLEY.lat, lon = DEATH_VALLEY.lon) {
  const d = julianDay(date) - 2451545.0;
  const L = (218.316 + 13.176396 * d) * rad;
  const M = (134.963 + 13.064993 * d) * rad;
  const F = (93.272 + 13.22935 * d) * rad;
  const lambda = L + 6.289 * rad * Math.sin(M);
  const beta = 5.128 * rad * Math.sin(F);
  const eps = 23.4397 * rad;
  const ra = Math.atan2(Math.sin(lambda) * Math.cos(eps) - Math.tan(beta) * Math.sin(eps), Math.cos(lambda)) * deg;
  const dec = Math.asin(Math.sin(beta) * Math.cos(eps) + Math.cos(beta) * Math.sin(eps) * Math.sin(lambda)) * deg;
  // illuminated fraction from the sun-moon elongation
  const sunL = (280.46 + 0.9856474 * d) * rad;
  const phase = (1 - Math.cos(lambda - sunL)) / 2;
  return { ...toHorizon(ra, dec, date, lat, lon), phase };
}

// Local clock text for the HUD, in Death Valley's time zone.
export function localClock(date) {
  return date.toLocaleTimeString('en-US', { timeZone: DEATH_VALLEY.tz, hour: 'numeric', minute: '2-digit' });
}
export function localDate(date) {
  return date.toLocaleDateString('en-US', { timeZone: DEATH_VALLEY.tz, month: 'short', day: 'numeric' });
}
