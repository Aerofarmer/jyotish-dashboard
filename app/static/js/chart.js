/**
 * North Indian Kundli chart renderer (Canvas 2D).
 * Draws the classic 4×4 grid with triangular houses.
 * Houses 1-12 are placed in the traditional North Indian layout.
 *
 * Layout map (cell positions in a 4×4 grid, 0-indexed row,col):
 *   [0,1]=H12  [0,2]=H1   [0,3]=H2
 *   [1,0]=H11  center     [1,3]=H3
 *   [2,0]=H10  center     [2,3]=H4
 *   [3,1]=H9   [3,2]=H8   [3,3] is outside -> use bottom row
 *
 * Actual North Indian layout (3×3 outer + center hollow):
 *   H12 | H1  | H2
 *   H11 |     | H3
 *   H10 | H9  | H8   <- bottom row mirrored
 * with H4–H7 on right/bottom continuation...
 *
 * Canonical North Indian diamond-square layout:
 * +----+----+----+
 * | 12 |  1 |  2 |
 * +----+    +----+
 * | 11 |    |  3 |
 * +----+    +----+
 * | 10 |  9 |  8 |  (7, 6, 5, 4 on right side going up)
 * +----+----+----+
 */

const RASHI_ABBR = [
  "Mes","Vri","Mit","Kar","Sim","Kan","Tul","Vri","Dha","Mak","Kum","Min"
];

const RASHI_GLYPHS = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];

/**
 * House positions in the North Indian chart.
 * Each entry: { row, col } in a 4×4 grid (0-indexed).
 * Center cells (rows 1-2, cols 1-2) are hollow (chart name area).
 *
 * Canonical North Indian 4×4 layout:
 * (0,0)=12  (0,1)=1  (0,2)=2  (0,3)=3
 * (1,0)=11  [CENTER] [CENTER] (1,3)=4
 * (2,0)=10  [CENTER] [CENTER] (2,3)=5
 * (3,0)=9   (3,1)=8  (3,2)=7  (3,3)=6
 */
const HOUSE_CELLS = {
  1:  { r:0, c:1 },
  2:  { r:0, c:2 },
  3:  { r:0, c:3 },
  4:  { r:1, c:3 },
  5:  { r:2, c:3 },
  6:  { r:3, c:3 },
  7:  { r:3, c:2 },
  8:  { r:3, c:1 },
  9:  { r:3, c:0 },
  10: { r:2, c:0 },
  11: { r:1, c:0 },
  12: { r:0, c:0 },
};

const PLANET_COLORS = {
  Sun:"#FF6B35", Moon:"#C8D8E8", Mars:"#FF4444", Mercury:"#00CC88",
  Jupiter:"#FFD700", Venus:"#FF69B4", Saturn:"#9CA3AF",
  Rahu:"#8B5CF6", Ketu:"#EC4899",
};

const PLANET_SYMBOLS = {
  Sun:"☉", Moon:"☽", Mars:"♂", Mercury:"☿",
  Jupiter:"♃", Venus:"♀", Saturn:"♄", Rahu:"☊", Ketu:"☋",
};

// ─────────────────────────────────────────────────────
//  Main renderer
// ─────────────────────────────────────────────────────
function renderNorthIndianChart(canvasId, houseOccupants, lagnaRashi, planets) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const dpr  = window.devicePixelRatio || 1;
  const size = canvas.offsetWidth || 440;
  canvas.width  = size * dpr;
  canvas.height = size * dpr;
  canvas.style.width  = size + "px";
  canvas.style.height = size + "px";

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const S  = size;
  const CW = S / 4;   // cell width
  const CH = S / 4;   // cell height

  // Background
  ctx.fillStyle = "#0d0820";
  ctx.fillRect(0, 0, S, S);

  // Outer border
  ctx.strokeStyle = "#FFD700";
  ctx.lineWidth = 2;
  ctx.strokeRect(2, 2, S-4, S-4);

  // Draw all 12 house cells
  for (let h = 1; h <= 12; h++) {
    const { r, c } = HOUSE_CELLS[h];
    const x = c * CW;
    const y = r * CH;
    drawHouseCell(ctx, x, y, CW, CH, h, lagnaRashi, houseOccupants, planets);
  }

  // Center box (2×2 cells, rows 1-2, cols 1-2)
  const cx = CW, cy = CH;
  const cw = CW * 2, ch = CH * 2;

  // Center fill
  ctx.fillStyle = "#130d2e";
  ctx.fillRect(cx, cy, cw, ch);
  ctx.strokeStyle = "#2e1f6e";
  ctx.lineWidth = 1;
  ctx.strokeRect(cx, cy, cw, ch);

  // Diagonal lines in center (decorative)
  ctx.strokeStyle = "#2e1f6e";
  ctx.lineWidth = 0.5;
  ctx.beginPath();
  ctx.moveTo(cx, cy);         ctx.lineTo(cx + cw, cy + ch);
  ctx.moveTo(cx + cw, cy);    ctx.lineTo(cx, cy + ch);
  ctx.stroke();

  // "OM" symbol in center
  ctx.font = `bold ${Math.floor(S * 0.09)}px serif`;
  ctx.fillStyle = "rgba(255,215,0,0.18)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("ॐ", cx + cw / 2, cy + ch / 2);

  // Lagna label
  ctx.font = `bold ${Math.floor(S * 0.028)}px 'Cinzel', serif`;
  ctx.fillStyle = "#FFD700";
  ctx.fillText("LAGNA", cx + cw / 2, cy + ch / 2 + S * 0.065);
  ctx.font = `${Math.floor(S * 0.024)}px Inter, sans-serif`;
  ctx.fillStyle = "#b8960c";
  ctx.fillText(RASHI_ABBR[lagnaRashi] || "", cx + cw / 2, cy + ch / 2 + S * 0.1);
}

