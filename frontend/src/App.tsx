import { ChangeEvent, DragEvent, useMemo, useRef, useState } from 'react'
import {
  buildPurchaseDrafts,
  DEMO_SUPPLIERS,
  draftLineTotal,
  draftTotal,
  groupDraftsBySupplier,
  PurchaseDraft,
  Recommendation,
  supplierMessage,
  todayInputValue,
  validateDrafts,
} from './workflow'

type Result = {
  budget: number
  proposed_spend: number
  budget_utilization: number
  items: Recommendation[]
  audit: { model_version: string; input_sha256: string; data_cutoff: string; review_period_days: number }
}

type Problem = { title?: string; details?: Array<{ field: string; issue: string }>; trace_id?: string }
type WorkflowStage = 'idle' | 'review' | 'approved' | 'simulated'

const rupiah = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })

function App() {
  const inputRef = useRef<HTMLInputElement>(null)
  const workflowRef = useRef<HTMLDivElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<Problem | null>(null)
  const [drafts, setDrafts] = useState<PurchaseDraft[]>([])
  const [workflowStage, setWorkflowStage] = useState<WorkflowStage>('idle')
  const [ownerConfirmed, setOwnerConfirmed] = useState(false)

  const buyNow = useMemo(() => result?.items.filter((item) => item.decision === 'BELI_SEKARANG') ?? [], [result])
  const postpone = useMemo(() => result?.items.filter((item) => item.decision === 'TUNDA') ?? [], [result])
  const issues = useMemo(() => validateDrafts(drafts, result?.budget ?? 0), [drafts, result])
  const approvedSpend = useMemo(() => draftTotal(drafts), [drafts])
  const supplierGroups = useMemo(() => groupDraftsBySupplier(drafts), [drafts])

  function resetWorkflow(items: Recommendation[] = result?.items ?? []) {
    setDrafts(buildPurchaseDrafts(items))
    setWorkflowStage('idle')
    setOwnerConfirmed(false)
  }

  function selectFile(next: File | undefined) {
    if (!next) return
    setFile(next)
    setResult(null)
    setError(null)
    resetWorkflow([])
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
      const nextResult = payload.data as Result
      setResult(nextResult)
      resetWorkflow(nextResult.items)
    } catch (problem) {
      setError(problem instanceof Error ? { title: problem.message } : (problem as Problem))
    } finally {
      setLoading(false)
    }
  }

  function openReview() {
    setWorkflowStage('review')
    setOwnerConfirmed(false)
    window.setTimeout(() => workflowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 0)
  }

  function updateDraft(index: number, patch: Partial<PurchaseDraft>) {
    setDrafts((current) => current.map((draft, draftIndex) => draftIndex === index ? { ...draft, ...patch } : draft))
    setWorkflowStage('review')
    setOwnerConfirmed(false)
  }

  function downloadCsv() {
    if (!result) return
    const keys = Object.keys(result.items[0] ?? {}) as Array<keyof Recommendation>
    const escape = (value: unknown) => `"${String(value).replaceAll('"', '""')}"`
    const csv = [keys.join(','), ...result.items.map((row) => keys.map((key) => escape(row[key])).join(','))].join('\n')
    downloadText(csv, 'lumbung_recommendations.csv', 'text/csv')
  }

  function downloadPurchaseOrder() {
    if (!result || workflowStage === 'review' || workflowStage === 'idle') return
    const poNumber = `LBG-${result.audit.input_sha256.slice(0, 8).toUpperCase()}`
    const header = ['po_number', 'supplier', 'sku_id', 'category', 'approved_qty', 'unit_price_idr', 'line_total_idr', 'requested_arrival_date']
    const rows = drafts.map((draft) => [
      poNumber,
      draft.supplier,
      draft.sku_id,
      draft.category,
      draft.approved_qty,
      draft.unit_price,
      draftLineTotal(draft),
      draft.requested_arrival_date,
    ])
    const escape = (value: unknown) => `"${String(value).replaceAll('"', '""')}"`
    const csv = [header.join(','), ...rows.map((row) => row.map(escape).join(','))].join('\n')
    downloadText(csv, `${poNumber.toLowerCase()}-draft.csv`, 'text/csv')
  }

  return (
    <main>
      <header className="nav">
        <a className="brand" href="#top" aria-label="Lumbung beranda">
          <span className="brand-mark">L</span><span>Lumbung</span>
        </a>
        <span className="nav-note"><span className="status-dot" /> Berjalan lokal dan dapat diaudit</span>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow">AI REPLENISHMENT COPILOT</div>
        <h1>Ubah data stok menjadi<br /><em>rencana belanja.</em></h1>
        <p className="hero-copy">Prioritaskan barang yang perlu dibeli tanpa melewati anggaran toko.</p>
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
          <div className="head-actions">
            <button className="secondary" onClick={downloadCsv}>Unduh hasil CSV</button>
            <button onClick={openReview}>Tinjau dan siapkan draft <span>→</span></button>
          </div>
        </div>
        <div className="summary-grid">
          <Summary label="Anggaran tersedia" value={rupiah.format(result.budget)} />
          <Summary label="Usulan belanja" value={rupiah.format(result.proposed_spend)} accent />
          <Summary label="Pemakaian anggaran" value={`${(result.budget_utilization * 100).toFixed(1)}%`} />
          <Summary label="SKU dibeli" value={`${buyNow.length} dari ${result.items.length}`} />
        </div>
        <DecisionTable title="Beli sekarang" subtitle="Prioritas terpilih di bawah batas anggaran" items={buyNow} buy />
        <DecisionTable title="Tunda" subtitle="Stok cukup atau belum masuk prioritas anggaran" items={postpone} />
        <div className="audit"><strong>Jejak keputusan</strong><span>Model {result.audit.model_version}</span><span>Input {result.audit.input_sha256.slice(0, 12)}…</span><span>Horizon: lead time + {result.audit.review_period_days} hari</span></div>

        {workflowStage !== 'idle' && <div className="purchase-workflow" ref={workflowRef}>
          <div className="workflow-heading">
            <div>
              <div className="eyebrow">02 · REVIEW PEMBELIAN</div>
              <h2>Setujui draft pesanan</h2>
              <p>Periksa jumlah, harga, supplier, dan tanggal tiba. Lumbung memeriksa ulang MOQ dan anggaran setelah perubahan.</p>
            </div>
            <span className="demo-badge">Data supplier simulasi</span>
          </div>

          <div className="draft-list">
            {drafts.map((draft, index) => <div className="draft-card" key={draft.sku_id}>
              <div className="draft-card-head">
                <div><strong>{draft.sku_id}</strong><small>{draft.category} · rekomendasi AI {draft.recommended_qty} unit</small></div>
                <strong>{rupiah.format(draftLineTotal(draft))}</strong>
              </div>
              <div className="draft-fields">
                <label>Jumlah disetujui<input aria-label={`Jumlah ${draft.sku_id}`} type="number" min={draft.moq} step={draft.moq} value={draft.approved_qty} disabled={workflowStage !== 'review'} onChange={(event) => updateDraft(index, { approved_qty: Number(event.target.value) })} /><small>Kelipatan MOQ {draft.moq}</small></label>
                <label>Harga per unit<input aria-label={`Harga ${draft.sku_id}`} type="number" min="1" step="1" value={draft.unit_price} disabled={workflowStage !== 'review'} onChange={(event) => updateDraft(index, { unit_price: Number(event.target.value) })} /><small>Rupiah · data demo</small></label>
                <label>Supplier<select aria-label={`Supplier ${draft.sku_id}`} value={draft.supplier} disabled={workflowStage !== 'review'} onChange={(event) => updateDraft(index, { supplier: event.target.value })}>{DEMO_SUPPLIERS.map((supplier) => <option key={supplier}>{supplier}</option>)}</select><small>Registry simulasi</small></label>
                <label>Tanggal tiba<input aria-label={`Tanggal tiba ${draft.sku_id}`} type="date" min={todayInputValue()} value={draft.requested_arrival_date} disabled={workflowStage !== 'review'} onChange={(event) => updateDraft(index, { requested_arrival_date: event.target.value })} /><small>Permintaan owner</small></label>
              </div>
            </div>)}
          </div>

          <div className={`approval-summary ${issues.length > 0 ? 'has-issues' : ''}`}>
            <div><small>Total draft</small><strong>{rupiah.format(approvedSpend)}</strong><span>dari {rupiah.format(result.budget)}</span></div>
            <div><small>Sisa anggaran</small><strong>{rupiah.format(result.budget - approvedSpend)}</strong><span>{drafts.length} SKU · {supplierGroups.length} supplier</span></div>
            <div className="validation-status"><small>Validasi</small><strong>{issues.length === 0 ? 'Siap disetujui' : `${issues.length} hal perlu diperbaiki`}</strong><span>MOQ, harga, tanggal, dan budget</span></div>
          </div>

          {issues.length > 0 && <div className="error" role="alert">{issues.map((issue) => <span key={`${issue.field}-${issue.issue}`}><strong>{issue.field}</strong>: {issue.issue}</span>)}</div>}

          {workflowStage === 'review' && <div className="approval-controls">
            <label className="confirmation"><input type="checkbox" checked={ownerConfirmed} onChange={(event) => setOwnerConfirmed(event.target.checked)} /><span>Saya sudah memeriksa draft dan menyetujui nilai pesanan di atas.</span></label>
            <div className="approval-buttons">
              <button className="secondary" onClick={() => { resetWorkflow(); setWorkflowStage('review') }}>Kembalikan rekomendasi AI</button>
              <button disabled={issues.length > 0 || !ownerConfirmed} onClick={() => setWorkflowStage('approved')}>Setujui dan buat draft PO <span>→</span></button>
            </div>
          </div>}

          {(workflowStage === 'approved' || workflowStage === 'simulated') && <PurchaseOrderPreview
            drafts={drafts}
            inputHash={result.audit.input_sha256}
            simulated={workflowStage === 'simulated'}
            onEdit={() => { setWorkflowStage('review'); setOwnerConfirmed(false) }}
            onDownload={downloadPurchaseOrder}
            onSimulate={() => setWorkflowStage('simulated')}
          />}
        </div>}
      </section>}

      <footer><span>Lumbung memberi rekomendasi dan draft. Owner menyetujui pembelian.</span><span>Supplier dan pengiriman pada prototype ini menggunakan simulasi.</span></footer>
    </main>
  )
}

