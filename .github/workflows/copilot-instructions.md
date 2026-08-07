# Python code rules

## Formatting

- Line length: 78 soft (black), 80 hard limit.
- No string quote normalization — keep quotes as written.
- No unused imports/variables, except re-exports in `__init__.py`.

## Structure

- All code lives in classes; one class per file, named after the class (`class Foo` → `Foo.py`).
- Max file length: 100 lines. Split oversized files into named Mixins; if a class has Mixins, put class + Mixins in their own folder.
- Max function length: 40 lines. Split oversized functions into helpers.
- Max cyclomatic complexity: 5. Split functions that exceed this.

## Style

- No comments or docstrings anywhere. Code must be self-explanatory.

## Verification

After writing or editing Python, run on each changed file, in order:

```bash
python3 -m autoflake -r --in-place --remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports <file>
python3 -m autopep8 --aggressive --max-line-length 78 --in-place -r <file>
python3 -m black --quiet --skip-string-normalization --line-length 78 <file>
python3 -m flake8 --ignore="CFQ002,W503" --per-file-ignores="__init__.py:F401" --max-function-length 40 --max-line-length 80 --max-complexity 5 <file>
```

Make sure no file is longer than 100 lines, buy running the following. If any file is too long, split as described above:

```bash
function pyl_long_files {
    local folder="${1:-.}"
    local min="${2:-100}"
    find "$folder" -name '*.py' -type f -print0 |
        xargs -0 wc -l |
        awk -v min="$min" '$2 != "total" && $1 > min {print $1, $2}' |
        sort -rn
}
```

Also, run any unittests, if they exist

Fix all flake8 output before finishing.

```

```
