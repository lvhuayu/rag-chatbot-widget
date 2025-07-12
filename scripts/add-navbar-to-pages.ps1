#!/usr/bin/env pwsh

Write-Host "🔧 Adding Navbar to All HTML Pages" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Get the navbar template content
$navbarTemplate = Get-Content "public/navbar-template.html" -Raw

# Split the template into CSS and HTML parts
$cssStart = $navbarTemplate.IndexOf("<!-- Navbar CSS Template -->")
$cssEnd = $navbarTemplate.IndexOf("<!-- Navbar HTML Template -->")
$htmlStart = $cssEnd
$htmlEnd = $navbarTemplate.IndexOf("<!-- Mobile Menu JavaScript -->")
$jsStart = $htmlEnd
$jsEnd = $navbarTemplate.Length

$navbarCSS = $navbarTemplate.Substring($cssStart, $cssEnd - $cssStart)
$navbarHTML = $navbarTemplate.Substring($htmlStart, $jsStart - $htmlStart)
$navbarJS = $navbarTemplate.Substring($jsStart, $jsEnd - $jsStart)

# Find all HTML files in the public directory
$htmlFiles = Get-ChildItem -Path "public" -Filter "*.html" -Recurse

$filesUpdated = 0
$filesSkipped = 0

foreach ($file in $htmlFiles) {
    Write-Host "Processing: $($file.Name)" -ForegroundColor Yellow
    
    $content = Get-Content $file.FullName -Raw
    $originalContent = $content
    
    # Check if navbar already exists
    if ($content -match "navbar") {
        Write-Host "  ⏭️  Skipping - navbar already exists" -ForegroundColor Gray
        $filesSkipped++
        continue
    }
    
    # Find the position to insert CSS (after existing <style> tags or in <head>)
    $headEnd = $content.IndexOf("</head>")
    if ($headEnd -eq -1) {
        Write-Host "  ❌ No </head> tag found, skipping" -ForegroundColor Red
        continue
    }
    
    # Find the position to insert HTML (after <body> tag)
    $bodyStart = $content.IndexOf("<body>")
    if ($bodyStart -eq -1) {
        Write-Host "  ❌ No <body> tag found, skipping" -ForegroundColor Red
        continue
    }
    
    # Insert CSS in head
    $content = $content.Insert($headEnd, "`n    $navbarCSS`n    ")
    
    # Insert HTML after body tag
    $bodyEnd = $content.IndexOf(">", $bodyStart) + 1
    $content = $content.Insert($bodyEnd, "`n    $navbarHTML`n    ")
    
    # Insert JavaScript before closing body tag
    $bodyClose = $content.LastIndexOf("</body>")
    if ($bodyClose -ne -1) {
        $content = $content.Insert($bodyClose, "`n    $navbarJS`n    ")
    }
    
    # Create backup
    $backupFile = "$($file.FullName).backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $file.FullName $backupFile
    
    # Write the modified content
    Set-Content $file.FullName $content -Encoding UTF8
    
    Write-Host "  ✅ Updated with navbar" -ForegroundColor Green
    $filesUpdated++
}

Write-Host "`n📊 Summary:" -ForegroundColor Cyan
Write-Host "Files updated: $filesUpdated" -ForegroundColor Green
Write-Host "Files skipped: $filesSkipped" -ForegroundColor Yellow

if ($filesUpdated -gt 0) {
    Write-Host "`n🎉 Navbar has been added to all HTML pages!" -ForegroundColor Green
    Write-Host "The navbar will now be visible on all pages with:" -ForegroundColor White
    Write-Host "  • Fixed positioning (always visible)" -ForegroundColor White
    Write-Host "  • Responsive design (mobile-friendly)" -ForegroundColor White
    Write-Host "  • Dropdown menus for organized navigation" -ForegroundColor White
    Write-Host "  • Proper z-index to stay on top" -ForegroundColor White
} else {
    Write-Host "`nℹ️  No files needed updating - navbar already exists on all pages" -ForegroundColor Blue
}

Write-Host "`nScript complete!" -ForegroundColor Cyan 