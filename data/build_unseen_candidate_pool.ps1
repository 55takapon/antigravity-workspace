param(
    [string]$DataDir = "data",
    [string]$ExistingJson = "data\webmarketing_exclude_live_20260731.json",
    [string]$OutputCsv = "data\webmarketing_unseen_pool_20260731.csv"
)

function Normalize-Domain([string]$Url) {
    if ([string]::IsNullOrWhiteSpace($Url)) { return "" }
    try {
        $candidate = $Url.Trim()
        if ($candidate -notmatch '^[a-zA-Z][a-zA-Z0-9+.-]*://') {
            $candidate = "https://$candidate"
        }
        $hostName = ([uri]$candidate).Host.ToLowerInvariant()
        return ($hostName -replace '^www\.', '')
    } catch {
        return ""
    }
}

$existing = Get-Content -LiteralPath $ExistingJson -Raw -Encoding UTF8 | ConvertFrom-Json
$existingDomains = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
foreach ($row in $existing) {
    $domain = Normalize-Domain $row.url
    if ($domain) { [void]$existingDomains.Add($domain) }
}

$seen = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
$pool = [System.Collections.Generic.List[object]]::new()
$files = Get-ChildItem -LiteralPath $DataDir -Filter "*.csv" |
    Where-Object {
        $_.Name -ne (Split-Path -Leaf $OutputCsv) -and
        $_.Name -match 'candidate|marketing|verified|member|partner|filtered|refiltered'
    }

foreach ($file in $files) {
    try {
        $rows = Import-Csv -LiteralPath $file.FullName -Encoding UTF8
    } catch {
        continue
    }
    foreach ($row in $rows) {
        $company = [string]$row.company_name
        $url = [string]$row.url
        $domain = Normalize-Domain $url
        if (-not $company.Trim() -or -not $domain) { continue }
        if ($existingDomains.Contains($domain) -or -not $seen.Add($domain)) { continue }
        $pool.Add([pscustomobject]@{
            company_name = $company.Trim()
            url = $url.Trim()
            address = [string]$row.address
            phone = [string]$row.phone
            maps_url = [string]$row.maps_url
            source_file = $file.Name
        })
    }
}

$pool | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation -Encoding UTF8
[pscustomobject]@{
    scanned_files = $files.Count
    existing_domains = $existingDomains.Count
    unseen_candidates = $pool.Count
    output = $OutputCsv
} | ConvertTo-Json -Compress
