# Repository maintenance

This directory is an independent Git repository candidate for:

`https://github.com/qq783840671-png/recursive-center-field-theory`

The maintenance interface separates preparation from remote publication:

```powershell
# Read-only local/remote report
./scripts/repository-maintenance/status.ps1

# Run repository validation and display the pending update
./scripts/repository-maintenance/prepare-update.ps1

# Remote publication is rejected without the explicit switch.
# Run only after the user explicitly authorizes upload.
./scripts/repository-maintenance/publish.ps1 -ExplicitUpload -Message "release message"
```

`publish.ps1` never creates a missing GitHub repository and never force-pushes. If the target repository does not exist, creation requires a separate explicit “create and upload” instruction. A version is written to the publication ledger only after the remote branch hash equals the local commit.

