param(
    [string]$AdminUser = "postgres",
    [string]$AdminPassword = "arsal123",
    [string]$PostgresBin = "C:\Program Files\PostgreSQL\16\bin"
)

$ErrorActionPreference = "Stop"

$psql = Join-Path $PostgresBin "psql.exe"
$createdb = Join-Path $PostgresBin "createdb.exe"

if (-not (Test-Path -LiteralPath $psql)) {
    throw "psql.exe was not found at: $psql"
}

if (-not (Test-Path -LiteralPath $createdb)) {
    throw "createdb.exe was not found at: $createdb"
}

$env:PGPASSWORD = $AdminPassword

function Invoke-PostgresQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Database,

        [Parameter(Mandatory = $true)]
        [string]$Query
    )

    $output = & $psql `
        -h 127.0.0.1 `
        -p 5432 `
        -U $AdminUser `
        -d $Database `
        -tA `
        -v ON_ERROR_STOP=1 `
        -c $Query 2>&1

    if ($LASTEXITCODE -ne 0) {
        $errorMessage = ($output | Out-String).Trim()

        if ([string]::IsNullOrWhiteSpace($errorMessage)) {
            $errorMessage = "Unknown PostgreSQL error."
        }

        throw "PostgreSQL command failed: $errorMessage"
    }

    if ($null -eq $output) {
        return ""
    }

    return ($output | Out-String).Trim()
}

try {
    Write-Host "Testing PostgreSQL administrator connection..." -ForegroundColor Cyan

    $connectionTest = Invoke-PostgresQuery `
        -Database "postgres" `
        -Query "SELECT current_user;"

    if ($connectionTest -ne $AdminUser) {
        throw "Connected as '$connectionTest' instead of '$AdminUser'."
    }

    Write-Host "Connected successfully as '$AdminUser'." -ForegroundColor Green

    Write-Host "Checking genesis PostgreSQL role..." -ForegroundColor Cyan

    $roleExists = Invoke-PostgresQuery `
        -Database "postgres" `
        -Query "SELECT 1 FROM pg_roles WHERE rolname = 'genesis';"

    if ($roleExists -eq "1") {
        Write-Host "Role 'genesis' already exists. Updating its password..." -ForegroundColor Yellow

        Invoke-PostgresQuery `
            -Database "postgres" `
            -Query "ALTER ROLE genesis WITH LOGIN PASSWORD 'genesis';" | Out-Null

        Write-Host "Role 'genesis' updated." -ForegroundColor Green
    }
    else {
        Write-Host "Creating role 'genesis'..." -ForegroundColor Cyan

        Invoke-PostgresQuery `
            -Database "postgres" `
            -Query "CREATE ROLE genesis WITH LOGIN PASSWORD 'genesis';" | Out-Null

        Write-Host "Role 'genesis' created." -ForegroundColor Green
    }

    Write-Host "Checking genesis database..." -ForegroundColor Cyan

    $databaseExists = Invoke-PostgresQuery `
        -Database "postgres" `
        -Query "SELECT 1 FROM pg_database WHERE datname = 'genesis';"

    if ($databaseExists -ne "1") {
        Write-Host "Creating database 'genesis'..." -ForegroundColor Cyan

        $createDatabaseOutput = & $createdb `
            -h 127.0.0.1 `
            -p 5432 `
            -U $AdminUser `
            -O genesis `
            genesis 2>&1

        if ($LASTEXITCODE -ne 0) {
            $errorMessage = ($createDatabaseOutput | Out-String).Trim()

            if ([string]::IsNullOrWhiteSpace($errorMessage)) {
                $errorMessage = "Unknown PostgreSQL database creation error."
            }

            throw "Could not create database 'genesis': $errorMessage"
        }

        Write-Host "Database 'genesis' created." -ForegroundColor Green
    }
    else {
        Write-Host "Database 'genesis' already exists. Updating its owner..." -ForegroundColor Yellow

        Invoke-PostgresQuery `
            -Database "postgres" `
            -Query "ALTER DATABASE genesis OWNER TO genesis;" | Out-Null

        Write-Host "Database ownership assigned to 'genesis'." -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "Local PostgreSQL is ready for GENESIS." -ForegroundColor Green
    Write-Host "Database: genesis" -ForegroundColor Green
    Write-Host "Username: genesis" -ForegroundColor Green
    Write-Host "Password: genesis" -ForegroundColor Green
    Write-Host "Host: 127.0.0.1" -ForegroundColor Green
    Write-Host "Port: 5432" -ForegroundColor Green
    Write-Host ""
    Write-Host "Connection URL:" -ForegroundColor Cyan
    Write-Host "postgresql://genesis:genesis@127.0.0.1:5432/genesis"
}
catch {
    Write-Host ""
    Write-Host "PostgreSQL setup failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
