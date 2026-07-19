# GBP review reply production rollback snapshot

- Created: 2026-07-19 17:48:23 +09:00
- Scope: the 10 production targets approved for iteration-3 only
- Snapshot contains the 9 files that existed before deployment. `examples/quality-boundaries.md` was absent before deployment.

| Production path | Before | SHA-256 before | Snapshot path |
|:---|:---:|:---|:---|
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\SKILL.md` | present | `E86A69E3DA391D81C96977ACBDC4222304F94D6861B0500D8980B07BC4648ECB` | `skill/SKILL.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\approved-replies.md` | present | `2BD294A8BD637277D85AEA5691FD84A7125C8173B7857403ECA1FA02E63A5045` | `skill/examples/approved-replies.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\good-output.md` | present | `2B8BE7A78538D80294FF33360990869E311DD6406E9618E03DD99B41210E9137` | `skill/examples/good-output.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\quality-boundaries.md` | absent | n/a | n/a; remove this file when rolling back |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\changelog.md` | present | `EC85D67C9C6852C20C3C8BA689B568E8DB8089639D838CE5C1F5E9646C14976F` | `skill/references/changelog.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\evidence.md` | present | `EF3188B62DE34E94B5F68B2CDD2602A1C906F288300AB186EF57BEFA5CE20C8A` | `skill/references/evidence.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\feedback-loop.md` | present | `00E6C68C8A35ED9946B4AD689F969BE1D1A84A84CA136D1B67883087C610C713` | `skill/references/feedback-loop.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\reply-rules.md` | present | `6115B3643F1996C00CC9A432B195C5267E3923370E5CE2C889DD020F2F39780B` | `skill/references/reply-rules.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\profile.md` | present | `E3F6C43CE73EDAEBD2A00162A9365879ABC1C184B73190560CF9AF7D3AE1C07D` | `client/profile.md` |
| `C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\log.md` | present | `3796EFCCB304E37AE1A792763EE1BA607869E00D63179710545A98D0CDF814BE` | `client/log.md` |

## Restore procedure

1. Stop GBP review-reply generation.
2. Copy the 9 snapshot files back to their corresponding production paths.
3. Remove only `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\quality-boundaries.md` because it did not exist before deployment.
4. Recompute SHA-256 and confirm exact agreement with the table above.
5. Confirm the two target production directories have no unexpected files or diffs.

## Post-deployment verification

- Deployment result: success
- Production files changed: exactly 10 approved targets (8 shared-skill files and 2 client files)
- Candidate/live SHA-256: 10/10 exact matches
- Staged target changes: none
- `git diff --check`: pass
- Formal gate: allowed
- Confirmed evaluation artifacts: 36 cases, candidate 144/144 assertions, G1/G2/G3 pass
- No formal runner that regenerates the 36 responses directly from the production paths exists in the iteration-3 or `skill-update` scripts. Production equivalence is therefore established by exact SHA-256 identity with the evaluated candidate for all 10 inputs.

| Production path | SHA-256 after | Candidate match |
|:---|:---|:---:|
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\SKILL.md` | `9B0B65F937F327449D482F15BE2BB0223CE9AE33628661A168E51803E5E79EDA` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\approved-replies.md` | `766D4DAF6D1FD8392334B00036A16B745319044960F029363341CEA8D9557B59` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\good-output.md` | `A4E56EEB908850F8B81734166499D5E3B6391AC914C5512AB01557E58788849E` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\examples\quality-boundaries.md` | `64373553793E621D1C9C67E2A937CB74047141DD3E4BBDBF01EBE18AF89182E6` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\changelog.md` | `3D848057C092264CC44A02FDC040B5192AC958FEA8BD39FDF38DCB16A387E62B` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\evidence.md` | `7D4261D2E7490475F0D748F5F5EAFED06728BB5BDEEBC36BC655C192E16D1D8A` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\feedback-loop.md` | `60E72BD39833C03A457BD94E289E8E8D7A6275F2C3EFE22948400851123948DF` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply\references\reply-rules.md` | `45D30EF2284C8170BBE8F8E47795DBE41ACA24607E0C0DD7438682F4B92E8A75` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\profile.md` | `DD646D750A6043A7C81CC75F2D0B247E0578AF912611CB9FD870E785C9BEF7C1` | yes |
| `C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\log.md` | `D3F39D080AEB90E82AEE964F049E812023118C3A402C040EC9B156F7C769AC1D` | yes |
