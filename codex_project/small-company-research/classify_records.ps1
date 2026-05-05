param(
  [string]$InputTsv,
  [int]$StartRecord,
  [int]$EndRecord
)

. .\classify_industries.ps1 -InputTsv $InputTsv -StartRow 999999 -EndRow 999999 | Out-Null

$rows = Import-Csv -LiteralPath $InputTsv -Delimiter "`t" -Encoding UTF8
$out = for ($i = $StartRecord - 1; $i -le $EndRecord - 1; $i++) {
  if ($i -ge $rows.Count) {
    ""
    continue
  }
  $row = $rows[$i]
  $existing = ""
  $props = $row.PSObject.Properties
  if ($props.Count -gt 14) {
    $existing = [string]$props[14].Value
  }
  switch ($existing) {
    'Web制作' { 'web_production'; continue }
    'Webマーケ' { 'web_marketing'; continue }
    'ハイブリッド' { 'hybrid'; continue }
  }

  $text = Get-TextSnippet -Url $row.URL
  Get-Industry -Company $row.'企業名' -Text $text
}

$out -join "`n"

