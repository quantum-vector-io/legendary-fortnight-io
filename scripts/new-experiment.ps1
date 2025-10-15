param(
    [Parameter(Mandatory = $true)]
    [string]$Topic,
    [string]$Description,
    [DateTime]$Date = (Get-Date)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Normalize the topic into a filesystem-safe slug.
$slug = $Topic.ToLowerInvariant()
$slug = [System.Text.RegularExpressions.Regex]::Replace($slug, "[^a-z0-9]+", "-").Trim("-")
if (-not $slug) {
    throw "Topic `'$Topic`' produces an empty slug. Choose a different name."
}

$period = $Date.ToString("yyyy-MM")
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$experimentsRoot = Join-Path $repoRoot "experiments"
$monthDir = Join-Path $experimentsRoot $period
$experimentDir = Join-Path $monthDir $slug

if (Test-Path $experimentDir) {
    throw "Experiment at '$experimentDir' already exists."
}

New-Item -ItemType Directory -Path $monthDir -Force | Out-Null
New-Item -ItemType Directory -Path $experimentDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $experimentDir "src") -Force | Out-Null

$summaryLine = if ($Description) { "**Summary:** $Description`r`n" } else { "" }
$readmeContent = @"
# $Topic

**Date:** $($Date.ToString("yyyy-MM-dd"))
$summaryLine
## Goal
- What question am I answering?
- What does success look like?

## Findings
- 

## Next Steps
- 
"@

Set-Content -Path (Join-Path $experimentDir "README.md") -Value $readmeContent -NoNewline:$false

$notesContent = @"
# Notes
- Observations:
- Blockers:
- Resources:
"@
Set-Content -Path (Join-Path $experimentDir "notes.md") -Value $notesContent -NoNewline:$false

$commandsContent = @"
# Commands
```sh
# List commands or scripts you ran during the experiment.
```
"@
Set-Content -Path (Join-Path $experimentDir "commands.md") -Value $commandsContent -NoNewline:$false

Write-Host "Created experiment scaffold at $experimentDir"
