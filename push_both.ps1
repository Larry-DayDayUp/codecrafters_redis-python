# push_both.ps1 - Push to both CodeCrafters and GitHub
param(
    [string]$message = "Update Redis implementation"
)

Write-Host "📝 Git Status:" -ForegroundColor Cyan
git status --short

Write-Host "`n🚀 Pushing to CodeCrafters..." -ForegroundColor Green
$codecraftersResult = git push origin master
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CodeCrafters push successful!" -ForegroundColor Green
} else {
    Write-Host "❌ CodeCrafters push failed!" -ForegroundColor Red
}

$githubExists = git remote | Select-String "github"
if ($githubExists) {
    Write-Host "`n📊 Pushing to GitHub for contributions..." -ForegroundColor Blue
    $githubResult = git push github master
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GitHub push successful!" -ForegroundColor Green
        Write-Host "🎉 Your contributions will now appear on GitHub!" -ForegroundColor Magenta
    } else {
        Write-Host "❌ GitHub push failed! Make sure the repository exists." -ForegroundColor Red
        Write-Host "Create it at: https://github.com/new" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  GitHub remote not configured. Add it with:" -ForegroundColor Yellow
    Write-Host "git remote add github https://github.com/Larry-DayDayUp/codecrafters-redis-python.git" -ForegroundColor Yellow
}
