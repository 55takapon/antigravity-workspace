リポジトリルートに移動して単発バックアップを実行します。

```powershell
cd C:\Users\hangy\.gemini\antigravity
.\sync-github.ps1 -Once
```

PowerShellでは `&&` が使えないため、連結する場合は `;` を使います。