function Summary({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <div className={`summary ${accent ? 'accent' : ''}`}><small>{label}</small><strong>{value}</strong></div>
}

function DecisionTable({ title, subtitle, items, buy = false }: { title: string; subtitle: string; items: Recommendation[]; buy?: boolean }) {
  return <div className="decision-card">
    <div className="decision-title"><span className={buy ? 'buy-badge' : 'hold-badge'}>{buy ? '✓' : '–'}</span><div><h3>{title}</h3><p>{subtitle}</p></div><strong className="count">{items.length} SKU</strong></div>
    {items.length === 0 ? <p className="empty">Tidak ada SKU pada kelompok ini.</p> : <div className="table-wrap"><table><thead><tr><th>SKU</th><th>Stok tersedia</th><th>Kebutuhan P50–P90</th><th>Rekomendasi</th><th>Biaya</th><th>Risiko</th><th>Alasan</th></tr></thead><tbody>{items.map((item) => <tr key={item.sku_id}><td><strong>{item.sku_id}</strong><small>{item.category}</small></td><td>{item.stock_on_hand} unit<small>{item.on_order > 0 ? `+${item.on_order} dalam pesanan` : 'Tidak ada on-order'}</small></td><td>{item.forecast_p50.toFixed(1)}–{item.forecast_p90.toFixed(1)}<small>{item.horizon_days} hari</small></td><td>{item.order_qty > 0 ? `${item.order_qty} unit` : 'Belum dibeli'}<small>MOQ {item.moq}</small></td><td>{rupiah.format(item.order_cost)}</td><td><span className="risk-track"><i style={{ width: `${Math.round(item.stockout_risk * 100)}%` }} /></span><small>{Math.round(item.stockout_risk * 100)}%</small></td><td>{item.reason}</td></tr>)}</tbody></table></div>}
  </div>
}

function PurchaseOrderPreview({ drafts, inputHash, simulated, onEdit, onDownload, onSimulate }: { drafts: PurchaseDraft[]; inputHash: string; simulated: boolean; onEdit: () => void; onDownload: () => void; onSimulate: () => void }) {
  const poNumber = `LBG-${inputHash.slice(0, 8).toUpperCase()}`
  return <div className="po-preview">
    <div className="po-heading">
      <div><div className="eyebrow">03 · DRAFT PURCHASE ORDER</div><h2>{poNumber}</h2><p>Owner telah menyetujui draft ini. Belum ada pesan yang dikirim ke supplier.</p></div>
      <span className={`order-status ${simulated ? 'sent' : ''}`}>{simulated ? 'Simulasi terkirim' : 'Disetujui owner'}</span>
    </div>
    <div className="supplier-grid">
      {groupDraftsBySupplier(drafts).map(([supplier, supplierDrafts]) => <article className="supplier-order" key={supplier}>
        <div className="supplier-order-head"><div><small>Supplier demo</small><h3>{supplier}</h3></div><strong>{rupiah.format(draftTotal(supplierDrafts))}</strong></div>
        <ul>{supplierDrafts.map((draft) => <li key={draft.sku_id}><span>{draft.sku_id}<small>{draft.approved_qty} unit · tiba {draft.requested_arrival_date}</small></span><strong>{rupiah.format(draftLineTotal(draft))}</strong></li>)}</ul>
        <label className="message-preview">Preview pesan<textarea readOnly value={supplierMessage(supplier, supplierDrafts)} /></label>
      </article>)}
    </div>
    <div className="simulation-note"><strong>Mode simulasi</strong><span>Lumbung tidak menghubungi Telegram atau WhatsApp. Tombol di bawah hanya memperbarui status pada browser ini.</span></div>
    <div className="approval-buttons">
      <button className="secondary" onClick={onEdit}>Ubah draft</button>
      <button className="secondary" onClick={onDownload}>Unduh draft PO</button>
      <button disabled={simulated} onClick={onSimulate}>{simulated ? 'Simulasi selesai' : 'Simulasikan pengiriman'} <span>→</span></button>
    </div>
    {simulated && <div className="simulation-result" role="status"><span>✓</span><div><strong>Status demo diperbarui</strong><p>Prototype mencatat simulasi pada browser. Supplier belum menerima pesan dan status akan hilang saat halaman dimuat ulang.</p></div></div>}
  </div>
}

function downloadText(content: string, filename: string, mediaType: string) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([content], { type: mediaType }))
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

export default App
