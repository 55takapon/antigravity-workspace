import { isPreviewMode } from '@/lib/env'
import { previewWeightRepository } from '@/features/weights/preview-repository'
import { supabaseWeightRepository } from '@/features/weights/supabase-repository'
import type { WeightRepository } from '@/features/weights/types'

/** 環境変数の有無で実装を切り替える。画面側はこれだけを見る。 */
export const weightRepository: WeightRepository = isPreviewMode
  ? previewWeightRepository
  : supabaseWeightRepository
