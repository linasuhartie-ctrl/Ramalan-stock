'use strict';

/* ==========================================================
   GPR STOCK SCANNER — IDX
   - Batch scanning maksimal 50 saham per permintaan
   - Mendukung 50, 300, 500, dan seluruh saham tersedia
   - Ranking hanya menampilkan skor MEDIUM ke atas (>= 40)
   - Analisis saham, grafik GPR, navigasi dan status backend
   ========================================================== */

const BATCH_SIZE = 50;
const MIN_DISPLAY_SCORE = 40;

let scanItems = [];
let chart = null;
let lastScan = null;
let selectedCode = null;
let scanRunning = false;
let stopRequested = false;

const $ = id => document.getElementById(id);


/* ==========================================================
   UTILITAS
   ========================================================== */

function setText(id, value) {
  const element = $(id);
  if (element) element.textContent = value;
}

function setHTML(id, value) {
  const element = $(id);
  if (element) element.innerHTML = value;
}

function showElement(id) {
  const element = $(id);
  if (element) element.classList.remove('hidden');
}

function hideElement(id) {
  const element = $(id);
  if (element) element.classList.add('hidden');
}

function money(value) {
  const n = Number(value);

  if (!Number.isFinite(n)) return '—';

  return n.toLocaleString('id-ID', {
    maximumFractionDigits: 2
  });
}

function pct(value) {
  const n = Number(value);

  if (!Number.isFinite(n)) return '—';

  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`;
}

function num(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[char]);
}

async function fetchJSON(url) {
  const response = await fetch(url, {
    cache: 'no-store',
    headers: {
      Accept: 'application/json'
    }
  });

  let data;

  try {
    data = await response.json();
  } catch (_) {
    throw new Error(
      `Respons server tidak valid (HTTP ${response.status}).`
    );
  }

  if (!response.ok) {
    throw new Error(
      data.error || `Permintaan gagal (HTTP ${response.status}).`
    );
  }

  return data;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


/* ==========================================================
   NAVIGASI BAWAH
   ========================================================== */

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

  let target = $(destinations[page]);

  // Kompatibilitas dengan HTML versi sebelumnya.
  if (!target) {
    if (page === 'scanner') {
      target = document.querySelector('.controls');
    } else if (page === 'analysis') {
      target = $('analysisPanel');
    } else if (page === 'status') {
      target = $('providerNote');
    }
  }

  if (!target) {
    console.warn('Bagian halaman tidak ditemukan:', page);
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
  document.querySelectorAll('.bottom-nav a').forEach(link => {
    link.addEventListener('click', event => {
      let page = link.dataset.page;

      if (!page) {
        const href = link.getAttribute('href') || '';

        if (href === '#top') page = 'scanner';
        if (href === '#analysisPanel') page = 'analysis';
        if (href === '#providerNote') page = 'status';
      }

      if (!page) return;

      event.preventDefault();
      navigateTo(page);

      try {
        history.replaceState(null, '', `#${page}`);
      } catch (_) {
        // Tidak perlu tindakan tambahan.
      }
    });
  });
}


/* ==========================================================
   STATUS BACKEND DAN API KEY
   ========================================================== */

async function checkStatus() {
  const badge = $('apiBadge');

  if (badge) badge.textContent = 'MEMERIKSA API…';

  setText('backendStatus', 'Memeriksa…');
  setText('statusApiKey', 'Memeriksa…');
  setText('statusConnection', 'Menghubungi backend…');

  try {
    const data = await fetchJSON('/api/status');

    const configured = Boolean(data.api_key_configured);

    if (badge) {
      badge.textContent = configured
        ? 'API KEY TERPASANG'
        : 'API KEY BELUM DIATUR';

      badge.style.color = configured
        ? '#39d7a0'
        : '#ffca73';
    }

    setText('backendStatus', 'ONLINE');
    setText(
      'statusApiKey',
      configured ? 'TERPASANG' : 'BELUM DIATUR'
    );

    if ($('backendStatus')) {
      $('backendStatus').className = 'status-ok';
    }

    if ($('statusApiKey')) {
      $('statusApiKey').className = configured
        ? 'status-ok'
        : 'status-warn';
    }

    setText(
      'statusConnection',
      configured
        ? 'Backend merespons dan API key terdeteksi. Keberhasilan pengambilan data perlu dikonfirmasi melalui scan.'
        : 'Backend merespons, tetapi API key belum terdeteksi. Periksa Environment Variables SnapDeploy.'
    );

    setText(
      'providerNote',
      configured
        ? 'Backend online. Jalankan scan untuk memeriksa ketersediaan data saham.'
        : 'API key belum terdeteksi. Periksa konfigurasi SnapDeploy.'
    );

  } catch (error) {
    if (badge) {
      badge.textContent = 'BACKEND OFFLINE';
      badge.style.color = '#ff7a90';
    }

    setText('backendStatus', 'TIDAK TERHUBUNG');
    setText('statusApiKey', 'TIDAK DIKETAHUI');
    setText('statusConnection', error.message);
    setText('providerNote', `Backend tidak dapat diperiksa: ${error.message}`);
  }

  updateLastScanStatus();
}


