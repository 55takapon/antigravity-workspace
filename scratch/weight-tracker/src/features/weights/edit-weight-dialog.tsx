import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { formatDateTime, toDateTimeLocalValue } from '@/lib/date'
import { useDeleteWeight, useUpdateWeight } from '@/features/weights/queries'
import type { WeightRecord } from '@/features/weights/types'
import {
  WeightFormFields,
  toWeightInput,
  weightFormSchema,
  type WeightFormValues,
} from '@/features/weights/weight-form'

type EditWeightDialogProps = {
  /** 編集対象。null ならモーダルを閉じる */
  record: WeightRecord | null
  onClose: () => void
}

export function EditWeightDialog({ record, onClose }: EditWeightDialogProps) {
  return (
    <Dialog open={record !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>記録を編集</DialogTitle>
          <DialogDescription>
            {record ? formatDateTime(record.recorded_at) : ''} の記録
          </DialogDescription>
        </DialogHeader>
        {/* record が変わるたびにフォームを作り直す */}
        {record && <EditForm key={record.id} record={record} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  )
}

function EditForm({ record, onClose }: { record: WeightRecord; onClose: () => void }) {
  const updateWeight = useUpdateWeight()
  const deleteWeight = useDeleteWeight()
  const [confirmOpen, setConfirmOpen] = useState(false)

  const form = useForm<WeightFormValues>({
    resolver: zodResolver(weightFormSchema),
    defaultValues: {
      weight: record.weight_kg.toFixed(1),
      recordedAt: toDateTimeLocalValue(record.recorded_at),
      note: record.note ?? '',
    },
  })

  const onSubmit = (values: WeightFormValues) => {
    updateWeight.mutate(
      { id: record.id, input: toWeightInput(values) },
      {
        onSuccess: () => {
          toast.success('更新しました')
          onClose()
        },
        onError: (error) => {
          toast.error('更新に失敗しました', {
            description: error instanceof Error ? error.message : undefined,
          })
        },
      },
    )
  }

  const onDelete = () => {
    deleteWeight.mutate(record.id, {
      onSuccess: () => {
        toast.success('削除しました')
        setConfirmOpen(false)
        onClose()
      },
      onError: (error) => {
        toast.error('削除に失敗しました', {
          description: error instanceof Error ? error.message : undefined,
        })
      },
    })
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5" noValidate>
      <WeightFormFields form={form} idPrefix={`edit-${record.id}`} />

      <DialogFooter className="gap-2 sm:justify-between">
        <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <AlertDialogTrigger asChild>
            <Button type="button" variant="ghost" className="text-destructive">
              <Trash2 className="size-4" />
              削除
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>この記録を削除しますか？</AlertDialogTitle>
              <AlertDialogDescription>
                {formatDateTime(record.recorded_at)} の {record.weight_kg.toFixed(1)} kg
                を削除します。この操作は取り消せません。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>キャンセル</AlertDialogCancel>
              <AlertDialogAction
                onClick={(event) => {
                  event.preventDefault()
                  onDelete()
                }}
                disabled={deleteWeight.isPending}
              >
                {deleteWeight.isPending && <Loader2 className="size-4 animate-spin" />}
                削除する
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <Button type="submit" disabled={updateWeight.isPending}>
          {updateWeight.isPending && <Loader2 className="size-4 animate-spin" />}
          保存
        </Button>
      </DialogFooter>
    </form>
  )
}
