# Test script for PlatformIO sample code generation across boards and frameworks
# Tests various chip series with their supported frameworks

$testDir = "C:\Users\Max\temp\codegen_tests"
$testBases = @(
    # CH32V series
    @{ board = "ch32v003f4p6_evt_r0"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH32V103C8T6"; frameworks = @("noneos-sdk", "freertos") },
    @{ board = "genericCH32V203C8T6"; frameworks = @("noneos-sdk", "freertos") },
    @{ board = "genericCH32V307RCT6"; frameworks = @("noneos-sdk", "freertos") },
    
    # CH32L series
    @{ board = "ch32l103c8t6_evt_r0"; frameworks = @("noneos-sdk", "freertos") },
    
    # CH32X series
    @{ board = "ch32x035c8t6_evt_r0"; frameworks = @("noneos-sdk") },
    
    # CH5x series (each variant: CH570, CH571, CH572, CH573, CH56x)
    @{ board = "genericCH570D"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH571D"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH572D"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH573F"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH565M"; frameworks = @("noneos-sdk") },
    
    # CH58x and CH59x series (with FreeRTOS support)
    @{ board = "genericCH581F"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH582F"; frameworks = @("noneos-sdk", "freertos") },
    @{ board = "genericCH591D"; frameworks = @("noneos-sdk") },
    
    # CH6xx series
    @{ board = "genericCH641F"; frameworks = @("noneos-sdk") },
    @{ board = "genericCH643Q"; frameworks = @("noneos-sdk") }
)

$results = @()
$testCount = 0
$passCount = 0
$failCount = 0

Write-Host "PlatformIO Sample Code Generation Test Suite" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

foreach ($testBase in $testBases) {
    $board = $testBase.board
    
    foreach ($framework in $testBase.frameworks) {
        $testCount++
        $testName = "$board + $framework"
        Write-Host "Test $testCount`: $testName" -ForegroundColor Yellow
        
        # Create test directory
        $workDir = "$testDir\test_$($board)_$($framework)"
        if (Test-Path $workDir) {
            Remove-Item -Path $workDir -Recurse -Force | Out-Null
        }
        New-Item -ItemType Directory -Path $workDir | Out-Null
        
        try {
            Push-Location $workDir
            
            # Generate sample code
            Write-Host "  [1/2] Generating sample code..." -ForegroundColor Gray
            $genCmd = "pio --caller vscode init --sample-code -b $board --ide=vscode -O ""framework=$framework"""
            $output = Invoke-Expression $genCmd 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  [X] Code generation failed!" -ForegroundColor Red
                $failCount++
                $results += @{
                    Test = $testName
                    Status = "FAILED (generation)"
                    Error = ($output | Select-Object -Last 1)
                }
                Pop-Location
                continue
            }
            
            # Compile
            Write-Host "  [2/2] Compiling..." -ForegroundColor Gray
            $output = pio run 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] PASSED" -ForegroundColor Green
                $passCount++
                $results += @{
                    Test = $testName
                    Status = "PASSED"
                }
            } else {
                Write-Host "  [X] Compilation failed!" -ForegroundColor Red
                $failCount++
                $results += @{
                    Test = $testName
                    Status = "FAILED (compilation)"
                    Error = ($output | Select-Object -Last 3 | Out-String).Trim()
                }
            }
        }
        catch {
            Write-Host "  [X] Exception: $_" -ForegroundColor Red
            $failCount++
            $results += @{
                Test = $testName
                Status = "FAILED (exception)"
                Error = $_.Exception.Message
            }
        }
        finally {
            Pop-Location
        }
        
        Write-Host ""
    }
}

# Summary
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Total Tests: $testCount"
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failCount -gt 0) {
    Write-Host "Failed Tests Details:" -ForegroundColor Yellow
    Write-Host ""
    $results | Where-Object { $_.Status -like "FAILED*" } | ForEach-Object {
        Write-Host "Test: $($_.Test)" -ForegroundColor Yellow
        Write-Host "Status: $($_.Status)" -ForegroundColor Red
        if ($_.Error) {
            Write-Host "Error: $($_.Error)" -ForegroundColor Red
        }
        Write-Host ""
    }
}

Write-Host "Test run complete!" -ForegroundColor Cyan
