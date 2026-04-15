#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Batch compress images with CaesiumCLT.

Usage:
  batch-compress.sh --input PATH [options]

Required:
  --input PATH              Input file or directory

Compression mode (choose at most one):
  --quality N               Quality 0-100 (default: 82 when no mode is provided)
  --lossless                Use lossless compression

Output and behavior:
  --output PATH             Output directory
  --format FORMAT           jpeg|png|gif|webp|tiff|original (default: webp)
  --width PX                Resize to target width (default: 700 when width/height are both omitted)
  --height PX               Resize to target height (height stays proportional when omitted)
  --no-upscale              Prevent enlarging smaller images
  --suffix TEXT             Append suffix to output filenames
  --overwrite MODE          all|never|bigger (default: bigger)
  --threads N               Parallel jobs, 0 = auto

Directory handling:
  --recursive               Recurse into subfolders for directory input
  --no-recursive            Disable recursion
  --keep-structure          Preserve directory structure when recursive
  --flat                    Do not preserve directory structure

Other:
  --exif                    Keep EXIF metadata
  --dry-run                 Preview without writing files
  -h, --help                Show this help
EOF
}

fail() {
  echo "Error: $*" >&2
  exit 1
}

file_size_bytes() {
  local file="$1"
  if stat -f%z "$file" >/dev/null 2>&1; then
    stat -f%z "$file"
  else
    stat -c%s "$file"
  fi
}

human_size() {
  local bytes="$1"
  awk -v b="$bytes" 'BEGIN {
    split("B KB MB GB TB PB", u, " ");
    i = 1;
    while (b >= 1024 && i < 6) {
      b = b / 1024;
      i++;
    }
    if (i == 1) {
      printf "%d %s", b, u[i];
    } else {
      printf "%.2f %s", b, u[i];
    }
  }'
}

print_output_sizes() {
  local output_dir="$1"
  local file
  local bytes
  local count=0
  local total=0
  local threshold_bytes=$((100 * 1024))
  local over_count=0
  local final_over_count=0
  local final_total=0
  local before_bytes=0
  local after_bytes=0
  local parent=""
  local -a over_files=()

  echo "Output files over 100 KB:"

  while IFS= read -r -d '' file; do
    bytes="$(file_size_bytes "$file")"
    total=$((total + bytes))
    count=$((count + 1))

    if (( bytes > threshold_bytes )); then
      over_count=$((over_count + 1))
      over_files+=("$file")
      printf '  %s  %s\n' "$(human_size "$bytes")" "$file"
    fi
  done < <(
    find "$output_dir" -type f \( \
      -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.gif" -o -iname "*.tiff" \
    \) -print0
  )

  if [[ "$count" -eq 0 ]]; then
    echo "  (no output images found)"
    return
  fi

  if [[ "$over_count" -eq 0 ]]; then
    echo "  (none)"
  else
    echo "Recompressing files over 100 KB with quality 70..."
    for file in "${over_files[@]}"; do
      before_bytes="$(file_size_bytes "$file")"
      parent="$(dirname "$file")"
      caesiumclt --quality 70 --output "$parent" --format original --overwrite all "$file" >/dev/null
      after_bytes="$(file_size_bytes "$file")"
      printf '  recompressed: %s  %s -> %s\n' "$file" "$(human_size "$before_bytes")" "$(human_size "$after_bytes")"
    done

    echo "Files still over 100 KB after quality 70:"
    while IFS= read -r -d '' file; do
      bytes="$(file_size_bytes "$file")"
      final_total=$((final_total + bytes))
      if (( bytes > threshold_bytes )); then
        final_over_count=$((final_over_count + 1))
        printf '  %s  %s\n' "$(human_size "$bytes")" "$file"
      fi
    done < <(
      find "$output_dir" -type f \( \
        -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.gif" -o -iname "*.tiff" \
      \) -print0
    )
    if [[ "$final_over_count" -eq 0 ]]; then
      echo "  (none)"
    fi
  fi

  echo "Over 100 KB: $over_count files"
  echo "Total: $(human_size "$total") across $count files"
  if [[ "$over_count" -gt 0 ]]; then
    echo "Over 100 KB after quality 70: $final_over_count files"
    echo "Final total: $(human_size "$final_total") across $count files"
  fi
}

ensure_caesiumclt() {
  if command -v caesiumclt >/dev/null 2>&1; then
    return 0
  fi

  echo "caesiumclt not found. Attempting to install it..." >&2

  case "$(uname -s)" in
    Darwin)
      if ! command -v brew >/dev/null 2>&1; then
        fail "Homebrew is required to auto-install caesiumclt on macOS. Install Homebrew first or install CaesiumCLT manually."
      fi
      brew install caesiumclt || fail "Automatic installation failed. Try running 'brew install caesiumclt' manually."
      ;;
    *)
      fail "caesiumclt is not installed. Install it first: https://saerasoft.com/caesiumclt"
      ;;
  esac

  command -v caesiumclt >/dev/null 2>&1 || fail "caesiumclt is still unavailable after installation."
}

