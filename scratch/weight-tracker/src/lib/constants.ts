/**
 * アプリ全体で使う定数。
 * 仕様変更で迷いやすい値はここに集約する。
 */

/**
 * 1日に複数回記録があるとき、グラフ用に1点へ丸める際どちらを採用するか。
 * 'first' = その日の最初の記録（デフォルト） / 'last' = その日の最後の記録
 */
export const DAILY_SAMPLE: 'first' | 'last' = 'first'

/** グラフに重ねる移動平均の日数 */
export const MOVING_AVERAGE_DAYS = 7

/** 履歴画面の1ページあたりの取得件数 */
export const HISTORY_PAGE_SIZE = 50

/** グラフY軸に取る上下マージン（kg） */
export const CHART_Y_MARGIN_KG = 1.5

/** 体重入力の許容範囲（DBのCHECK制約と揃える） */
export const WEIGHT_MIN_KG = 0
export const WEIGHT_MAX_KG = 500
