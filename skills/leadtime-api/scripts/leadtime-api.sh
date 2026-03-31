#!/usr/bin/env bash
set -euo pipefail

DEFAULT_BASE="https://leadtime.app/api/public"

usage() {
  cat <<'EOF'
Usage:
  leadtime-api.sh METHOD /path [options]

Options:
  --keyfile PATH   Path to .leadtime-api-key.json (auto-detected if omitted)
  --profile INDEX  Profile index in the keyfile (default: 0)
  -d JSON          Inline JSON request body
  -f FILE          Read JSON request body from file
  -q QUERY         Append query string
  -o FILE          Write response body to file
  -H HEADER        Extra header (repeatable)
  --raw            Print raw response body
EOF
}

find_keyfile() {
  for candidate in "./.leadtime-api-key.json" "$HOME/.leadtime-api-key.json"; do
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return
    fi
  done
  return 1
}

KEYFILE=""
PROFILE_INDEX=0
QUERY=""
BODY=""
BODY_FILE=""
OUTPUT_FILE=""
RAW=0
LT_EXTRA_HEADERS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keyfile)
      KEYFILE="${2:-}"
      shift 2
      ;;
    --profile)
      PROFILE_INDEX="${2:-0}"
      shift 2
      ;;
    -q)
      QUERY="${2:-}"
      shift 2
      ;;
    -d)
      BODY="${2:-}"
      shift 2
      ;;
    -f)
      BODY_FILE="${2:-}"
      shift 2
      ;;
    -o)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    -H)
      LT_EXTRA_HEADERS+=("${2:-}")
      shift 2
      ;;
    --raw)
      RAW=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

METHOD="${1:-}"
PATH_PART="${2:-}"

if [[ -z "$METHOD" || -z "$PATH_PART" ]]; then
  usage >&2
  exit 1
fi

if [[ -n "$BODY" && -n "$BODY_FILE" ]]; then
  echo "Use either -d or -f, not both." >&2
  exit 1
fi

# --- resolve keyfile ---
if [[ -z "$KEYFILE" ]]; then
  KEYFILE="$(find_keyfile)" || {
    echo "No .leadtime-api-key.json found. Searched: ./ and ~/" >&2
    echo "Set up a key first (see SKILL.md) or pass --keyfile PATH." >&2
    exit 1
  }
fi

if [[ ! -f "$KEYFILE" ]]; then
  echo "Keyfile not found: $KEYFILE" >&2
  exit 1
fi

# --- extract token and base from JSON keyfile ---
read_profile() {
  python3 - "$KEYFILE" "$PROFILE_INDEX" <<'PY'
import json, sys
keyfile = sys.argv[1]
index = int(sys.argv[2])
with open(keyfile, encoding="utf-8") as f:
    data = json.load(f)
profiles = data.get("profiles", [])
if not profiles:
    print("ERROR:No profiles in keyfile", file=sys.stderr)
    sys.exit(1)
if index >= len(profiles):
    print(f"ERROR:Profile index {index} out of range (have {len(profiles)})", file=sys.stderr)
    sys.exit(1)
p = profiles[index]
api_key = p.get("apiKey", "")
api_base = p.get("apiBase", "")
if not api_key:
    print("ERROR:Profile has no apiKey", file=sys.stderr)
    sys.exit(1)
print(f"{api_key}\n{api_base}")
PY
}

PROFILE_DATA="$(read_profile)"
TOKEN="$(echo "$PROFILE_DATA" | head -1)"
BASE="$(echo "$PROFILE_DATA" | tail -1)"
BASE="${BASE:-$DEFAULT_BASE}"

# --- build URL ---
URL="${BASE%/}/${PATH_PART#/}"
if [[ -n "$QUERY" ]]; then
  SEP="?"
  [[ "$URL" == *\?* ]] && SEP="&"
  URL="${URL}${SEP}${QUERY}"
fi

# --- build curl args ---
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

METHOD_UPPER="$(printf '%s' "$METHOD" | tr '[:lower:]' '[:upper:]')"
CURL_ARGS=(
  -fsS
  -X "$METHOD_UPPER"
  -H "Authorization: Bearer $TOKEN"
  -H "Accept: application/json"
)

_n_headers=${#LT_EXTRA_HEADERS[@]}
for ((i = 0; i < _n_headers; i++)); do
  CURL_ARGS+=(-H "${LT_EXTRA_HEADERS[i]}")
done

if [[ -n "$BODY" || -n "$BODY_FILE" ]]; then
  CURL_ARGS+=(-H "Content-Type: application/json")
fi

if [[ -n "$BODY" ]]; then
  CURL_ARGS+=(-d "$BODY")
elif [[ -n "$BODY_FILE" ]]; then
  CURL_ARGS+=(--data-binary "@$BODY_FILE")
fi

curl "${CURL_ARGS[@]}" "$URL" -o "$TMP_FILE"

# --- output ---
if [[ -n "$OUTPUT_FILE" ]]; then
  cp "$TMP_FILE" "$OUTPUT_FILE"
  exit 0
fi

if [[ "$RAW" -eq 1 ]]; then
  cat "$TMP_FILE"
  exit 0
fi

python3 - "$TMP_FILE" <<'PY'
import json, pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text()
if not text.strip():
    sys.exit(0)
try:
    parsed = json.loads(text)
except json.JSONDecodeError:
    print(text, end="")
else:
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
PY
