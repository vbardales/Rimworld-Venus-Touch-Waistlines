#!/usr/bin/env bash
set -euo pipefail

# Optional: when .github/publish.config.json names a build project (build.project), rebuild it on the runner, report
# whether the rebuilt Mod/ differs from the tracked one, then put the tracked files back. What ships is what is
# committed and was tested: on 2026-09-25 the runner's DLL of a mod differed from the committed one (same source, same
# reference assemblies), so the difference is a report, not a reason to ship the rebuilt file. A project that does not
# compile stops the run. Files the build creates and Git does not track are kept.
#
#   build-check.sh            (run at the root of the commit being published)
#   build-check.sh --ci       (the `build` workflow of a push or a pull request: compile from scratch, then require every
#                              path of requirePaths. The tracked assemblies named there are deleted first: they are committed,
#                              so the check would otherwise pass on the repository's file whatever the build did.)
config=".github/publish.config.json"
project="$(node -e "const c = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8')); process.stdout.write(c.build?.project ?? '')" "$config")"
mode="${1:-}"
[[ -z "$mode" || "$mode" == "--ci" ]] || { echo "usage: build-check.sh [--ci]" >&2; exit 2; }
if [[ -z "$project" ]]; then
  [[ "$mode" != "--ci" ]] || { echo "$config names no build project (build.project): the build workflow has nothing to build" >&2; exit 1; }
  echo "No build project in $config: the tracked Mod/ ships as it is."
  exit 0
fi
[[ -f "$project" ]] || { echo "the build project $project does not exist in this commit" >&2; exit 1; }

if [[ "$mode" == "--ci" ]]; then
  mapfile -t required < <(node -e "for (const p of JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8')).requirePaths ?? []) console.log(p)" "$config")
  for path in "${required[@]}"; do [[ "$path" != *.dll ]] || rm -f "Mod/$path"; done
  dotnet build "$project" -c Release --nologo
  for path in "${required[@]}"; do
    [[ -e "Mod/$path" ]] || { echo "::error::Mod/$path is required (requirePaths) and the build did not produce it" >&2; exit 1; }
  done
  echo "Built $project from scratch; every required path exists."
  exit 0
fi

dotnet build "$project" -c Release --nologo
changed="$(git diff --name-only -- Mod)"
summary="${GITHUB_STEP_SUMMARY:-/dev/null}"
if [[ -z "$changed" ]]; then
  echo "The build reproduces the tracked Mod/ byte for byte." | tee -a "$summary"
else
  echo "::warning::The runner's build differs from the tracked Mod/: the committed files ship, not the rebuilt ones."
  {
    echo "The runner's build differs from the tracked files below. The committed (tested) ones ship, the rebuilt ones are discarded:"
    while IFS= read -r file; do echo "- $file: committed $(git show "HEAD:$file" | sha256sum | cut -d' ' -f1), rebuilt $(sha256sum "$file" | cut -d' ' -f1)"; done <<<"$changed"
  } | tee -a "$summary"
  git checkout -- Mod
fi
