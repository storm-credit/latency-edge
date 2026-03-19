#!/usr/bin/env bash
# Stop hook: 수정된 파일에서 디버그 코드 체크 (print, console.log)
input=$(cat)

# Check staged/modified Python files for print()
changed_py=$(git diff --name-only --diff-filter=M 2>/dev/null | grep '\.py$' || true)
if [ -n "$changed_py" ]; then
  for f in $changed_py; do
    if [ -f "$f" ]; then
      hits=$(grep -n 'print(' "$f" 2>/dev/null | grep -v '# debug ok' || true)
      if [ -n "$hits" ]; then
        echo "[Hook] print() found in $f — remove before commit:" >&2
        echo "$hits" >&2
      fi
    fi
  done
fi

# Check modified TS/TSX files for console.log
changed_ts=$(git diff --name-only --diff-filter=M 2>/dev/null | grep '\.\(ts\|tsx\)$' || true)
if [ -n "$changed_ts" ]; then
  for f in $changed_ts; do
    if [ -f "$f" ]; then
      hits=$(grep -n 'console\.log' "$f" 2>/dev/null | grep -v '// debug ok' || true)
      if [ -n "$hits" ]; then
        echo "[Hook] console.log found in $f — remove before commit:" >&2
        echo "$hits" >&2
      fi
    fi
  done
fi

echo "$input"
