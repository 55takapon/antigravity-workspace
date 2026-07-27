# OS別スケジューラ 詳細（Mac / Windows）

`setup_schedule.py` が OS を自動判定して下記を実行する。ユーザーは意識しなくてよいが、
トラブル時・手動確認用に控える。

## 共通の物理制約（AIでも消せない）
- **PCが起動・ログイン中でないと走らない**。スリープ/シャットダウンの時刻は実行されない。
  - prep は毎日必須なので **起動時catch-up**（前回実行から24h超なら起動直後に1回）＋ **heartbeat通知** を推奨（別途実装）。
- **初回のOS権限**（送信でブラウザ操作＝Mac:オートメーション/アクセシビリティ、Win:UAC/フォアグラウンド）は
  本人がGUIで許可する必要がある。ここだけは自動化不可。

## macOS（launchd）
| 操作 | コマンド |
|---|---|
| 登録/更新 | plist を `~/Library/LaunchAgents/com.claude.simesapo-sales-{prep,send}.plist` に生成 → `launchctl bootout gui/$UID/<label>`（旧を外す）→ `launchctl bootstrap gui/$UID <plist>` |
| 一覧 | `launchctl list | grep com.claude.simesapo-sales` |
| 即時実行（動作確認） | `launchctl kickstart -k gui/$UID/com.claude.simesapo-sales-prep` |
| 解除 | `launchctl bootout gui/$UID/<label>` ＋ plist 削除 |
| スリープ対策 | 任意で `pmset` の `repeat`/`schedule` で wake を仕込む（電源設定依存） |
| ログ | `~/Library/Logs/claude-sales-{prep,send}.log` / `*-error.log` |

- 平日のみは `StartCalendarInterval` を Weekday 1..5 の配列で表現（1=月〜5=金）。

## Windows（Task Scheduler / schtasks）
| 操作 | コマンド |
|---|---|
| 登録（毎日） | `schtasks /Create /F /TN com.claude.simesapo-sales-prep /TR "powershell -NoProfile -ExecutionPolicy Bypass -File <kick_sales.ps1> prep" /SC DAILY /ST 08:30 /RL LIMITED` |
| 登録（平日） | 上記に `/SC WEEKLY /D MON,TUE,WED,THU,FRI` |
| 変更（時刻） | `schtasks /Change /TN com.claude.simesapo-sales-send /ST 14:00` |
| 一覧 | `schtasks /Query /TN com.claude.simesapo-sales-prep /V /FO LIST` |
| 即時実行 | `schtasks /Run /TN com.claude.simesapo-sales-prep` |
| 解除 | `schtasks /Delete /F /TN com.claude.simesapo-sales-prep` |
| スリープ対策 | タスクのプロパティ「Wake the computer to run this task」を有効化（`Register-ScheduledTask` の `-Settings (New-ScheduledTaskSettingsSet -WakeToRun)`） |
| ログ | `%LOCALAPPDATA%\simesapo-sales\logs\claude-sales-{prep,send}.log` |

- ★Windows のブラウザ送信（Playwright）権限は**未実地検証**。auto 送信を配布前に1台で要検証。
- PowerShell 実行ポリシーで弾かれる場合は `-ExecutionPolicy Bypass`（タスク定義に既に付与）。
