'use strict';

/* =========================================================
   GPR STOCK SCANNER
   Batch scanning: maksimum 50 saham per permintaan backend
   ========================================================= */

let scanItems = [];
let chart = null;
let lastScan = null;
let selectedCode = null;

let scanRunning = false;
let stopRequested = false;

const BATCH_SIZE = 50;
const $ = (id) => document.getElementById(id);


/* =========================================================
   UTILITAS
   ========================================================= */

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
  const number = Number(value);

  if (!Number.isFinite(number)) return '—';

  return number.toLocaleString('id-ID', {
    maximumFractionDigits: 2
  });
}

function pct(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return '—';

  return `${number > 0 ? '+' : ''}${number.toFixed(2)}%`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[character]);
}

function numberValue(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

async function fetchJSON(url) {
  const response = await fetch(url, {
    cache: 'no-store',
    headers: {
      'Accept': 'application/json'
    }
  });

  let data;

  try {
    data = await response.json();
  } catch (_) {
    throw new Error(
      `Server mengirim respons yang tidak valid (HTTP ${response.status}).`
    );
  }

  if (!response.ok) {
    throw new Error(
      data.error || `Permintaan gagal (HTTP ${response.status}).`
    );
  }

  return data;
}


/* =========================================================
   NAVIGASI BAWAH
   ========================================================= */

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

  const target = $(destinations[page]);

  if (!target) {
    // Fallback untuk HTML versi lama.
    const fallback = {
      scanner: document.querySelector('.controls'),
      analysis: $('analysisPanel'),
      status: $('providerNote')
    };

    const fallbackTarget = fallback[page];

    if (!fallbackTarget) {
      console.warn('Bagian navigasi tidak ditemukan:', page);
      return;
    }

    fallbackTarget.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });

    setActiveNavigation(page);
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
      const page = link.dataset.page;

      if (!page) {
        // Dukungan untuk HTML lama yang memakai href="#analysisPanel".
        const href = link.getAttribute('href') || '';

        if (href === '#analysisPanel') {
          event.preventDefault();
          navigateTo('analysis');
        } else if (href === '#providerNote') {
          event.preventDefault();
          navigateTo('status');
        } else if (href === '#top') {
          event.preventDefault();
          navigateTo('scanner');
        }

        return;
      }

      event.preventDefault();
      navigateTo(page);

      try {
        history.replaceState(null, '', `#${page}`);
      } catch (_) {
        // Navigasi tetap berfungsi jika history tidak tersedia.
      }
    });
  });
}


/* =========================================================
   STATUS BACKEND
   ========================================================= */

