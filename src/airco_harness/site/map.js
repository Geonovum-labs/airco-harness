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

const geometry = new Map();
/** The panden of a reference extract, fetched once per page. */
export function panden(root, file) {
  if (!geometry.has(file)) geometry.set(file, fetch(root + file).then(r => r.json()));
  return geometry.get(file);
}

/** A map in `element` that draws one run at a time; returns show(run, sample, panden) giving the counts per kind. */
export function createMap(element) {
  const crs = new L.Proj.CRS("EPSG:28992", RD, {resolutions: RESOLUTIONS, origin: [-285401.92, 903401.92],
    bounds: L.bounds([-285401.92, 22598.08], [595401.92, 903401.92])});
  const map = L.map(element, {crs, center: [52.1, 5.3], zoom: 3, maxZoom: 14});
  L.tileLayer("https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992/{z}/{x}/{y}.png",
    {minZoom: 0, maxZoom: 14, attribution: 'BRT achtergrondkaart: <a href="https://www.pdok.nl/">PDOK</a>, Kadaster'}).addTo(map);
  let layer = null;
  return function show(run, must, collection) {
    const required = new Set(must), shown = new Set(run.map ? run.map.shown : []);
    const kind = id => required.has(id) ? (shown.has(id) ? "hit" : "missing") : (shown.has(id) ? "extra" : "rest");
    const counts = {hit: 0, missing: 0, extra: 0, rest: 0, unmatched: run.map ? run.map.unmatched.length : 0};
    // A pand is a few meters wide, so at city scale a dot in its colour marks it too.
    const dots = [];
    const polygons = L.geoJSON(collection, {
      style: f => KINDS[kind(f.properties.identificatie)].style,
      onEachFeature: (f, l) => {
        const k = kind(f.properties.identificatie);
        counts[k]++;
        const tip = `pand ${f.properties.identificatie}: ${KINDS[k].label}`;
        l.bindTooltip(tip);
        dots.push(L.circleMarker(l.getBounds().getCenter(),
          {...KINDS[k].style, radius: k === "rest" ? 3 : 5, fillOpacity: k === "rest" ? 0 : 0.9}).bindTooltip(tip));
      },
    });
    const places = (run.map ? run.map.unmatched : []).map(([lon, lat]) =>
      L.circleMarker([lat, lon], PLACE).bindTooltip(`on no pand: ${lat.toFixed(5)}, ${lon.toFixed(5)}`));
    if (layer) layer.remove();
    layer = L.layerGroup([polygons, ...dots, ...places]).addTo(map);
    map.invalidateSize();
    map.fitBounds(polygons.getBounds(), {padding: [20, 20]});
    return counts;
  };
}

export const PLACE_STYLE = PLACE;