/* ==========================================================
   RINGKASAN SCAN
   ========================================================== */

function updateLastScanStatus() {
  if (!lastScan) {
    setText('statusTimeframe', 'Belum ada scan');
    setText('statusScanned', '—');
    setText(
      'statusScanSummary',
      'Belum ada pemindaian pada sesi halaman ini.'
    );
    return;
  }

  setText('statusTimeframe', lastScan.timeframe || '—');

  setText(
    'statusScanned',
    `${lastScan.scanned} / ${lastScan.total}`
  );

  setText(
    'statusScanSummary',
    `Timeframe: ${lastScan.timeframe}. ` +
    `Berhasil dianalisis: ${lastScan.scanned}. ` +
    `Gagal: ${lastScan.errors}.`
  );
}


/* ==========================================================
   UI PROGRES SCAN
   ========================================================== */

function ensureProgressUI() {
  if ($('batchProgress')) return;

  const anchor = $('providerNote');

  if (!anchor) return;

  const box = document.createElement('div');

  box.id = 'batchProgress';

  box.style.cssText = [
    'margin-top:12px',
    'padding:12px',
    'border:1px solid #30415a',
    'border-radius:12px',
    'background:rgba(10,20,35,.65)',
    'color:#cbd5e1',
    'font-size:14px'
  ].join(';');

  box.innerHTML = `
    <div id="batchProgressText">
      Menunggu pemindaian.
    </div>

    <div style="
      height:7px;
      margin-top:10px;
      border-radius:10px;
      background:#263449;
      overflow:hidden;
    ">
      <div id="batchProgressBar" style="
        height:100%;
        width:0%;
        background:linear-gradient(90deg,#49a7ff,#55dfb2);
        transition:width .2s;
      "></div>
    </div>

    <button id="stopScanBtn" type="button" style="
      display:none;
      margin-top:10px;
      padding:9px 13px;
      border:1px solid #7b3545;
      border-radius:9px;
      background:#301c2a;
      color:#ff9cae;
    ">
      ■ Hentikan pemindaian
    </button>
  `;

  anchor.insertAdjacentElement('afterend', box);

  const stopButton = $('stopScanBtn');

  if (stopButton) {
    stopButton.addEventListener('click', () => {
      stopRequested = true;
      stopButton.disabled = true;
      stopButton.textContent = 'Menghentikan…';

      setText(
        'batchProgressText',
        'Permintaan berhenti diterima. Menunggu batch berjalan selesai…'
      );
    });
  }
}

function updateProgress(processed, total, message = '') {
  ensureProgressUI();

  const percentage = total > 0
    ? Math.min(100, Math.round(processed / total * 100))
    : 0;

  setText(
    'batchProgressText',
    message || `${processed} dari ${total} kode (${percentage}%).`
  );

  const bar = $('batchProgressBar');

  if (bar) {
    bar.style.width = `${percentage}%`;
  }
}

function setStopButtonVisible(visible) {
  ensureProgressUI();

  const button = $('stopScanBtn');

  if (!button) return;

  button.style.display = visible ? 'inline-block' : 'none';
  button.disabled = false;
  button.textContent = '■ Hentikan pemindaian';
}


/* ==========================================================
   FILTER JUMLAH SAHAM DAN UNIVERSE
   ========================================================== */

