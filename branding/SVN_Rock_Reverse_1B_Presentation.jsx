import { useState, useEffect, useRef, useCallback } from "react";

const LOGO_SRC = "data:image/jpeg;base64,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";

const GOLD = "#C9993A";
const DARK = "#0F1218";
const DARKER = "#0A0D11";
const CARD = "#161B24";
const CARD_BORDER = "#1E2530";
const TEXT = "#E8E6E1";
const TEXT_DIM = "#8B8A87";
const GREEN = "#3DB06B";
const RED = "#D94F4F";

function formatCurrency(val, decimals = 0) {
  if (Math.abs(val) >= 1e6) return "$" + (val / 1e6).toFixed(decimals || 1) + "M";
  if (Math.abs(val) >= 1e3) return "$" + (val / 1e3).toFixed(0) + "K";
  return "$" + val.toFixed(decimals);
}
function formatPct(val) { return (val * 100).toFixed(2) + "%"; }

function AnimatedNumber({ value, format = "currency", duration = 600 }) {
  const [display, setDisplay] = useState(value);
  const ref = useRef(null);
  const startRef = useRef(value);
  const startTime = useRef(null);

  useEffect(() => {
    startRef.current = display;
    startTime.current = performance.now();
    function tick(now) {
      const elapsed = now - startTime.current;
      const t = Math.min(elapsed / duration, 1);
      const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      setDisplay(startRef.current + (value - startRef.current) * ease);
      if (t < 1) ref.current = requestAnimationFrame(tick);
    }
    ref.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(ref.current);
  }, [value]);

  const formatted = format === "currency" ? formatCurrency(display)
    : format === "pct" ? formatPct(display)
    : format === "multiple" ? display.toFixed(2) + "x"
    : display.toFixed(2);
  return <span>{formatted}</span>;
}

function Slider({ label, value, min, max, step, onChange, format = "currency", unit = "" }) {
  const pct = ((value - min) / (max - min)) * 100;
  const formatted = format === "currency" ? formatCurrency(value, 2)
    : format === "pct" ? (value * 100).toFixed(2) + "%"
    : value.toFixed(2);
  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ color: TEXT_DIM, fontSize: 13, letterSpacing: 1.5, textTransform: "uppercase", fontFamily: "'DM Sans', sans-serif" }}>{label}</span>
        <span style={{ color: GOLD, fontSize: 18, fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>{formatted}{unit}</span>
      </div>
      <div style={{ position: "relative", height: 6, background: "#1E2530", borderRadius: 3 }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: 6, borderRadius: 3, width: pct + "%", background: `linear-gradient(90deg, ${GOLD}, #E8C16A)`, transition: "width 0.1s" }} />
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width: "100%", marginTop: -6, opacity: 0, cursor: "pointer", height: 24 }} />
    </div>
  );
}

function MetricCard({ label, value, format, sub, highlight }) {
  return (
    <div style={{
      background: CARD, border: `1px solid ${CARD_BORDER}`, borderRadius: 16, padding: "28px 24px",
      flex: 1, minWidth: 200, transition: "all 0.3s",
      boxShadow: highlight ? `0 0 30px ${GOLD}22` : "none",
      borderColor: highlight ? GOLD + "44" : CARD_BORDER,
    }}>
      <div style={{ color: TEXT_DIM, fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 12, fontFamily: "'DM Sans', sans-serif" }}>{label}</div>
      <div style={{ fontSize: 36, fontWeight: 700, color: TEXT, fontFamily: "'Instrument Serif', serif", lineHeight: 1.1 }}>
        <AnimatedNumber value={value} format={format} />
      </div>
      {sub && <div style={{ color: TEXT_DIM, fontSize: 13, marginTop: 8, fontFamily: "'DM Sans', sans-serif" }}>{sub}</div>}
    </div>
  );
}

// === PROJECT DATA (2240 Birchmount) ===
const PROJECT = {
  name: "2240 Birchmount Road",
  city: "Scarborough, ON",
  units: 170,
  storeys: 10,
  gfa: 145000,
  parking_sf: 67000,
  unit_mix: "1-Bed, 2-Bed, 3-Bed",
};