// ─────────────────────────────────────────────────────
//  Draw a single house cell
// ─────────────────────────────────────────────────────
function drawHouseCell(ctx, x, y, w, h, houseNum, lagnaRashi, houseOccupants, planets) {
  // Cell background
  const isLagna = houseNum === 1;
  ctx.fillStyle = isLagna ? "rgba(255,215,0,0.07)" : "#130d2e";
  ctx.fillRect(x, y, w, h);

  // Cell border
  ctx.strokeStyle = isLagna ? "#FFD700" : "#2e1f6e";
  ctx.lineWidth = isLagna ? 1.5 : 1;
  ctx.strokeRect(x, y, w, h);

  // House number (top-left corner)
  ctx.font = `bold ${Math.floor(w * 0.18)}px Inter, sans-serif`;
  ctx.fillStyle = isLagna ? "#FFD700" : "#4a3f7a";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText(houseNum, x + w * 0.07, y + h * 0.06);

  // Rashi name (small, top-right)
  const rashiIdx = (lagnaRashi + houseNum - 1) % 12;
  ctx.font = `${Math.floor(w * 0.13)}px Inter, sans-serif`;
  ctx.fillStyle = "#7B6FA0";
  ctx.textAlign = "right";
  ctx.textBaseline = "top";
  ctx.fillText(RASHI_ABBR[rashiIdx], x + w * 0.95, y + h * 0.06);

  // Rashi glyph (center-background, very subtle)
  ctx.font = `${Math.floor(w * 0.28)}px serif`;
  ctx.fillStyle = "rgba(255,215,0,0.05)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(RASHI_GLYPHS[rashiIdx], x + w / 2, y + h / 2);

  // Planets in this house
  const occupants = houseOccupants[houseNum] || houseOccupants[String(houseNum)] || [];
  if (occupants.length === 0) return;

  const maxCols = 3;
  const pSize   = Math.max(Math.floor(w * 0.16), 10);
  const padX    = w * 0.1;
  const padY    = h * 0.28;
  const lineH   = pSize + 2;

  occupants.forEach((pname, i) => {
    const col = i % maxCols;
    const row = Math.floor(i / maxCols);
    const px  = x + padX + col * (w - padX * 2) / maxCols;
    const py  = y + padY + row * lineH;

    const color = (planets && planets[pname]) ? planets[pname].color : "#FFFFFF";
    const sym   = PLANET_SYMBOLS[pname] || pname[0];
    const retro = planets && planets[pname] && planets[pname].retrograde;

    ctx.font = `bold ${pSize}px Inter, sans-serif`;
    ctx.fillStyle = color;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText((retro ? "℞" : "") + sym + pname.substring(0, 3), px, py);
  });
}

// ─────────────────────────────────────────────────────
//  Navamsa (D9) chart — same grid, different rashis
// ─────────────────────────────────────────────────────
function renderNavamsaChart(canvasId, navamsa) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !navamsa) return;

  // Build a pseudo house-occupants from navamsa data
  const lagnaRashi = navamsa["Lagna"] ? navamsa["Lagna"].rashi : 0;

  // Map each planet to its navamsa rashi, then to house (relative to navamsa lagna)
  const houseOccupants = {};
  for (let i = 1; i <= 12; i++) houseOccupants[i] = [];

  for (const [pname, data] of Object.entries(navamsa)) {
    if (pname === "Lagna") continue;
    const rashi = data.rashi;
    const house = ((rashi - lagnaRashi + 12) % 12) + 1;
    houseOccupants[house].push(pname);
  }

  // Build minimal planets map (just colors)
  const planetsMap = {};
  for (const pname of Object.keys(navamsa)) {
    planetsMap[pname] = { color: PLANET_COLORS[pname] || "#fff", retrograde: false };
  }

  renderNorthIndianChart(canvasId, houseOccupants, lagnaRashi, planetsMap);
}

// ─────────────────────────────────────────────────────
//  Resize handler — redraw on window resize
// ─────────────────────────────────────────────────────
window.addEventListener("resize", () => {
  document.querySelectorAll(".kundli-canvas").forEach(canvas => {
    const chartData  = canvas.dataset.chart;
    const navData    = canvas.dataset.navamsa;
    const lagnaRashi = canvas.dataset.lagnaRashi;

    if (chartData) {
      try {
        const d = JSON.parse(chartData);
        renderNorthIndianChart(canvas.id, d.house_occupants, d.lagna.rashi, d.planets);
      } catch(e) {}
    } else if (navData) {
      try {
        renderNavamsaChart(canvas.id, JSON.parse(navData));
      } catch(e) {}
    }
  });
});
