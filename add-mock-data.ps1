#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Add comprehensive mock data to the RAG chatbot database
    
.DESCRIPTION
    This script adds sample users and documents to the Prisma database
    for testing and demonstration purposes.
#>

Write-Host "🚀 Adding Mock Data to RAG Chatbot Database" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "prisma/schema.prisma")) {
    Write-Host "❌ Error: prisma/schema.prisma not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Function to run Prisma commands
function Invoke-PrismaCommand {
    param([string]$Command)
    Write-Host "Running: npx prisma $Command" -ForegroundColor Yellow
    npx prisma $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Prisma command failed: $Command" -ForegroundColor Red
        exit 1
    }
}

# Function to add a user via Prisma
function Add-User {
    param(
        [string]$Username,
        [string]$Password,
        [string]$PublicKey = $null,
        [string]$PrivateKey = $null
    )
    
    $userData = @{
        username = $Username
        password = $Password
    }
    
    if ($PublicKey) { $userData.publicKey = $PublicKey }
    if ($PrivateKey) { $userData.privateKey = $PrivateKey }
    
    $jsonData = $userData | ConvertTo-Json -Compress
    
    Write-Host "Adding user: $Username" -ForegroundColor Cyan
    
    # Use Prisma Studio or direct database access to add users
    # For now, we'll create a simple script
    $userScript = @"
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function addUser() {
    try {
        const user = await prisma.user.create({
            data: {
                username: '$Username',
                password: '$Password'$(
                    if ($PublicKey) { ",`n                publicKey: '$PublicKey'" }
                    if ($PrivateKey) { ",`n                privateKey: '$PrivateKey'" }
                )
            }
        });
        console.log('User created:', user.id);
    } catch (error) {
        console.error('Error creating user:', error.message);
    } finally {
        await prisma.$disconnect();
    }
}

addUser();
"@
    
    $userScript | Out-File -FilePath "temp-add-user.js" -Encoding UTF8
    node temp-add-user.js
    Remove-Item "temp-add-user.js" -ErrorAction SilentlyContinue
}

