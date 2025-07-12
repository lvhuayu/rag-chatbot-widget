#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Database consolidation migration script
.DESCRIPTION
    Migrates data from SQLite RAG database to unified Prisma database
#>

Write-Host "🔄 Starting Database Consolidation Migration..." -ForegroundColor Cyan

# Step 1: Generate Prisma client
Write-Host "📦 Generating Prisma client..." -ForegroundColor Yellow
try {
    npx prisma generate
    Write-Host "✅ Prisma client generated successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to generate Prisma client: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Run database migration
Write-Host "🔄 Running Prisma database migration..." -ForegroundColor Yellow
try {
    npx prisma db push
    Write-Host "✅ Database schema updated successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update database schema: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Run data migration
Write-Host "📄 Migrating RAG data to Prisma..." -ForegroundColor Yellow
try {
    node migrate-to-prisma.js
    Write-Host "✅ Data migration completed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to migrate data: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Verify migration
Write-Host "🔍 Verifying migration..." -ForegroundColor Yellow
try {
    $verificationScript = @"
const { PrismaClient } = require('./prisma/generated/client');

const prisma = new PrismaClient();

async function verifyMigration() {
    try {
        const [docCount, embeddingCount, userCount] = await Promise.all([
            prisma.rAGDocument.count(),
            prisma.rAGEmbedding.count(),
            prisma.user.count()
        ]);
        
        console.log(JSON.stringify({
            success: true,
            documents: docCount,
            embeddings: embeddingCount,
            users: userCount
        }));
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
    } finally {
        await prisma.$disconnect();
    }
}

verifyMigration();
"@

    $verificationScript | Out-File -FilePath "verify-migration.js" -Encoding UTF8
    $result = node verify-migration.js | ConvertFrom-Json
    
    if ($result.success) {
        Write-Host "✅ Migration verification successful:" -ForegroundColor Green
        Write-Host "   📄 Documents: $($result.documents)" -ForegroundColor White
        Write-Host "   🧠 Embeddings: $($result.embeddings)" -ForegroundColor White
        Write-Host "   👤 Users: $($result.users)" -ForegroundColor White
    } else {
        Write-Host "❌ Migration verification failed: $($result.error)" -ForegroundColor Red
    }
    
    # Clean up
    Remove-Item "verify-migration.js" -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "❌ Failed to verify migration: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Database consolidation completed!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Update your backend to use PrismaRAGStorage instead of SQLite storage" -ForegroundColor White
Write-Host "   2. Test the new unified database" -ForegroundColor White
Write-Host "   3. Remove the old SQLite database files when ready" -ForegroundColor White 