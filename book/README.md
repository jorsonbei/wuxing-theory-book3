# Book Source And Downloads

The generated HTML reading pages are public.

Downloadable manuscript files are intentionally not committed here. Put DOCX / Markdown downloads in the private Supabase Storage bucket described in `docs/supabase-setup.md`, then serve them through the authenticated download Edge Function.

For local rebuilds, keep the source manuscript on disk and run:

```bash
WUXING_SOURCE_MD=/absolute/path/to/物性論3_投稿前總審版.md python3 tools/build_site.py
```
