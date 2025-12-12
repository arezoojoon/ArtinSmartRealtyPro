# ArtinSmartRealty - Professional Cleanup Script
# Removes all obsolete documentation and legacy files

Write-Host "🧹 ArtinSmartRealty Professional Cleanup" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "i:\real state salesman\ArtinSmartRealty"
Set-Location $projectRoot

# Create backup first
Write-Host "📦 Creating backup..." -ForegroundColor Yellow
$backupDir = "i:\real state salesman\ArtinSmartRealty_BACKUP_$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
Copy-Item -Path $projectRoot -Destination $backupDir -Recurse -Force
Write-Host "✅ Backup created at: $backupDir" -ForegroundColor Green
Write-Host ""

# ==================== DELETE OBSOLETE DOCUMENTATION ====================

Write-Host "🗑️  Deleting obsolete documentation files..." -ForegroundColor Yellow

$obsoleteDocs = @(
    # Bug fix reports (historical, not needed)
    "ADMIN_PANEL_FIXES.md",
    "ALL_BUGS_FIXED_FINAL.md",
    "BUGFIXES_DEC_10_2025.md",
    "BUGS_FIXED.md",
    "BUG_FIXES_ADMIN_INSPECTION.md",
    "BUG_FIXES_DEPLOYMENT.md",
    "BUG_FIXES_TYPE_CHECKING.md",
    "BUG_REPORT.md",
    "CRITICAL_BUGS_FIXED.md",
    "CRITICAL_BUGS_UNIFIED_SYSTEM.md",
    "HIDDEN_BUGS_DEEP_REVIEW.md",
    "PM_REVIEW_BUGS_FOUND.md",
    "QUICK_DEBUG.md",
    
    # Debug/Fix documentation
    "DEBUG_VOICE_HANDLER.md",
    "DEBUG_VOICE_SILENT.md",
    "DEEP_BUG_ANALYSIS_FA.md",
    "DEPLOY_VOICE_FIX.md",
    "EMERGENCY_FIX.md",
    "FIX_DOCKER_CACHE.md",
    "PDF_UPLOAD_FIX_REPORT.md",
    "VOICE_FIX_GUIDE.md",
    "WEBHOOK_FIX.md",
    "WHATSAPP_DEBUG.md",
    
    # Deployment guides (duplicates)
    "DEPLOYMENT_BROCHURE_PDF.md",
    "DEPLOYMENT_GUIDE.md",
    "DEPLOYMENT_TESTING_GUIDE.md",
    "DEPLOY_CRITICAL_FIXES.md",
    "DEPLOY_NOW.md",
    "DEPLOY_TO_PRODUCTION.sh",
    "FEATURE_FLAGS_DEPLOYMENT.md",
    "FINAL_DEPLOYMENT.md",
    "LATEST_FIXES_DEPLOYMENT.md",
    "LEAD_SCORING_DEPLOYMENT.md",
    "PRODUCTION_FIXES_SUMMARY.md",
    "PRODUCTION_MIGRATION_GUIDE.md",
    "QUICK_DEPLOY_5MIN.md",
    "VERIFY_DEPLOYMENT.md",
    "VPS_CRITICAL_FIX.md",
    "VPS_DEPLOYMENT_FIX_8.md",
    "VPS_DEPLOYMENT_FIX_9.md",
    "VPS_DEPLOYMENT_STEPS.md",
    "VPS_DEPLOY_NOW.md",
    "VPS_MERGE_FIX.md",
    "VPS_VERIFICATION.md",
    
    # Implementation reports (completed)
    "CAPTURE_CONTACT_IMPLEMENTATION.md",
    "COMPLETE_FIX_SUMMARY.md",
    "COMPLETE_IMPLEMENTATION_INDEX.md",
    "COMPLETE_IMPLEMENTATION_SUMMARY.md",
    "CONSULTATION_BUTTON_FIX.md",
    "FINAL_VERIFICATION_REPORT.md",
    "FRONTEND_IMPLEMENTATION_COMPLETE.md",
    "HIGH_VELOCITY_SALES_FEATURES.md",
    "HIGH_VELOCITY_SALES_IMPLEMENTATION.md",
    "IMPLEMENTATION_COMPLETE.md",
    "IMPLEMENTATION_COMPLETION_CERTIFICATE.md",
    "IMPLEMENTATION_PACKAGE_README.md",
    "THREE_SALES_FEATURES_COMPLETE.md",
    "UIUX_ENHANCEMENT_COMPLETE.md",
    "UNIFIED_SYSTEM_FINAL_REPORT.md",
    
    # Persian/FA documentation (rewriting in English)
    "DEEP_BUG_ANALYSIS_FA.md",
    "FINAL_SUMMARY_FA.md",
    "SETUP_GUIDE_FA.md",
    "SSL_GUIDE_FA.md",
    "USER_GUIDE_FA.md",
    
    # UX reports (already applied)
    "FINAL_UX_FIXES_REPORT.md",
    "FINAL_UX_REVIEW_REPORT.md",
    "UX_CONVERSION_IMPROVEMENTS.md",
    "UX_CUSTOMER_JOURNEY_ANALYSIS.md",
    "UX_IMPROVEMENTS_SUMMARY.md",
    "UX_ISSUES_ANALYSIS.md",
    
    # Summary/Delivery docs (project management, not technical)
    "DELIVERY_SUMMARY.md",
    "DOCUMENTATION_INDEX.md",
    "EXECUTIVE_SUMMARY.md",
    "FOLLOWUP_SYSTEM_EXPLAINED.md",
    "MORNING_COFFEE_CODE_REFERENCE.md",
    "MORNING_COFFEE_QUICK_SUMMARY.md",
    "MORNING_COFFEE_REPORT_DOCUMENTATION.md",
    "PITCH_DECK_SCRIPT.md",
    "PRODUCT_10_OUT_OF_10.md",
    "PRODUCT_PRESENTATION.md",
    "PROJECT_COMPLETE.md",
    "RAG_DELIVERY_SUMMARY.md",
    "WOLF_CLOSER_TRANSFORMATION.md",
    
    # Misc outdated docs
    "COMPETITIVE_ANALYSIS.md",
    "COMPREHENSIVE_QA_REPORT.md",
    "EXACT_CHANGES_LINE_BY_LINE.md",
    "EXACT_CODE_CHANGES_FINAL.md",
    "MULTI_VERTICAL_ROUTING_GUIDE.md",
    "QUICK_REFERENCE_CAPTURE_CONTACT.md",
    "RAG_IMPLEMENTATION_GUIDE.md",
    "RAG_QUICK_REFERENCE.md",
    "RAG_VISUAL_FLOWS.md",
    "TESTING_GUIDE.md",
    "TESTING_GUIDE_QUICK_REFERENCE.md",
    "VERIFICATION_REPORT.md",
    "VISUAL_GUIDE_ARCHITECTURE.md",
    "WAHA_WHATSAPP_SETUP.md",
    "WEBHOOK_SETUP_GUIDE.md",
    "WHATSAPP_QUICKSTART.md",
    "WHATSAPP_SETUP_GUIDE.md",
    "TWILIO_WHATSAPP_GUIDE.md"
)

