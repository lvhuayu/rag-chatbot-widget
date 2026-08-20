# Local pull-request auto-merge

The repository automatically merges pull requests created by the repository owner from branches in this repository.

## Flow

1. The repository owner creates a local branch, pushes it to this repository, and opens a non-draft pull request.
2. `local-pr-auto-merge.yml` enables squash auto-merge.
3. `agent-quality-gate.yml` validates generated CSS and JavaScript/Python syntax.
4. GitHub merges only after the branch is current with `main` and the required `Agent quality gate` check succeeds.

## Required repository configuration

- Enable repository auto-merge.
- Protect `main` and require the `Agent quality gate` status check.
- Keep force pushes and branch deletion disabled.

## Security notes

- Only pull requests authored by the repository owner are eligible.
- The pull request branch must belong to this repository; fork pull requests are excluded.
- Draft pull requests are excluded until marked ready for review.
- The auto-merge workflow does not check out or execute pull-request code.
- The quality gate receives no repository secrets.
- The repository owner remains responsible for reviewing local changes before opening a pull request.
