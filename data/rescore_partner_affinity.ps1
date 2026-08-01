$ErrorActionPreference = "Stop"
$root = "C:\Users\hangy\.gemini\antigravity"
Set-Location $root

$pairs = @(
    @("data\sns_partner_archive_official.csv", "data\sns_partner_archive_affinity_v5.csv"),
    @("data\sns_partner_official_wave2.csv", "data\sns_partner_affinity_wave2_v5.csv"),
    @("data\sns_partner_official_wave3.csv", "data\sns_partner_affinity_wave3_v5.csv"),
    @("data\sns_partner_official_wave4.csv", "data\sns_partner_affinity_wave4_v5.csv"),
    @("data\sns_partner_official_wave5.csv", "data\sns_partner_affinity_wave5_v5.csv"),
    @("data\sns_partner_official_wave6.csv", "data\sns_partner_affinity_wave6_v5.csv")
)

foreach ($pair in $pairs) {
    python data\score_sns_partner_affinity.py $pair[0] $pair[1] --allow-digital
}
