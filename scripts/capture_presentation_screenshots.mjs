import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const OUTPUT_DIR = path.resolve('artifacts/prayaas_presentation_screenshots');
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function run() {
  console.log('Starting PRAYAAS presentation screenshot suite...');

  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-gpu',
      '--window-size=1920,1080',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // In-memory interception to safe-guard zoom control without modifying disk files
  await page.setRequestInterception(true);
  page.on('request', async (req) => {
    if (req.url().includes('CommandCentreMap.tsx')) {
      try {
        const res = await fetch(req.url());
        let text = await res.text();
        text = text.replace('function CustomZoomControls() {', 'function CustomZoomControls() { return null; ');
        req.respond({
          status: 200,
          contentType: 'application/javascript',
          body: text,
        });
      } catch (e) {
        req.continue();
      }
    } else {
      req.continue();
    }
  });

  // ─────────────────────────────────────────────────────────────
  // 1. 01_command_centre.png
  // ─────────────────────────────────────────────────────────────
  console.log('1. Capturing 01_command_centre.png...');
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'load', timeout: 20000 });
  await new Promise((r) => setTimeout(r, 4000));

  // Open the LAYERS drawer on top-left to display layer names
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const layersBtn = buttons.find((b) => b.textContent?.includes('LAYERS'));
    if (layersBtn) layersBtn.click();
  });
  await new Promise((r) => setTimeout(r, 1200));

  await page.screenshot({
    path: path.join(OUTPUT_DIR, '01_command_centre.png'),
  });
  console.log('Saved 01_command_centre.png');

  // Close layers panel
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const layersBtn = buttons.find((b) => b.textContent?.includes('LAYERS'));
    if (layersBtn) layersBtn.click();
  });
  await new Promise((r) => setTimeout(r, 600));

  // ─────────────────────────────────────────────────────────────
  // 2. 02_raini_assessment.png
  // ─────────────────────────────────────────────────────────────
  console.log('2. Capturing 02_raini_assessment.png...');
  // Expand drawer
  await page.evaluate(() => {
    const expandBtn = Array.from(document.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('EXPAND DRAWER')
    );
    if (expandBtn) expandBtn.click();
  });
  await new Promise((r) => setTimeout(r, 1200));

  // Click on Raini Settlement row in the priority queue
  await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    const raini = rows.find(
      (r) => r.innerText.includes('Raini Settlement') || r.innerText.includes('HAB-002')
    );
    if (raini) raini.click();
  });
  await new Promise((r) => setTimeout(r, 2000));

  // Switch to RELOCATION NEED subtab in FeatureInspector
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const relocBtn = buttons.find((b) => b.textContent?.trim() === 'RELOCATION NEED');
    if (relocBtn) relocBtn.click();
  });
  await new Promise((r) => setTimeout(r, 2000));

  await page.screenshot({
    path: path.join(OUTPUT_DIR, '02_raini_assessment.png'),
  });
  console.log('Saved 02_raini_assessment.png');

  // ─────────────────────────────────────────────────────────────
  // 3. 03_candidate_discovery_map.png
  // ─────────────────────────────────────────────────────────────
  console.log('3. Capturing 03_candidate_discovery_map.png...');
  // Click FIND RELOCATION LAND (TASK 6)
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const findLandBtn = buttons.find((b) => b.textContent?.includes('FIND RELOCATION LAND'));
    if (findLandBtn) findLandBtn.click();
  });

  // Wait for candidate discovery API call to complete
  console.log('Waiting 8s for candidate discovery execution...');
  await new Promise((r) => setTimeout(r, 8000));

  // Enable Feasible Land Mask in layer panel
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const layersBtn = buttons.find((b) => b.textContent?.includes('LAYERS'));
    if (layersBtn) layersBtn.click();
  });
  await new Promise((r) => setTimeout(r, 1000));

  await page.evaluate(() => {
    const labels = Array.from(document.querySelectorAll('label, div'));
    labels.forEach((l) => {
      if (l.textContent?.includes('Feasible Land Mask') || l.textContent?.includes('Discovered Parcels')) {
        const checkbox = l.querySelector('input[type="checkbox"]');
        if (checkbox && !checkbox.checked) {
          checkbox.click();
        }
      }
    });
  });
  await new Promise((r) => setTimeout(r, 1000));

  // Close layers panel
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const layersBtn = buttons.find((b) => b.textContent?.includes('LAYERS'));
    if (layersBtn) layersBtn.click();
  });
  await new Promise((r) => setTimeout(r, 1500));

  await page.screenshot({
    path: path.join(OUTPUT_DIR, '03_candidate_discovery_map.png'),
  });
  console.log('Saved 03_candidate_discovery_map.png');

  // ─────────────────────────────────────────────────────────────
  // 4. 04_candidate_detail.png
  // ─────────────────────────────────────────────────────────────
  console.log('4. Capturing 04_candidate_detail.png...');
  // Click on a candidate site or candidate parcel on the map
  const parcelFound = await page.evaluate(async () => {
    // Click one of the interactive polygon paths on the Leaflet map
    const paths = Array.from(document.querySelectorAll('path.leaflet-interactive'));
    // Select a polygon with stroke #0891b2 (cyan candidate parcel) or #059669 (feasible land)
    const candPath = paths.find((p) => p.getAttribute('stroke') === '#0891b2' || p.getAttribute('fill') === '#06b6d4');
    if (candPath) {
      candPath.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return 'PARCEL_CLICKED';
    }
    // Alternatively, click the green candidate site marker (RS-002 or RS-001)
    const circles = Array.from(document.querySelectorAll('path.leaflet-interactive'));
    if (circles.length > 5) {
      circles[5].dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return 'FEATURE_CLICKED';
    }
    return null;
  });
  await new Promise((r) => setTimeout(r, 2500));

  await page.screenshot({
    path: path.join(OUTPUT_DIR, '04_candidate_detail.png'),
  });
  console.log(`Saved 04_candidate_detail.png (${parcelFound})`);

  // ─────────────────────────────────────────────────────────────
  // 5. 05_candidate_sites_inventory.png
  // ─────────────────────────────────────────────────────────────
  console.log('5. Capturing 05_candidate_sites_inventory.png...');
  await page.goto('http://127.0.0.1:5173/candidate-sites', { waitUntil: 'load', timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2000));
  await page.screenshot({
    path: path.join(OUTPUT_DIR, '05_candidate_sites_inventory.png'),
  });
  console.log('Saved 05_candidate_sites_inventory.png');

  // ─────────────────────────────────────────────────────────────
  // 6. 07_relocation_priority_matrix.png
  // ─────────────────────────────────────────────────────────────
  console.log('6. Capturing 07_relocation_priority_matrix.png...');
  await page.goto('http://127.0.0.1:5173/relocation-priority', { waitUntil: 'load', timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2000));
  await page.screenshot({
    path: path.join(OUTPUT_DIR, '07_relocation_priority_matrix.png'),
  });
  console.log('Saved 07_relocation_priority_matrix.png');

  // ─────────────────────────────────────────────────────────────
  // 7. 08_scenario_lab_workspace.png
  // ─────────────────────────────────────────────────────────────
  console.log('7. Capturing 08_scenario_lab_workspace.png...');
  await page.goto('http://127.0.0.1:5173/scenario-lab', { waitUntil: 'load', timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2000));
  await page.screenshot({
    path: path.join(OUTPUT_DIR, '08_scenario_lab_workspace.png'),
  });
  console.log('Saved 08_scenario_lab_workspace.png');

  // ─────────────────────────────────────────────────────────────
  // 8. 09_digital_twin_3d_workspace.png
  // ─────────────────────────────────────────────────────────────
  console.log('8. Capturing 09_digital_twin_3d_workspace.png...');
  await page.goto('http://127.0.0.1:5173/digital-twin', { waitUntil: 'load', timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2000));
  await page.screenshot({
    path: path.join(OUTPUT_DIR, '09_digital_twin_3d_workspace.png'),
  });
  console.log('Saved 09_digital_twin_3d_workspace.png');

  // ─────────────────────────────────────────────────────────────
  // 9. 10_evidence_layers_pipeline.png
  // ─────────────────────────────────────────────────────────────
  console.log('9. Capturing 10_evidence_layers_pipeline.png...');
  await page.goto('http://127.0.0.1:5173/data-sources', { waitUntil: 'load', timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2000));
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const evBtn = buttons.find((b) => b.textContent?.includes('EVIDENCE LAYERS'));
    if (evBtn) evBtn.click();
  });
  await new Promise((r) => setTimeout(r, 1200));
  await page.screenshot({
    path: path.join(OUTPUT_DIR, '10_evidence_layers_pipeline.png'),
  });
  console.log('Saved 10_evidence_layers_pipeline.png');

  await browser.close();
  console.log('Screenshot suite completed successfully!');
}

run().catch((err) => {
  console.error('Error during capture:', err);
  process.exit(1);
});