$deletedDocs = 0
foreach ($doc in $obsoleteDocs) {
    $filePath = Join-Path $projectRoot $doc
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        $deletedDocs++
        Write-Host "  ✓ Deleted: $doc" -ForegroundColor Gray
    }
}

Write-Host "✅ Deleted $deletedDocs obsolete documentation files" -ForegroundColor Green
Write-Host ""

# ==================== DELETE DUPLICATE DEPLOY SCRIPTS ====================

Write-Host "🗑️  Deleting duplicate deployment scripts..." -ForegroundColor Yellow

$duplicateDeployScripts = @(
    "deploy-bot-fix.sh",
    "deploy_all_fixes.sh",
    "deploy_collecting_name_migration.sh",
    "deploy_feature_flags.sh",
    "deploy_jwt_fix.sh",
    "deploy_now.sh",
    "deploy_now.sh.backup",
    "deploy_subscription_fix.sh",
    "deploy_ux_fixes.sh",
    "emergency_recovery.sh",
    "fix_docker_deployment.sh",
    "fix_pdf_upload.sh",
    "fix_production_db.sh",
    "fix_voice_and_brochure.sh",
    "quick_deploy.sh",
    "safe_deploy.sh",
    "set_webhook.sh",
    "setup_ssl.sh",
    "verify_deployment.sh"
)

$deletedScripts = 0
foreach ($script in $duplicateDeployScripts) {
    $filePath = Join-Path $projectRoot $script
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        $deletedScripts++
        Write-Host "  ✓ Deleted: $script" -ForegroundColor Gray
    }
}

Write-Host "✅ Deleted $deletedScripts duplicate deployment scripts" -ForegroundColor Green
Write-Host ""

# ==================== DELETE OLD MIGRATION SCRIPTS ====================

Write-Host "🗑️  Deleting old migration scripts..." -ForegroundColor Yellow

