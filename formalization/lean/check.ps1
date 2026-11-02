param(
    [string]$LakeExe = "lake"
)
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    $pinnedVersion = (Get-Content -LiteralPath lean-toolchain -Raw).Trim() -replace '^leanprover/lean4:v', ''
    $versionOutput = & $LakeExe env lean --version
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read Lean version.' }
    if ($versionOutput -notmatch ('^Lean \(version ' + [regex]::Escape($pinnedVersion) + '(?:,|\))')) {
        throw "Lean version does not match lean-toolchain: $versionOutput"
    }
    Write-Output $versionOutput
    & $LakeExe build
    if ($LASTEXITCODE -ne 0) { throw "Lean build failed ($LASTEXITCODE)." }

    $auditLines = & $LakeExe env lean -DwarningAsError=true Audit.lean 2>&1
    $auditExit = $LASTEXITCODE
    $auditText = $auditLines -join [Environment]::NewLine
    Write-Output $auditText
    if ($auditExit -ne 0) { throw "Lean axiom audit failed ($auditExit)." }

    $allowed = @("propext", "Classical.choice", "Quot.sound")
    $reports = [regex]::Matches($auditText, 'depends on axioms:\s*\[([^\]]*)\]')
    $emptyReports = [regex]::Matches($auditText, 'does not depend on any axioms')
    if (($reports.Count + $emptyReports.Count) -eq 0) {
        throw "No axiom reports found; refusing an empty audit."
    }
    # These modules use one explicit namespace and public `theorem` declarations.
    # Require an axiom report for each, so adding a theorem cannot silently leave
    # it outside the checked inventory. Private lemmas are covered transitively.
    # Dotted names (e.g. `theorem CovarianceGate.foo`) are declared inside the
    # `NoeticDiffusion` namespace and audited under their full qualified name.
    $theoremPattern = '(?m)^(?:@\[[^\]]+\]\s*)?theorem\s+([A-Za-z_][A-Za-z0-9_.]*)'
    $sourceFiles = Get-ChildItem -LiteralPath Noetic -Filter '*.lean'
    foreach ($sourceFile in $sourceFiles) {
        $sourceText = Get-Content -LiteralPath $sourceFile.FullName -Raw
        foreach ($theorem in [regex]::Matches($sourceText, $theoremPattern)) {
            $qualifiedName = 'NoeticDiffusion.' + $theorem.Groups[1].Value
            $reportPattern = "'" + [regex]::Escape($qualifiedName) + "' (?:depends on axioms:|does not depend on any axioms)"
            if ($auditText -notmatch $reportPattern) {
                throw "Missing axiom report for $qualifiedName"
            }
        }
    }
    foreach ($report in $reports) {
        foreach ($entry in ($report.Groups[1].Value -split ',')) {
            $axiomName = $entry.Trim()
            if ($axiomName -and $axiomName -notin $allowed) {
                throw "Unapproved proof dependency: $axiomName"
            }
        }
    }
    Write-Output "PASS: build and axiom audit."
}
finally {
    Pop-Location
}
