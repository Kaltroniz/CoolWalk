#!/usr/bin/env bash
# One-command deploy: backend + hosting, then publish the website with its config.
#   export AWS_REGION=us-east-1            # a region where Amazon Location Maps/Places/Routes v2 exist
#   export MAP_API_KEY=v1.public....       # Amazon Location API key (see README step 4)
#   ./scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."
: "${AWS_REGION:?Set AWS_REGION}"
: "${MAP_API_KEY:?Set MAP_API_KEY (Amazon Location API key)}"
STACK="${STACK:-coolwalk}"

sam build -t infra/template.yaml
sam deploy --stack-name "$STACK" --region "$AWS_REGION" --resolve-s3 \
  --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset

out() { aws cloudformation describe-stacks --stack-name "$STACK" --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
API_URL="$(out ApiUrl)"; SITE_BUCKET="$(out SiteBucket)"; SITE_URL="$(out SiteUrl)"
DIST_ID="$(out DistributionId)"; DATA_BUCKET="$(out DataBucket)"

cat > frontend/config.js <<CFG
window.COOLWALK = {
  region: "$AWS_REGION",
  mapKey: "$MAP_API_KEY",
  apiUrl: "$API_URL",
  bbox: [77.19, 28.585, 77.26, 28.668]
};
CFG

aws s3 sync frontend/ "s3://$SITE_BUCKET/" --delete --region "$AWS_REGION"
if [ -n "$DIST_ID" ] && [ "$DIST_ID" != "None" ]; then
  aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" >/dev/null || true
fi

# Deploy to AWS Amplify Hosting (provides managed HTTPS)
python3 scripts/deploy_amplify.py

echo
echo "Amplify:     https://main.d3miw0zrayytbj.amplifyapp.com"
echo "S3 fallback: $SITE_URL"
echo "API:         $API_URL"
echo "Data bucket: $DATA_BUCKET   (export COOLWALK_BUCKET=$DATA_BUCKET)"
echo "Add https://main.d3miw0zrayytbj.amplifyapp.com/* to the API key's allowed referers."
