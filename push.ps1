# ScholarBot Safe Git Push Script 🚀
# Run this script in PowerShell to safely commit and push your project to GitHub.

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   ScholarBot Safe Git Push Assistant      " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$remoteUrl = "git@github.com:loxleyftsck/SCHOLARBOT-AI.git"

# 1. Ask user for confirmation to unify repositories
$title = "Penyatuan Repositori"
$message = "Apakah Anda ingin menyatukan folder backend (scholarbot) and frontend (scholarbot-web) di bawah satu repositori utama di scholarbot-ai? (Rekomendasi)"
$options = [System.Management.Automation.Host.ChoiceDescription[]] @(
    New-Object System.Management.Automation.Host.ChoiceDescription "&Ya", "Satukan dalam satu Git repositori induk"
    New-Object System.Management.Automation.Host.ChoiceDescription "&Tidak", "Gunakan Git backend saja di subfolder scholarbot"
)
$result = $host.ui.PromptForChoice($title, $message, $options, 0)

if ($result -eq 0) {
    Write-Host "`n[1/4] Menghapus Git lama di backend dan menyatukan di folder induk..." -ForegroundColor Yellow
    if (Test-Path "scholarbot\.git") {
        Remove-Item -Recurse -Force "scholarbot\.git" -ErrorAction SilentlyContinue
    }
    
    if (-not (Test-Path ".git")) {
        git init
    }
    
    # Create main .gitignore
    $gitignoreContent = @"
# Backend ignores
scholarbot/.env
scholarbot/*.env
scholarbot/storage/data/
scholarbot/storage/data/**
scholarbot/__pycache__/
scholarbot/*.pyc
scholarbot/venv/
scholarbot/env/
scholarbot/.venv/

# Frontend ignores
scholarbot-web/node_modules/
scholarbot-web/dist/
scholarbot-web/.env
scholarbot-web/*.env
scholarbot-web/.DS_Store
"@
    Set-Content -Path ".gitignore" -Value $gitignoreContent -Force
} else {
    Write-Host "`n[1/4] Menggunakan Git di subfolder backend..." -ForegroundColor Yellow
    cd scholarbot
}

# 2. Configure Git Remote
Write-Host "`n[2/4] Mengonfigurasi remote GitHub ke $remoteUrl..." -ForegroundColor Yellow
$remotes = git remote
if ($remotes -contains "origin") {
    git remote set-url origin $remoteUrl
} else {
    git remote add origin $remoteUrl
}

# 3. Checkout to feature branch
Write-Host "`n[3/4] Membuat branch baru 'feature/v3.2-semantic-feedback'..." -ForegroundColor Yellow
git checkout -b feature/v3.2-semantic-feedback 2>$null
if ($lastExitCode -ne 0) {
    git checkout feature/v3.2-semantic-feedback
}

# 4. Stage and Commit
Write-Host "`n[4/4] Menambahkan berkas dan membuat commit..." -ForegroundColor Yellow
git add .

$commitMessage = "feat(rag): implement lightweight semantic search using numpy and hybrid retrieve"
$commitDesc = @"
- Add Cosine Similarity semantic search using free Hugging Face Inference API
- Implement graceful fallback to keyword-based search if offline
- Resolve source starvation using Round-Robin Source Balancing algorithm
- Add fully functional interactive message feedback system (Like/Dislike)
- Update ROADMAP.md to mark Phase 3.2 tasks as completed
"@

git commit -m $commitMessage -m $commitDesc

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "  Commit Berhasil Dibuat Secara Aman! 🎉    " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# 5. Prompt for automatic push
$titlePush = "Push ke GitHub"
$messagePush = "Apakah Anda ingin langsung melakukan PUSH branch 'feature/v3.2-semantic-feedback' ke GitHub sekarang?"
$optionsPush = [System.Management.Automation.Host.ChoiceDescription[]] @(
    New-Object System.Management.Automation.Host.ChoiceDescription "&Ya", "Push otomatis sekarang menggunakan SSH key Anda"
    New-Object System.Management.Automation.Host.ChoiceDescription "&Tidak", "Saya akan lakukan push manual nanti"
)
$resultPush = $host.ui.PromptForChoice($titlePush, $messagePush, $optionsPush, 0)

if ($resultPush -eq 0) {
    Write-Host "`nSedang melakukan push ke GitHub... Mohon tunggu." -ForegroundColor Yellow
    git push -u origin feature/v3.2-semantic-feedback
    if ($lastExitCode -eq 0) {
        Write-Host "`n=============================================" -ForegroundColor Green
        Write-Host "   PUSH KE GITHUB SELESAI DENGAN SUKSES! 🚀   " -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Green
    } else {
        Write-Host "`nPeringatan: Push gagal. Pastikan SSH Key Anda telah terdaftar di GitHub." -ForegroundColor Red
        Write-Host "Anda bisa mencoba kembali secara manual nanti dengan perintah: git push -u origin feature/v3.2-semantic-feedback" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nSiap! Anda dapat melakukan push manual kapan saja dengan perintah:" -ForegroundColor Cyan
    Write-Host "git push -u origin feature/v3.2-semantic-feedback" -ForegroundColor Yellow
    Write-Host "=============================================" -ForegroundColor Green
}
