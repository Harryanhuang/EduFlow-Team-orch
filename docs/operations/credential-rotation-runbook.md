# Credential Rotation Runbook

## Scope and authority

This runbook is a production operation, not an automatic deployment step.
The project owner is the security owner and must explicitly approve every
provider, Feishu, Lark, or agent credential rotation before it begins. The
runtime operator may perform approved steps but may not self-approve them.

This repository change only prepares the controls and documentation. It does
not rotate a credential, revoke an old credential, inspect secret values, or
rewrite Git history.

## Detach Deployment Config Before Updating

This release stops tracking the deployment-specific `eduflow.toml`. On an
existing checkout, do the following **before** checking out the release that
removes it; otherwise Git may remove the old tracked file together with the
code update.

1. Stop the affected services or enter human takeover if they are active.
2. Copy the current config to a private location outside the checkout. Keep
   its owner and mode `0600`; do not print or inspect its values while doing
   this.

   ```bash
   install -d -m 700 "$HOME/.eduflow-deploy"
   install -m 600 eduflow.toml "$HOME/.eduflow-deploy/eduflow.toml"
   ```

3. Set `EDUFLOW_CONFIG_FILE=$HOME/.eduflow-deploy/eduflow.toml` in the
   service or wrapper environment before updating the checkout. Alternatively,
   after the code update, restore the private copy to the checkout as the new
   ignored `eduflow.toml` before starting any service.
4. Confirm the running process uses the intended config path and that the
   private local file remains ignored. A clean new deployment starts by
   copying `eduflow.example.toml` and filling only non-secret identifiers;
   credentials remain environment references in the private source.

## Preconditions

1. Record the approval, affected credential *identifiers* (not values), owner,
   provider, planned window, and rollback/recovery contact in the incident or
   change record.
2. Enter human takeover before changing a credential used by an active runtime.
   Confirm that new automatic work is stopped.
3. Confirm the active checkout, `EDUFLOW_CONFIG_FILE`, and state directory.
   Do not infer production from a directory that merely exists on disk.
4. Confirm every local secret source is ignored by Git and private:

   ```bash
   chmod 600 .env eduflow.toml
   git check-ignore -v .env eduflow.toml eduflow.local.toml secrets/provider.env
   ```

5. Keep `eduflow.toml` free of literal secret values. Use only `${NAME}`
   references; the values belong in the private secret source or approved
   external secret manager.

## Rotation procedure

1. Create a replacement credential at the provider. Record only its provider
   key ID, creation time, and intended consumer. Never paste the value into a
   terminal command, chat, task, commit, issue, card, test, or evidence file.
2. Update the approved private secret source. Preserve mode `0600` and the
   same owner. Do not copy credentials into `eduflow.toml` or state snapshots.
3. Restart only the affected runtime through the approved lifecycle command.
   Confirm the new process selected the intended runtime and credential source
   without printing its value.
4. Perform the approved live verification. Use redacted output only, for
   example `eduflow runtime verify <agent> --json` and the scoped provider or
   Feishu smoke specified by the approval.
5. Revoke the old provider credential only after the new credential has passed
   the approved live verification. Record old-value invalidation as a provider
   event/identifier, never by storing or printing the old value.
6. Clear human takeover only after the owner confirms the new path is healthy.

## Failure and recovery

- Keep human takeover active if a new credential fails, a runtime cannot prove
  readiness, or the credential source cannot be read with private permissions.
- Do not restore a revoked old credential as rollback. Create another approved
  replacement and repeat the verification sequence.
- Treat a suspected disclosure as an incident: stop automated work, rotate the
  exposed credential under a fresh approval, and preserve only redacted
  diagnostics.

## Evidence hygiene

Evidence may contain configuration paths, variable names, file modes, provider
credential IDs, timestamps, exit codes, and redacted verification results. It
must not contain token, API key, password, secret, authorization header,
credential value, full shell environment, or raw curl command containing a
credential.

Run a scoped repository scan before handoff and inspect every finding rather
than treating a pattern count as proof:

```bash
git grep -n -I -E '(BEGIN [A-Z ]+ PRIVATE KEY|Authorization: Bearer|sk-[A-Za-z0-9_-]{20,})' -- . \
  ':!docs/operations/credential-rotation-runbook.md'
```

Git-history remediation is a separate owner-approved operation. Do not rewrite
history as part of a credential rotation or ordinary code rollback.