$oldMigrations = @(
    "backend\migrate_enums_direct.py",
    "backend\migrate_enums_sql.py",
    "backend\migrate_enums_to_lowercase.py",
    "backend\migrate_enums_to_uppercase.py",
    "backend\migrate_property_images.py",
    "migrate_linkedin_sqlite.py",
    "migrate_image_fields.py"
)

$deletedMigrations = 0
foreach ($migration in $oldMigrations) {
    $filePath = Join-Path $projectRoot $migration
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        $deletedMigrations++
        Write-Host "  ✓ Deleted: $migration" -ForegroundColor Gray
    }
}

Write-Host "✅ Deleted $deletedMigrations old migration scripts" -ForegroundColor Green
Write-Host ""

# ==================== DELETE SQL SCRIPTS ====================

Write-Host "🗑️  Deleting one-time SQL scripts..." -ForegroundColor Yellow

$sqlScripts = @(
    "fix_brochure_pdf_column.sql",
    "update_whatsapp_token.sql",
    "backend\migration_add_slot_fields.sql"
)

$deletedSQL = 0
foreach ($sql in $sqlScripts) {
    $filePath = Join-Path $projectRoot $sql
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        $deletedSQL++
        Write-Host "  ✓ Deleted: $sql" -ForegroundColor Gray
    }
}

Write-Host "✅ Deleted $deletedSQL SQL scripts" -ForegroundColor Green
Write-Host ""

# ==================== DELETE OLD TEST FILES ====================

Write-Host "🗑️  Deleting test files from root..." -ForegroundColor Yellow

$testFiles = @(
    "test_e2e.py",
    "test_enum.py",
    "test_linkedin_integration.py",
    "test_new_features.py",
    "test_production_data.py",
    "check_properties.py"
)

$deletedTests = 0
foreach ($test in $testFiles) {
    $filePath = Join-Path $projectRoot $test
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        $deletedTests++
        Write-Host "  ✓ Deleted: $test" -ForegroundColor Gray
    }
}

Write-Host "✅ Deleted $deletedTests test files" -ForegroundColor Green
Write-Host ""

# ==================== DELETE OTHER FILES ====================

Write-Host "🗑️  Deleting other obsolete files..." -ForegroundColor Yellow

$otherFiles = @(
    "setup_sample_data.py",
    "setup_telegram_webhook.py",
    "setup_whatsapp_webhook.py",
    "licensed-image.jpg",
    "README_START_HERE.md"
)

$deletedOther = 0
foreach ($file in $otherFiles) {
    $filePath = Join-Path $projectRoot $file
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        $deletedOther++
        Write-Host "  ✓ Deleted: $file" -ForegroundColor Gray
    }
}

Write-Host "✅ Deleted $deletedOther other obsolete files" -ForegroundColor Green
Write-Host ""

# ==================== DELETE WHATSAPP_ROUTER FOLDER ====================

Write-Host "🗑️  Deleting unused whatsapp_router folder..." -ForegroundColor Yellow

$whatsappRouter = Join-Path $projectRoot "whatsapp_router"
if (Test-Path $whatsappRouter) {
    Remove-Item $whatsappRouter -Recurse -Force
    Write-Host "✅ Deleted whatsapp_router/ directory" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  whatsapp_router/ already removed" -ForegroundColor Gray
}

Write-Host ""

# ==================== SUMMARY ====================

$totalDeleted = $deletedDocs + $deletedScripts + $deletedMigrations + $deletedSQL + $deletedTests + $deletedOther + 1

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ CLEANUP COMPLETE!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  • Obsolete documentation:  $deletedDocs files" -ForegroundColor White
Write-Host "  • Duplicate deploy scripts: $deletedScripts files" -ForegroundColor White
Write-Host "  • Old migrations:           $deletedMigrations files" -ForegroundColor White
Write-Host "  • SQL scripts:              $deletedSQL files" -ForegroundColor White
Write-Host "  • Test files:               $deletedTests files" -ForegroundColor White
Write-Host "  • Other files:              $deletedOther files" -ForegroundColor White
Write-Host "  • Directories:              1 folder" -ForegroundColor White
Write-Host "  ─────────────────────────────────────" -ForegroundColor Gray
Write-Host "  TOTAL DELETED:              $totalDeleted items" -ForegroundColor Yellow
Write-Host ""
Write-Host "📦 Backup location:" -ForegroundColor Cyan
Write-Host "  $backupDir" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review remaining files" -ForegroundColor White
Write-Host "  2. Run: git status" -ForegroundColor White
Write-Host "  3. Create professional English documentation" -ForegroundColor White
Write-Host "  4. Push to https://github.com/arezoojoon/ArtinSmartRealtyPro.git" -ForegroundColor White
Write-Host ""
