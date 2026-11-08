# Decodes the south DDS textures extracted from the RimWorld 1.7 Assets.zip (BC7 / BC1 / BC3) with the game's own AssetRipper.TextureDecoder,
# writes the top mip as PNG (native size) and a x4 nearest-neighbour copy at 512 to match the vanilla bodies used so far. Run with pwsh 7.
$S = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
Add-Type -AssemblyName System.Drawing
$dll = $S + 'dec17\AssetRipper.TextureDecoder.dll'; [void][System.Reflection.Assembly]::LoadFrom($dll)
Add-Type -IgnoreWarnings -CompilerOptions '/nowarn:1701' -ReferencedAssemblies $dll -TypeDefinition @'
public static class Dec { public static byte[] Run(byte[] d, int off, int len, int w, int h, int kind) { byte[] o; var s = new System.ReadOnlySpan<byte>(d, off, len);
  if (kind == 7) AssetRipper.TextureDecoder.Bc.Bc7.Decompress(s, w, h, out o); else if (kind == 1) AssetRipper.TextureDecoder.Bc.Bc1.Decompress(s, w, h, out o); else AssetRipper.TextureDecoder.Bc.Bc3.Decompress(s, w, h, out o); return o; } }
'@
$out1 = $S + 'core17png\'; $out4 = $S + 'core17_512\'; New-Item -ItemType Directory -Force $out1, $out4 | Out-Null
$n = 0; $skip = @()
foreach ($f in (Get-ChildItem -Recurse ($S + 'core17\Resources\Textures\Things\Pawn\Humanlike') -Filter '*.dds') + (Get-ChildItem -Recurse ($S + 'dlc17') -Filter '*.dds')) {
  if ($f.Name -notmatch '_(south|east|north)\.(png|psd)\.dds$') { continue }
  $d = [System.IO.File]::ReadAllBytes($f.FullName)
  $h = [BitConverter]::ToInt32($d, 12); $w = [BitConverter]::ToInt32($d, 16); $four = [System.Text.Encoding]::ASCII.GetString($d, 84, 4)
  $off = 128; $fmt = $four
  if ($four -eq 'DX10') { $fmt = [string][BitConverter]::ToInt32($d, 128); $off = 148 }
  $bw = [Math]::Floor(($w + 3) / 4); $bh = [Math]::Floor(($h + 3) / 4)
  $px = $null
  switch ($fmt) {
    { $_ -in '98','99' } { $len = $bw * $bh * 16; $px = [Dec]::Run($d, $off, $len, $w, $h, 7) }
    { $_ -in '71','72','DXT1' } { $len = $bw * $bh * 8; $px = [Dec]::Run($d, $off, $len, $w, $h, 1) }
    { $_ -in '77','78','DXT5' } { $len = $bw * $bh * 16; $px = [Dec]::Run($d, $off, $len, $w, $h, 3) }
    default { $skip += "$($f.Name) ($fmt)" }
  }
  if ($null -eq $px) { continue }
  $name = $f.Name -replace '\.(png|psd)\.dds$', ''
  $bm = New-Object System.Drawing.Bitmap $w, $h, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $bd = $bm.LockBits((New-Object System.Drawing.Rectangle 0, 0, $w, $h), 'WriteOnly', $bm.PixelFormat)
  [System.Runtime.InteropServices.Marshal]::Copy($px, 0, $bd.Scan0, $w * $h * 4); $bm.UnlockBits($bd)
  $bm.Save($out1 + $name + '.png', [System.Drawing.Imaging.ImageFormat]::Png)
  $big = New-Object System.Drawing.Bitmap 512, 512; $g = [System.Drawing.Graphics]::FromImage($big); $g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $g.DrawImage($bm, 0, 0, 512, 512); $g.Dispose()
  $big.Save($out4 + $name + '.png', [System.Drawing.Imaging.ImageFormat]::Png); $big.Dispose(); $bm.Dispose(); $n++
}
"decoded $n; skipped: " + ($skip -join ', ')
