import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
  type InfiniteData,
} from '@tanstack/react-query'
import { useQuery } from '@tanstack/react-query'
import { HISTORY_PAGE_SIZE } from '@/lib/constants'
import { daysAgoStart } from '@/lib/date'
import { weightRepository } from '@/features/weights/repository'
import type { PeriodKey } from '@/features/weights/chart-data'
import type { WeightInput, WeightRecord } from '@/features/weights/types'

export const weightKeys = {
  all: ['weights'] as const,
  history: () => [...weightKeys.all, 'history'] as const,
  range: (period: PeriodKey) => [...weightKeys.all, 'range', period] as const,
}

const PERIOD_DAYS: Record<PeriodKey, number | null> = {
  '7d': 7,
  '30d': 30,
  '90d': 90,
  all: null,
}

/** グラフ用。指定期間の記録を古い順で取得する */
export function useWeightRange(period: PeriodKey) {
  return useQuery({
    queryKey: weightKeys.range(period),
    queryFn: () => {
      const days = PERIOD_DAYS[period]
      return weightRepository.listSince(days === null ? null : daysAgoStart(days))
    },
  })
}

type HistoryData = InfiniteData<WeightRecord[], number>

const sortDesc = (records: WeightRecord[]) =>
  [...records].sort((a, b) => b.recorded_at.localeCompare(a.recorded_at))

/** 履歴（新しい順・50件ずつ）。記録画面の最新値もこのキャッシュから読む。 */
export function useWeightHistory() {
  return useInfiniteQuery({
    queryKey: weightKeys.history(),
    queryFn: ({ pageParam }) =>
      weightRepository.list({ limit: HISTORY_PAGE_SIZE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length < HISTORY_PAGE_SIZE ? undefined : allPages.length * HISTORY_PAGE_SIZE,
  })
}

/** 各ミューテーション後に、履歴とグラフのキャッシュをまとめて作り直す */
function useInvalidateWeights() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: weightKeys.all })
}

export function useCreateWeight() {
  const queryClient = useQueryClient()
  const invalidate = useInvalidateWeights()

  return useMutation({
    mutationFn: (input: WeightInput) => weightRepository.create(input),

    // 楽観的更新: サーバー応答を待たずに一覧へ差し込む
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: weightKeys.history() })
      const previous = queryClient.getQueryData<HistoryData>(weightKeys.history())

      const optimistic: WeightRecord = { id: `optimistic-${crypto.randomUUID()}`, ...input }
      queryClient.setQueryData<HistoryData>(weightKeys.history(), (old) => {
        if (!old) return old
        const [first = [], ...rest] = old.pages
        return { ...old, pages: [sortDesc([optimistic, ...first]), ...rest] }
      })

      return { previous }
    },

    onError: (_error, _input, context) => {
      if (context?.previous) {
        queryClient.setQueryData(weightKeys.history(), context.previous)
      }
    },

    onSettled: invalidate,
  })
}

export function useUpdateWeight() {
  const queryClient = useQueryClient()
  const invalidate = useInvalidateWeights()

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: WeightInput }) =>
      weightRepository.update(id, input),

    onMutate: async ({ id, input }) => {
      await queryClient.cancelQueries({ queryKey: weightKeys.history() })
      const previous = queryClient.getQueryData<HistoryData>(weightKeys.history())

      queryClient.setQueryData<HistoryData>(weightKeys.history(), (old) => {
        if (!old) return old
        return {
          ...old,
          pages: old.pages.map((page) =>
            sortDesc(page.map((record) => (record.id === id ? { id, ...input } : record))),
          ),
        }
      })

      return { previous }
    },

    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(weightKeys.history(), context.previous)
      }
    },

    onSettled: invalidate,
  })
}

export function useDeleteWeight() {
  const queryClient = useQueryClient()
  const invalidate = useInvalidateWeights()

  return useMutation({
    mutationFn: (id: string) => weightRepository.remove(id),

    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: weightKeys.history() })
      const previous = queryClient.getQueryData<HistoryData>(weightKeys.history())

      queryClient.setQueryData<HistoryData>(weightKeys.history(), (old) => {
        if (!old) return old
        return {
          ...old,
          pages: old.pages.map((page) => page.filter((record) => record.id !== id)),
        }
      })

      return { previous }
    },

    onError: (_error, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(weightKeys.history(), context.previous)
      }
    },

    onSettled: invalidate,
  })
}
