(function () {
  "use strict";
  // Emission factors in kg CO2 (or CO2e) per unit; sources listed on the page.
  var F = {
    kwh: 0.394,            // EPA Equivalencies, electricity used, US average (3.94e-4 t/kWh)
    therm: 5.3,            // EPA Equivalencies (0.0053 t/therm)
    gasoline: 8.887,       // EPA, 8,887 g per gallon
    diesel: 10.21,         // EPA Emission Factors Hub 2025
    propane: 12.68 * 0.45359237, // 12.68 lb per gallon (US DOE)
    f_short: 0.2089, f_med: 0.1301, f_long: 0.1640, // EPA Hub, per passenger mile
    bus: 0.0666, crail: 0.1340, trail: 0.0935,       // EPA Hub 2025
    car_year: 4290         // EPA, average passenger vehicle per year
  };
  // Heat content in Btu per unit (EIA)
  var B = { kwh: 3412, therm: 100000, gasoline: 120214, diesel: 137381, propane: 91452 };
  var mode = "home";
  function $(id) { return document.getElementById(id); }
  function n(id) { var e = $(id); if (!e) return 0; var v = parseFloat(e.value); return isFinite(v) && v > 0 ? v : 0; }
  function fmt(x, d) { return x.toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d }); }
  function t(x) { return x >= 100 ? fmt(x, 0) : x >= 10 ? fmt(x, 1) : fmt(x, 2); }
  function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

  function compute() {
    var co = mode === "co";
    var kwhRate = n("gridlb") ? n("gridlb") * 0.45359237 / 1000 : F.kwh; // lb/MWh to kg/kWh
    var clean = clamp(n("clean"), 0, 100) / 100;
    var kwh = n("kwh");
    var elecLoc = kwh * kwhRate;
    var elecMkt = elecLoc * (1 - clean);
    var gas = n("therms") * F.therm, prop = n("propane") * F.propane;
    var gasGal, dieselGal;
    if (co) { gasGal = n("gas_gal"); dieselGal = n("diesel"); }
    else { gasGal = $("ev").checked ? 0 : (n("mpg") ? n("miles") / n("mpg") : 0); dieselGal = 0; }
    var car = gasGal * F.gasoline + dieselGal * F.diesel;
    var fly = n("f_short") * F.f_short + n("f_med") * F.f_med + n("f_long") * F.f_long;
    var transit = n("bus") * F.bus + n("crail") * F.crail + n("trail") * F.trail;
    // Households count the electricity they buy net of clean contracts; companies headline market-based Scope 2.
    var elec = elecMkt;
    var parts = [
      { k: "Electricity", v: elec, c: "#F2C14E" },
      { k: "Natural gas", v: gas, c: "#E4572E" },
      { k: "Propane", v: prop, c: "#F08A5D" },
      { k: co ? "Fleet fuel" : "Driving", v: car, c: "#B8401C" },
      { k: "Flights", v: fly, c: "#2B8A9E" },
      { k: "Transit", v: transit, c: "#7FC3D1" }
    ];
    var total = parts.reduce(function (s, p) { return s + p.v; }, 0); // kg
    var mmbtu = (kwh * B.kwh + n("therms") * B.therm + n("propane") * B.propane + gasGal * B.gasoline + dieselGal * B.diesel) / 1e6;

    $("r_total").textContent = t(total / 1000);
    $("r_energy").textContent = fmt(mmbtu, mmbtu >= 100 ? 0 : 1);
    $("r_cars").textContent = fmt(total / F.car_year, 1);
    if (co) {
      var emp = n("employees") || 1, rev = n("revenue");
      $("r_per").textContent = t(total / 1000 / emp) + " t per employee" + (rev ? ", " + t(total / 1000 / rev) + " t per $1 million of revenue" : "");
      $("r_scopes").innerHTML =
        "<div><span>Scope 1, fuels burned</span><b>" + t((gas + prop + car) / 1000) + " t</b></div>" +
        "<div><span>Scope 2, market based</span><b>" + t(elecMkt / 1000) + " t</b></div>" +
        "<div><span>Scope 2, location based</span><b>" + t(elecLoc / 1000) + " t</b></div>" +
        "<div><span>Scope 3, business travel</span><b>" + t((fly + transit) / 1000) + " t</b></div>";
    } else {
      var ppl = n("people") || 1;
      $("r_per").textContent = t(total / 1000 / ppl) + " t per person";
    }

    var max = Math.max.apply(null, parts.map(function (p) { return p.v; })) || 1;
    $("r_bars").innerHTML = parts.filter(function (p) { return p.v > 0; }).map(function (p) {
      var pct = total ? Math.round(p.v / total * 100) : 0;
      return '<div class="bar"><div class="bl"><span>' + p.k + "</span><span>" + t(p.v / 1000) + " t, " + pct + '%</span></div><div class="track"><div class="fill" style="width:' + (p.v / max * 100).toFixed(1) + "%;background:" + p.c + '"></div></div></div>';
    }).join("") || '<p class="per">Enter your numbers to see the breakdown.</p>';

    // Nexus Score: five levers, up to 20 points each
    var flyShare = total ? (fly / total) : 0;
    var flyPts = flyShare <= 0.10 ? 20 : flyShare <= 0.25 ? 10 : 0;
    var lev;
    if (co) {
      lev = [
        ["Clean electricity share", Math.round(clean * 20)],
        ["Electric share of fleet", Math.round(clamp(n("fleetev"), 0, 100) / 100 * 20)],
        ["Measured from meters and invoices", $("measured").checked ? 20 : 0],
        ["Emissions target", parseInt($("target").value, 10) || 0],
        ["Business flights share of footprint", flyPts]
      ];
    } else {
      var carPts = $("ev").checked ? 20 : Math.round(clamp((n("mpg") - 20) / 30, 0, 1) * 20);
      var heat = $("heat").value, heatPts = heat === "hp" ? 20 : heat === "resist" ? 10 : 0;
      lev = [
        ["Clean electricity share", Math.round(clean * 20)],
        ["Car efficiency", carPts],
        ["Heating", heatPts],
        ["Flights share of footprint", flyPts],
        ["Measured from real bills", $("measured").checked ? 20 : 0]
      ];
    }
    var score = lev.reduce(function (s, l) { return s + l[1]; }, 0);
    $("r_score").textContent = score;
    $("r_levers").innerHTML = lev.map(function (l) { return "<li><span>" + l[0] + "</span><b>" + l[1] + " / 20</b></li>"; }).join("");
  }

  function setMode(m) {
    mode = m;
    document.querySelectorAll(".mode button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.mode === m ? "true" : "false"); });
    document.querySelectorAll(".m-home").forEach(function (e) { e.hidden = m !== "home"; });
    document.querySelectorAll(".m-co").forEach(function (e) { e.hidden = m !== "co"; });
    if (m === "co") {
      if (!$("kwh").dataset.touched) $("kwh").value = 250000;
      if (!$("therms").dataset.touched) $("therms").value = 8000;
      if (!$("f_med").dataset.touched) $("f_med").value = 60000;
    } else {
      if (!$("kwh").dataset.touched) $("kwh").value = 12000;
      if (!$("therms").dataset.touched) $("therms").value = 600;
      if (!$("f_med").dataset.touched) $("f_med").value = 3000;
    }
    compute();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = $("calc");
    form.addEventListener("input", function (e) { if (e.target && e.target.id) e.target.dataset.touched = "1"; compute(); });
    form.addEventListener("change", compute);
    form.addEventListener("submit", function (e) { e.preventDefault(); });
    document.querySelectorAll(".mode button").forEach(function (b) { b.addEventListener("click", function () { setMode(b.dataset.mode); }); });
    setMode("home");
  });
})();
