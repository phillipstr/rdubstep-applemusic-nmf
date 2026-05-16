# r/dubstep NMF Apple Music

Automatically syncs the r/dubstep New Music Friday playlist from [Spotify](https://open.spotify.com/playlist/18ePsc36VbfsskyTBHpGZN?si=JHZULF_HSEW80Hdjtq6R_A)
to [Apple Music](https://music.apple.com/us/playlist/r-dubstep-nmf/pl.u-NpXmza4Cm6xAyp6).

Previously this was entirely manual, so it's a pretty welcome change.

If you're here because the playlist has not updated in Apple Music, see the `Schedule` section.

## How It Works

1. Reads all tracks from a Spotify playlist
2. Compares a hash of the playlist contents against the previous run — skips the sync entirely if nothing has changed
3. Searches for each track on Apple Music
4. Clears the target Apple Music playlist
5. Adds all matched tracks to the Apple Music playlist
6. Outputs any unmatched tracks as a downloadable CSV artifact in the Actions run


## Schedule

The sync runs automatically every **Friday at 10am EST**. It can also be triggered manually from the **Actions** tab via `workflow_dispatch`.

In the event that the Spotify playlist is updated after 10am EST, simply trigger a manual run.

> Note: GitHub Actions schedules run in UTC. 10am EST = 15:00 UTC. During daylight saving time (EDT, UTC-4), the job will fire at 11am local time. Update the cron to `0 14 * * 5` during EDT months if needed.

## Unmatched Tracks

Any tracks not found on Apple Music are written to a timestamped CSV (`unmatched_tracks_YYYYMMDD_HHMMSS.csv`) and uploaded as a GitHub Actions artifact. Artifacts are available for 90 days under the relevant Actions run.

## Linting

The script is linted with [Ruff](https://docs.astral.sh/ruff/) (code style + formatting) and [Mypy](https://mypy-lang.org/) (type checking) before every sync run. A lint failure will prevent the sync from executing.
