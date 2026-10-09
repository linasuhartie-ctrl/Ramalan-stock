let scanItems = [];
let chart = null;
let lastScan = null;
let selectedCode = null;

const $ = (id) => document.getElementById(id);


/* =====================================================
   UTILITAS
   ===================================================== */

function money(n) {
  const value = Number(n);

  if (!Number.isFinite(value)) return '—';

  return value.toLocaleString('id-ID', {
    maximumFractionDigits: 2
  });
}


function pct(n) {
  const value = Number(n);

  if (!Number.isFinite(value)) return '—';

  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
}


function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[c]);
}


function setText(id, value) {
  const el = $(id);

  if (el) {
    el.textContent = value;
  }
}


/* =====================================================
   NAVIGASI BAWAH
   ===================================================== */

function setActiveNavigation(page) {
  document.querySelectorAll('.bottom-nav a').forEach(link => {
    const active = link.dataset.page === page;

    link.classList.toggle('active', active);

    if (active) {
      link.setAttribute('aria-current', 'page');
    } else {
      link.removeAttribute('aria-current');
    }
  });
}


function navigateTo(page) {
  const destinations = {
    scanner: 'scannerPanel',
    analysis: 'analysisPanel',
    status: 'statusPanel'
  };

  const targetId = destinations[page];
  const target = targetId ? $(targetId) : null;

  if (!target) {
    console.error('Tujuan navigasi tidak ditemukan:', page);
    return;
  }

  setActiveNavigation(page);

  target.scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  });

  if (page === 'status') {
    checkStatus();
  }
}


function setupNavigation() {
  document.querySelectorAll('.bottom-nav a[data-page]').forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();

      const page = link.dataset.page;

      navigateTo(page);

      history.replaceState(null, '', `#${link.getAttribute('href').slice(1)}`);
    });
  });
}


/* =====================================================
   STATUS API DAN BACKEND
   ===================================================== */

async function checkStatus() {
  const badge = $('apiBadge');

  if (badge) {
    badge.textContent = 'MEMERIKSA API…';
  }

  setText('backendStatus', 'Memeriksa…');
  setText('statusApiKey', 'Memeriksa…');
  setText('statusConnection', 'Menghubungi backend…');

  try {
    const response = await fetch('/api/status', {
      cache: 'no-store'
    });

    let statusData = {};

    try {
      statusData = await response.json();
    } catch (_) {
      statusData = {};
    }

    if (!response.ok) {
      throw new Error(
        statusData.error || `HTTP ${response.status}`
      );
    }

    const keyConfigured = Boolean(statusData.api_key_configured);

    if (badge) {
      badge.textContent = keyConfigured
        ? 'API KEY TERPASANG'
        : 'API KEY BELUM DIATUR';

      badge.style.color = keyConfigured
        ? '#39d7a0'
        : '#ffca73';
    }

    setText('backendStatus', 'ONLINE');
    $('backendStatus').className = 'status-ok';

    setText(
      'statusApiKey',
      keyConfigured ? 'TERPASANG' : 'BELUM DIATUR'
    );

    $('statusApiKey').className = keyConfigured
      ? 'status-ok'
      : 'status-warn';

    setText(
      'statusConnection',
      keyConfigured
        ? 'Backend merespons dan variabel API key terdeteksi. Ini belum membuktikan bahwa permintaan data Arjum berhasil.'
        : 'Backend merespons, tetapi API key belum terdeteksi. Periksa Environment Variables di SnapDeploy.'
    );

    setText(
      'providerNote',
      keyConfigured
        ? 'Backend merespons. Ketersediaan data harus diverifikasi melalui hasil scan.'
        : 'API key belum terdeteksi. Periksa konfigurasi backend.'
    );

  } catch (error) {
    if (badge) {
      badge.textContent = 'BACKEND OFFLINE';
      badge.style.color = '#ff7a90';
    }

    setText('backendStatus', 'TIDAK TERHUBUNG');
    $('backendStatus').className = 'status-error';

    setText('statusApiKey', 'TIDAK DIKETAHUI');
    $('statusApiKey').className = 'status-warn';

    setText(
      'statusConnection',
      `Pemeriksaan gagal: ${error.message}`
    );

    setText(
      'providerNote',
      `Backend tidak dapat diperiksa: ${error.message}`
    );
  }

  updateLastScanStatus();
}


/* =====================================================
   RINGKASAN PEMINDAIAN
   ===================================================== */

