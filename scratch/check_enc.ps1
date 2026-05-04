$p = 'C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-analysis\SKILL.md'
$bytes = [System.IO.File]::ReadAllBytes($p)
$sjis = [System.Text.Encoding]::GetEncoding('shift_jis')
$text = $sjis.GetString($bytes)
$desc = $text -split "`n" | Where-Object { $_ -match '^description:' } | Select-Object -First 1
Write-Host "SJIS desc: $desc"