export default function App() {
  const [rentPerSqft, setRentPerSqft] = useState(3.50);
  const [capRate, setCapRate] = useState(0.0475);
  const [costPerSqft, setCostPerSqft] = useState(325);
  const [margin, setMargin] = useState(0.20);
  const [activeSection, setActiveSection] = useState(0);

  // Calculations (simplified reverse 1B logic)
  const avgUnitSf = 750;
  const pgi = rentPerSqft * avgUnitSf * PROJECT.units * 12;
  const vacancy = 0.03;
  const egi = pgi * (1 - vacancy);
  const opexPerUnit = 5800;
  const totalOpex = opexPerUnit * PROJECT.units;
  const noi = egi - totalOpex;
  const buildingValue = noi / capRate;
  const hardCosts = costPerSqft * PROJECT.gfa;
  const softCostsPct = 0.30;
  const totalDevCost = hardCosts / (1 - softCostsPct);
  const devYield = noi / totalDevCost;
  const yieldSpread = devYield - capRate;
  const equityMultiple = buildingValue / totalDevCost;
  const devProfit = buildingValue - totalDevCost;

  // Rent impact demo
  const baseRent = 3.50;
  const rentDelta = rentPerSqft - baseRent;
  const baseNoi = (baseRent * avgUnitSf * PROJECT.units * 12 * (1 - vacancy)) - totalOpex;
  const baseBV = baseNoi / capRate;
  const valueDelta = buildingValue - baseBV;

  const sections = ["Overview", "Revenue", "Costs", "Metrics", "Sensitivity", "Financing"];

  return (
    <div style={{
      background: DARK, color: TEXT, minHeight: "100vh", fontFamily: "'DM Sans', sans-serif",
      overflowX: "hidden",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{
        position: "sticky", top: 0, zIndex: 100, background: DARKER + "EE",
        backdropFilter: "blur(20px)", borderBottom: `1px solid ${CARD_BORDER}`,
        padding: "14px 48px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <img src={LOGO_SRC} alt="Rock Advisors" style={{ height: 38, opacity: 0.95 }} />
        <div style={{ display: "flex", gap: 8 }}>
          {sections.map((s, i) => (
            <button key={s} onClick={() => setActiveSection(i)} style={{
              background: activeSection === i ? GOLD + "22" : "transparent",
              border: `1px solid ${activeSection === i ? GOLD + "66" : "transparent"}`,
              color: activeSection === i ? GOLD : TEXT_DIM,
              padding: "6px 16px", borderRadius: 20, fontSize: 12, cursor: "pointer",
              letterSpacing: 0.5, fontFamily: "'DM Sans', sans-serif", transition: "all 0.3s",
            }}>{s}</button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 48px" }}>

        {/* HERO */}
        <div style={{ paddingTop: 80, paddingBottom: 60, textAlign: "center" }}>
          <div style={{ color: GOLD, fontSize: 12, letterSpacing: 3, textTransform: "uppercase", marginBottom: 12, fontWeight: 500 }}>
            Reverse 1B Financial Analysis
          </div>
          <h1 style={{ fontFamily: "'Instrument Serif', serif", fontSize: 56, fontWeight: 400, margin: 0, lineHeight: 1.1 }}>
            {PROJECT.name}
          </h1>
          <p style={{ color: TEXT_DIM, fontSize: 18, marginTop: 8 }}>{PROJECT.city}</p>
          <div style={{
            marginTop: 48, display: "inline-block", padding: "12px 48px", borderRadius: 20,
            background: `linear-gradient(135deg, ${GOLD}15, ${GOLD}08)`,
            border: `1px solid ${GOLD}33`,
          }}>
            <div style={{ color: TEXT_DIM, fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 4 }}>Estimated Building Value</div>
            <div style={{ fontFamily: "'Instrument Serif', serif", fontSize: 64, fontWeight: 400, color: TEXT, lineHeight: 1 }}>
              <AnimatedNumber value={buildingValue} format="currency" />
            </div>
          </div>
        </div>

        {/* PROJECT OVERVIEW */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 64 }}>
          {[
            { l: "Total Units", v: PROJECT.units },
            { l: "Storeys", v: PROJECT.storeys },
            { l: "GFA (Above Grade)", v: PROJECT.gfa.toLocaleString() + " sf" },
            { l: "Parking", v: PROJECT.parking_sf.toLocaleString() + " sf" },
            { l: "Unit Mix", v: PROJECT.unit_mix },
          ].map(({ l, v }) => (
            <div key={l} style={{
              background: CARD, border: `1px solid ${CARD_BORDER}`, borderRadius: 12, padding: "20px 24px", flex: "1 1 180px"
            }}>
              <div style={{ color: TEXT_DIM, fontSize: 11, letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 6 }}>{l}</div>
              <div style={{ fontSize: 20, fontWeight: 600, fontFamily: "'JetBrains Mono', monospace" }}>{v}</div>
            </div>
          ))}
        </div>

        {/* KEY METRICS */}
        <div style={{ marginBottom: 64 }}>
          <h2 style={{ fontFamily: "'Instrument Serif', serif", fontSize: 36, fontWeight: 400, marginBottom: 32 }}>Key Metrics</h2>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <MetricCard label="Development Yield" value={devYield} format="pct" sub="NOI / Total Dev Cost" highlight={devYield > capRate} />
            <MetricCard label="Yield Spread" value={yieldSpread} format="pct" sub="Dev Yield − Cap Rate" highlight={yieldSpread > 0} />
            <MetricCard label="Equity Multiple" value={equityMultiple} format="multiple" sub="Building Value / Dev Cost" />
            <MetricCard label="Development Profit" value={devProfit} format="currency" sub="Value − Total Dev Cost" />
          </div>
        </div>

        {/* REVENUE */}
        <div style={{ marginBottom: 64 }}>
          <h2 style={{ fontFamily: "'Instrument Serif', serif", fontSize: 36, fontWeight: 400, marginBottom: 32 }}>Revenue Summary</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {[
              { l: "Avg Rent / SF", v: formatCurrency(rentPerSqft, 2) + " /sf" },
              { l: "Potential Gross Income", v: formatCurrency(pgi) },
              { l: "Vacancy Provision", v: (vacancy * 100).toFixed(1) + "%" },
              { l: "Effective Gross Income", v: formatCurrency(egi) },
              { l: "Total Operating Expenses", v: formatCurrency(totalOpex) },
              { l: "Net Operating Income", v: formatCurrency(noi) },
            ].map(({ l, v }) => (
              <div key={l} style={{
                display: "flex", justifyContent: "space-between", padding: "16px 20px",
                background: CARD, borderRadius: 10, border: `1px solid ${CARD_BORDER}`,
              }}>
                <span style={{ color: TEXT_DIM, fontSize: 14 }}>{l}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 500 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* COST BREAKDOWN */}
        <div style={{ marginBottom: 64 }}>
          <h2 style={{ fontFamily: "'Instrument Serif', serif", fontSize: 36, fontWeight: 400, marginBottom: 32 }}>Development Cost</h2>
          {(() => {
            const items = [
              { l: "Hard Costs (Construction)", v: hardCosts, c: GOLD },
              { l: "Soft Costs (30%)", v: totalDevCost - hardCosts, c: "#6B8AE0" },
            ];
            const total = totalDevCost;
            return (
              <div>
                <div style={{ display: "flex", height: 12, borderRadius: 6, overflow: "hidden", marginBottom: 24 }}>
                  {items.map(it => (
                    <div key={it.l} style={{ width: (it.v / total * 100) + "%", background: it.c, transition: "width 0.5s" }} />
                  ))}
                </div>
                <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                  {items.map(it => (
                    <div key={it.l} style={{ flex: 1, background: CARD, border: `1px solid ${CARD_BORDER}`, borderRadius: 12, padding: "20px 24px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                        <div style={{ width: 10, height: 10, borderRadius: 3, background: it.c }} />
                        <span style={{ color: TEXT_DIM, fontSize: 13 }}>{it.l}</span>
                      </div>
                      <div style={{ fontSize: 24, fontWeight: 600, fontFamily: "'JetBrains Mono', monospace" }}>
                        <AnimatedNumber value={it.v} format="currency" />
                      </div>
                    </div>
                  ))}
                  <div style={{ flex: 1, background: `linear-gradient(135deg, ${GOLD}15, ${GOLD}08)`, border: `1px solid ${GOLD}33`, borderRadius: 12, padding: "20px 24px" }}>
                    <div style={{ color: TEXT_DIM, fontSize: 13, marginBottom: 8 }}>Total Development Cost</div>
                    <div style={{ fontSize: 24, fontWeight: 600, fontFamily: "'JetBrains Mono', monospace", color: GOLD }}>
                      <AnimatedNumber value={totalDevCost} format="currency" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>

        {/* SENSITIVITY — THE SHOWSTOPPER */}
        <div style={{ marginBottom: 64, padding: "48px 40px", background: `linear-gradient(180deg, ${CARD}, ${DARKER})`, borderRadius: 24, border: `1px solid ${CARD_BORDER}` }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div style={{ color: GOLD, fontSize: 11, letterSpacing: 3, textTransform: "uppercase", marginBottom: 8 }}>Interactive</div>
            <h2 style={{ fontFamily: "'Instrument Serif', serif", fontSize: 40, fontWeight: 400, margin: 0 }}>Sensitivity Analysis</h2>
            <p style={{ color: TEXT_DIM, marginTop: 8, fontSize: 15 }}>Adjust assumptions to see how they impact your building's value</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48 }}>
            <div>
              <Slider label="Rent per Square Foot" value={rentPerSqft} min={2.50} max={4.50} step={0.05} onChange={setRentPerSqft} format="currency" unit="/sf" />
              <Slider label="Capitalization Rate" value={capRate} min={0.03} max={0.07} step={0.0025} onChange={setCapRate} format="pct" />
              <Slider label="Construction Cost / SF" value={costPerSqft} min={250} max={450} step={5} onChange={setCostPerSqft} format="currency" unit="/sf" />
            </div>
            <div>
              <div style={{ textAlign: "center", padding: "24px 0" }}>
                <div style={{ color: TEXT_DIM, fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 8 }}>Building Value</div>
                <div style={{ fontFamily: "'Instrument Serif', serif", fontSize: 56, color: TEXT, lineHeight: 1 }}>
                  <AnimatedNumber value={buildingValue} format="currency" />
                </div>
              </div>

              {/* THE KILLER CALLOUT */}
              {rentDelta !== 0 && (
                <div style={{
                  marginTop: 24, padding: "24px 28px", borderRadius: 16,
                  background: valueDelta >= 0 ? GREEN + "12" : RED + "12",
                  border: `1px solid ${valueDelta >= 0 ? GREEN + "33" : RED + "33"}`,
                  textAlign: "center",
                }}>
                  <div style={{ fontSize: 13, color: TEXT_DIM, marginBottom: 4 }}>
                    A <span style={{ color: GOLD, fontWeight: 600 }}>${Math.abs(rentDelta).toFixed(2)}/sf</span> rent {rentDelta > 0 ? "increase" : "decrease"}
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 700, color: valueDelta >= 0 ? GREEN : RED, fontFamily: "'JetBrains Mono', monospace" }}>
                    {valueDelta >= 0 ? "+" : ""}<AnimatedNumber value={valueDelta} format="currency" />
                  </div>
                  <div style={{ fontSize: 13, color: TEXT_DIM, marginTop: 4 }}>in building value</div>
                </div>
              )}

              <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
                <MetricCard label="Dev Yield" value={devYield} format="pct" highlight={devYield > capRate} />
                <MetricCard label="Equity Multiple" value={equityMultiple} format="multiple" />
              </div>
            </div>
          </div>
        </div>

        {/* FINANCING PREVIEW */}
        <div style={{ marginBottom: 64 }}>
          <h2 style={{ fontFamily: "'Instrument Serif', serif", fontSize: 36, fontWeight: 400, marginBottom: 8 }}>Financing Preview</h2>
          <p style={{ color: TEXT_DIM, fontSize: 14, marginBottom: 32 }}>Preliminary debt structure — Joanna and the debt advisory team can walk through these in detail.</p>
          {(() => {
            const ltv = 0.75;
            const permLoan = buildingValue * ltv;
            const rate = 0.05;
            const term = 25;
            const annualDebt = permLoan * (rate / (1 - Math.pow(1 + rate, -term)));
            const dscr = noi / annualDebt;
            const equity = totalDevCost - permLoan;
            return (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                {[
                  { l: "Permanent Loan", v: formatCurrency(permLoan), s: `${(ltv * 100).toFixed(0)}% LTV` },
                  { l: "Annual Debt Service", v: formatCurrency(annualDebt), s: `${(rate * 100).toFixed(1)}% / ${term}yr` },
                  { l: "Debt Service Coverage", v: dscr.toFixed(2) + "x", s: dscr > 1.2 ? "Meets threshold" : "Below typical minimum" },
                  { l: "Equity Requirement", v: formatCurrency(equity > 0 ? equity : 0), s: "Total Dev Cost − Loan" },
                  { l: "Cash-on-Cash Return", v: equity > 0 ? ((noi - annualDebt) / equity * 100).toFixed(2) + "%" : "N/A", s: "(NOI − Debt) / Equity" },
                ].map(({ l, v, s }) => (
                  <div key={l} style={{ background: CARD, border: `1px solid ${CARD_BORDER}`, borderRadius: 12, padding: "20px 24px" }}>
                    <div style={{ color: TEXT_DIM, fontSize: 11, letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 8 }}>{l}</div>
                    <div style={{ fontSize: 22, fontWeight: 600, fontFamily: "'JetBrains Mono', monospace" }}>{v}</div>
                    {s && <div style={{ color: TEXT_DIM, fontSize: 12, marginTop: 6 }}>{s}</div>}
                  </div>
                ))}
              </div>
            );
          })()}
        </div>

        {/* DATA SOURCES */}
        <div style={{
          borderTop: `1px solid ${CARD_BORDER}`, padding: "32px 0 64px",
          display: "flex", gap: 24, flexWrap: "wrap", justifyContent: "center",
        }}>
          {[
            { l: "Construction Costs", v: "Altus Guide", d: "Through Jun 2026" },
            { l: "Property Taxes", v: "City of Toronto", d: "2025 Rates" },
            { l: "Rental Data", v: "CMHC / SVN Rock", d: "Fall 2025" },
          ].map(({ l, v, d }) => (
            <div key={l} style={{ textAlign: "center" }}>
              <span style={{ color: TEXT_DIM, fontSize: 11 }}>{l}: </span>
              <span style={{ color: TEXT, fontSize: 11, fontWeight: 500 }}>{v}</span>
              <span style={{ color: GOLD, fontSize: 11 }}> ({d})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