async function getScanPlan() {
  const selector = $('limit');
  const value = selector ? selector.value : '50';

  if (value === 'all') {
    const universe = await fetchJSON('/api/universe');
    const total = Number(universe.count);

    if (!Number.isFinite(total) || total <= 0) {
      throw new Error(
        'Universe saham kosong. Periksa endpoint /api/universe.'
      );
    }

    return {
      total,
      source: universe.source || 'Universe backend'
    };
  }

  const total = Number(value);

  if (!Number.isFinite(total) || total < 1) {
    throw new Error('Pilihan jumlah saham tidak valid.');
  }

  return {
    total,
    source: 'Jumlah saham pilihan'
  };
}


/* ==========================================================
   SCAN BERTAHAP
   ========================================================== */

async function runScan() {
  if (scanRunning) {
    setText(
      'providerNote',
      'Pemindaian masih berjalan. Tunggu atau tekan tombol berhenti.'
    );
    return;
  }

  const button = $('scanBtn');

  if (!button || !$('timeframe') || !$('horizon')) {
    setText('providerNote', 'Elemen pengaturan scan tidak ditemukan.');
    return;
  }

  scanRunning = true;
  stopRequested = false;

  button.disabled = true;
  button.textContent = 'Menyiapkan scan…';

  setStopButtonVisible(true);
  ensureProgressUI();

  scanItems = [];

  const errors = [];

  let total = 0;
  let processed = 0;
  let successful = 0;
  let offset = 0;

  const timeframe = $('timeframe').value;
  const horizon = Number($('horizon').value) || 10;

  setHTML('results', `
    <tr>
      <td colspan="5" class="empty">
        Menyiapkan pemindaian saham…
      </td>
    </tr>
  `);

  hideElement('errors');

  try {
    const plan = await getScanPlan();

    total = plan.total;

    lastScan = {
      timeframe,
      total,
      processed: 0,
      scanned: 0,
      errors: 0
    };

    updateProgress(
      0,
      total,
      `Universe berisi ${total} kode. Maksimal ${BATCH_SIZE} kode per permintaan.`
    );

    while (offset < total && !stopRequested) {
      const batchLimit = Math.min(BATCH_SIZE, total - offset);

      const batchNumber = Math.floor(offset / BATCH_SIZE) + 1;

      button.textContent =
        `Memindai batch ${batchNumber} · ${Math.min(offset + batchLimit, total)}/${total}`;

      updateProgress(
        processed,
        total,
        `Batch ${batchNumber}: meminta kode posisi ${offset + 1}–${offset + batchLimit}.`
      );

      const query = new URLSearchParams({
        timeframe,
        horizon: String(horizon),
        limit: String(batchLimit),
        offset: String(offset)
      });

      /*
       * Penting:
       * app.py harus mendukung offset dan membatasi batch maksimal 50.
       */
      const data = await fetchJSON(`/api/scan?${query.toString()}`);

      const batchItems = Array.isArray(data.items)
        ? data.items
        : [];

      const batchErrors = Array.isArray(data.errors)
        ? data.errors
        : [];

      scanItems.push(...batchItems);
      errors.push(...batchErrors);

      successful += batchItems.length;

      const requested = Number(data.requested);

      const consumed = (
        Number.isFinite(requested) && requested > 0
      ) ? requested : batchLimit;

      processed += consumed;
      offset += batchLimit;

      lastScan = {
        timeframe,
        total,
        processed: Math.min(processed, total),
        scanned: successful,
        errors: errors.length
      };

      updateProgress(
        Math.min(processed, total),
        total,
        `Progres ${Math.min(processed, total)}/${total}. ` +
        `Berhasil: ${successful}. Gagal: ${errors.length}.`
      );

      updateSummaryCards();
      renderResults(scanItems);
      updateLastScanStatus();

      // Beri kesempatan browser memperbarui layar.
      await sleep(100);
    }

    scanItems.sort((a, b) => {
      const scoreDifference = num(b.score) - num(a.score);

      if (scoreDifference !== 0) return scoreDifference;

      return num(b.gpr_return_pct) - num(a.gpr_return_pct);
    });

    renderResults(scanItems);
    updateSummaryCards();

    lastScan = {
      timeframe,
      total,
      processed: Math.min(processed, total),
      scanned: successful,
      errors: errors.length
    };

    updateLastScanStatus();

    if (errors.length) {
      showElement('errors');

      setText(
        'errors',
        `${errors.length} saham atau permintaan gagal. ` +
        errors.slice(0, 5)
          .map(error =>
            `${error.code || 'Error'}: ${error.error || 'Tidak diketahui'}`
          )
          .join(' · ')
      );
    }

    if (stopRequested) {
      updateProgress(
        processed,
        total,
        `Scan dihentikan. Berhasil: ${successful}; gagal: ${errors.length}.`
      );

      setText(
        'providerNote',
        `Pemindaian dihentikan. ${successful} saham berhasil dianalisis.`
      );
    } else {
      updateProgress(
        total,
        total,
        `Selesai. Universe: ${total}; berhasil: ${successful}; gagal: ${errors.length}.`
      );

      setText(
        'providerNote',
        `Scan selesai. Berhasil dianalisis: ${successful} dari ${total} kode. Gagal: ${errors.length}.`
      );
    }

  } catch (error) {
    console.error('GPR scan gagal:', error);

    setText('providerNote', error.message);

    updateProgress(
      processed,
      total,
      `Scan terhenti: ${error.message}`
    );

    if (!scanItems.length) {
      setHTML('results', `
        <tr>
          <td colspan="5" class="empty">
            ${escapeHtml(error.message)}
          </td>
        </tr>
      `);
    } else {
      renderResults(scanItems);
      updateSummaryCards();
    }

    lastScan = {
      timeframe,
      total,
      processed,
      scanned: successful,
      errors: errors.length + 1
    };

    updateLastScanStatus();

  } finally {
    scanRunning = false;

    button.disabled = false;
    button.textContent = '▶ Jalankan GPR Scanner';

    setStopButtonVisible(false);
  }
}


