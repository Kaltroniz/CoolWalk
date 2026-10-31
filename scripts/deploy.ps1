# PowerShell deploy script for CoolWalk
param(
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
    [string]$MapKey = $(if ($env:MAP_API_KEY) { $env:MAP_API_KEY } else { "" }),
    [string]$StackName = "coolwalk"
)

$ErrorActionPreference = "Stop"
$root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $root

if (-not $MapKey) {
    # Check if key exists
    $keyDesc = aws location describe-key --key-name CoolWalkMapKey 2>$null | ConvertFrom-Json
    if ($keyDesc -and $keyDesc.Key) {
        $MapKey = $keyDesc.Key
    } else {
        Write-Error "Please specify -MapKey or set `$env:MAP_API_KEY"
    }
}

sam build -t infra/template.yaml
sam deploy --stack-name $StackName --region $Region --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset

$stackDesc = aws cloudformation describe-stacks --stack-name $StackName --region $Region | ConvertFrom-Json
$outputs = @{}
foreach ($o in $stackDesc.Stacks[0].Outputs) {
    $outputs[$o.OutputKey] = $o.OutputValue
}

$apiUrl = $outputs["ApiUrl"]
$siteBucket = $outputs["SiteBucket"]
$siteUrl = $outputs["SiteUrl"]
$dataBucket = $outputs["DataBucket"]
$distId = $outputs["DistributionId"]

$cfg = @"
window.COOLWALK = {
  region: "$Region",
  mapKey: "$MapKey",
  apiUrl: "$apiUrl",
  bbox: [77.19, 28.585, 77.26, 28.668]
};
"@

Set-Content -Path (Join-Path $root "frontend\config.js") -Value $cfg -NoNewline

aws s3 sync (Join-Path $root "frontend") "s3://$siteBucket/" --delete --region $Region
if ($distId) {
    aws cloudfront create-invalidation --distribution-id $distId --paths "/*"
}

# Deploy to AWS Amplify Hosting (provides managed HTTPS)
python (Join-Path $root "scripts\deploy_amplify.py")

Write-Host ""
Write-Host "Amplify:     https://main.d3miw0zrayytbj.amplifyapp.com"
Write-Host "S3 fallback: $siteUrl"
Write-Host "API:         $apiUrl"
Write-Host "Data bucket: $dataBucket   (`$env:COOLWALK_BUCKET = '$dataBucket')"

