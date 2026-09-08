param([ValidateSet('plan','build','verify')][string]$Command='build', [string]$Scope='liberty', [switch]$Force)
$ErrorActionPreference='Stop'
$cfg=Get-Content -Raw (Join-Path $PSScriptRoot 'config.json') | ConvertFrom-Json
$py=Join-Path (Split-Path $cfg.blender) '5.2/python/bin/python.exe'
$argsList=@((Join-Path $PSScriptRoot 'pipeline/run.py'),$Command,'--scope',$Scope)
if ($Force) {$argsList+='--force'}
& $py @argsList
exit $LASTEXITCODE
