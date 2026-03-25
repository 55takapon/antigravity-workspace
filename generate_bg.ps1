Add-Type -AssemblyName System.Drawing

$width = 1920
$height = 1080
$filename = "$PSScriptRoot\luxury-salon-website\assets\hero_bg.png"

$bmp = New-Object System.Drawing.Bitmap($width, $height)
$g = [System.Drawing.Graphics]::FromImage($bmp)

# Background color (Dark luxury base)
$g.Clear([System.Drawing.Color]::FromArgb(30, 30, 30))

# Create a gradient brush
$rect = New-Object System.Drawing.Rectangle(0, 0, $width, $height)
$brush1 = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, 
    [System.Drawing.Color]::FromArgb(30, 30, 30), 
    [System.Drawing.Color]::FromArgb(60, 50, 40), 
    [System.Drawing.Drawing2D.LinearGradientMode]::ForwardDiagonal)

$g.FillRectangle($brush1, $rect)

# Add some "gold" accents (circles)
$rnd = New-Object System.Random
for ($i = 0; $i -lt 15; $i++) {
    $x = $rnd.Next(-200, $width)
    $y = $rnd.Next(-200, $height)
    $size = $rnd.Next(200, 600)
    $alpha = $rnd.Next(20, 60)
    
    $goldColor = [System.Drawing.Color]::FromArgb($alpha, 197, 160, 89)
    $solidBrush = New-Object System.Drawing.SolidBrush($goldColor)
    
    $g.FillEllipse($solidBrush, $x, $y, $size, $size)
}

# Save
$bmp.Save($filename, [System.Drawing.Imaging.ImageFormat]::Png)

$g.Dispose()
$bmp.Dispose()

Write-Host "Generated $filename"
