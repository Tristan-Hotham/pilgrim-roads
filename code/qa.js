// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server PORT; set PORT).
// MapLibre comes from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked
// here, so the screenshots show the offline base map (Natural Earth outlines). NOML=1 blocks MapLibre too, to check
// that the page falls back to its own canvas map.
const { chromium } = require("playwright");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  const tag = process.env.NOML ? "noml_" : "";
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    if (process.env.NOML) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError|tile/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + process.env.PORT + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(4000);
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const idle = () => p.evaluate(() => new Promise(r => { if (!window.map || !map.loaded) return r(); let done = false; const fin = () => { if (!done) { done = true; r(); } }; map.once("idle", fin); map.triggerRepaint(); setTimeout(fin, 30000); }));
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(500); if (!process.env.NOML && /atlas|map/.test(sel)) await idle(); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    if (!process.env.NOML) {
      await p.click('#showRow [data-k="rings"]'); await p.waitForTimeout(800); await shot("#atlas", "map_rings"); await p.click('#showRow [data-k="rings"]');
      await p.click("#famRow .btn:nth-child(3)"); await p.waitForTimeout(700); await shot("#atlas", "fam_francigena"); await p.click("#famRow .btn:nth-child(3)");
      await p.click("#focusRow .btn:nth-child(3)"); await p.waitForTimeout(2500); await shot("#atlas", "zoom_santiago");
      await p.fill("#q", "Camino Podolico"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2800); await shot("#atlas", "search_podolico");
      await p.fill("#q", "Fatima"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2800); await shot("#atlas", "search_fatima");
      await p.click("#focusRow .btn:nth-child(9)"); await p.waitForTimeout(2800); await shot("#atlas", "shikoku");
      await p.click("#focusRow .btn:nth-child(4)"); await p.waitForTimeout(2800);
      await p.click(".lyrBtn"); await p.waitForTimeout(300); await p.locator('.lyrPanel [data-k="cities"]').check(); await p.waitForTimeout(600); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
      const hit = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["routes"] }); if (!f.length) return null; const c = f[Math.floor(f.length / 2)]; const g = c.geometry.coordinates; const pt = (c.geometry.type === "MultiLineString" ? g[0] : g)[1]; const xy = map.project(pt); const r = map.getContainer().getBoundingClientRect(); return [r.left + xy.x, r.top + xy.y]; });
      if (hit) { await p.mouse.click(hit[0], hit[1]); await p.waitForTimeout(800); await shot("#side", "side_route"); } else errs.push(nm + ": no routes rendered");
      const n = await p.evaluate(() => [map.queryRenderedFeatures({ layers: ["routes"] }).length, map.queryRenderedFeatures({ layers: ["sites"] }).length, ROUTES ? ROUTES.features.length : 0]);
      console.log(nm, "routes, sites rendered here, routes loaded:", n);
    }
    for (const c of ["caminoChart", "bandChart", "famChart", "longTable", "siteChart", "tradChart", "compChart"]) await shot("#" + c, c);
    if (nm === "phone" && !process.env.NOML) {
      await p.click("#theme"); await p.waitForTimeout(1200); await shot("#atlas", "dark_map"); await shot("#compChart", "dark_comp");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
      await p.click(".mfs-btn"); await p.waitForTimeout(600);
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
