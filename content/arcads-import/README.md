# Arcads import

`scripts.csv` (in the parent folder) is structured for human review. Arcads' bulk-script importer typically wants a narrower schema — usually just `actor` and `script` per row, with optional `language` / `aspect_ratio`.

## How to use

1. Open `../scripts.csv`.
2. For each row, in your Arcads account, pick a specific actor matching the `archetype` column (see `../actor-pairings.md`).
3. Either:
   - **Manual:** paste the `full_script` column into Arcads' single-script flow and select the actor and aspect ratio.
   - **Bulk:** if your plan has CSV bulk upload, copy `full_script` and the actor name into Arcads' template (download it from their UI — schema changes occasionally), then upload.
4. Generate, download MP4s, drop them into `../../assets/videos/phase1/` (create as needed).

## Notes

- **Aspect ratio:** all phase 1 scripts target 9:16 for IG Reels / TikTok / FB Reels. If you also want 1:1 or 16:9, regenerate in those formats *only after* a winner emerges in 9:16. Don't burn tokens generating every aspect upfront.
- **Music:** leave music off in Arcads. Add it in your editor (CapCut / Premiere) so the same generated MP4 can ship with multiple music beds for further A/B testing without burning Arcads tokens.
- **Captions:** Arcads' built-in captions are fine for phase 1. For phase 3 scaling, swap to Captions.ai or Submagic for branded captions in the navy/gold palette.
