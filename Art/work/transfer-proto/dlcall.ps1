# Extract the apparel and body DDS (south, east, north) of the 1.7 Core and DLC Assets.zip and decode them at once (extracted folders do not survive between calls here).
$S = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$W = '\\wsl.localhost\Ubuntu-24.04\home\nelim\rimworld17\'
if (-not (Test-Path ($S + 'dec17\AssetRipper.TextureDecoder.dll'))) { New-Item -ItemType Directory -Force ($S + 'dec17') | Out-Null; Copy-Item ($W + 'AssetRipper.TextureDecoder.dll') ($S + 'dec17') }
$o = $S + 'core17'; New-Item -ItemType Directory -Force $o | Out-Null; Push-Location $o; & C:\Windows\System32\tar.exe -xf ($W + 'Assets.zip') 'Resources/Textures/Things/Pawn/Humanlike/Apparel/*' 'Resources/Textures/Things/Pawn/Humanlike/Bodies/*'; Pop-Location
foreach ($d in 'Royalty','Ideology','Biotech','Anomaly','Odyssey') { $o = $S + 'dlc17\' + $d; New-Item -ItemType Directory -Force $o | Out-Null; Push-Location $o; & C:\Windows\System32\tar.exe -xf ($W + 'Data\' + $d + '\Assets.zip') '*Apparel*'; Pop-Location }
& ($S + 'dds2png.ps1')
