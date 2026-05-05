param(
  [string]$InputTsv = "sheet_251127_gid1828149422.tsv",
  [int]$StartRow = 101,
  [int]$EndRow = 400
)

$ErrorActionPreference = "SilentlyContinue"

function Get-TextSnippet {
  param([string]$Url)
  if ([string]::IsNullOrWhiteSpace($Url)) { return "" }
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10 -MaximumRedirection 5
    $html = [string]$response.Content
    $html = [regex]::Replace($html, '<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', 'IgnoreCase')
    $text = [regex]::Replace($html, '<[^>]+>', ' ')
    $text = [System.Net.WebUtility]::HtmlDecode($text)
    $text = [regex]::Replace($text, '\s+', ' ').Trim()
    if ($text.Length -gt 4500) { return $text.Substring(0, 4500) }
    return $text
  } catch {
    return ""
  }
}

function Has-Any {
  param([string]$Text, [string[]]$Patterns)
  foreach ($pattern in $Patterns) {
    if ($Text -match [regex]::Escape($pattern)) { return $true }
  }
  return $false
}

function Get-Industry {
  param([string]$Company, [string]$Text)
  $haystack = (($Company + " " + $Text) -replace '\s+', ' ')

  $productionPatterns = @(
    'Web制作', 'WEB制作', 'ウェブ制作', 'ホームページ制作', 'サイト制作',
    'Webサイト制作', 'WEBサイト制作', 'LP制作', 'ランディングページ制作',
    'ECサイト制作', 'Shopify構築', 'WordPress', 'CMS', 'UI/UX',
    'Webデザイン', 'WEBデザイン', 'コーディング', 'Webシステム',
    'WEBシステム', 'Webアプリケーション開発', 'Web開発', 'フロントエンド'
  )

  $marketingPatterns = @(
    'Webマーケティング', 'WEBマーケティング', 'デジタルマーケティング',
    'マーケティング支援', '広告運用', '広告代理', 'SEO', 'MEO', 'SNS運用',
    'SNSマーケティング', 'インフルエンサー', '集客', 'リスティング広告',
    'Google広告', 'Yahoo広告', 'アクセス解析', 'EC運用', 'TikTok Shop',
    'プロモーション', 'デジタル広告', 'PR支援'
  )

  $prod = Has-Any -Text $haystack -Patterns $productionPatterns
  $mark = Has-Any -Text $haystack -Patterns $marketingPatterns

  if ($prod -and $mark) { return "hybrid" }
  if ($mark) { return "web_marketing" }
  if ($prod) { return "web_production" }
  return "業種違い"
}

$rows = Import-Csv -LiteralPath $InputTsv -Delimiter "`t" -Encoding UTF8
$out = foreach ($row in $rows) {
  $sheetRow = [int]$row.'№' + 1
  if ($sheetRow -lt $StartRow -or $sheetRow -gt $EndRow) { continue }
  $text = Get-TextSnippet -Url $row.URL
  [pscustomobject]@{
    '行' = $sheetRow
    '業種判定' = Get-Industry -Company $row.'企業名' -Text $text
  }
}

$out | Sort-Object '行' | ConvertTo-Csv -Delimiter "`t" -NoTypeInformation