function updateLastScanStatus() {
  if (!lastScan) {
    setText('statusTimeframe', 'Belum ada scan');
    setText('statusScanned', '—');
    setText(
      'statusScanSummary',
      'Belum ada pemindaian yang dijalankan pada sesi halaman ini.'
    );

    return;
  }

  setText(
    'statusTimeframe',
    lastScan.timeframe || 'Tidak diketahui'
  );

  setText(
    'statusScanned',
    String(lastScan.scanned ?? 0)
  );

  const requested = lastScan.requested ?? '—';
  const scanned = lastScan.scanned ?? 0;
  const errors = lastScan.errors_count ?? 0;

  setText(
    'statusScanSummary',
    `Timeframe: ${lastScan.timeframe || '—'}. ` +
    `Berhasil dihitung: ${scanned} dari ${requested} permintaan. ` +
    `Saham gagal diproses: ${errors}.`
  );
}


/* =====================================================
   SCAN SAHAM
   ===================================================== */

async function runScan() {
  const button = $('scanBtn');

  button.disabled = true;
  button.textContent = 'Memindai…';

  $('results').innerHTML = `
    <tr>
      <td colspan="5" class="empty">
        Mengambil data dan menghitung model GPR.
        Proses awal dapat memerlukan waktu.
      </td>
    </tr>
  `;

  $('errors').classList.add('hidden');

  try {
    const query = new URLSearchParams({
      timeframe: $('timeframe').value,
      horizon: $('horizon').value,
      limit: $('limit').value
    });

    const response = await fetch(`/api/scan?${query.toString()}`, {
      cache: 'no-store'
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Permintaan scan gagal.');
    }

    scanItems = Array.isArray(data.items)
      ? data.items
      : [];

    lastScan = {
      timeframe: data.timeframe || $('timeframe').value,
      scanned: data.scanned ?? scanItems.length,
      requested: data.requested ?? $('limit').value,
      errors_count: data.errors_count ?? 0
    };

    renderResults(scanItems);

    setText('scanned', data.scanned ?? scanItems.length);

    setText(
      'universe',
      `Sumber: ${data.universe_source || 'Arjum'}`
    );

    setText(
      'candidates',
      scanItems.filter(x => x.signal === 'KANDIDAT').length
    );

    setText(
      'bestReturn',
      scanItems.length
        ? pct(scanItems[0].gpr_return_pct)
        : '—'
    );

    if (data.errors_count) {
      $('errors').classList.remove('hidden');

      const examples = (data.errors || [])
        .slice(0, 4)
        .map(x => `${x.code}: ${x.error}`)
        .join(' · ');

      $('errors').textContent =
        `${data.errors_count} saham gagal diproses.` +
        (examples ? ` ${examples}` : '');
    }

    setText(
      'providerNote',
      `Timeframe diminta: ${data.timeframe || $('timeframe').value}. ` +
      `${data.scanned ?? scanItems.length} berhasil dihitung dari ` +
      `${data.requested ?? $('limit').value} permintaan.`
    );

    updateLastScanStatus();

  } catch (error) {
    $('results').innerHTML = `
      <tr>
        <td colspan="5" class="empty">
          ${escapeHtml(error.message)}
        </td>
      </tr>
    `;

    setText('providerNote', error.message);

  } finally {
    button.disabled = false;
    button.textContent = '▶ Jalankan GPR Scanner';
  }
}


/* =====================================================
   TABEL RANKING
   ===================================================== */

function renderResults(items) {
  const searchTerm = $('search').value
    .trim()
    .toLowerCase();

  const filtered = items.filter(item =>
    String(item.code || '')
      .toLowerCase()
      .includes(searchTerm)
  );

  if (!filtered.length) {
    $('results').innerHTML = `
      <tr>
        <td colspan="5" class="empty">
          Tidak ada saham yang cocok atau belum ada data.
        </td>
      </tr>
    `;

    return;
  }

  $('results').innerHTML = filtered.map(item => {
    const code = escapeHtml(item.code || '');
    const signal = escapeHtml(item.signal || '');
    const trend = escapeHtml(item.trend || 'UNKNOWN');

    const returnValue = Number(item.gpr_return_pct);
    const relativeVolume = Number(item.relative_volume);
    const score = Number(item.score);

    return `
      <tr data-code="${code}" tabindex="0" role="button"
          aria-label="Analisis saham ${code}">

        <td>
          <span class="code">${code}</span>
          <span class="sub">${signal}</span>
        </td>

        <td class="${returnValue >= 0 ? 'pos' : 'neg'}">
          ${pct(returnValue)}
        </td>

        <td>
          <span class="trend ${trend === 'BEARISH' ? 'down' : ''}">
            ${trend}
          </span>
        </td>

        <td>
          ${Number.isFinite(relativeVolume)
            ? relativeVolume.toFixed(2) + '×'
            : '—'}
        </td>

        <td>
          ${Number.isFinite(score) ? score.toFixed(0) : '—'}
        </td>

      </tr>
    `;
  }).join('');

  document.querySelectorAll('#results tr[data-code]').forEach(row => {
    const openAnalysis = () => {
      analyze(row.dataset.code);
    };

    row.addEventListener('click', openAnalysis);

    row.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openAnalysis();
      }
    });
  });
}


