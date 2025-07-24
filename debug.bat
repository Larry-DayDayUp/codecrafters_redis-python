@echo off
:: Redis CMD Debug Tools
:: Usage: debug.bat [test_type]
:: test_type: basic, replica, all

if "%1"=="basic" goto basic_test
if "%1"=="replica" goto replica_test  
if "%1"=="all" goto all_tests
if "%1"=="" goto show_help

:show_help
echo.
echo Redis CMD Debug Tools
echo =====================
echo Usage: debug.bat [test_type]
echo.
echo Available test types:
echo   basic    - Test basic Redis commands (PING, SET, GET, INFO)
echo   replica  - Test replica mode functionality
echo   all      - Run all tests
echo.
goto end

:basic_test
echo Running basic Redis tests...
echo.
call cmd_test_suite.bat
goto end

:replica_test
echo Running replica mode tests...
echo.
call test_replica_cmd.bat
goto end

:all_tests
echo Running all Redis tests...
echo.
echo === BASIC TESTS ===
call cmd_test_suite.bat
echo.
echo === REPLICA TESTS ===
call test_replica_cmd.bat
goto end

:end
echo.
echo Debug session completed.
