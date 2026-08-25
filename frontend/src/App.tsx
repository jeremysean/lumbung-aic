import { ChangeEvent, DragEvent, useMemo, useRef, useState } from 'react'

type Recommendation = {
  sku_id: string
  category: string
  decision: 'BELI_SEKARANG' | 'TUNDA'
  order_qty: number
  moq: number
  unit_cost: number
  order_cost: number
  stock_on_hand: number
  on_order: number
  horizon_days: number
  forecast_p50: number
  forecast_p90: number
  stockout_risk: number
  priority_score: number
  reason: string
}

type Result = {
  budget: number
  proposed_spend: number
  budget_utilization: number
  items: Recommendation[]
  audit: { model_version: string; input_sha256: string; data_cutoff: string; review_period_days: number }
}

type Problem = { title?: string; details?: Array<{ field: string; issue: string }>; trace_id?: string }

const rupiah = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })

function App() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<Problem | null>(null)

  const buyNow = useMemo(() => result?.items.filter((item) => item.decision === 'BELI_SEKARANG') ?? [], [result])
  const postpone = useMemo(() => result?.items.filter((item) => item.decision === 'TUNDA') ?? [], [result])

  function selectFile(next: File | undefined) {
    if (!next) return
    setFile(next)
    setResult(null)
    setError(null)
  }

  async function submit() {
    if (!file) return
    setLoading(true)
    setError(null)
    const body = new FormData()
    body.append('file', file)
    try {
      const response = await fetch('/api/v1/recommendations', { method: 'POST', body })
      const payload = await response.json()
      if (!response.ok) throw payload as Problem
      setResult(payload.data)
    } catch (problem) {
      setError(problem instanceof Error ? { title: problem.message } : (problem as Problem))
    } finally {
      setLoading(false)
    }
  }

  function downloadCsv() {
    if (!result) return
    const keys = Object.keys(result.items[0] ?? {}) as Array<keyof Recommendation>
    const escape = (value: unknown) => `"${String(value).replaceAll('"', '""')}"`
    const csv = [keys.join(','), ...result.items.map((row) => keys.map((key) => escape(row[key])).join(','))].join('\n')
    const link = document.createElement('a')
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    link.download = 'lumbung_recommendations.csv'
    link.click()
    URL.revokeObjectURL(link.href)
  }

  return (
    <main>
      <header className="nav">
        <a className="brand" href="#top" aria-label="Lumbung beranda">
          <span className="brand-mark">L</span><span>Lumbung</span>
        </a>
        <span className="nav-note"><span className="status-dot" /> Berjalan lokal & dapat diaudit</span>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow">AI REPLENISHMENT COPILOT</div>
        <h1>Ubah data stok menjadi<br /><em>rencana belanja.</em></h1>
        <p className="hero-copy">Prioritaskan barang yang paling perlu dibeli, tanpa melewati anggaran toko.</p>
      </section>

      <section className="workspace" aria-label="Unggah data toko">
        <div className="step"><span>01</span><div><strong>Unggah snapshot toko</strong><small>Minimal 28 hari histori per SKU</small></div></div>
        <div
          className={`dropzone ${dragging ? 'dragging' : ''}`}
          onDragOver={(event: DragEvent) => { event.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event: DragEvent) => { event.preventDefault(); setDragging(false); selectFile(event.dataTransfer.files[0]) }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => event.key === 'Enter' && inputRef.current?.click()}
        >
          <input ref={inputRef} type="file" accept=".csv,text/csv" hidden onChange={(event: ChangeEvent<HTMLInputElement>) => selectFile(event.target.files?.[0])} />
          <div className="upload-icon">↑</div>
          {file ? <><strong>{file.name}</strong><small>{(file.size / 1024).toFixed(1)} KB · klik untuk mengganti</small></> : <><strong>Tarik store_snapshot.csv ke sini</strong><small>atau klik untuk memilih · maksimal 10 MB</small></>}
        </div>
        <div className="actions">
          <a className="template-link" href="/api/v1/templates/store-snapshot" download>↓ Unduh contoh CSV</a>
          <button disabled={!file || loading} onClick={submit}>{loading ? 'Menghitung…' : 'Buat rencana belanja'} <span>→</span></button>
        </div>
        {error && <div className="error" role="alert"><strong>{error.title ?? 'Data belum dapat diproses.'}</strong>{error.details?.slice(0, 5).map((detail) => <span key={`${detail.field}-${detail.issue}`}>{detail.field}: {detail.issue}</span>)}</div>}
      </section>

      {result && <section className="results" aria-live="polite">
        <div className="results-head">
          <div><div className="eyebrow">RENCANA SIAP DITINJAU</div><h2>Keputusan belanja minggu ini</h2></div>
          <button className="secondary" onClick={downloadCsv}>Unduh hasil CSV</button>
        </div>
        <div className="summary-grid">
          <Summary label="Anggaran tersedia" value={rupiah.format(result.budget)} />
          <Summary label="Usulan belanja" value={rupiah.format(result.proposed_spend)} accent />
          <Summary label="Pemakaian anggaran" value={`${(result.budget_utilization * 100).toFixed(1)}%`} />
          <Summary label="SKU dibeli" value={`${buyNow.length} dari ${result.items.length}`} />
        </div>
        <DecisionTable title="Beli sekarang" subtitle="Prioritas terpilih di bawah batas anggaran" items={buyNow} buy />
        <DecisionTable title="Tunda" subtitle="Aman atau belum masuk prioritas anggaran" items={postpone} />
        <div className="audit"><strong>Jejak keputusan</strong><span>Model {result.audit.model_version}</span><span>Input {result.audit.input_sha256.slice(0, 12)}…</span><span>Horizon: lead time + {result.audit.review_period_days} hari</span></div>
      </section>}

      <footer><span>Lumbung memberi rekomendasi, bukan keputusan otomatis.</span><span>Owner tetap menyetujui setiap pembelian.</span></footer>
    </main>
  )
}

function Summary({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <div className={`summary ${accent ? 'accent' : ''}`}><small>{label}</small><strong>{value}</strong></div>
}

function DecisionTable({ title, subtitle, items, buy = false }: { title: string; subtitle: string; items: Recommendation[]; buy?: boolean }) {
  return <div className="decision-card">
    <div className="decision-title"><span className={buy ? 'buy-badge' : 'hold-badge'}>{buy ? '✓' : '–'}</span><div><h3>{title}</h3><p>{subtitle}</p></div><strong className="count">{items.length} SKU</strong></div>
    {items.length === 0 ? <p className="empty">Tidak ada SKU pada kelompok ini.</p> : <div className="table-wrap"><table><thead><tr><th>SKU</th><th>Rekomendasi</th><th>Biaya</th><th>Risiko</th><th>Alasan</th></tr></thead><tbody>{items.map((item) => <tr key={item.sku_id}><td><strong>{item.sku_id}</strong><small>{item.category}</small></td><td>{item.order_qty > 0 ? `${item.order_qty} unit` : 'Belum dibeli'}<small>MOQ {item.moq}</small></td><td>{rupiah.format(item.order_cost)}</td><td><span className="risk-track"><i style={{ width: `${Math.round(item.stockout_risk * 100)}%` }} /></span><small>{Math.round(item.stockout_risk * 100)}%</small></td><td>{item.reason}</td></tr>)}</tbody></table></div>}
  </div>
}

export default App

