// Capture Sales Cockpit filtered to a specific rep's book.
// Usage: node capture-rep.js <rep name>
// Requires env: TRIMIT_PLAY_URL, TRIMIT_WEB_USER, TRIMIT_WEB_PASS
//   (source /opt/data/home/.secrets/trimit-web-login.env first)
//
// Output: OK /tmp/dashboard-salescockpit-<rep-slug>.png  (Book: <rep name>)
//         PAGE_TEXT_START ... PAGE_TEXT_END  (column totals + cards)
//
// The Book dropdown is a native <select> that includes "Whole team" as an option.
// This script finds that select, fuzzy-matches the rep name, triggers change,
// waits for reload, screenshots, and dumps the page text.
const PW = require("playwright-core");
(async () => {
  const rep = process.argv.slice(2).join(" ").trim();
  if (!rep) { console.log("ERR: no rep name given"); process.exit(1); }
  const base = process.env.TRIMIT_PLAY_URL;
  const user = process.env.TRIMIT_WEB_USER;
  const pass = process.env.TRIMIT_WEB_PASS;
  const out = "/tmp/dashboard-salescockpit-" + rep.toLowerCase().replace(/[^a-z0-9]+/g, "-") + ".png";

  const brow = await PW.chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const pg = await (await brow.newContext({ viewport: { width: 1680, height: 1200 }, deviceScaleFactor: 2 })).newPage();
  try {
    await pg.goto(base + "/ClientLogin.cfm", { waitUntil: "networkidle", timeout: 45000 });
    const f = pg.frames().find(x => /Login\/index\.cfm/i.test(x.url())) || pg.mainFrame();
    await f.fill('input[name=LoginName]', user);
    await f.fill('input[name=Password]', pass);
    await Promise.all([
      pg.waitForNavigation({ timeout: 45000 }).catch(() => {}),
      f.evaluate(() => document.getElementById('form1').submit())
    ]);

    // IMPORTANT: URL includes /GSTS/ prefix — without it you get 404
    await pg.goto(base + "/GSTS/Dashboard-SalesCockpit.cfm", { waitUntil: "networkidle", timeout: 60000 });
    await pg.waitForTimeout(4000);

    // Dismiss welcome overlay
    await pg.evaluate(() => {
      const b = document.querySelector('#wcGotIt'); if (b) b.click();
      document.querySelectorAll('#welcomeOverlay,.welcome-overlay').forEach(o => { o.classList.remove('show'); o.style.display = 'none'; });
    });
    await pg.waitForTimeout(500);

    // Find and change the Book dropdown to the rep
    const changed = await pg.evaluate((repName) => {
      const selects = document.querySelectorAll('select');
      for (const sel of selects) {
        const opts = Array.from(sel.options).map(o => o.text.toLowerCase());
        if (opts.some(o => o.includes('whole team'))) {
          let bestIdx = -1, bestScore = 0;
          for (let i = 0; i < sel.options.length; i++) {
            const t = sel.options[i].text.toLowerCase();
            const words = repName.toLowerCase().split(/\s+/).filter(Boolean);
            const score = words.filter(w => t.includes(w)).length;
            if (score > bestScore) { bestScore = score; bestIdx = i; }
          }
          if (bestIdx >= 0 && bestScore > 0) {
            sel.selectedIndex = bestIdx;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return sel.options[bestIdx].text;
          }
          return "NOMATCH: " + opts.join(" | ");
        }
      }
      return "NO_BOOK_SELECT";
    }, rep);

    if (changed.startsWith("NOMATCH") || changed === "NO_BOOK_SELECT") {
      console.log("ERR: Could not find rep '" + rep + "' in Book dropdown. " + changed);
      await brow.close();
      process.exit(2);
    }

    await pg.waitForTimeout(5000);

    await pg.evaluate(() => {
      const b = document.querySelector('#wcGotIt'); if (b) b.click();
      document.querySelectorAll('#welcomeOverlay,.welcome-overlay').forEach(o => { o.classList.remove('show'); o.style.display = 'none'; });
    });

    const data = await pg.evaluate(() => (document.body.innerText || "").slice(0, 3000));

    await pg.screenshot({ path: out, fullPage: true });
    console.log("OK " + out + "  (Book: " + changed + ")");
    console.log("PAGE_TEXT_START");
    console.log(data);
    console.log("PAGE_TEXT_END");
  } catch (e) {
    console.log("ERR: " + String(e).slice(0, 300));
    await brow.close();
    process.exit(1);
  }
  await brow.close();
})();
