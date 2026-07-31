import { useMemo, useState } from 'react'
import { ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { formatShortWeekday } from '@/lib/date'
import { useWeightHistory } from '@/features/weights/queries'
import { EditWeightDialog } from '@/features/weights/edit-weight-dialog'
import { WeightDelta } from '@/features/weights/weight-delta'
import type { WeightRecord } from '@/features/weights/types'

/** 新しい順の配列に、直前（1つ古い）記録との差分を添える */
function withDelta(records: WeightRecord[]): { record: WeightRecord; delta: number | null }[] {
  return records.map((record, index) => {
    const older = records[index + 1]
    return { record, delta: older ? record.weight_kg - older.weight_kg : null }
  })
}

export function HistoryPage() {
  const history = useWeightHistory()
  const [editing, setEditing] = useState<WeightRecord | null>(null)

  const records = useMemo(() => history.data?.pages.flat() ?? [], [history.data])
  const rows = useMemo(() => withDelta(records), [records])

  if (history.isPending) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-muted h-14 animate-pulse rounded-lg" />
        ))}
      </div>
    )
  }

  if (records.length === 0) {
    return (
      <Card className="border-white/8">
        <CardContent className="text-muted-foreground py-10 text-center text-sm">
          まだ記録がありません
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden border-white/8 py-0">
        <ul className="divide-border divide-y">
          {rows.map(({ record, delta }) => (
            <li key={record.id}>
              <button
                type="button"
                onClick={() => setEditing(record)}
                className="hover:bg-accent/50 active:bg-accent flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
              >
                <span className="text-muted-foreground w-16 shrink-0 text-xs tabular-nums">
                  {formatShortWeekday(record.recorded_at)}
                </span>
                <span className="shrink-0 text-base font-semibold tabular-nums">
                  {record.weight_kg.toFixed(1)}
                  <span className="text-muted-foreground ml-0.5 text-xs font-normal">kg</span>
                </span>
                <WeightDelta delta={delta} className="shrink-0 text-xs" />
                <span className="text-muted-foreground flex-1 truncate text-right text-xs">
                  {record.note}
                </span>
                <ChevronRight className="text-muted-foreground size-4 shrink-0" />
              </button>
            </li>
          ))}
        </ul>
      </Card>

      {history.hasNextPage && (
        <Button
          variant="outline"
          className="w-full"
          onClick={() => history.fetchNextPage()}
          disabled={history.isFetchingNextPage}
        >
          {history.isFetchingNextPage && <Loader2 className="size-4 animate-spin" />}
          もっと見る
        </Button>
      )}

      <EditWeightDialog record={editing} onClose={() => setEditing(null)} />
    </div>
  )
}
