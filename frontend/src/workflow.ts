export type Recommendation = {
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

export type PurchaseDraft = {
  sku_id: string
  category: string
  recommended_qty: number
  approved_qty: number
  moq: number
  unit_price: number
  supplier: string
  requested_arrival_date: string
}

export type DraftIssue = {
  field: string
  issue: string
}

export const DEMO_SUPPLIERS = [
  'Mitra Pangan Demo',
  'Sumber Harian Demo',
  'Distribusi Sejahtera Demo',
] as const

function dateInputValue(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function todayInputValue(): string {
  return dateInputValue(new Date())
}

export function buildPurchaseDrafts(items: Recommendation[]): PurchaseDraft[] {
  const now = new Date()
  return items
    .filter((item) => item.decision === 'BELI_SEKARANG' && item.order_qty > 0)
    .map((item) => {
      const supplierIndex = [...item.category].reduce((sum, character) => sum + character.charCodeAt(0), 0) % DEMO_SUPPLIERS.length
      const arrival = new Date(now)
      arrival.setDate(arrival.getDate() + Math.max(1, item.horizon_days - 7))
      return {
        sku_id: item.sku_id,
        category: item.category,
        recommended_qty: item.order_qty,
        approved_qty: item.order_qty,
        moq: item.moq,
        unit_price: item.unit_cost,
        supplier: DEMO_SUPPLIERS[supplierIndex],
        requested_arrival_date: dateInputValue(arrival),
      }
    })
}

export function draftLineTotal(draft: PurchaseDraft): number {
  return draft.approved_qty * draft.unit_price
}

export function draftTotal(drafts: PurchaseDraft[]): number {
  return drafts.reduce((total, draft) => total + draftLineTotal(draft), 0)
}

export function validateDrafts(drafts: PurchaseDraft[], budget: number): DraftIssue[] {
  const issues: DraftIssue[] = []
  const today = todayInputValue()

  if (drafts.length === 0) {
    issues.push({ field: 'draft', issue: 'Tidak ada SKU yang dapat disetujui.' })
  }

  for (const draft of drafts) {
    if (!Number.isInteger(draft.approved_qty) || draft.approved_qty < draft.moq) {
      issues.push({ field: draft.sku_id, issue: `Jumlah minimal ${draft.moq} unit.` })
    } else if (draft.approved_qty % draft.moq !== 0) {
      issues.push({ field: draft.sku_id, issue: `Jumlah harus kelipatan MOQ ${draft.moq}.` })
    }
    if (!Number.isFinite(draft.unit_price) || draft.unit_price <= 0) {
      issues.push({ field: draft.sku_id, issue: 'Harga satuan harus lebih dari nol.' })
    }
    if (!DEMO_SUPPLIERS.includes(draft.supplier as (typeof DEMO_SUPPLIERS)[number])) {
      issues.push({ field: draft.sku_id, issue: 'Pilih supplier demo yang tersedia.' })
    }
    if (!draft.requested_arrival_date || draft.requested_arrival_date < today) {
      issues.push({ field: draft.sku_id, issue: 'Tanggal tiba tidak boleh sebelum hari ini.' })
    }
  }

  const total = draftTotal(drafts)
  if (total > budget) {
    issues.push({ field: 'budget', issue: `Draft melampaui anggaran sebesar Rp${Math.ceil(total - budget).toLocaleString('id-ID')}.` })
  }
  return issues
}

export function groupDraftsBySupplier(drafts: PurchaseDraft[]): Array<[string, PurchaseDraft[]]> {
  const grouped = new Map<string, PurchaseDraft[]>()
  for (const draft of drafts) {
    const current = grouped.get(draft.supplier) ?? []
    current.push(draft)
    grouped.set(draft.supplier, current)
  }
  return [...grouped.entries()]
}

export function supplierMessage(supplier: string, drafts: PurchaseDraft[]): string {
  const lines = drafts.map(
    (draft) => `- ${draft.sku_id}: ${draft.approved_qty} unit @ Rp${draft.unit_price.toLocaleString('id-ID')}`,
  )
  const requestedDate = drafts.map((draft) => draft.requested_arrival_date).sort()[0]
  return [
    `Halo ${supplier}, kami ingin meminta konfirmasi untuk draft pesanan berikut:`,
    ...lines,
    `Mohon konfirmasi ketersediaan, harga, dan estimasi tiba mulai ${requestedDate}.`,
    'Pesan ini merupakan simulasi prototype dan belum dikirim.',
  ].join('\n')
}