async function checkStatus() {
  const badge = $('apiBadge');

  if (badge) {
    badge.textContent = 'MEMERIKSA API…';
  }

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
    setText('statusApiKey', configured ? 'TERPASANG' : 'BELUM DIATUR');

    const backendStatus = $('backendStatus');
    const apiStatus = $('statusApiKey');

    if (backendStatus) {
      backendStatus.className = 'status-ok';
    }

    if (apiStatus) {
      apiStatus.className = configured
        ? 'status-ok'
        : 'status-warn';
    }

    const universeCount = Number(data.universe_count);

    setText(
      'statusUniverse',
      Number.isFinite(universeCount)
        ? universeCount.toLocaleString('id-ID')
        : 'Belum diketahui'
    );

    setText(
      'statusUniverseSource',
      data.universe_source || 'Sumber belum diketahui'
    );

    setText(
      'statusConnection',
      configured
        ? 'Backend merespons dan API key terdeteksi. Keberhasilan mengambil data harus dipastikan melalui hasil scan.'
        : 'Backend merespons, tetapi API key belum terdeteksi.'
    );

    setText(
      'providerNote',
      configured
        ? `Backend online. Universe terdeteksi: ${
            Number.isFinite(universeCount) ? universeCount : 'belum diketahui'
          } kode.`
        : 'API key belum terdeteksi. Periksa Environment Variables SnapDeploy.'
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


/* =========================================================
   RINGKASAN STATUS PEMINDAIAN
   ========================================================= */

function updateLastScanStatus() {
  if (!lastScan) {
    setText('statusTimeframe', 'Belum ada scan');
    setText('statusScanned', '—');
    setText('statusScanSummary', 'Belum ada pemindaian pada sesi halaman ini.');
    setText('scanProgress', 'Belum ada pemindaian.');
    return;
  }

  setText('statusTimeframe', lastScan.timeframe || '—');

  setText(
    'statusScanned',
    `${lastScan.scanned} / ${lastScan.total}`
  );

  setText(
    'statusScanSummary',
    `Timeframe: ${lastScan.timeframe}. Berhasil: ${lastScan.scanned}. ` +
    `Gagal: ${lastScan.errors}.`
  );

  setText(
    'scanProgress',
    `Selesai memeriksa ${lastScan.processed} dari ${lastScan.total} kode.`
  );
}


/* =========================================================
   UI PROGRES BATCH
   ========================================================= */

function ensureProgressUI() {
  if ($('batchProgress')) return;

  const controls = $('providerNote');

  if (!controls) return;

  const container = document.createElement('div');

  container.id = 'batchProgress';
  container.style.cssText = [
    'margin-top:12px',
    'padding:12px',
    'border:1px solid #30415a',
    'border-radius:12px',
    'background:rgba(10,20,35,.6)',
    'color:#cbd5e1',
    'font-size:14px'
  ].join(';');

  container.innerHTML = `
    <div id="batchProgressText">Menunggu pemindaian.</div>
    <div style="height:7px;margin-top:10px;border-radius:10px;background:#263449;overflow:hidden">
      <div id="batchProgressBar" style="height:100%;width:0%;background:linear-gradient(90deg,#49a7ff,#55dfb2);transition:width .2s"></div>
    </div>
    <button id="stopScanBtn" type="button"
      style="display:none;margin-top:10px;padding:9px 13px;border:1px solid #7b3545;border-radius:9px;background:#301c2a;color:#ff9cae">
      ■ Hentikan pemindaian
    </button>
  `;

  controls.insertAdjacentElement('afterend', container);

  const stopButton = $('stopScanBtn');

  if (stopButton) {
    stopButton.addEventListener('click', () => {
      stopRequested = true;
      setText(
        'batchProgressText',
        'Permintaan berhenti diterima. Menunggu batch yang sedang berjalan selesai…'
      );
      stopButton.disabled = true;
      stopButton.textContent = 'Menghentikan…';
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
    message || `${processed} dari ${total} kode diproses (${percentage}%).`
  );

  const bar = $('batchProgressBar');

  if (bar) {
    bar.style.width = `${percentage}%`;
  }

  setText(
    'scanProgress',
    message || `${processed} dari ${total} kode diproses.`
  );
}

function setStopButtonVisible(visible) {
  ensureProgressUI();

  const button = $('stopScanBtn');

  if (button) {
    button.style.display = visible ? 'inline-block' : 'none';
    button.disabled = false;
    button.textContent = '■ Hentikan pemindaian';
  }
}


/* =========================================================
   MENENTUKAN JUMLAH SAHAM
   ========================================================= */

async function getScanPlan() {
  const selector = $('limit');

  const requestedValue = selector
    ? selector.value
    : '50';

  if (requestedValue === 'all') {
    const universe = await fetchJSON('/api/universe');

    const total = Number(universe.count);

    if (!Number.isFinite(total) || total <= 0) {
      throw new Error('Daftar saham kosong atau tidak dapat dibaca.');
    }

    return {
      total,
      source: universe.source || 'Universe backend',
      mode: 'all'
    };
  }

  const requested = Number(requestedValue);

  if (!Number.isFinite(requested) || requested < 1) {
    throw new Error('Jumlah saham tidak valid.');
  }

  return {
    total: requested,
    source: 'Jumlah saham pilihan',
    mode: 'limited'
  };
}


/* =========================================================
   PEMINDAIAN BERTAHAP
   ========================================================= */

async function runScan() {
  if (scanRunning) {
    setText(
      'providerNote',
      'Pemindaian sedang berjalan. Tunggu hingga selesai atau hentikan dahulu.'
    );
    return;
  }

  const button = $('scanBtn');
  const timeframeElement = $('timeframe');
  const horizonElement = $('horizon');

  if (!button || !timeframeElement || !horizonElement) {
    console.error('Elemen pengaturan scan tidak ditemukan.');
    return;
  }

  scanRunning = true;
  stopRequested = false;

  button.disabled = true;
  button.textContent = 'Memulai pemindaian…';

  setStopButtonVisible(true);
  ensureProgressUI();

  setHTML('results', `
    <tr>
      <td colspan="5" class="empty">
        Menyiapkan pemindaian saham…
      </td>
    </tr>
  `);

  hideElement('errors');

  scanItems = [];

  const errors = [];
  let processed = 0;
  let successful = 0;
  let total = 0;
  let offset = 0;

  const timeframe = timeframeElement.value;
  const horizon = Number(horizonElement.value) || 10;

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
      `Universe: ${total} kode. Pemindaian maksimal ${BATCH_SIZE} kode per permintaan.`
    );

    while (offset < total && !stopRequested) {
      const batchLimit = Math.min(BATCH_SIZE, total - offset);

      button.textContent = `Memindai ${Math.min(offset + batchLimit, total)} / ${total}…`;

      const query = new URLSearchParams({
        timeframe,
        horizon: String(horizon),
        limit: String(batchLimit),
        offset: String(offset)
      });

      updateProgress(
        processed,
        total,
        `Batch ${Math.floor(offset / BATCH_SIZE) + 1}: meminta data kode ${offset + 1}–${offset + batchLimit}.`
      );

      let data;

      try {
        data = await fetchJSON(`/api/scan?${query.toString()}`);
      } catch (error) {
        errors.push({
          code: `Batch offset ${offset}`,
          error: error.message
        });

        /*
         * Jika endpoint tidak tersedia atau terjadi error server,
         * hentikan agar tidak mengulang error yang sama untuk ratusan kode.
         */
        throw new Error(
          `Batch pada offset ${offset} gagal: ${error.message}`
        );
      }

      const batchItems = Array.isArray(data.items)
        ? data.items
        : [];

      const batchErrors = Array.isArray(data.errors)
        ? data.errors
        : [];

      scanItems.push(...batchItems);
      errors.push(...batchErrors);

      successful += batchItems.length;

      const batchProcessed = Number(data.requested);

      /*
       * Gunakan jumlah yang diminta sebagai dasar progres.
       * Jika server tidak mengembalikannya, gunakan ukuran batch.
       */
      processed += Number.isFinite(batchProcessed) && batchProcessed > 0
        ? batchProcessed
        : batchLimit;

      offset += batchLimit;

      lastScan = {
        timeframe,
        total,
        processed,
        scanned: successful,
        errors: errors.length
      };

      updateProgress(
        processed,
        total,
        `Progres ${Math.min(processed, total)} / ${total}. Berhasil dianalisis: ${successful}. Gagal: ${errors.length}.`
      );

      renderResults(scanItems);

      setText('scanned', successful);
      setText(
        'universe',
        `Sumber: ${data.universe_source || plan.source}`
      );

      setText(
        'candidates',
        scanItems.filter(item => item.signal === 'KANDIDAT').length
      );

      setText(
        'bestReturn',
        scanItems.length
          ? pct(
              [...scanItems].sort(
                (a, b) =>
                  numberValue(b.gpr_return_pct) -
                  numberValue(a.gpr_return_pct)
              )[0].gpr_return_pct
            )
          : '—'
      );

      updateLastScanStatus();

      /*
       * Beri browser waktu memperbarui tampilan sebelum batch selanjutnya.
       */
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    /*
     * Urutkan seluruh hasil gabungan.
     */
    scanItems.sort((a, b) => {
      const scoreDifference =
        numberValue(b.score) - numberValue(a.score);

      if (scoreDifference !== 0) {
        return scoreDifference;
      }

      return (
        numberValue(b.gpr_return_pct)
        - numberValue(a.gpr_return_pct)
      );
    });

    renderResults(scanItems);

    setText('scanned', successful);

    setText(
      'universe',
      `Sumber: ${plan.source}`
    );

    setText(
      'candidates',
      scanItems.filter(item => item.signal === 'KANDIDAT').length
    );

    setText(
      'bestReturn',
      scanItems.length
        ? pct(
            [...scanItems].sort(
              (a, b) =>
                numberValue(b.gpr_return_pct) -
                numberValue(a.gpr_return_pct)
            )[0].gpr_return_pct
          )
        : '—'
    );

    lastScan = {
      timeframe,
      total,
      processed: Math.min(processed, total),
      scanned: successful,
      errors: errors.length
    };

    if (errors.length) {
      showElement('errors');

      setText(
        'errors',
        `${errors.length} saham atau permintaan gagal. ` +
        errors.slice(0, 5)
          .map(error => `${error.code || 'Error'}: ${error.error}`)
          .join(' · ')
      );
    }

    if (stopRequested) {
      updateProgress(
        processed,
        total,
        `Pemindaian dihentikan. Berhasil: ${successful}; gagal: ${errors.length}.`
      );

      setText(
        'providerNote',
        `Pemindaian dihentikan pengguna. Hasil yang terkumpul: ${successful} saham.`
      );

    } else {
      updateProgress(
        total,
        total,
        `Selesai. Universe: ${total}; berhasil dianalisis: ${successful}; gagal: ${errors.length}.`
      );

      setText(
        'providerNote',
        `Pemindaian selesai. Berhasil: ${successful} dari ${total} kode. Gagal: ${errors.length}.`
      );
    }

    updateLastScanStatus();

  } catch (error) {
    console.error('Scan error:', error);

    setText('providerNote', error.message);

    updateProgress(
      processed,
      total,
      `Pemindaian terhenti: ${error.message}`
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
    }

  } finally {
    scanRunning = false;

    button.disabled = false;
    button.textContent = '▶ Jalankan GPR Scanner';

    setStopButtonVisible(false);

    const stopButton = $('stopScanBtn');

    if (stopButton) {
      stopButton.disabled = false;
    }
  }
}


/* =========================================================
   TABEL RANKING
   ========================================================= */

function renderResults(items) {
  const table = $('results');

  if (!table) return;

  const searchElement = $('search');

  const searchTerm = searchElement
    ? searchElement.value.trim().toLowerCase()
    : '';

  const filtered = items.filter(item =>
    String(item.code || '')
      .toLowerCase()
      .includes(searchTerm)
  );

  if (!filtered.length) {
    setHTML('results', `
      <tr>
        <td colspan="5" class="empty">
          Tidak ada saham yang cocok atau belum ada hasil.
        </td>
      </tr>
    `);
    return;
  }

  table.innerHTML = filtered.map(item => {
    const code = escapeHtml(item.code || '');
    const signal = escapeHtml(item.signal || '');
    const trend = escapeHtml(item.trend || 'UNKNOWN');

    const returnValue = numberValue(item.gpr_return_pct, NaN);
    const relativeVolume = numberValue(item.relative_volume, NaN);
    const score = numberValue(item.score, NaN);

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


/* =========================================================
   ANALISIS SAHAM
   ========================================================= */

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
      <b class="${numberValue(data.gpr_return_pct) >= 0 ? 'pos' : 'neg'}">
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
          <td class="${numberValue(prediction.return_pct) >= 0 ? 'pos' : 'neg'}">
            ${pct(prediction.return_pct)}
          </td>
          <td>${money(prediction.upper)}</td>
          <td>${money(prediction.lower)}</td>
        </tr>
      `).join(''));
    }

    const canvas = $('projectionChart');

    if (chart) {
      chart.destroy();
      chart = null;
    }

    if (canvas && window.Chart) {
      const labels = [
        'Sekarang',
        ...predictions.map(prediction => `+${prediction.step}`)
      ];

      const values = [
        numberValue(data.price, NaN),
        ...predictions.map(
          prediction => numberValue(prediction.price, NaN)
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


/* =========================================================
   EVENT LISTENERS
   ========================================================= */

function setupEventListeners() {
  const scanButton = $('scanBtn');
  const refreshButton = $('refreshBtn');
  const searchInput = $('search');
  const timeframeInput = $('timeframe');
  const refreshStatusButton = $('refreshStatusBtn');

  if (scanButton) {
    scanButton.addEventListener('click', runScan);
  }

  if (refreshButton) {
    refreshButton.addEventListener('click', runScan);
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      renderResults(scanItems);
    });
  }

  if (timeframeInput) {
    timeframeInput.addEventListener('change', () => {
      setText(
        'providerNote',
        'Timeframe berubah. Jalankan scan ulang untuk memuat data baru.'
      );
    });
  }

  if (refreshStatusButton) {
    refreshStatusButton.addEventListener('click', checkStatus);
  }
}


/* =========================================================
   MULAI APLIKASI
   ========================================================= */

document.addEventListener('DOMContentLoaded', () => {
  ensureProgressUI();
  setupNavigation();
  setupEventListeners();
  checkStatus();
});
