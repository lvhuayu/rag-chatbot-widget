# Copilot issue-to-merge automation

The repository uses a guarded automation flow for Copilot-generated changes.

## Flow

1. A maintainer reviews an issue and applies `agent-ready`.
2. `copilot-issue-agent.yml` verifies that the labeler has write permission and starts a `lingwen-maintainer` Copilot Agent Task.
3. Copilot implements the issue and opens a pull request.
4. `agent-quality-gate.yml` validates generated CSS and JavaScript/Python syntax.
5. After the quality gate succeeds, `copilot-pr-review.yml` starts the independent `lingwen-reviewer` agent against the PR branch.
6. The reviewer submits an approval or change request and applies either `ai-review-passed` or `ai-review-blocked`.
7. `agent-auto-merge.yml` enables squash auto-merge only for Copilot-authored pull requests carrying `ai-review-passed`.
8. GitHub merges only after the required `Agent quality gate` check succeeds and an approval is present.

## Required repository configuration

- Enable Copilot cloud agent for the repository.
- Add an Actions secret named `COPILOT_AGENT_PAT`.
  - It must be a user-to-server token because GitHub's agent task API does not accept `GITHUB_TOKEN`.
  - Prefer a fine-grained token limited to this repository with Agent Tasks read/write plus the Actions, Contents, Issues, and Pull Requests permissions needed by the agents.
- Enable repository auto-merge.
- Protect `main`, require one approving review, and require the `Agent quality gate` status check.
- Keep force pushes and branch deletion disabled.

## Labels

- `agent-ready`: maintainer approval to let the implementation agent start.
- `agent-infrastructure-approved`: explicit approval for an issue that must change workflows or agent configuration.
- `ai-review-passed`: independent agent found no blocker.
- `ai-review-blocked`: independent agent found a blocker or could not validate the change.

## Security notes

- The repository is public, so native Copilot Automations are unavailable.
- New issues do not trigger code changes automatically. A write-authorized maintainer must add `agent-ready`.
- Workflows containing `COPILOT_AGENT_PAT` do not check out or execute pull-request code.
- The quality gate receives no repository secrets.
- Do not enable automatic merging without the required status check on `main`.
