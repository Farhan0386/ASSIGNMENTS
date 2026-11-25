# Run from the project root in PowerShell after PostgreSQL is installed.
# Requires psql.exe and createdb.exe on PATH. Uses a dedicated payroll_db database.
$ErrorActionPreference = "Stop"

$database = "payroll_db"
$pgUser = "postgres"

Write-Host "Checking PostgreSQL connection..."
$dbExists = & psql -X -U $pgUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$database'" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Could not connect to PostgreSQL as $pgUser. Check the service, password and PATH."
}

if (($dbExists | Out-String).Trim() -ne "1") {
    Write-Host "Creating database $database ..."
    & createdb -U $pgUser $database
    if ($LASTEXITCODE -ne 0) { throw "Could not create $database." }
} else {
    Write-Warning "$database already exists. The next schema script drops and recreates ONLY its payroll schema. Back up any payroll schema data you need before continuing."
}

$files = @(
    "database/01_schema.sql",
    "database/02_functions.sql",
    "database/03_procedures.sql",
    "database/04_triggers.sql",
    "database/05_seed_data.sql"
)
foreach ($file in $files) {
    Write-Host "Executing $file ..."
    & psql -X -U $pgUser -d $database -v ON_ERROR_STOP=1 -f $file
    if ($LASTEXITCODE -ne 0) { throw "SQL setup failed at $file" }
}
Write-Host "Database setup completed. Now configure .env and run scripts/run_windows.ps1."
