# generate-data.ps1
# SKILL.md をスキャンして skills-data.js を再生成するスクリプト

$skillsDir      = "C:\Users\hangy\.gemini\antigravity\.agent\skills"
$outputFile     = "$PSScriptRoot\skills-data.js"
$categoriesFile = "$PSScriptRoot\categories.js"
$logFile        = "$PSScriptRoot\generate-data.log"
$timestamp      = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$categoryMap = @{
  "skill-management"               = "system"
  "chat-ng-learner"                = "system"
  "anticrow"                       = "system"
  "git-backup"                     = "system"
  "company-search"                 = "system"
  "company-search-quality-check"   = "system"
  "form-automation"                = "system"
  "contact-auto"                   = "system"
  "ops-pdca"                       = "system"
  "idea-inbox"                     = "system"
  "daily-report"                   = "report"
  "daily-report-quality-check"     = "report"
  "sns"                            = "content"
  "content-strategy"               = "content"
  "blog-title-research"            = "content"
  "blog-writing"                   = "content"
  "blog-writing-qa"                = "content"
  "website-production"             = "web"
  "coconala-listing"               = "web"
  "great-presenter"                = "web"
  "coaching"                       = "web"
  "small-company-research"         = "research"
  "gbp-partner-research"           = "research"
  "gbp-meo-core"                   = "gbp-core"
  "gbp-diagnostic"                 = "gbp-core"
  "gbp-meo-post-core"              = "gbp-core"
  "gbp-report-quality-check"       = "gbp-core"
  "gbp-monthly-report"             = "gbp-core"
  "gbp-review-analysis"            = "gbp-core"
  "gbp-review-qa"                  = "gbp-core"
  "gbp-meo-post-dental-occlusion"  = "gbp-post"
  "gbp-meo-post-dental-preventive" = "gbp-post"
  "gbp-meo-post-jetproduce"        = "gbp-post"
  "gbp-meo-beauty"                 = "gbp-industry"
  "gbp-meo-bodywork"               = "gbp-industry"
  "gbp-meo-education"              = "gbp-industry"
  "gbp-meo-legal"                  = "gbp-industry"
  "gbp-meo-medical"                = "gbp-industry"
  "gbp-meo-real-estate"            = "gbp-industry"
  "gbp-meo-restaurant"             = "gbp-industry"
  "gbp-meo-retail"                 = "gbp-industry"
  "gbp-meo-service"                = "gbp-industry"
  "gbp-meo-taxi"                   = "gbp-industry"
  "gbp-meo-welfare"                = "gbp-industry"
}

function Get-AutoCategory($f) {
  if ($f -match "^gbp-meo-post-") { return "gbp-post" }
  if ($f -match "^gbp-meo-")      { return "gbp-industry" }
  if ($f -match "^gbp-")          { return "gbp-core" }
  if ($f -match "report|quality-check") { return "report" }
  if ($f -match "blog|content|sns")     { return "content" }
  if ($f -match "research|search")      { return "research" }
  if ($f -match "web|site|page")        { return "web" }
  return "system"
}

$warns   = @()
$entries = @()

Get-ChildItem $skillsDir -Recurse -Filter "SKILL.md" |
  Where-Object { $_.FullName -notmatch "gbp-diagnostic\\.agent" } |
  Sort-Object { $_.Directory.Name } |
  ForEach-Object {
    $lines     = Get-Content $_.FullName -Encoding UTF8
    $folder    = $_.Directory.Name
    $lastWrite = $_.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss")

    $nameLine    = ($lines | Select-String -Pattern "^name:\s*"        | Select-Object -First 1).Line
    $descLine    = ($lines | Select-String -Pattern "^description:\s*" | Select-Object -First 1).Line
    $commandLine = ($lines | Select-String -Pattern "^command:\s*"     | Select-Object -First 1).Line

    $name = if ($nameLine)    { ($nameLine    -replace "^name:\s*","").Trim() }        else { $folder }
    $desc = if ($descLine)    { ($descLine    -replace "^description:\s*","").Trim() } else { "" }
    $cmd  = if ($commandLine) { ($commandLine -replace "^command:\s*","").Trim() }     else { "" }

    $name = $name -replace '"', '\"'
    $desc = $desc -replace '"', '\"'

    if ($categoryMap.ContainsKey($folder)) {
      $cat = $categoryMap[$folder]
    } else {
      $cat = Get-AutoCategory $folder
      $warns += "  [NEW] $folder -> $cat (auto-assigned)"
    }

    $cmdJs = if ($cmd -ne "") { """$cmd""" } else { "null" }

    $entry  = "  {" + [System.Environment]::NewLine
    $entry += "    id: " + """$folder""" + "," + [System.Environment]::NewLine
    $entry += "    name: " + """$name""" + "," + [System.Environment]::NewLine
    $entry += "    folder: " + """$folder""" + "," + [System.Environment]::NewLine
    $entry += "    category: " + """$cat""" + "," + [System.Environment]::NewLine
    $entry += "    description: " + """$desc""" + "," + [System.Environment]::NewLine
    $entry += "    command: $cmdJs," + [System.Environment]::NewLine
    $entry += "    lastModified: " + """$lastWrite""" + "," + [System.Environment]::NewLine
    $entry += "    tags: []" + [System.Environment]::NewLine
    $entry += "  }"
    $entries += $entry
  }

$nl  = [System.Environment]::NewLine
$out = "// Auto-generated by generate-data.ps1" + $nl
$out += "// $timestamp" + $nl + $nl
$out += "const SKILLS_DATA = [" + $nl
$out += ($entries -join ("," + $nl))
$out += $nl + "];" + $nl

if (Test-Path $categoriesFile) {
    $out += $nl + (Get-Content $categoriesFile -Encoding UTF8 -Raw)
}

[System.IO.File]::WriteAllText($outputFile, $out, [System.Text.Encoding]::UTF8)

$logMsg = "[$timestamp] OK: $($entries.Count) skills -> skills-data.js"
if ($warns.Count -gt 0) {
    $logMsg += " | WARN $($warns.Count) auto-categorized: " + ($warns -join "; ")
}
Add-Content $logFile $logMsg -Encoding UTF8

Write-Host "OK: $($entries.Count) skills regenerated." -ForegroundColor Green
if ($warns.Count -gt 0) {
    Write-Host "WARN: Unregistered skills (auto-categorized):" -ForegroundColor Yellow
    $warns | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
}
