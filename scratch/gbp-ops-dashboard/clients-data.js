/**
 * GBP運用管理ダッシュボード — クライアント & タスク定義
 * 
 * クライアント追加手順:
 *   1. CLIENTS配列に新しいオブジェクトを追加
 *   2. id はフォルダ名と一致させる（.agent/clients/{id}/）
 *   3. invoice/receipt: trueで請求書/領収書タスクを表示
 */

const CLIENTS = [
  {
    id: "iami-kakogawa",
    name: "アイアムアイ加古川",
    icon: "🍽️",
    category: "飲食",
    invoice: false,
  },
  {
    id: "kamada-dental",
    name: "かまだ歯科医院",
    icon: "🦷",
    category: "歯科",
    invoice: false,
  },
  {
    id: "meet-dental",
    name: "ミート歯科",
    icon: "🦷",
    category: "歯科",
    invoice: false,
  },
  {
    id: "sapporo-occlusion",
    name: "幸健美歯科クリニック",
    icon: "🦷",
    category: "歯科",
    invoice: false,
  },
  {
    id: "jetproduce",
    name: "ジェットプロデュース",
    icon: "🚀",
    category: "Web",
    invoice: false,
  },
  {
    id: "eiwa-juku-kita",
    name: "英和塾 北校",
    icon: "📚",
    category: "教育",
    invoice: true,
  },
  {
    id: "eiwa-juku-minami",
    name: "英和塾 南校",
    icon: "📚",
    category: "教育",
    invoice: false,
  },
  {
    id: "sakakibara-tax",
    name: "榊原税理士事務所",
    icon: "📊",
    category: "士業",
    invoice: false,
  },
  {
    id: "shibamoto-legal",
    name: "芝本司法書士事務所",
    icon: "⚖️",
    category: "士業",
    invoice: false,
  },
  {
    id: "unaginokagura",
    name: "鰻の神楽 京都店",
    icon: "🍽️",
    category: "飲食",
    invoice: false,
  },
  {
    id: "happycars",
    name: "ハッピーカーズ 和泉岸和田店",
    icon: "🚗",
    category: "車買取",
    invoice: false,
  },
];

// タスク定義（表示順）
const TASKS = [
  { id: "insight",  label: "インサイト抽出<br>前月分", icon: "📊", deadline: "1日",  required: true,  description: "GBPインサイトデータをダウンロード" },
  { id: "report_gen",   label: "月次レポート<br>生成",   icon: "📋", deadline: "3日",  required: true,  description: "月次パフォーマンスレポート生成", autoDetect: true },
  { id: "report_share", label: "月次レポート<br>仕上げと共有", icon: "🤝", deadline: "5日",  required: true,  description: "月次レポートの仕上げとクライアントへの共有" },
  { id: "writing",  label: "投稿文作成",     icon: "✍️", deadline: "5日",  required: true,  description: "GBP投稿文の執筆", autoDetect: true },
  { id: "schedule", label: "投稿予約設定",   icon: "📅", deadline: "7日",  required: true,  description: "GBP管理画面で予約投稿セット" },
  { id: "invoice",  label: "請求書発行",     icon: "💰", deadline: "月末", required: false, description: "請求書の発行・送付" },
];

// カテゴリ色マップ
const CATEGORY_COLORS = {
  "飲食":   "#fb923c",
  "歯科":   "#60a5fa",
  "Web":    "#a78bfa",
  "教育":   "#34d399",
  "士業":   "#fbbf24",
  "未定":   "#64748b",
  "車買取": "#f87171",
};
