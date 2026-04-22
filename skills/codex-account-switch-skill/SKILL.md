---
name: codex-account-switch-skill
description: Switch the local Codex account profile between hefeng and agora by copying the saved files from ~/.codex/hefeng or ~/.codex/agora into ~/.codex, then restart the Codex app. Chinese trigger phrases include "切换codex账号", "切换 codex 账号", "codex账号切换", and "切到hefeng/agora".
---

# Codex Account Switch

## Trigger Phrases (中文)

- 切换codex账号
- 切换 codex 账号
- codex账号切换
- 切到hefeng
- 切到agora

Use this skill when the user wants to switch the local Codex login/profile between the saved `hefeng` and `agora` snapshots.

## Workflow

1. Confirm the target account if the user did not state it clearly.
2. Run the bundled script:

```bash
bash scripts/switch_codex_account.sh
```

Or run it directly with an explicit target:

```bash
bash scripts/switch_codex_account.sh hefeng
bash scripts/switch_codex_account.sh agora
```

3. After switching, make sure Codex is fully quit and restarted once.

## What The Script Does

- copies files from `~/.codex/hefeng/` or `~/.codex/agora/` into `~/.codex/`
- overwrites files with the same name
- fully quits the macOS `Codex` app, then attempts to reopen it once after the copy finishes
- prints a manual restart reminder if auto-restart fails

## Notes

- The saved account snapshots must already exist at `~/.codex/hefeng` and `~/.codex/agora`.
- This workflow is macOS-specific because it restarts the `Codex.app` application.
- The script uses `rsync` for reliable overwrite behavior.