/* ==========================================================
   RINGKASAN KARTU
   ========================================================== */

function updateSummaryCards() {
  const qualified = scanItems.filter(item =>
    Number.isFinite(Number(item.score)) &&
    Number(item.score) >= MIN_DISPLAY_SCORE
  );

  const candidates = qualified.filter(item =>
    item.signal === 'KANDIDAT'
  );

  const bestReturn = qualified.length
    ? Math.max(...qualified.map(item =>
        num(item.gpr_return_pct, -Infinity)
      ))
    : null;

  setText('scanned', scanItems.length);
  setText('candidates', candidates.length);
  setText(
    'bestReturn',
    bestReturn !== null && Number.isFinite(bestReturn)
      ? pct(bestReturn)
      : '—'
  );
}


/* ==========================================================
   RANKING SAHAM — MEDIUM KE ATAS SAJA
   ========================================================== */

function renderResults(items) {
  const table = $('results');

  if (!table) return;

  const searchElement = $('search');

  const searchTerm = searchElement
    ? searchElement.value.trim().toLowerCase()
    : '';

  /*
   * Ambang minimum 40:
   * 80–100 = HIGH
   * 60–79  = MEDIUM–HIGH
   * 40–59  = MEDIUM
   * <40    = disembunyikan dari ranking
   */
  const qualified = items.filter(item => {
    const score = Number(item.score);

    return Number.isFinite(score) && score >= MIN_DISPLAY_SCORE;
  });

  qualified.sort((a, b) => {
    const difference = num(b.score) - num(a.score);

    if (difference !== 0) return difference;

    return num(b.gpr_return_pct) - num(a.gpr_return_pct);
  });

  const filtered = qualified.filter(item =>
    String(item.code || '')
      .toLowerCase()
      .includes(searchTerm)
  );

  if (!filtered.length) {
    setHTML('results', `
      <tr>
        <td colspan="5" class="empty">
          Belum ada saham dengan skor MEDIUM ke atas.
          Coba scan ulang atau ubah timeframe.
        </td>
      </tr>
    `);
    return;
  }

  table.innerHTML = filtered.map(item => {
    const code = escapeHtml(item.code || '');
    const signal = escapeHtml(item.signal || '');
    const trend = escapeHtml(item.trend || 'UNKNOWN');

    const score = Number(item.score);
    const returnValue = Number(item.gpr_return_pct);
    const relativeVolume = Number(item.relative_volume);

    let category = 'MEDIUM';
    let categoryClass = 'medium';

    if (score >= 80) {
      category = 'HIGH';
      categoryClass = 'high';
    } else if (score >= 60) {
      category = 'MEDIUM–HIGH';
      categoryClass = 'medium-high';
    }

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
          <strong>${Number.isFinite(score) ? score.toFixed(0) : '—'}</strong>
          <span class="sub">${category}</span>
        </td>
      </tr>
    `;
  }).join('');

  table.querySelectorAll('tr[data-code]').forEach(row => {
    const open = () => analyze(row.dataset.code);

    row.addEventListener('click', open);

    row.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        open();
      }
    });
  });
}


/* ==========================================================
   ANALISIS DAN GRAFIK GPR
   ========================================================== */

async function analyze(code) {
  selectedCode = code;

  navigateTo('analysis');

  setText('analysisTitle', `Analisis ${code}`);
  setText('analysisMeta', 'Menghitung proyeksi GPR…');

  setHTML('projectionRows', `
    <tr>
      <td colspan="5" class="empty">
        Menghitung proyeksi…
      </td>
    </tr>
  `);

  const timeframe = $('timeframe')
    ? $('timeframe').value
    : '1d';

  const horizon = $('horizon')
    ? $('horizon').value
    : '10';

  const query = new URLSearchParams({
    timeframe,
    horizon
  });

  try {
    const data = await fetchJSON(
      `/api/analyze/${encodeURIComponent(code)}?${query.toString()}`
    );

    const predictions = Array.isArray(data.predictions)
      ? data.predictions
      : [];

    setHTML('analysisMeta', `
      Harga terakhir: <b>${money(data.price)}</b>
      · Tren: <b>${escapeHtml(data.trend || '—')}</b>
      · Momentum: <b>${escapeHtml(data.momentum || '—')}</b>
      · Rel. volume: <b>${escapeHtml(data.relative_volume ?? '—')}×</b>
      <br>
      Return GPR pada candle ke-${escapeHtml(data.horizon ?? '—')}:
      <b class="${num(data.gpr_return_pct) >= 0 ? 'pos' : 'neg'}">
        ${pct(data.gpr_return_pct)}
      </b>
      · Data: ${escapeHtml(data.bars ?? '—')} candle
    `);

    if (!predictions.length) {
      setHTML('projectionRows', `
        <tr>
          <td colspan="5" class="empty">
            Data proyeksi tidak tersedia.
          </td>
        </tr>
      `);
    } else {
      setHTML('projectionRows', predictions.map(prediction => `
        <tr>
          <td>${escapeHtml(prediction.step)}</td>
          <td>${money(prediction.price)}</td>
          <td class="${num(prediction.return_pct) >= 0 ? 'pos' : 'neg'}">
            ${pct(prediction.return_pct)}
          </td>
          <td>${money(prediction.upper)}</td>
          <td>${money(prediction.lower)}</td>
        </tr>
      `).join(''));
    }

    if (chart) {
      chart.destroy();
      chart = null;
    }

    const canvas = $('projectionChart');

    if (canvas && window.Chart) {
      const labels = [
        'Sekarang',
        ...predictions.map(prediction => `+${prediction.step}`)
      ];

      const values = [
        num(data.price, NaN),
        ...predictions.map(prediction =>
          num(prediction.price, NaN)
        )
      ];

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

    setHTML('projectionRows', `
      <tr>
        <td colspan="5" class="empty">
          ${escapeHtml(error.message)}
        </td>
      </tr>
    `);
  }
}


/* ==========================================================
   EVENT LISTENERS
   ========================================================== */

function setupEventListeners() {
  if ($('scanBtn')) {
    $('scanBtn').addEventListener('click', runScan);
  }

  if ($('refreshBtn')) {
    $('refreshBtn').addEventListener('click', runScan);
  }

  if ($('search')) {
    $('search').addEventListener('input', () => {
      renderResults(scanItems);
    });
  }

  if ($('timeframe')) {
    $('timeframe').addEventListener('change', () => {
      setText(
        'providerNote',
        'Timeframe berubah. Jalankan scan ulang untuk mengambil data baru.'
      );
    });
  }

  if ($('refreshStatusBtn')) {
    $('refreshStatusBtn').addEventListener('click', checkStatus);
  }
}


/* ==========================================================
   INISIALISASI
   ========================================================== */

document.addEventListener('DOMContentLoaded', () => {
  ensureProgressUI();
  setupNavigation();
  setupEventListeners();
  checkStatus();
});
