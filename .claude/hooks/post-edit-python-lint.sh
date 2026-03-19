#!/usr/bin/env bash
# PostToolUse hook: Python 파일 수정 후 기본 문법 체크
input=$(cat)
file_path=$(echo "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')

if [[ "$file_path" == *.py ]]; then
  python -c "import py_compile; py_compile.compile('$file_path', doraise=True)" 2>&1
  if [ $? -ne 0 ]; then
    echo "[Hook] Python syntax error in $file_path" >&2
  fi
fi

echo "$input"
