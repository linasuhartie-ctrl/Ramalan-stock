# GPR Stock Scanner — starter

Dashboard web responsif untuk iPhone/desktop, backend Flask, dan port Python dari inti model GPR pada Pine Script yang diberikan.

## Status penting sebelum dipakai

- Integrasi memakai API Arjum dan menyimpan API key hanya di backend.
- Situs Arjum saat ini mendeskripsikan riwayat OHLCV sebagai **Daily, Weekly, Monthly**. Dukungan candle intraday 5m/15m/1h belum terkonfirmasi.
- Dropdown intraday disediakan untuk menguji dukungan endpoint. Jika API menolak interval tersebut atau mengabaikannya, gunakan `1d` untuk pengujian awal. Jangan menganggap hasil harian sebagai sinyal day trading.
- Screener mencoba mengambil universe dari `/api/screener/latest`; bila format respons tidak cocok atau endpoint gagal, ia memakai starter watchlist 24 saham. Karena itu, **pemindaian seluruh BEI belum dijamin** sampai format response endpoint dikonfirmasi.
- Bentuk JSON `/api/history/{code}` dapat berubah; parser dibuat fleksibel, tetapi perlu diuji dengan respons aktual.
- Port Python mempertahankan kernel Matérn 3/2, lima fitur, parameter inti, Cholesky, dan proyeksi return kumulatif. Kesetaraan numerik dengan Pine belum tervalidasi; perbedaan kecil dapat muncul akibat penanganan indikator/riwayat. Validasi silang diperlukan.
- Skor 0–100 adalah ranking heuristik yang transparan, bukan probabilitas keuntungan dan bukan rekomendasi investasi.

## Menjalankan di komputer

1. Install Python 3.11 atau lebih baru.
2. Ekstrak ZIP.
3. Buat virtual environment (opsional tetapi disarankan).
4. Install dependensi:

   ```bash
   pip install -r requirements.txt
   ```

5. Salin `.env.example` menjadi `.env`.
6. Isi `ARJUM_API_KEY` di `.env` dengan API Key Arjum. Jangan bagikan file `.env`.
7. Jalankan:

   ```bash
   python -m flask --app app run --host 0.0.0.0 --port 5000
   ```

8. Buka `http://127.0.0.1:5000`.

## Menjalankan online

Deploy sebagai web service Python di hosting yang mendukung Flask. Set environment variables `ARJUM_API_KEY`, `ARJUM_BASE_URL`, `PORT`. Jangan commit `.env` ke GitHub. Gunakan HTTPS dan batasi akses dashboard bila dibutuhkan.

## Endpoint internal

- `GET /api/status` — status konfigurasi key
- `GET /api/scan?timeframe=1d&horizon=10&limit=50` — jalankan scan
- `GET /api/analyze/BBCA?timeframe=1d&horizon=10` — detail model

## Jika intraday tidak tersedia

Pilih sumber data yang menyediakan OHLCV intraday BEI dengan izin penggunaan API yang sesuai. Integrasikan provider tersebut di fungsi `get_history()` tanpa mengubah `gpr_project()`. Sumber data perlu menyediakan cukup candle historis untuk window training dan indikator, serta timestamp zona waktu yang konsisten.

## Keamanan dan batasan

- API key hanya di backend.
- Jangan letakkan API key di JavaScript, HTML, atau screenshot publik.
- Atur cache/rate limit sesuai kuota API provider.
- Jangan gunakan sinyal live sebelum menguji data, interval, jam bursa, candle yang belum tutup, biaya transaksi, slippage, dan performa out-of-sample.
