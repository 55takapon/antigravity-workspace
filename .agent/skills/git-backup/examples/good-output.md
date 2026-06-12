# git-backup 入力→出力例

評価ケース（git-backup-workspace/iteration-1）の実出力から採録。

## 例1（正常系）: 通常バックアップ

**入力:**

> バックアップして

**出力:**

リポジトリルートに移動して単発バックアップを実行します。

```powershell
cd C:\Users\hangy\.gemini\antigravity
.\sync-github.ps1 -Once
```

PowerShellでは `&&` が使えないため、連結する場合は `;` を使います。

## 例2（正常系）: カスタムメッセージ付き

**入力:**

> 「feat: 新スキル追加」のメッセージでgitに保存して

**出力:**

コミットメッセージ規則（feat: = 新機能・新スキル追加）に従い、単発実行でメッセージを指定します。

```powershell
cd C:\Users\hangy\.gemini\antigravity
.\sync-github.ps1 -Once -Message "feat: 新スキル追加"
```

## 例3（異常系）: push が拒否された

**入力:**

> push が non-fast-forward で拒否された。どうすればいい？

**出力:**

まず rebase で取り込み、その後に push します。force push は第一手にしません。

```powershell
git pull --rebase origin main
git push origin main
```

なお sync-github.ps1 は pull --rebase を自動で行います。
