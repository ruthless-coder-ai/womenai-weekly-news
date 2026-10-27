# Cloud automation

ChatGPT Routine runs at **12:00 every Sunday in `Europe/Berlin`** and creates a
structured `[weekly-news]` issue in this repository. That issue starts
`.github/workflows/weekly-news.yml` on a GitHub-hosted runner. The Routine provides
the researched copy; GitHub handles deterministic rendering and publishing.

The workflow:

1. checks out this generator and the private cards archive;
2. validates the Routine payload and determines the current Monday-Sunday issue;
3. reuses an existing folder on reruns so the issue number stays idempotent;
4. renders and validates four 2160×2880 PNGs;
5. commits the cards and copy to `womenai-weekly-news-cards`;
6. publishes the four images to Xiaohongshu;
7. records a publish marker in the cards repository.

## GitHub Actions secrets

Configure these in **womenai-weekly-news → Settings → Secrets and variables →
Actions**:

| Secret | Purpose |
| --- | --- |
| `CARDS_REPO_TOKEN` | Fine-grained GitHub PAT with **Contents: read/write** on `ruthless-coder-ai/womenai-weekly-news-cards` |
| `XHS_COOKIES_B64` | Required only when `publish` is `true`. Base64-encoded `~/.xhs-mcp/cookies.json`; treated as a login credential |

Optional repository variable:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_MODEL` | `gpt-6-astra` | Used only for optional manual API-backed runs |

Never commit any of these values. Xiaohongshu cookies provide account access and must
be rotated if exposed.

The exact scheduled-task prompt is in
[`CHATGPT_ROUTINE_PROMPT.md`](CHATGPT_ROUTINE_PROMPT.md). The ChatGPT GitHub
connection must have access to both private repositories. The first dry run needs
`CARDS_REPO_TOKEN`; it does not need `XHS_COOKIES_B64`.

## Create the Xiaohongshu cookie secret once

The publishing bridge is the community `xhs-mcp` package pinned to version `0.8.13`.
It uses browser automation because Xiaohongshu's generally available Open Platform
does not currently provide broad `write_notes` access.

On a trusted computer with Node.js installed:

```bash
npx --yes xhs-mcp@0.8.13 browser
npx --yes xhs-mcp@0.8.13 login --timeout 120
npx --yes xhs-mcp@0.8.13 status
base64 < "$HOME/.xhs-mcp/cookies.json" | tr -d '\n'
```

Paste the final command's output into the `XHS_COOKIES_B64` GitHub secret. Test with a
non-production account first when possible. Browser automation may need maintenance
when Xiaohongshu changes its web UI, and a login session can expire.

## Safe first run

For the first Routine run, set `publish` to `false` in its issue payload. Confirm the
four-card artifact and the commit in the cards repo. After that succeeds, update the
Routine prompt to set `publish` to `true`.

The workflow writes `.xhs-publish-lock.json` before the external publish call. If a run
fails after that point, the next automatic retry stops instead of risking a duplicate
post. Inspect Xiaohongshu and the failed run, then use `force_publish=true` only when no
post exists.

Manual runs also support a `week_end` Sunday for backfills and `force_regenerate` for a
deliberate rewrite. Regeneration never increments the issue number when that week's
folder already exists.

