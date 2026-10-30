// The map of a map question: the panden of the sample's BAG extract on the BRT achtergrondkaart of PDOK in RD
// (EPSG:28992), coloured by what one run showed. Leaflet with Proj4Leaflet, because NL Maps offers the BRT only in
// Web Mercator. Pand colours are status-like but read on the grey BRT in both themes; each has a label in the legend.

const RD = "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 " +
  "+ellps=bessel +towgs84=565.417,50.3319,465.552,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs";
const RESOLUTIONS = [3440.64, 1720.32, 860.16, 430.08, 215.04, 107.52, 53.76, 26.88, 13.44, 6.72, 3.36, 1.68, 0.84, 0.42, 0.21];
export const KINDS = {
  hit: {label: "required and shown", style: {color: "#1a7f37", fillColor: "#2da44e", fillOpacity: 0.65, weight: 2}},
  missing: {label: "required, not shown", style: {color: "#cf222e", fillColor: "#cf222e", fillOpacity: 0.15, weight: 2, dashArray: "4 3"}},
  extra: {label: "optional, shown", style: {color: "#0969da", fillColor: "#218bff", fillOpacity: 0.5, weight: 2}},
  rest: {label: "optional, not shown", style: {color: "#6e7781", fillOpacity: 0, weight: 1}},
};
const PLACE = {radius: 6, color: "#9a6700", fillColor: "#d4a72c", fillOpacity: 0.9, weight: 2};

// The agent's own name for a place, from the properties it gave its GeoJSON feature.
const NAME_KEYS = ["name", "naam", "title", "titel", "label", "adres", "address"];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function nameOf(place) {
  const key = NAME_KEYS.find(k => place.details[k]);
  return key ? place.details[key] : null;
}

/** A value the agent gave, as text; an http(s) value becomes a link. The details come from the logs, so they go in
 * as text nodes. */
function detailValue(value) {
  if (!/^https?:\/\//.test(value)) return document.createTextNode(value);
  const a = el("a", null, value);
  a.href = value; a.target = "_blank"; a.rel = "noopener noreferrer";
  return a;
}

/** A popup with what the agent said about the places on one pand (or on no pand): per place a table of its details. */
function placeInfo(title, kind, list) {
  const box = el("div", "placeinfo");
  const head = el("div", "placehead");
  head.append(el("b", null, title), " ", el("span", "muted", kind));
  box.append(head);
  if (!list.length) {
    box.append(el("p", "muted", "The agent did not put this pand on the map."));
    return box;
  }
  for (const place of list) {
    const entries = Object.entries(place.details);
    if (list.length > 1) box.append(el("div", "placesub", `Place ${list.indexOf(place) + 1} of ${list.length}`));
    if (!entries.length) box.append(el("p", "muted", "The agent gave no details for this place."));
    else {
      const table = el("table");
      for (const [key, value] of entries) {
        const row = el("tr");
        const td = el("td");
        td.append(detailValue(value));
        row.append(el("th", null, key), td);
        table.append(row);
      }
      box.append(table);
    }
    box.append(el("div", "coords", `put at ${place.lat.toFixed(5)}, ${place.lon.toFixed(5)}`));
  }
  return box;
}

const geometry = new Map();
/** The panden of a reference extract, fetched once per page. */
export function panden(root, file) {
  if (!geometry.has(file)) geometry.set(file, fetch(root + file).then(r => r.json()));
  return geometry.get(file);
}

/** A map in `element` that draws one run at a time; returns show(run, must, panden) giving the counts per kind. */
export function createMap(element) {
  const crs = new L.Proj.CRS("EPSG:28992", RD, {resolutions: RESOLUTIONS, origin: [-285401.92, 903401.92],
    bounds: L.bounds([-285401.92, 22598.08], [595401.92, 903401.92])});
  const map = L.map(element, {crs, center: [52.1, 5.3], zoom: 3, maxZoom: 14});
  L.tileLayer("https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992/{z}/{x}/{y}.png",
    {minZoom: 0, maxZoom: 14, attribution: 'BRT achtergrondkaart: <a href="https://www.pdok.nl/">PDOK</a>, Kadaster'}).addTo(map);
  let layer = null;
  return function show(run, must, collection) {
    const required = new Set(must), shown = new Set(run.map ? run.map.shown : []);
    // What the agent said per pand; a run from before the places were kept has none, and the map still colours the panden.
    const places = run.map && run.map.places ? run.map.places : null;
    const byPand = new Map();
    for (const place of places || []) if (place.pand) (byPand.get(place.pand) || byPand.set(place.pand, []).get(place.pand)).push(place);
    const kind = id => required.has(id) ? (shown.has(id) ? "hit" : "missing") : (shown.has(id) ? "extra" : "rest");
    const counts = {hit: 0, missing: 0, extra: 0, rest: 0, unmatched: run.map ? run.map.unmatched.length : 0};
    // A pand is a few meters wide, so at city scale a dot in its colour marks it too.
    const dots = [];
    const polygons = L.geoJSON(collection, {
      style: f => KINDS[kind(f.properties.identificatie)].style,
      onEachFeature: (f, l) => {
        const id = f.properties.identificatie, k = kind(id);
        counts[k]++;
        const own = byPand.get(id) || [];
        const name = own.map(nameOf).find(Boolean);
        const tip = `${name ? `${name} · ` : ""}pand ${id}: ${KINDS[k].label}`;
        const dot = L.circleMarker(l.getBounds().getCenter(), {...KINDS[k].style, radius: k === "rest" ? 3 : 5, fillOpacity: k === "rest" ? 0 : 0.9});
        for (const layer of [l, dot]) {
          layer.bindTooltip(tip);
          if (places) layer.bindPopup(() => placeInfo(`pand ${id}`, KINDS[k].label, own), {maxWidth: 360});
        }
        dots.push(dot);
      },
    });
    const loose = places ? places.filter(p => !p.pand) : (run.map ? run.map.unmatched : []).map(([lon, lat]) => ({lon, lat, details: {}}));
    const markers = loose.map(place => {
      const name = nameOf(place);
      const marker = L.circleMarker([place.lat, place.lon], PLACE).bindTooltip(`${name ? `${name} · ` : ""}on no pand: ${place.lat.toFixed(5)}, ${place.lon.toFixed(5)}`);
      if (places) marker.bindPopup(() => placeInfo(name || "Place on no pand", "invented, on no pand", [place]), {maxWidth: 360});
      return marker;
    });
    if (layer) layer.remove();
    layer = L.layerGroup([polygons, ...dots, ...markers]).addTo(map);
    map.invalidateSize();
    map.fitBounds(polygons.getBounds(), {padding: [20, 20]});
    return counts;
  };
}

export const PLACE_STYLE = PLACE;