/* =====================================================
   ANALISIS DAN GRAFIK GPR
   ===================================================== */

async function analyze(code) {
  selectedCode = code;

  navigateTo('analysis');

  setText('analysisTitle', `Analisis ${code}`);
  setText('analysisMeta', 'Menghitung proyeksi…');

  $('projectionRows').innerHTML = `
    <tr>
      <td colspan="5" class="empty">
        Menghitung proyeksi GPR…
      </td>
    </tr>
  `;

  const query = new URLSearchParams({
    timeframe: $('timeframe').value,
    horizon: $('horizon').value
  });

  try {
    const response = await fetch(
      `/api/analyze/${encodeURIComponent(code)}?${query.toString()}`,
      { cache: 'no-store' }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Analisis gagal.');
    }

    const predictions = Array.isArray(data.predictions)
      ? data.predictions
      : [];

    $('analysisMeta').innerHTML = `
      Harga terakhir: <b>${money(data.price)}</b>
      · Tren: <b>${escapeHtml(data.trend || '—')}</b>
      · Momentum: <b>${escapeHtml(data.momentum || '—')}</b>
      · Rel. volume: <b>${escapeHtml(data.relative_volume ?? '—')}×</b>
      <br>
      Return GPR pada candle ke-${escapeHtml(data.horizon ?? '—')}:
      <b class="${Number(data.gpr_return_pct) >= 0 ? 'pos' : 'neg'}">
        ${pct(data.gpr_return_pct)}
      </b>
      · Data: ${escapeHtml(data.bars ?? '—')} candle
    `;

    if (!predictions.length) {
      $('projectionRows').innerHTML = `
        <tr>
          <td colspan="5" class="empty">
            Data proyeksi tidak tersedia.
          </td>
        </tr>
      `;
    } else {
      $('projectionRows').innerHTML = predictions.map(prediction => `
        <tr>
          <td>${escapeHtml(prediction.step)}</td>
          <td>${money(prediction.price)}</td>
          <td class="${Number(prediction.return_pct) >= 0 ? 'pos' : 'neg'}">
            ${pct(prediction.return_pct)}
          </td>
          <td>${money(prediction.upper)}</td>
          <td>${money(prediction.lower)}</td>
        </tr>
      `).join('');
    }

    const labels = [
      'Sekarang',
      ...predictions.map(prediction => `+${prediction.step}`)
    ];

    const values = [
      Number(data.price),
      ...predictions.map(prediction => Number(prediction.price))
    ];

    const canvas = $('projectionChart');

    if (chart) {
      chart.destroy();
      chart = null;
    }

    if (canvas && window.Chart) {
      chart = new Chart(canvas, {
        type: 'line',

        data: {
          labels,

          datasets: [{
            label: 'Harga proyeksi GPR',
            data: values,
            borderColor: '#39d7a0',
            backgroundColor: '#39d7a022',
            fill: true,
            tension: 0.2,
            pointRadius: 3
          }]
        },

        options: {
          responsive: true,
          maintainAspectRatio: false,

          plugins: {
            legend: {
              labels: {
                color: '#91a2ba'
              }
            }
          },

          scales: {
            x: {
              ticks: {
                color: '#91a2ba'
              },
              grid: {
                color: '#243147'
              }
            },

            y: {
              ticks: {
                color: '#91a2ba'
              },
              grid: {
                color: '#243147'
              }
            }
          }
        }
      });
    }

  } catch (error) {
    setText(
      'analysisMeta',
      `Tidak dapat menganalisis ${code}: ${error.message}`
    );

    $('projectionRows').innerHTML = `
      <tr>
        <td colspan="5" class="empty">
          ${escapeHtml(error.message)}
        </td>
      </tr>
    `;
  }
}


/* =====================================================
   EVENT LISTENERS
   ===================================================== */

$('scanBtn').addEventListener('click', runScan);

$('refreshBtn').addEventListener('click', runScan);

$('search').addEventListener('input', () => {
  renderResults(scanItems);
});

$('timeframe').addEventListener('change', () => {
  setText(
    'providerNote',
    'Timeframe berubah. Jalankan scan ulang untuk memuat data timeframe tersebut.'
  );
});

$('refreshStatusBtn').addEventListener('click', checkStatus);


/* =====================================================
   MULAI APLIKASI
   ===================================================== */

setupNavigation();
checkStatus();
