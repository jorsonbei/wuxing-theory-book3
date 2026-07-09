#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f ".env.deploy.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env.deploy.local"
  set +a
fi

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required env var: $name" >&2
    exit 1
  fi
}

require_var SUPABASE_PROJECT_REF
require_var SUPABASE_DB_PASSWORD
require_var SUPABASE_URL
require_var SUPABASE_ANON_KEY
require_var SUPABASE_SERVICE_ROLE_KEY

DOCX_PATH="${DOCX_PATH:-$ROOT/book/wuxing-theory-book3.docx}"
MD_PATH="${MD_PATH:-$ROOT/book/wuxing-theory-book3.md}"

if [[ ! -f "$DOCX_PATH" ]]; then
  echo "DOCX not found: $DOCX_PATH" >&2
  exit 1
fi

if [[ ! -f "$MD_PATH" ]]; then
  echo "Markdown not found: $MD_PATH" >&2
  exit 1
fi

echo "Linking Supabase project..."
supabase link --project-ref "$SUPABASE_PROJECT_REF" --password "$SUPABASE_DB_PASSWORD"

echo "Pushing database migrations..."
supabase db push --linked --password "$SUPABASE_DB_PASSWORD"

echo "Setting Edge Function secrets..."
supabase secrets set \
  --project-ref "$SUPABASE_PROJECT_REF" \
  "SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY" \
  "PRIVATE_DOWNLOAD_BUCKET=private-downloads"

echo "Deploying download Edge Function..."
supabase functions deploy download --project-ref "$SUPABASE_PROJECT_REF" --use-api

upload_private_file() {
  local file="$1"
  local object_path="$2"
  local content_type="$3"
  local code

  code=$(/usr/bin/curl -sS -o /tmp/wuxing_supabase_upload_response.json -w "%{http_code}" \
    -X POST "$SUPABASE_URL/storage/v1/object/private-downloads/$object_path" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
    -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
    -H "x-upsert: true" \
    -H "Content-Type: $content_type" \
    --data-binary "@$file")

  if [[ "$code" != "200" && "$code" != "201" ]]; then
    echo "Upload failed for $object_path, HTTP $code" >&2
    sed -n '1,120p' /tmp/wuxing_supabase_upload_response.json >&2
    exit 1
  fi

  echo "Uploaded $object_path"
}

echo "Uploading private manuscript files..."
upload_private_file "$DOCX_PATH" "wuxing-theory-book3/wuxing-theory-book3.docx" "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
upload_private_file "$MD_PATH" "wuxing-theory-book3/wuxing-theory-book3.md" "text/markdown"

echo "Verifying private storage objects..."
supabase storage ls "ss:///private-downloads/wuxing-theory-book3" --experimental --linked

echo "Enabling frontend platform config..."
python3 - <<'PY'
import json
import os
from pathlib import Path

config = {
    "enabled": True,
    "supabaseUrl": os.environ["SUPABASE_URL"],
    "supabaseAnonKey": os.environ["SUPABASE_ANON_KEY"],
    "downloadFunctionUrl": os.environ["SUPABASE_URL"].rstrip("/") + "/functions/v1/download",
    "bookId": "wuxing-theory-book3",
}
Path("assets/platform-config.js").write_text(
    "window.WUXING_PLATFORM_CONFIG = " + json.dumps(config, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
PY

echo "Rebuilding static site..."
WUXING_SOURCE_MD="$MD_PATH" python3 tools/build_site.py
node --check assets/site.js

echo "Checking generated local links..."
python3 - <<'PY'
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, urldefrag

root = Path(".")
files = list(root.glob("*.html")) + list(root.glob("chapters/*.html")) + list(root.glob("resources/*.html"))
missing = []

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ("href", "src"):
            if key in values:
                self.links.append(values[key])

for file in files:
    parser = Parser()
    parser.feed(file.read_text(encoding="utf-8"))
    for link in parser.links:
        parsed = urlparse(link)
        if parsed.scheme in ("http", "https", "mailto", "javascript"):
            continue
        path, _ = urldefrag(parsed.path)
        if not path or path.startswith("#"):
            continue
        target = (file.parent / path).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            continue
        if not target.exists():
            missing.append((str(file), link, str(target)))

print(f"html_files {len(files)}")
print(f"missing_links {len(missing)}")
if missing:
    for row in missing[:50]:
        print(row)
    raise SystemExit(1)
PY

echo "Committing and pushing website changes..."
git add .gitignore .env.deploy.example assets/platform-config.js index.html chapters resources assets tools supabase docs README.md
if git diff --cached --quiet; then
  echo "No git changes to commit."
else
  git commit -m "Enable Supabase backend"
  git push origin main
fi

echo "Done."
echo "Live site: https://jorsonbei.github.io/wuxing-theory-book3/index.html"
