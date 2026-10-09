let scanItems = [];
let chart = null;
const $ = (id) => document.getElementById(id);

async function checkStatus(){
  try{
    const r = await fetch('/api/status');
    const s = await r.json();
    $('apiBadge').textContent = s.api_key_configured ? 'API KEY TERPASANG' : 'API KEY BELUM DIATUR';
    $('apiBadge').style.color = s.api_key_configured ? '#39d7a0' : '#ffca73';
    $('providerNote').textContent = s.api_key_configured
      ? 'Koneksi backend siap. Dukungan intraday akan diverifikasi dari respons endpoint.'
      : 'Tambahkan API Key di backend melalui file .env. Jangan masukkan key di browser.';
  }catch(e){
    $('apiBadge').textContent='BACKEND OFFLINE';
    $('providerNote').textContent='Backend belum berjalan atau tidak dapat dihubungi.';
  }
}

function money(n){ return Number(n).toLocaleString('id-ID',{maximumFractionDigits:2}); }
function pct(n){ return `${Number(n)>0?'+':''}${Number(n).toFixed(2)}%`; }

async function runScan(){
  const btn=$('scanBtn'); btn.disabled=true; btn.textContent='Memindai…';
  $('results').innerHTML='<tr><td colspan="5" class="empty">Mengambil data dan menghitung model GPR. Proses awal dapat memerlukan waktu.</td></tr>';
  $('errors').classList.add('hidden');
  try{
    const q=new URLSearchParams({timeframe:$('timeframe').value,horizon:$('horizon').value,limit:$('limit').value});
    const r=await fetch('/api/scan?'+q.toString());
    const data=await r.json();
    if(!r.ok) throw new Error(data.error || 'Permintaan gagal');
    scanItems=data.items||[];
    renderResults(scanItems);
    $('scanned').textContent=data.scanned ?? '0';
    $('universe').textContent=`Sumber: ${data.universe_source||'Arjum'}`;
    $('candidates').textContent=scanItems.filter(x=>x.signal==='KANDIDAT').length;
    $('bestReturn').textContent=scanItems.length?pct(scanItems[0].gpr_return_pct):'—';
    if(data.errors_count){
      $('errors').classList.remove('hidden');
      const examples=(data.errors||[]).slice(0,4).map(x=>`${x.code}: ${x.error}`).join(' · ');
      $('errors').textContent=`${data.errors_count} saham gagal diproses. ${examples}`;
    }
    $('providerNote').textContent=`Timeframe diminta: ${data.timeframe}. ${data.scanned} berhasil dihitung dari ${data.requested} permintaan. Jika intraday ditolak provider, pilih Harian untuk uji awal atau tambahkan provider intraday.`;
  }catch(e){
    $('results').innerHTML=`<tr><td colspan="5" class="empty">${escapeHtml(e.message)}</td></tr>`;
    $('providerNote').textContent=e.message;
  }finally{
    btn.disabled=false;btn.textContent='▶ Jalankan GPR Scanner';
  }
}

function renderResults(items){
  const filtered=items.filter(x=>x.code.toLowerCase().includes($('search').value.trim().toLowerCase()));
  if(!filtered.length){$('results').innerHTML='<tr><td colspan="5" class="empty">Tidak ada saham yang cocok atau belum ada data.</td></tr>';return;}
  $('results').innerHTML=filtered.map((x,i)=>`
    <tr data-code="${escapeHtml(x.code)}">
      <td><span class="code">${escapeHtml(x.code)}</span><span class="sub">${escapeHtml(x.signal||'')}</span></td>
      <td class="${x.gpr_return_pct>=0?'pos':'neg'}">${pct(x.gpr_return_pct)}</td>
      <td><span class="trend ${x.trend==='BEARISH'?'down':''}">${x.trend}</span></td>
      <td>${Number(x.relative_volume).toFixed(2)}×</td>
      <td>${Number(x.score).toFixed(0)}</td>
    </tr>`).join('');
  document.querySelectorAll('#results tr[data-code]').forEach(tr=>tr.addEventListener('click',()=>analyze(tr.dataset.code)));
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

async function analyze(code){
  $('analysisTitle').textContent=`Analisis ${code}`;
  $('analysisMeta').textContent='Menghitung proyeksi…';
  const q=new URLSearchParams({timeframe:$('timeframe').value,horizon:$('horizon').value});
  try{
    const r=await fetch(`/api/analyze/${encodeURIComponent(code)}?${q.toString()}`);
    const d=await r.json(); if(!r.ok)throw new Error(d.error||'Analisis gagal');
    $('analysisMeta').innerHTML=`Harga terakhir: <b>${money(d.price)}</b> · Tren: <b>${d.trend}</b> · Momentum: <b>${d.momentum}</b> · Rel. volume: <b>${d.relative_volume}×</b><br>Return GPR pada candle ke-${d.horizon}: <b class="${d.gpr_return_pct>=0?'pos':'neg'}">${pct(d.gpr_return_pct)}</b> · Data: ${d.bars} candle`;
    $('projectionRows').innerHTML=d.predictions.map(p=>`<tr><td>${p.step}</td><td>${money(p.price)}</td><td class="${p.return_pct>=0?'pos':'neg'}">${pct(p.return_pct)}</td><td>${money(p.upper)}</td><td>${money(p.lower)}</td></tr>`).join('');
    const labels=['Sekarang',...d.predictions.map(p=>`+${p.step}`)];
    const values=[d.price,...d.predictions.map(p=>p.price)];
    if(chart)chart.destroy();
    chart=new Chart($('projectionChart'),{
      type:'line',
      data:{labels,datasets:[{label:'Harga proyeksi GPR',data:values,borderColor:'#39d7a0',backgroundColor:'#39d7a022',fill:true,tension:.2,pointRadius:3}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#91a2ba'}}},scales:{x:{ticks:{color:'#91a2ba'},grid:{color:'#243147'}},y:{ticks:{color:'#91a2ba'},grid:{color:'#243147'}}}}
    });
    $('analysisPanel').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){$('analysisMeta').textContent=`Tidak dapat menganalisis ${code}: ${e.message}`;}
}

$('scanBtn').addEventListener('click',runScan);
$('refreshBtn').addEventListener('click',runScan);
$('search').addEventListener('input',()=>renderResults(scanItems));
$('timeframe').addEventListener('change',()=>{ $('providerNote').textContent='Timeframe berubah. Jalankan scan ulang untuk memuat data timeframe tersebut.'; });
checkStatus();
