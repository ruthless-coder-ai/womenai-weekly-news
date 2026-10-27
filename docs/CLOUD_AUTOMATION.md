# Cloud automation

`.github/workflows/weekly-news.yml` runs the entire weekly pipeline on GitHub-hosted
runners at **12:00 every Sunday in `Europe/Berlin`**. GitHub's timezone-aware schedule
keeps the wall-clock time at noon across daylight-saving changes.

The workflow:

1. checks out this generator and the private cards archive;
2. determines the current Monday-Sunday issue and reuses an existing folder on reruns;
3. uses the OpenAI Responses API with web search to research and write the issue;
4. renders and validates four 2160×2880 PNGs;
5. commits the cards and copy to `womenai-weekly-news-cards`;
6. publishes the four images to Xiaohongshu;
7. records a publish marker in the cards repository.

## Required GitHub Actions secrets

Configure these in **womenai-weekly-news → Settings → Secrets and variables →
Actions**:

| Secret | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Responses API web research and structured copy generation |
| `CARDS_REPO_TOKEN` | Fine-grained GitHub PAT with **Contents: read/write** on `ruthless-coder-ai/womenai-weekly-news-cards` |
| `XHS_COOKIES_B64` | Base64-encoded `~/.xhs-mcp/cookies.json`; treated as a login credential |

Optional repository variable:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_MODEL` | `gpt-6-astra` | Model used for weekly research and writing |

Never commit any of these values. Xiaohongshu cookies provide account access and must
be rotated if exposed.

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

Use **Actions → Weekly AI news to Xiaohongshu → Run workflow** with
`skip_publish=true`. Confirm the four-card artifact and the commit in the cards repo.
Then run the same week again with publishing enabled.

The workflow writes `.xhs-publish-lock.json` before the external publish call. If a run
fails after that point, the next automatic retry stops instead of risking a duplicate
post. Inspect Xiaohongshu and the failed run, then use `force_publish=true` only when no
post exists.

Manual runs also support a `week_end` Sunday for backfills and `force_regenerate` for a
deliberate rewrite. Regeneration never increments the issue number when that week's
folder already exists.