INPUT=""
OUTPUT=""
FORMAT="webp"
MAX_SIZE=""
QUALITY=""
LOSSLESS=0
RECURSIVE=""
KEEP_STRUCTURE=""
SUFFIX=""
OVERWRITE="bigger"
THREADS=""
KEEP_EXIF=0
DRY_RUN=0
WIDTH=""
HEIGHT=""
NO_UPSCALE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      INPUT="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --format)
      FORMAT="${2:-}"
      shift 2
      ;;
    --width)
      WIDTH="${2:-}"
      shift 2
      ;;
    --height)
      HEIGHT="${2:-}"
      shift 2
      ;;
    --no-upscale)
      NO_UPSCALE=1
      shift
      ;;
    --max-size)
      MAX_SIZE="${2:-}"
      shift 2
      ;;
    --quality)
      QUALITY="${2:-}"
      shift 2
      ;;
    --lossless)
      LOSSLESS=1
      shift
      ;;
    --recursive)
      RECURSIVE=1
      shift
      ;;
    --no-recursive)
      RECURSIVE=0
      shift
      ;;
    --keep-structure)
      KEEP_STRUCTURE=1
      shift
      ;;
    --flat)
      KEEP_STRUCTURE=0
      shift
      ;;
    --suffix)
      SUFFIX="${2:-}"
      shift 2
      ;;
    --overwrite)
      OVERWRITE="${2:-}"
      shift 2
      ;;
    --threads)
      THREADS="${2:-}"
      shift 2
      ;;
    --exif)
      KEEP_EXIF=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

ensure_caesiumclt

[[ -n "$INPUT" ]] || fail "--input is required"
[[ -e "$INPUT" ]] || fail "Input path does not exist: $INPUT"

case "$FORMAT" in
  jpeg|png|gif|webp|tiff|original) ;;
  *) fail "Invalid --format value: $FORMAT" ;;
esac

case "$OVERWRITE" in
  all|never|bigger) ;;
  *) fail "Invalid --overwrite value: $OVERWRITE" ;;
esac

if [[ -n "$MAX_SIZE" ]]; then
  fail "--max-size is disabled in this skill. Use --quality or --lossless."
fi

compression_modes=0
[[ -n "$QUALITY" ]] && compression_modes=$((compression_modes + 1))
[[ "$LOSSLESS" -eq 1 ]] && compression_modes=$((compression_modes + 1))

if [[ "$compression_modes" -gt 1 ]]; then
  fail "Choose at most one of --quality or --lossless"
fi

if [[ "$compression_modes" -eq 0 ]]; then
  QUALITY="82"
fi

# Default resize behavior: width 700, proportional height.
if [[ -z "$WIDTH" && -z "$HEIGHT" ]]; then
  WIDTH="700"
fi

if [[ -n "$QUALITY" ]]; then
  [[ "$QUALITY" =~ ^[0-9]+$ ]] || fail "--quality must be an integer from 0 to 100"
  (( QUALITY >= 0 && QUALITY <= 100 )) || fail "--quality must be an integer from 0 to 100"
fi

if [[ -n "$THREADS" ]]; then
  [[ "$THREADS" =~ ^[0-9]+$ ]] || fail "--threads must be a non-negative integer"
fi

if [[ -n "$WIDTH" ]]; then
  [[ "$WIDTH" =~ ^[0-9]+$ ]] || fail "--width must be a positive integer"
  (( WIDTH > 0 )) || fail "--width must be a positive integer"
fi

if [[ -n "$HEIGHT" ]]; then
  [[ "$HEIGHT" =~ ^[0-9]+$ ]] || fail "--height must be a positive integer"
  (( HEIGHT > 0 )) || fail "--height must be a positive integer"
fi

if [[ -d "$INPUT" ]]; then
  if [[ -z "$RECURSIVE" ]]; then
    RECURSIVE=1
  fi
  if [[ -z "$KEEP_STRUCTURE" ]]; then
    KEEP_STRUCTURE=1
  fi
  if [[ -z "$OUTPUT" ]]; then
    OUTPUT="${INPUT%/}-compressed"
  fi
else
  RECURSIVE=0
  KEEP_STRUCTURE=0
  if [[ -z "$OUTPUT" ]]; then
    OUTPUT="$(dirname "$INPUT")/compressed-output"
  fi
fi

mkdir -p "$OUTPUT"

cmd=(caesiumclt)

if [[ -n "$QUALITY" ]]; then
  cmd+=(--quality "$QUALITY")
else
  cmd+=(--lossless)
fi

cmd+=(--output "$OUTPUT")
cmd+=(--format "$FORMAT")
cmd+=(--overwrite "$OVERWRITE")

if [[ "$RECURSIVE" -eq 1 ]]; then
  cmd+=(--recursive)
fi

if [[ "$RECURSIVE" -eq 1 && "$KEEP_STRUCTURE" -eq 1 ]]; then
  cmd+=(--keep-structure)
fi

if [[ -n "$SUFFIX" ]]; then
  cmd+=(--suffix "$SUFFIX")
fi

if [[ -n "$THREADS" ]]; then
  cmd+=(--threads "$THREADS")
fi

if [[ "$KEEP_EXIF" -eq 1 ]]; then
  cmd+=(--exif)
fi

if [[ -n "$WIDTH" ]]; then
  cmd+=(--width "$WIDTH")
fi

if [[ -n "$HEIGHT" ]]; then
  cmd+=(--height "$HEIGHT")
fi

if [[ "$NO_UPSCALE" -eq 1 ]]; then
  cmd+=(--no-upscale)
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  cmd+=(--dry-run)
fi

cmd+=("$INPUT")

printf 'Running:'
printf ' %q' "${cmd[@]}"
printf '\n'

"${cmd[@]}"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Size report skipped in dry-run mode."
  exit 0
fi

print_output_sizes "$OUTPUT"
