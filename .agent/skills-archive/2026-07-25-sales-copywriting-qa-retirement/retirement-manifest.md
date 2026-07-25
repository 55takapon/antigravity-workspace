# sales-copywriting-qa retirement manifest

## Retirement

- Date: 2026-07-25
- Decision: RETIRE_WITH_LEGACY_SALES_COPYWRITING
- Archive root: `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement`
- Reason: `sales-copywriting-qa` has no executable code or external automation dependency. Its only active hard dependency is the already-deprecated legacy `sales-copywriting` workflow. `sales-copywriting` is archived in the same unit to avoid leaving a broken required QA gate or extending the old design without QA.
- Additional scope: `sales-copywriting-workspace` and the three `sales-copywriting*.zip` artifacts are archived as historical/generated artifacts because they sit directly under `skills/` and retain retired-name references. `sales-copywriting-workspace` has no root `SKILL.md` and was not treated as an active skill.
- Successor status: `proposal-writing` is a future planned name only. It was not created or connected.

## Files

| Source path | Archive path | Size bytes | Last write time | SHA-256 | Reason |
|---|---|---:|---|---|---|
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting-qa\SKILL.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting-qa\SKILL.md` | 7504 | 2026-05-05 07:55:09 | `71B59FBF3100F87C0138D318D14422ACE9EB4B7FA3D2D07D06DF816AE0F9EF1A` | Retired QA skill |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\SKILL.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\SKILL.md` | 7795 | 2026-07-17 21:53:22 | `ACAFF063A011775197138464F2DC1433741EC5945B8842F3FE44A5CFEEA90E9E` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\examples\good-output.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\examples\good-output.md` | 1817 | 2026-07-17 21:55:18 | `626F9ECC8B3A6145ACB47FED077797199889B13A47D4FF177FB4EAF5C046A404` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\knowledge\profile-registry.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\knowledge\profile-registry.md` | 2000 | 2026-07-17 21:53:38 | `62E254A60346CDB99F16B6D33E1256082B6E309EF698CDEB60FC11B3370F6946` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\references\02_sending-context.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\references\02_sending-context.md` | 2880 | 2026-07-17 21:53:53 | `681C087D5956373660A05352D23C54DB6C9F608EC39254FB6270B197901F510B` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\references\changelog.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\references\changelog.md` | 1632 | 2026-07-17 21:54:02 | `413D9B3AAFCDF8C9634659DE8E69072929320DEECB9A104695E1FC52C7AA5FE8` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\references\frameworks.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\references\frameworks.md` | 6848 | 2026-05-05 07:52:13 | `627FCF9F5182AA1B7F6238224D83CD0EE1C724F8B18465DA8DB3FDC7C920D9BC` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\references\ng-patterns.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\references\ng-patterns.md` | 6142 | 2026-05-05 07:53:49 | `0647E9BE088145709752193276F474DA34CC6BF68889F7C3934C33DB253B770B` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\references\pdca-log.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\references\pdca-log.md` | 2605 | 2026-05-05 07:54:12 | `84EC0EA6ABE35016066F5BB6A6A43E08E9BCCC40D26D01E1EB491C71783AE5D9` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting\references\psychology-triggers.md` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting\references\psychology-triggers.md` | 5004 | 2026-05-05 07:53:00 | `C0BEED54E727E030CBD2FEAE1D69AD4D942EBD2E33CC1ECC58DEE220C9FEABC6` | Legacy skill archived with required QA |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting-qa.zip` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting-qa.zip` | 3293 | 2026-07-24 17:23:54 | `0E94CEB17B07C10E4120534FBE10BFC63540348888AD0B21DB6E6A1F80F806CD` | Retired QA zip artifact |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting.zip` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting.zip` | 20726 | 2026-07-24 17:21:36 | `FBFC76BF874F6A13E83C659F5385F0388C8DAFAA0655F255D70011D66D9CFB7E` | Legacy skill zip artifact |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting-workspace.zip` | `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting-workspace.zip` | 34683 | 2026-07-24 17:24:01 | `1C9EB54E6211AD8CEEE6E94D205ED34562C9E7E276FB10604387481ACC434931` | Historical evaluation workspace zip artifact |

## Historical workspace aggregate

- Source path: `C:\Users\hangy\.gemini\antigravity\.agent\skills\sales-copywriting-workspace`
- Archive path: `C:\Users\hangy\.gemini\antigravity\.agent\skills-archive\2026-07-25-sales-copywriting-qa-retirement\sales-copywriting-workspace`
- Root `SKILL.md`: none
- File count: 25
- Total bytes: 49055
- Detailed file hashes: see `workspace-file-hashes-before.csv`

## Expected archive verification

- Retired skill file count: 10
- Retired skill total bytes: 44227
- Historical workspace file count: 25
- Historical workspace total bytes: 49055
- Zip artifact count: 3
- Zip artifact total bytes: 58702
