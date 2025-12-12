# ArtinSmartRealty - Professional Cleanup Script
# Removes all obsolete documentation and legacy files

Write-Host "ArtinSmartRealty Professional Cleanup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "i:\real state salesman\ArtinSmartRealty"
Set-Location $projectRoot

# ==================== DELETE OBSOLETE DOCUMENTATION ====================

Write-Host "Deleting obsolete documentation files..." -ForegroundColor Yellow

$obsoleteDocs = @(
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
    "DEPLOYMENT_BROCHURE_PDF.md",
    "DEPLOYMENT_GUIDE.md",
    "DEPLOYMENT_TESTING_GUIDE.md",
    "DEPLOY_CRITICAL_FIXES.md",
    "DEPLOY_NOW.md",
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
    "FINAL_SUMMARY_FA.md",
    "SETUP_GUIDE_FA.md",
    "SSL_GUIDE_FA.md",
    "USER_GUIDE_FA.md",
    "FINAL_UX_FIXES_REPORT.md",
    "FINAL_UX_REVIEW_REPORT.md",
    "UX_CONVERSION_IMPROVEMENTS.md",
    "UX_CUSTOMER_JOURNEY_ANALYSIS.md",
    "UX_IMPROVEMENTS_SUMMARY.md",
    "UX_ISSUES_ANALYSIS.md",
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
    "RAG_DELIVERY_SUMMARY.md",
    "WOLF_CLOSER_TRANSFORMATION.md",
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
    if (Test-Path $doc) {
        Remove-Item $doc -Force
        $deletedDocs++
    }
}
Write-Host "Deleted $deletedDocs documentation files" -ForegroundColor Green

# ==================== DELETE DEPLOY SCRIPTS ====================

Write-Host "Deleting duplicate deployment scripts..." -ForegroundColor Yellow

$deployScripts = @(
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
foreach ($script in $deployScripts) {
    if (Test-Path $script) {
        Remove-Item $script -Force
        $deletedScripts++
    }
}
Write-Host "Deleted $deletedScripts deployment scripts" -ForegroundColor Green

# ==================== DELETE MIGRATIONS ====================

Write-Host "Deleting old migration scripts..." -ForegroundColor Yellow

$migrations = @(
    "backend\migrate_enums_direct.py",
    "backend\migrate_enums_sql.py",
    "backend\migrate_enums_to_lowercase.py",
    "backend\migrate_enums_to_uppercase.py",
    "backend\migrate_property_images.py",
    "migrate_linkedin_sqlite.py",
    "migrate_image_fields.py",
    "fix_brochure_pdf_column.sql",
    "update_whatsapp_token.sql",
    "backend\migration_add_slot_fields.sql"
)

$deletedMigrations = 0
foreach ($m in $migrations) {
    if (Test-Path $m) {
        Remove-Item $m -Force
        $deletedMigrations++
    }
}
Write-Host "Deleted $deletedMigrations migration files" -ForegroundColor Green

# ==================== DELETE TEST FILES ====================

Write-Host "Deleting test files from root..." -ForegroundColor Yellow

$tests = @(
    "test_e2e.py",
    "test_enum.py",
    "test_linkedin_integration.py",
    "test_new_features.py",
    "test_production_data.py",
    "check_properties.py",
    "setup_sample_data.py",
    "setup_telegram_webhook.py",
    "setup_whatsapp_webhook.py",
    "licensed-image.jpg",
    "README_START_HERE.md"
)

$deletedTests = 0
foreach ($t in $tests) {
    if (Test-Path $t) {
        Remove-Item $t -Force
        $deletedTests++
    }
}
Write-Host "Deleted $deletedTests test/misc files" -ForegroundColor Green

# ==================== DELETE WHATSAPP_ROUTER ====================

if (Test-Path "whatsapp_router") {
    Remove-Item "whatsapp_router" -Recurse -Force
    Write-Host "Deleted whatsapp_router directory" -ForegroundColor Green
}

# ==================== SUMMARY ====================

$total = $deletedDocs + $deletedScripts + $deletedMigrations + $deletedTests + 1
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "CLEANUP COMPLETE!" -ForegroundColor Green
Write-Host "Total deleted: $total items" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next: Run 'git status' to review changes" -ForegroundColor White
