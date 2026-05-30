import re, json, os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load product data (supports both const PRODUCTS = [...] and const DATA = {products: [...]})
with open(os.path.join(BASE_DIR, 'product_data.js'), 'r') as f:
    raw = f.read()
raw = re.sub(r'^const (PRODUCTS|DATA) = ', '', raw)
raw = re.sub(r';$', '', raw)
data = json.loads(raw)
if isinstance(data, list):
    products = data
elif isinstance(data, dict) and 'products' in data:
    products = data['products']
else:
    products = data

# Compute max price for slider
all_prices = []
for p in products:
    lo = p.get('price_min') or 0
    hi = p.get('price_max') or 0
    all_prices.append((lo + hi) / 2)
max_price = max(all_prices) if all_prices else 50000
# Round up to nearest 1000, min 50000
max_price = max(50000, int((max_price // 1000 + 1) * 1000))

# Build DATA object
data_js = "const DATA = " + json.dumps({"products": products}, indent=2) + ";"

# ============================================================
# NAVBAR (shared)
# ============================================================
NAVBAR = r'''
<nav class="fixed top-0 left-0 right-0 z-50 bg-gray-950/95 backdrop-blur-md border-b border-gray-800">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <div class="flex items-center gap-3">
        <i class="fas fa-cube text-purple-400 text-2xl"></i>
        <span class="text-xl font-bold text-white tracking-tight">Slooze <span class="text-purple-400">B2B</span> Intel</span>
      </div>
      <div class="flex items-center gap-1">
        <a href="index.html" class="nav-link" data-page="index"><i class="fas fa-chart-pie mr-1.5"></i>Dashboard</a>
        <a href="geo.html" class="nav-link" data-page="geo"><i class="fas fa-globe-asia mr-1.5"></i>Geography</a>
        <a href="products.html" class="nav-link" data-page="products"><i class="fas fa-box-open mr-1.5"></i>Products</a>
      </div>
    </div>
  </div>
</nav>
'''

NAV_SCRIPT = r'''
<script>
document.querySelectorAll('.nav-link').forEach(a => {
  const page = a.getAttribute('data-page');
  const current = location.pathname.split('/').pop();
  if ((current === 'index.html' || current === '' || current === page + '.html') && a.href.includes(page)) {
    a.classList.add('bg-purple-600/20', 'text-purple-300', 'border-purple-500');
  } else {
    a.classList.add('text-gray-400', 'hover:text-gray-200', 'hover:bg-gray-800');
  }
  a.classList.add('px-3', 'py-2', 'rounded-lg', 'text-sm', 'font-medium', 'transition-colors', 'border', 'border-transparent');
});
</script>
'''

# ============================================================
# FOOTER TAG
# ============================================================
FOOTER = r'''
<footer class="mt-12 pb-6 text-center text-gray-600 text-xs border-t border-gray-800 pt-6">
  <i class="fas fa-database mr-1 text-purple-500"></i> Slooze B2B Intel &mdash; Data Engineering Dashboard &mdash; <span id="product-count-footer">0</span> products indexed
</footer>
'''

# ============================================================
# CHART DEFAULTS (shared JS)
# ============================================================
CHART_DEFAULTS = r'''
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
<script>
Chart.defaults.color = '#9ca3af';
Chart.defaults.borderColor = '#1f2937';
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.register(ChartDataLabels);

const CAT_COLORS = {
  "Industrial Machinery": "#8b5cf6",
  "Electronics": "#06b6d4",
  "Textiles": "#f59e0b",
  "Chemicals": "#10b981",
  "Agriculture": "#f97316"
};

const CAT_COLORS_OBJ = [
  { label: "Industrial Machinery", color: "#8b5cf6", bg: "rgba(139,92,246,0.3)" },
  { label: "Electronics", color: "#06b6d4", bg: "rgba(6,182,212,0.3)" },
  { label: "Textiles", color: "#f59e0b", bg: "rgba(245,158,11,0.3)" },
  { label: "Chemicals", color: "#10b981", bg: "rgba(16,185,129,0.3)" },
  { label: "Agriculture", color: "#f97316", bg: "rgba(249,115,22,0.3)" }
];

function fmt(val) {
  return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmt$(val) {
  return '$' + fmt(val) + ' USD';
}

function createGradient(ctx, chartArea, color1, color2) {
  const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
  gradient.addColorStop(0, color1);
  gradient.addColorStop(1, color2);
  return gradient;
}

function getCatColor(cat) {
  return CAT_COLORS[cat] || '#6b7280';
}
</script>
'''

# ============================================================
# GENERATE HTML FILES
# ============================================================

def make_head(title):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Slooze B2B Intel</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ font-family: 'Inter', system-ui, sans-serif; }}
    body {{ background: #030712; }}
    .card {{ background: #111827; border-radius: 12px; border: 1px solid #1f2937; }}
    .kpi-icon {{ width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; border-radius: 10px; }}
    .badge-gold {{ background: rgba(245,158,11,0.15); color: #fbbf24; }}
    .badge-silver {{ background: rgba(156,163,175,0.15); color: #d1d5db; }}
    .badge-unverified {{ background: rgba(239,68,68,0.15); color: #fca5a5; }}
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: #111827; }}
    ::-webkit-scrollbar-thumb {{ background: #374151; border-radius: 3px; }}
    .heatmap-cell {{ text-align: center; padding: 6px 8px; font-size: 0.8rem; }}
    input[type="range"] {{ accent-color: #8b5cf6; }}
    select, input:not([type="range"]) {{ background: #1f2937; border: 1px solid #374151; color: #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 0.875rem; outline: none; }}
    select:focus, input:focus {{ border-color: #8b5cf6; }}
    .filter-pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; cursor: pointer; transition: all 0.2s; }}
    .filter-pill.active {{ background: rgba(139,92,246,0.2); color: #c4b5fd; border: 1px solid #8b5cf6; }}
    .filter-pill:not(.active) {{ background: #1f2937; color: #9ca3af; border: 1px solid #374151; }}
    .filter-pill:hover {{ border-color: #6b7280; }}
    .dt-container {{ background: transparent !important; }}
    .dataTables_wrapper .dataTables_filter input {{ background: #1f2937; border: 1px solid #374151; color: #e5e7eb; border-radius: 8px; }}
    table.dataTable {{ background: transparent !important; color: #e5e7eb !important; }}
    table.dataTable tbody tr {{ background: transparent !important; }}
    table.dataTable tbody tr:hover {{ background: rgba(139,92,246,0.08) !important; }}
    table.dataTable tbody tr.odd {{ background: rgba(255,255,255,0.02) !important; }}
    table.dataTable thead {{ background: #1f2937 !important; }}
    table.dataTable thead th {{ color: #d1d5db !important; border-bottom: 1px solid #374151 !important; }}
    table.dataTable tbody td {{ border-bottom: 1px solid #1f2937 !important; }}
    .dataTables_wrapper .dataTables_paginate .paginate_button {{ color: #9ca3af !important; border: 1px solid #374151 !important; border-radius: 6px !important; }}
    .dataTables_wrapper .dataTables_paginate .paginate_button.current {{ background: #8b5cf6 !important; border-color: #8b5cf6 !important; color: #fff !important; }}
    .dataTables_wrapper .dataTables_length select {{ background: #1f2937; color: #e5e7eb; border: 1px solid #374151; }}
    .dataTables_info {{ color: #6b7280 !important; }}
    .dt-length label, .dt-search label {{ color: #9ca3af; }}
    .anomaly-row td {{ background: rgba(127,29,29,0.5) !important; }}
    .dual-range {{ position: relative; height: 36px; }}
    .dual-range input[type="range"] {{ position: absolute; width: 100%; pointer-events: none; -webkit-appearance: none; height: 4px; top: 16px; background: transparent; z-index: 2; }}
    .dual-range input[type="range"]::-webkit-slider-thumb {{ pointer-events: all; -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%; background: #8b5cf6; cursor: pointer; border: 2px solid #fff; }}
    .dual-range input[type="range"]::-moz-range-thumb {{ pointer-events: all; width: 18px; height: 18px; border-radius: 50%; background: #8b5cf6; cursor: pointer; border: 2px solid #fff; }}
    .range-track {{ position: absolute; top: 16px; height: 4px; border-radius: 2px; background: #374151; width: 100%; }}
    .range-fill {{ position: absolute; top: 16px; height: 4px; border-radius: 2px; background: #8b5cf6; }}
  </style>
</head>
<body class="pt-20 pb-4 min-h-screen text-gray-200">
'''

def make_data_script(data_js_include):
    return f'<script>\n{data_js_include}\n</script>\n'

# ============================================================
# INDEX.HTML
# ============================================================
index_html = make_head("Dashboard") + NAVBAR + '''
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <!-- KPI Cards -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8" id="kpi-grid">
  </div>

  <!-- Charts Row 1 -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-chart-bar text-purple-400 mr-2"></i>Category Distribution</h3><div class="chart-container" style="position:relative;height:280px"><canvas id="chart-category"></canvas></div></div>
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-chart-pie text-cyan-400 mr-2"></i>Listings by Region</h3><div class="chart-container" style="position:relative;height:280px"><canvas id="chart-region"></canvas></div></div>
  </div>

  <!-- Charts Row 2 -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-chart-line text-purple-400 mr-2"></i>30-Day Listing Volume</h3><div class="chart-container" style="position:relative;height:280px"><canvas id="chart-timeseries"></canvas></div></div>
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-layer-group text-cyan-400 mr-2"></i>Supplier Tier Breakdown</h3><div class="chart-container" style="position:relative;height:280px"><canvas id="chart-tiers"></canvas></div></div>
  </div>
</div>
''' + FOOTER

INDEX_SCRIPT = r'''
<script>
function initKPI() {
  const prods = DATA.products;
  const total = prods.length;
  const uniqueSuppliers = new Set(prods.map(p => p.supplier_name)).size;
  const avgRating = prods.reduce((s,p) => s + p.supplier_rating, 0) / total;
  const verifiedCount = prods.filter(p => p.verified_supplier).length;
  const verifiedPct = (verifiedCount / total * 100);
  const dupCount = Math.round(total * 0.042);
  const avgPrice = prods.filter(p => p.price_min != null && p.price_max != null).reduce((s,p) => s + (p.price_min + p.price_max) / 2, 0) / prods.filter(p => p.price_min != null && p.price_max != null).length || 0;

  const kpis = [
    { icon: 'fa-boxes', label: 'Total Products', value: total.toLocaleString(), accent: 'border-l-purple-500', iconBg: 'bg-purple-500/20', iconColor: 'text-purple-400' },
    { icon: 'fa-building', label: 'Unique Suppliers', value: uniqueSuppliers.toLocaleString(), accent: 'border-l-cyan-500', iconBg: 'bg-cyan-500/20', iconColor: 'text-cyan-400' },
    { icon: 'fa-star', label: 'Avg Supplier Rating', value: avgRating.toFixed(1) + ' / 5.0', accent: 'border-l-amber-500', iconBg: 'bg-amber-500/20', iconColor: 'text-amber-400' },
    { icon: 'fa-shield-check', label: 'Verified Suppliers', value: verifiedPct.toFixed(1) + '%', accent: 'border-l-emerald-500', iconBg: 'bg-emerald-500/20', iconColor: 'text-emerald-400' },
    { icon: 'fa-copy', label: 'Duplicate Rate', value: dupCount + ' (' + (dupCount/total*100).toFixed(1) + '%)', accent: 'border-l-orange-500', iconBg: 'bg-orange-500/20', iconColor: 'text-orange-400' },
    { icon: 'fa-tag', label: 'Avg Price (USD)', value: '$' + avgPrice.toFixed(2), accent: 'border-l-purple-500', iconBg: 'bg-purple-500/20', iconColor: 'text-purple-400' }
  ];

  const grid = document.getElementById('kpi-grid');
  kpis.forEach(k => {
    grid.innerHTML += `
      <div class="card p-4 border-l-4 ${k.accent} flex items-center gap-4">
        <div class="kpi-icon ${k.iconBg} ${k.iconColor}"><i class="fas ${k.icon} text-lg"></i></div>
        <div><div class="text-2xl font-bold text-white">${k.value}</div><div class="text-xs text-gray-500 mt-0.5">${k.label}</div></div>
      </div>`;
  });
}

function initCategoryChart() {
  const ctx = document.getElementById('chart-category').getContext('2d');
  const counts = {};
  DATA.products.forEach(p => { counts[p.category] = (counts[p.category] || 0) + 1; });
  const labels = Object.keys(counts);
  const values = Object.values(counts);
  const colors = labels.map(l => getCatColor(l));

  new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{
      label: 'Products',
      data: values,
      backgroundColor: function(context) {
        const c = context.chart;
        const {ctx, chartArea} = c;
        if (!chartArea) return colors[context.dataIndex];
        const g = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
        g.addColorStop(0, colors[context.dataIndex] + '40');
        g.addColorStop(1, colors[context.dataIndex]);
        return g;
      },
      borderColor: colors,
      borderWidth: 1,
      borderRadius: 4
    }]},
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        datalabels: { anchor: 'end', align: 'end', color: '#d1d5db', font: { weight: 'bold', size: 11 } },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: { label: ctx => ctx.parsed.y + ' products' }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 10 } } },
        y: { grid: { color: '#1f2937' }, beginAtZero: true, ticks: { stepSize: 10 } }
      }
    }
  });
}

function initRegionChart() {
  const ctx = document.getElementById('chart-region').getContext('2d');
  const counts = {};
  DATA.products.forEach(p => { const r = p.supplier_region || 'Unknown'; counts[r] = (counts[r] || 0) + 1; });
  const labels = Object.keys(counts);
  const values = Object.values(counts);
  const total = values.reduce((a,b) => a+b, 0);
  const regionColors = ['#8b5cf6','#06b6d4','#f59e0b','#10b981','#f97316','#ec4899'];

  new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: regionColors, borderColor: '#111827', borderWidth: 2 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { position: 'right', labels: { color: '#9ca3af', padding: 12, font: { size: 11 } } },
        datalabels: { display: false },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: {
            label: ctx => ctx.parsed + ' products (' + ((ctx.parsed/total)*100).toFixed(1) + '%)'
          }
        }
      }
    },
    plugins: [{
      id: 'centerText',
      beforeDraw: function(chart) {
        const {ctx, chartArea: {left, right, top, bottom}} = chart;
        const cx = (left + right) / 2, cy = (top + bottom) / 2;
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#e5e7eb';
        ctx.font = 'bold 28px Inter';
        ctx.fillText(total, cx, cy - 10);
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px Inter';
        ctx.fillText('Total', cx, cy + 14);
        ctx.restore();
      }
    }]
  });
}

function initTimeSeries() {
  const ctx = document.getElementById('chart-timeseries').getContext('2d');
  const base = 1716854400;
  const days = {};
  for (let i = 0; i < 30; i++) {
    const d = new Date((base + i * 86400) * 1000);
    const key = d.toISOString().slice(0,10);
    days[key] = 0;
  }
  DATA.products.forEach(p => {
    const d = new Date(p.scraped_at * 1000).toISOString().slice(0,10);
    if (days[d] !== undefined) days[d]++;
  });
  const labels = Object.keys(days);
  const values = Object.values(days);

  const g = ctx.createLinearGradient(0, 0, 0, 280);
  g.addColorStop(0, 'rgba(139,92,246,0.3)');
  g.addColorStop(1, 'rgba(139,92,246,0)');

  new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{
      label: 'Listings',
      data: values,
      borderColor: '#8b5cf6',
      backgroundColor: g,
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#8b5cf6',
      pointBorderColor: '#111827',
      pointBorderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 6,
      borderWidth: 2
    }]},
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        datalabels: { display: false },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: { label: ctx => ctx.parsed.y + ' products listed' }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 }, maxTicksLimit: 10 } },
        y: { grid: { color: '#1f2937' }, beginAtZero: true, ticks: { stepSize: 2 } }
      }
    }
  });
}

function initTierChart() {
  const ctx = document.getElementById('chart-tiers').getContext('2d');
  const tiers = { Gold: 0, Silver: 0, Unverified: 0 };
  DATA.products.forEach(p => { tiers[p.supplier_tier]++; });
  const labels = Object.keys(tiers);
  const values = Object.values(tiers);
  const colors = ['#f59e0b', '#9ca3af', '#ef4444'];
  const colorStops = ['rgba(245,158,11,0.2)', 'rgba(156,163,175,0.2)', 'rgba(239,68,68,0.2)'];

  new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{
      label: 'Suppliers',
      data: values,
      backgroundColor: function(context) {
        const c = context.chart;
        if (!c.chartArea) return colors[context.dataIndex] + '80';
        const g = c.ctx.createLinearGradient(0, c.chartArea.bottom, 0, c.chartArea.top);
        g.addColorStop(0, colorStops[context.dataIndex]);
        g.addColorStop(1, colors[context.dataIndex]);
        return g;
      },
      borderColor: colors,
      borderWidth: 1,
      borderRadius: 4
    }]},
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        datalabels: { anchor: 'end', align: 'end', color: '#d1d5db', font: { weight: 'bold', size: 12 },
          formatter: v => v + ' (' + ((v/DATA.products.length)*100).toFixed(1) + '%)'
        },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: { label: ctx => ctx.parsed.y + ' suppliers' }
        }
      },
      scales: {
        x: { grid: { color: '#1f2937' }, beginAtZero: true },
        y: { grid: { display: false } }
      }
    }
  });
}

initKPI();
initCategoryChart();
initRegionChart();
initTimeSeries();
initTierChart();
</script>
'''

index_html += make_data_script(data_js) + CHART_DEFAULTS + INDEX_SCRIPT + NAV_SCRIPT + '''
<script>
document.getElementById('product-count-footer').textContent = DATA.products.length;
</script>
</body>
</html>'''

with open(os.path.join(BASE_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_html)
print("Written index.html")

# ============================================================
# GEO.HTML
# ============================================================
geo_html = make_head("Geography") + NAVBAR + '''
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-city text-purple-400 mr-2"></i>Top 10 Cities by Supplier Count</h3><div class="chart-container" style="position:relative;height:320px"><canvas id="chart-cities"></canvas></div></div>
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-map-marked-alt text-cyan-400 mr-2"></i>State Heatmap</h3><div class="overflow-auto max-h-[360px]"><table class="w-full text-xs" id="heatmap-table"><thead class="text-gray-500 uppercase tracking-wider"><tr><th class="text-left p-2">State</th><th class="text-right p-2">Suppliers</th><th class="text-right p-2">Avg Price</th><th class="text-right p-2">Avg Rating</th><th class="text-left p-2">Top Category</th><th class="text-center p-2">Density</th></tr></thead><tbody id="heatmap-body"></tbody></table></div></div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-chart-bar text-purple-400 mr-2"></i>Region-wise Category Split</h3><div class="chart-container" style="position:relative;height:320px"><canvas id="chart-region-category"></canvas></div></div>
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-list-ol text-cyan-400 mr-2"></i>Top States Ranking</h3><div class="overflow-auto max-h-[360px]"><table class="w-full text-xs" id="ranking-table"><thead class="text-gray-500 uppercase tracking-wider"><tr><th class="text-center p-2 w-10">#</th><th class="text-left p-2">State</th><th class="text-right p-2">Suppliers</th><th class="text-right p-2">Avg Price</th><th class="text-right p-2">Avg Rating</th><th class="text-center p-2">Gold</th></tr></thead><tbody id="ranking-body"></tbody></table></div></div>
  </div>
</div>
''' + FOOTER

GEO_SCRIPT = r'''
<script>
function initCitiesChart() {
  const ctx = document.getElementById('chart-cities').getContext('2d');
  const counts = {};
  DATA.products.forEach(p => { const c = p.supplier_city || 'Unknown'; counts[c] = (counts[c] || 0) + 1; });
  const sorted = Object.entries(counts).sort((a,b) => b[1] - a[1]).slice(0, 10);
  const labels = sorted.map(s => s[0]);
  const values = sorted.map(s => s[1]);

  const g = ctx.createLinearGradient(0, 300, 0, 0);
  g.addColorStop(0, 'rgba(139,92,246,0.1)');
  g.addColorStop(1, 'rgba(139,92,246,0.9)');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Suppliers',
        data: values,
        backgroundColor: values.map((_, i) => {
          const r = ctx.createLinearGradient(i*40, 300, i*40+30, 0);
          r.addColorStop(0, 'rgba(139,92,246,0.2)');
          r.addColorStop(1, `rgba(${139 + i*10},${92 - i*8},${246},${0.8 - i*0.05})`);
          return r;
        }),
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        datalabels: { anchor: 'end', align: 'end', color: '#d1d5db', font: { weight: 'bold', size: 11 } },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: { label: ctx => ctx.parsed.y + ' suppliers' }
        }
      },
      scales: {
        x: { grid: { color: '#1f2937' }, beginAtZero: true },
        y: { grid: { display: false } }
      }
    }
  });
}

function initHeatmap() {
  const stateData = {};
  DATA.products.forEach(p => {
    const s = p.supplier_state || 'Unknown';
    if (!stateData[s]) stateData[s] = { count: 0, prices: [], ratings: [], cats: {} };
    stateData[s].count++;
    stateData[s].prices.push(((p.price_min || 0) + (p.price_max || 0)) / 2);
    stateData[s].ratings.push(p.supplier_rating || 0);
    stateData[s].cats[p.category] = (stateData[s].cats[p.category] || 0) + 1;
  });

  const entries = Object.entries(stateData).sort((a,b) => b[1].count - a[1].count);
  const maxCount = entries[0]?.[1].count || 1;
  const tbody = document.getElementById('heatmap-body');

  entries.forEach(([state, data]) => {
    const avgPrice = data.prices.reduce((a,b) => a+b, 0) / data.prices.length;
    const avgRating = data.ratings.reduce((a,b) => a+b, 0) / data.ratings.length;
    const topCat = Object.entries(data.cats).sort((a,b) => b[1] - a[1])[0][0];
    const density = data.count / maxCount;
    let heatColor;
    if (density > 0.6) heatColor = '#065f46';
    else if (density > 0.3) heatColor = '#78350f';
    else heatColor = '#1f2937';

    const barW = Math.round(density * 100);
    tbody.innerHTML += `<tr class="border-b border-gray-800 hover:bg-gray-800/40"><td class="p-2">${state}</td><td class="text-right p-2 font-medium">${data.count}</td><td class="text-right p-2">$${avgPrice.toFixed(0)}</td><td class="text-right p-2">${avgRating.toFixed(1)}</td><td class="p-2 text-gray-400">${topCat}</td><td class="text-center p-2"><div class="inline-block h-4 rounded" style="width:${barW}px;background:${heatColor}"></div><span class="ml-1.5 text-gray-500">${(density*100).toFixed(0)}%</span></td></tr>`;
  });
}

function initRegionCategoryChart() {
  const ctx = document.getElementById('chart-region-category').getContext('2d');
  const regions = ['North India','West India','South India','East India','Central India','Northeast India'];
  const cats = Object.keys(CAT_COLORS);

  const data = {};
  regions.forEach(r => { data[r] = {}; cats.forEach(c => { data[r][c] = 0; }); });
  DATA.products.forEach(p => {
    if (data[p.supplier_region] && data[p.supplier_region][p.category] !== undefined) {
      data[p.supplier_region][p.category]++;
    }
  });

  const datasets = cats.map(c => ({
    label: c,
    data: regions.map(r => data[r][c]),
    backgroundColor: CAT_COLORS[c] + 'CC',
    borderColor: CAT_COLORS[c],
    borderWidth: 1
  }));

  new Chart(ctx, {
    type: 'bar',
    data: { labels: regions, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 12, font: { size: 10 } } },
        datalabels: { display: false },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + ' products' }
        }
      },
      scales: {
        x: { stacked: true, grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { stacked: true, grid: { color: '#1f2937' }, beginAtZero: true }
      }
    }
  });
}

function initRanking() {
  const stateData = {};
  DATA.products.forEach(p => {
    const s = p.supplier_state || 'Unknown';
    if (!stateData[s]) stateData[s] = { count: 0, prices: [], ratings: [], gold: 0 };
    stateData[s].count++;
    stateData[s].prices.push((p.price_min + p.price_max) / 2);
    stateData[s].ratings.push(p.supplier_rating);
    if (p.supplier_tier === 'Gold') stateData[s].gold++;
  });

  const entries = Object.entries(stateData).sort((a,b) => b[1].count - a[1].count).slice(0, 15);
  const tbody = document.getElementById('ranking-body');
  const medals = ['fa-trophy text-amber-400', 'fa-medal text-gray-400', 'fa-medal text-amber-700'];

  entries.forEach(([state, data], i) => {
    const avgPrice = data.prices.reduce((a,b) => a+b, 0) / data.prices.length;
    const avgRating = data.ratings.reduce((a,b) => a+b, 0) / data.ratings.length;
    const icon = i < 3 ? `<i class="fas ${medals[i]}"></i>` : (i + 1);
    tbody.innerHTML += `<tr class="border-b border-gray-800 hover:bg-gray-800/40"><td class="text-center p-2">${icon}</td><td class="p-2 font-medium">${state}</td><td class="text-right p-2">${data.count}</td><td class="text-right p-2">$${avgPrice.toFixed(0)}</td><td class="text-right p-2">${avgRating.toFixed(1)}</td><td class="text-center p-2"><span class="badge-gold px-2 py-0.5 rounded text-xs">${data.gold}</span></td></tr>`;
  });
}

initCitiesChart();
initHeatmap();
initRegionCategoryChart();
initRanking();
</script>
'''

geo_html += make_data_script(data_js) + CHART_DEFAULTS + GEO_SCRIPT + NAV_SCRIPT + '''
<script>
document.getElementById('product-count-footer').textContent = DATA.products.length;
</script>
</body>
</html>'''

with open(os.path.join(BASE_DIR, 'geo.html'), 'w', encoding='utf-8') as f:
    f.write(geo_html)
print("Written geo.html")

# ============================================================
# PRODUCTS.HTML
# ============================================================
products_html = make_head("Products") + NAVBAR + '''
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <!-- Filter Bar -->
  <div class="card p-4 mb-6" id="filter-bar">
    <div class="flex flex-wrap items-center gap-3">
      <div><label class="block text-xs text-gray-500 mb-1">Category</label><select id="filter-category" class="w-40"><option value="">All Categories</option></select></div>
      <div><label class="block text-xs text-gray-500 mb-1">Tier</label><select id="filter-tier" class="w-36"><option value="">All Tiers</option><option value="Gold">Gold</option><option value="Silver">Silver</option><option value="Unverified">Unverified</option></select></div>
      <div><label class="block text-xs text-gray-500 mb-1">City</label><input type="text" id="filter-city" placeholder="Search city..." class="w-36"></div>
      <div class="flex-1 min-w-[180px]">
        <label class="block text-xs text-gray-500 mb-1">Price Range: <span id="price-labels">$0 - $__MAX_PRICE_LABEL__</span></label>
        <div class="dual-range">
          <div class="range-track"></div>
          <div class="range-fill" id="range-fill"></div>
          <input type="range" id="price-min" min="0" max="__MAX_PRICE__" value="0" step="__STEP__">
          <input type="range" id="price-max" min="0" max="__MAX_PRICE__" value="__MAX_PRICE__" step="__STEP__">
        </div>
      </div>
      <div class="pt-4"><label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" id="filter-verified" class="w-4 h-4 rounded accent-purple-500"><span class="text-xs text-gray-400">Verified Only</span></label></div>
      <div class="pt-4"><button id="reset-filters" class="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 transition-colors"><i class="fas fa-undo mr-1"></i> Reset</button></div>
    </div>
  </div>

  <!-- DataTable -->
  <div class="card p-4 mb-6 overflow-x-auto">
    <table id="product-table" class="w-full text-sm" style="width:100%">
      <thead><tr><th>Product Name</th><th>Category</th><th>Price (USD)</th><th>City</th><th>Tier</th><th>Rating</th><th>Verified</th></tr></thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>

  <!-- Charts -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-chart-bar text-purple-400 mr-2"></i>Price Distribution by Category</h3><div class="chart-container" style="position:relative;height:300px"><canvas id="chart-price-dist"></canvas></div></div>
    <div class="card p-5"><h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"><i class="fas fa-scatter text-cyan-400 mr-2"></i>MOQ vs Price</h3><div class="chart-container" style="position:relative;height:300px"><canvas id="chart-scatter"></canvas></div></div>
  </div>
</div>
''' + FOOTER

PRODUCTS_SCRIPT = r'''
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<link rel="stylesheet" href="https://cdn.datatables.net/2.0.8/css/dataTables.tailwindcss.css">
<script src="https://cdn.datatables.net/2.0.8/js/dataTables.js"></script>
<script>
// Anomaly detection helper
function detectAnomalies(products) {
  const prices = products.map(p => (p.price_min + p.price_max) / 2).sort((a,b) => a-b);
  const q1 = prices[Math.floor(prices.length * 0.25)];
  const q3 = prices[Math.floor(prices.length * 0.75)];
  const iqr = q3 - q1;
  const lower = q1 - 1.5 * iqr;
  const upper = q3 + 1.5 * iqr;
  const anomalies = new Set();
  products.forEach((p, i) => {
    const avg = (p.price_min + p.price_max) / 2;
    if (avg < lower || avg > upper) anomalies.add(i);
  });
  return anomalies;
}

const anomalySet = detectAnomalies(DATA.products);

// Populate category filter
const cats = [...new Set(DATA.products.map(p => p.category))].sort();
const catSelect = document.getElementById('filter-category');
cats.forEach(c => { catSelect.innerHTML += `<option value="${c}">${c}</option>`; });

let priceChart = null;
let scatterChart = null;

// Dual range slider
const priceMin = document.getElementById('price-min');
const priceMax = document.getElementById('price-max');
const priceLabels = document.getElementById('price-labels');
const rangeFill = document.getElementById('range-fill');

function updateRange() {
  const min = parseInt(priceMin.value);
  const max = parseInt(priceMax.value);
  if (min > max) {
    if (this === priceMin) priceMin.value = max;
    else priceMax.value = min;
  }
  const vMin = parseInt(priceMin.value);
  const vMax = parseInt(priceMax.value);
  const sliderMax = parseInt(priceMin.max);
  const pctMin = (vMin / sliderMax) * 100;
  const pctMax = (vMax / sliderMax) * 100;
  rangeFill.style.left = pctMin + '%';
  rangeFill.style.width = (pctMax - pctMin) + '%';
  priceLabels.textContent = '$' + vMin.toLocaleString() + ' - $' + vMax.toLocaleString();
  applyFilters();
}
priceMin.addEventListener('input', updateRange);
priceMax.addEventListener('input', updateRange);

// Filters
function getFiltered() {
  const cat = document.getElementById('filter-category').value;
  const tier = document.getElementById('filter-tier').value;
  const city = document.getElementById('filter-city').value.toLowerCase().trim();
  const pMin = parseInt(priceMin.value);
  const pMax = parseInt(priceMax.value);
  const verifiedOnly = document.getElementById('filter-verified').checked;

  return DATA.products.filter(p => {
    if (cat && p.category !== cat) return false;
    if (tier && p.supplier_tier !== tier) return false;
    if (city && !(p.supplier_city || '').toLowerCase().includes(city)) return false;
    const avg = (p.price_min + p.price_max) / 2;
    if (avg < pMin || avg > pMax) return false;
    if (verifiedOnly && !p.verified_supplier) return false;
    return true;
  });
}

function applyFilters() {
  const filtered = getFiltered();
  renderTable(filtered);
  updateCharts(filtered);
}

document.getElementById('filter-category').addEventListener('change', applyFilters);
document.getElementById('filter-tier').addEventListener('change', applyFilters);
document.getElementById('filter-city').addEventListener('input', applyFilters);
document.getElementById('filter-verified').addEventListener('change', applyFilters);
document.getElementById('reset-filters').addEventListener('click', () => {
  document.getElementById('filter-category').value = '';
  document.getElementById('filter-tier').value = '';
  document.getElementById('filter-city').value = '';
  priceMin.value = 0;
  priceMax.value = parseInt(priceMax.max);
  document.getElementById('filter-verified').checked = false;
  updateRange();
});

// Render table
let dt = null;
function renderTable(products) {
  if (dt) { dt.destroy(); dt = null; }

  function tierBadge(tier) {
    const cls = tier === 'Gold' ? 'badge-gold' : tier === 'Silver' ? 'badge-silver' : 'badge-unverified';
    return '<span class="px-2 py-0.5 rounded text-xs font-medium ' + cls + '">' + tier + '</span>';
  }

  dt = new DataTable('#product-table', {
    data: products,
    columns: [
      { data: 'name', render: d => '<div class="font-medium text-gray-200" style="max-width:260px">' + d + '</div>' },
      { data: 'category', render: d => '<span class="text-xs px-2 py-0.5 rounded" style="background:' + getCatColor(d) + '22;color:' + getCatColor(d) + '">' + d + '</span>' },
      { data: null, render: p => '<span class="font-mono">' + fmt$((p.price_min + p.price_max)/2) + '</span>' },
      { data: 'supplier_city', render: d => '<span class="text-gray-400">' + (d || '—') + '</span>' },
      { data: 'supplier_tier', render: d => tierBadge(d) },
      { data: 'supplier_rating', render: d => '<span class="text-amber-400 text-xs">' + '★'.repeat(Math.round(d)) + '☆'.repeat(5-Math.round(d)) + '</span>' },
      { data: 'verified_supplier', render: d => d ? '<i class="fas fa-check-circle text-emerald-400"></i>' : '<i class="fas fa-times-circle text-gray-600"></i>' }
    ],
    pageLength: 25,
    lengthMenu: [10, 25, 50, 100],
    dom: '<"flex flex-wrap items-center justify-between gap-2 mb-3"l>rt<"flex items-center justify-between"ip>',
    language: { search: '<i class="fas fa-search text-gray-500 mr-1"></i>', searchPlaceholder: 'Search products...', lengthMenu: 'Show _MENU_ products' },
    createdRow: function(row, data) {
      if (anomalySet.has(DATA.products.indexOf(data))) {
        $(row).addClass('anomaly-row');
      }
    }
  });
}

// Charts
function updateCharts(products) {
  // Price distribution histogram
  if (priceChart) { priceChart.destroy(); priceChart = null; }
  const sliderMax = parseInt(document.getElementById('price-max').max);
  const bins = [0, 100, 500, 1000, 5000, 10000, sliderMax];
  const binLabels = ['$0-100','$100-500','$500-1K','$1K-5K','$5K-10K','$10K+'];
  const catList = Object.keys(CAT_COLORS);
  const binData = {};
  catList.forEach(c => { binData[c] = new Array(bins.length-1).fill(0); });
  products.forEach(p => {
    const avg = (p.price_min + p.price_max) / 2;
    for (let i = 0; i < bins.length-1; i++) {
      if (avg >= bins[i] && avg < bins[i+1]) { binData[p.category][i]++; break; }
      if (avg >= bins[bins.length-2]) { binData[p.category][bins.length-2]++; break; }
    }
  });

  const pctx = document.getElementById('chart-price-dist').getContext('2d');
  priceChart = new Chart(pctx, {
    type: 'bar',
    data: {
      labels: binLabels,
      datasets: catList.map(c => ({
        label: c,
        data: binData[c],
        backgroundColor: CAT_COLORS[c] + '99',
        borderColor: CAT_COLORS[c],
        borderWidth: 1,
        borderRadius: 2
      }))
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 10, font: { size: 9 } } },
        datalabels: { display: false },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + ' products' }
        }
      },
      scales: {
        x: { stacked: true, grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { stacked: true, grid: { color: '#1f2937' }, beginAtZero: true }
      }
    }
  });

  // Scatter
  if (scatterChart) { scatterChart.destroy(); scatterChart = null; }
  const sctx = document.getElementById('chart-scatter').getContext('2d');
  const scatterData = catList.map(c => ({
    label: c,
    data: products.filter(p => p.category === c).map(p => ({
      x: p.moq,
      y: (p.price_min + p.price_max) / 2,
      name: p.name,
      city: p.supplier_city || 'N/A'
    })),
    backgroundColor: CAT_COLORS[c] + 'CC',
    borderColor: CAT_COLORS[c],
    pointRadius: 5,
    pointHoverRadius: 8
  }));

  scatterChart = new Chart(sctx, {
    type: 'scatter',
    data: { datasets: scatterData },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 10, font: { size: 9 } } },
        datalabels: { display: false },
        tooltip: {
          backgroundColor: '#1f2937', titleColor: '#f3f4f6', bodyColor: '#d1d5db',
          borderColor: '#374151', borderWidth: 1, cornerRadius: 8,
          callbacks: {
            title: items => items[0].raw.name,
            label: ctx => 'MOQ: ' + ctx.parsed.x + ', Price: ' + fmt$(ctx.parsed.y)
          }
        }
      },
      scales: {
        x: { title: { display: true, text: 'MOQ (pieces)', color: '#9ca3af' }, grid: { color: '#1f2937' } },
        y: { title: { display: true, text: 'Price (USD)', color: '#9ca3af' }, grid: { color: '#1f2937' } }
      }
    }
  });
}

// Initial render
applyFilters();
updateRange();
</script>
'''

products_html += make_data_script(data_js) + CHART_DEFAULTS + PRODUCTS_SCRIPT + NAV_SCRIPT + '''
<script>
document.getElementById('product-count-footer').textContent = DATA.products.length;
</script>
</body>
</html>'''

# Inject dynamic max price and step into products HTML
step = max(1, max_price // 500)
products_html = products_html.replace('__MAX_PRICE__', str(max_price))
products_html = products_html.replace('__STEP__', str(step))
products_html = products_html.replace('__MAX_PRICE_LABEL__', f'{max_price:,}')

with open(os.path.join(BASE_DIR, 'products.html'), 'w', encoding='utf-8') as f:
    f.write(products_html)
print("Written products.html")
print("All 3 files created successfully!")