# Function to add RAG documents via API
function Add-RAGDocument {
    param(
        [string]$Title,
        [string]$Content,
        [string]$UserId,
        [string]$Url = "https://example.com/$($Title.ToLower().Replace(' ', '-'))"
    )
    
    $docData = @{
        title = $Title
        content = $Content
        user_id = $UserId
        url = $Url
    }
    
    $jsonData = $docData | ConvertTo-Json -Compress
    
    Write-Host "Adding document: $Title (User: $UserId)" -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/add-document" -Method POST -Body $jsonData -ContentType "application/json" -TimeoutSec 10
        if ($response.success) {
            Write-Host "✅ Added: $Title" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Failed to add: $Title - $($response.message)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error adding $Title`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check if RAG server is running
Write-Host "🔍 Checking RAG server status..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method GET -TimeoutSec 5
    Write-Host "✅ RAG server is running" -ForegroundColor Green
    Write-Host "Storage type: $($healthResponse.storage)" -ForegroundColor Green
} catch {
    Write-Host "❌ RAG server is not running. Please start it first." -ForegroundColor Red
    Write-Host "Run: cd backend && python rag_server_minimal.py" -ForegroundColor Yellow
    exit 1
}

# Generate Prisma client if needed
Write-Host "🔧 Ensuring Prisma client is up to date..." -ForegroundColor Yellow
Invoke-PrismaCommand "generate"

# Sample users data
$sampleUsers = @(
    @{
        Username = "john_doe"
        Password = "password123"
        PublicKey = "pk_test_john_123"
    },
    @{
        Username = "jane_smith"
        Password = "password456"
        PublicKey = "pk_test_jane_456"
    },
    @{
        Username = "admin_user"
        Password = "admin123"
        PublicKey = "pk_test_admin_789"
    },
    @{
        Username = "demo_user"
        Password = "demo123"
        PublicKey = "pk_test_demo_101"
    }
)

# Sample documents data
$sampleDocuments = @(
    @{
        Title = "Company Policy Handbook"
        Content = "This handbook outlines our company policies including work hours, dress code, vacation policies, and employee benefits. All employees must read and acknowledge these policies. The handbook is updated annually and employees will be notified of any changes."
        UserId = "john_doe"
    },
    @{
        Title = "Product Development Guide"
        Content = "Our product development process follows agile methodology with two-week sprints. Each sprint includes planning, development, testing, and review phases. We use JIRA for project management and GitHub for version control. Code reviews are mandatory for all changes."
        UserId = "john_doe"
    },
    @{
        Title = "Customer Service Procedures"
        Content = "Customer service representatives should always greet customers warmly, listen actively to their concerns, and provide solutions within 24 hours. Escalate complex issues to supervisors. Document all interactions in our CRM system. Follow up with customers to ensure satisfaction."
        UserId = "jane_smith"
    },
    @{
        Title = "IT Support Troubleshooting"
        Content = "Common IT issues and solutions: 1) Password reset - use self-service portal, 2) Network connectivity - check cables and restart router, 3) Software installation - contact IT for admin rights, 4) Email issues - check spam folder and server status. Contact IT support for unresolved issues."
        UserId = "jane_smith"
    },
    @{
        Title = "Financial Reporting Guidelines"
        Content = "Monthly financial reports must be submitted by the 5th of each month. Include revenue, expenses, profit margins, and cash flow analysis. Use approved templates and accounting software. All reports require manager approval before submission to finance department."
        UserId = "admin_user"
    },
    @{
        Title = "Employee Training Program"
        Content = "New employees complete orientation training in their first week. Ongoing training includes quarterly skill assessments and annual compliance training. Training materials are available in the learning management system. Managers track training completion and provide feedback."
        UserId = "admin_user"
    },
    @{
        Title = "Marketing Campaign Strategy"
        Content = "Our marketing campaigns target specific customer segments based on demographics and behavior. We use social media, email marketing, and content marketing channels. Campaign performance is measured by engagement rates, conversion rates, and ROI. A/B testing is used to optimize campaigns."
        UserId = "demo_user"
    },
    @{
        Title = "Sales Process Documentation"
        Content = "The sales process includes prospecting, qualification, presentation, proposal, negotiation, and closing stages. Sales representatives use CRM to track leads and opportunities. Each stage has specific criteria and required activities. Regular sales training ensures consistent process execution."
        UserId = "demo_user"
    },
    @{
        Title = "Quality Assurance Standards"
        Content = "Quality assurance processes ensure all products meet company standards. Testing includes unit tests, integration tests, and user acceptance testing. Defects are tracked in our issue management system. Quality metrics are reviewed weekly and improvements are implemented based on findings."
        UserId = "john_doe"
    },
    @{
        Title = "Data Security Protocols"
        Content = "Data security protocols include encryption of sensitive data, regular password changes, two-factor authentication, and access controls. Employees must complete security training annually. Incident response procedures are documented and tested quarterly. Regular security audits identify potential vulnerabilities."
        UserId = "admin_user"
    }
)

# Add users
Write-Host "`n👥 Adding sample users..." -ForegroundColor Yellow
$userSuccessCount = 0
foreach ($user in $sampleUsers) {
    Add-User -Username $user.Username -Password $user.Password -PublicKey $user.PublicKey
    $userSuccessCount++
}

# Add documents
Write-Host "`n📄 Adding sample documents..." -ForegroundColor Yellow
$docSuccessCount = 0
foreach ($doc in $sampleDocuments) {
    if (Add-RAGDocument -Title $doc.Title -Content $doc.Content -UserId $doc.UserId) {
        $docSuccessCount++
    }
}

# Get final stats
Write-Host "`n📊 Getting final database statistics..." -ForegroundColor Yellow
try {
    $statsResponse = Invoke-RestMethod -Uri "http://localhost:8001/stats" -Method GET -TimeoutSec 5
    Write-Host "`n=== Final Database State ===" -ForegroundColor Green
    Write-Host "Total documents: $($statsResponse.document_count)" -ForegroundColor White
    Write-Host "Unique users: $($statsResponse.unique_users)" -ForegroundColor White
} catch {
    Write-Host "Warning: Could not get final stats" -ForegroundColor Yellow
}

Write-Host "`n🎉 Mock data addition complete!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor White
Write-Host "- Users added: $userSuccessCount" -ForegroundColor White
Write-Host "- Documents added: $docSuccessCount" -ForegroundColor White
Write-Host "`nYou can now:" -ForegroundColor Yellow
Write-Host "1. View the database manager at: http://localhost:8001/db-manager.html" -ForegroundColor White
Write-Host "2. Test the chatbot with the sample data" -ForegroundColor White
Write-Host "3. Use the upload portal to add more documents" -ForegroundColor White 