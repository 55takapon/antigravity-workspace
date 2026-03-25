Add-Type -AssemblyName System.Drawing

function Generate-Image {
    param (
        [string]$Path,
        [int]$Width,
        [int]$Height,
        [string]$Color1,
        [string]$Color2,
        [string]$Style
    )

    $bitmap = New-Object System.Drawing.Bitmap($Width, $Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality

    # Parse Colors
    $c1 = [System.Drawing.ColorTranslator]::FromHtml($Color1)
    $c2 = [System.Drawing.ColorTranslator]::FromHtml($Color2)

    # Gradient Brush
    $rect = New-Object System.Drawing.Rectangle(0, 0, $Width, $Height)
    
    if ($Style -eq "Linear") {
        $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, $c1, $c2, 45.0)
    }
    elseif ($Style -eq "Radial") {
        # Fake radial by drawing varied circles or just standard linear for elegance
        $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, $c1, $c2, 90.0)
    }
    else {
        $brush = New-Object System.Drawing.SolidBrush($c1)
    }

    $graphics.FillRectangle($brush, $rect)

    # Add some "Texture" / Art
    $rand = New-Object Random
    for ($i = 0; $i -lt 20; $i++) {
        $a = $rand.Next(0, 50)
        $penColor = [System.Drawing.Color]::FromArgb($a, 255, 255, 255)
        $pen = New-Object System.Drawing.Pen($penColor, 1)
        if ($Style -eq "Linear") {
            $graphics.DrawLine($pen, 0, $rand.Next(0, $Height), $Width, $rand.Next(0, $Height))
        }
        else {
            $graphics.DrawEllipse($pen, $rand.Next(0, $Width), $rand.Next(0, $Height), $rand.Next(100, 500), $rand.Next(100, 500))
        }
    }

    # Save
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    
    $graphics.Dispose()
    $bitmap.Dispose()

    Write-Host "Generated $Path"
}

$OutputDir = "luxury_salon\images"
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Force -Path $OutputDir }

# Hero: Private Luxury Salon (Warm Beige/Gold Radial)
Generate-Image -Path "$OutputDir\hero_bg.jpg" -Width 1920 -Height 1080 -Color1 "#F5F3EF" -Color2 "#D8C3A5" -Style "Radial"

# Concept: Warm Light
Generate-Image -Path "$OutputDir\concept.jpg" -Width 600 -Height 800 -Color1 "#FDFBF7" -Color2 "#C5A059" -Style "Linear"

# Gallery: Various Luxury Tones
Generate-Image -Path "$OutputDir\gallery1.jpg" -Width 400 -Height 400 -Color1 "#1A1A1A" -Color2 "#333333" -Style "Radial"
Generate-Image -Path "$OutputDir\gallery2.jpg" -Width 400 -Height 400 -Color1 "#C5A059" -Color2 "#B08D48" -Style "Linear"
Generate-Image -Path "$OutputDir\gallery3.jpg" -Width 400 -Height 400 -Color1 "#F4F4F4" -Color2 "#E0E0E0" -Style "Linear"
Generate-Image -Path "$OutputDir\gallery4.jpg" -Width 400 -Height 400 -Color1 "#333333" -Color2 "#000000" -Style "Radial"
Generate-Image -Path "$OutputDir\gallery5.jpg" -Width 400 -Height 400 -Color1 "#D4AF37" -Color2 "#F7E7CE" -Style "Linear"
Generate-Image -Path "$OutputDir\gallery6.jpg" -Width 400 -Height 400 -Color1 "#555555" -Color2 "#777777" -Style "Radial"

# Map: Google Maps Style (Grid/Roads)
Generate-Image -Path "$OutputDir\map.jpg" -Width 800 -Height 450 -Color1 "#E5E3DF" -Color2 "#FFFFFF" -Style "Grid"
