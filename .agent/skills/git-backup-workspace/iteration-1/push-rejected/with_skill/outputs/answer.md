まず rebase で取り込み、その後に push します。force push は第一手にしません。

```powershell
git pull --rebase origin main
git push origin main
```

なお sync-github.ps1 は pull --rebase を自動で行います。