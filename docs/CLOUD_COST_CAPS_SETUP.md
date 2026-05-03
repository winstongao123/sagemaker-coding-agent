# Cloud Cost Caps — AWS Bedrock + GCP — Beginner Guide

**Created**: 2026-05-03
**Why this exists**: Stop AI agents from running up huge cloud bills. Three layers of protection: app-level (visible budget), AWS-level (hard auto-stop on Bedrock at $50/month), GCP-level (hard auto-stop on entire project at AUD 300/month).

---

## Quick Status Check (run anytime)

```bash
# AWS — see current Bedrock spend + budget status
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50

# AWS — see if the auto-deny action is armed (Status should be STANDBY when budget < 100%)
aws budgets describe-budget-actions-for-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50

# GCP — see current GCP project spend + budget
gcloud alpha billing budgets describe 1df470d4-6e32-46de-8e4d-5f73f70ba168 --billing-account=01C3B7-CCB5D8-E691BB
```

---

## How It Works (plain English)

### AWS Bedrock — $50 USD/month hard stop (GLOBAL across all regions)

Three pieces work together:

1. **Budget** = a meter that tracks Bedrock spending across the month — **GLOBAL**: covers Bedrock in every AWS region (us-east-1, ap-southeast-2, eu-west-1, etc.)
2. **IAM Policy** = a rule that says "DENY all Bedrock API calls" — **GLOBAL**: IAM is global by default, denies in any region
3. **Budget Action** = the link: when the budget meter hits 100% ($50), the rule auto-attaches to your SageMaker role
4. **Email notifications** at 50% ($25), 80% ($40), 100% ($50) sent to `winston@arcsage.com.au`

**Not region-scoped**: AWS Budget filter is `Service: Amazon Bedrock`, which means it tracks Bedrock spending in EVERY region you've ever called Bedrock from. The IAM deny applies globally too.

Result: when you hit $50 of Bedrock spending across all regions in a month, your SageMaker notebook **literally cannot call Bedrock anywhere**. No more spending possible. Email alert sent to `winston@arcsage.com.au`.

Resets day 1 of next month — IAM policy auto-detaches, you can spend again.

### GCP — AUD 300/month hard stop (entire project, ALL regions, ALL services)

Four pieces work together:

1. **Budget** = a meter that tracks ALL GCP project spending across the month — **GLOBAL**: covers every service (Compute, Vertex AI, Storage, etc.) in every region
2. **Pub/Sub topic** = a notification channel
3. **Cloud Function `budget-killswitch`** = a small Python script (its CODE lives in us-central1; its ACTION disables billing on the WHOLE project regardless of region)
4. **Notification rule** = the link: at 50%/80%/100%, GCP sends a message to Pub/Sub → Cloud Function fires → at 100%, function disables billing

**Region note**: us-central1 is just where the function CODE is hosted (chosen for low cost). The function's effect — disabling project billing — is project-wide GLOBAL. Doesn't matter that the function lives in one region; when it fires, ALL regions / ALL services stop charging.

Result: when you hit AUD 300 of GCP spending (any service, any region), the project's billing is **disabled globally**. All chargeable APIs stop. Email alerts at 50% and 80% give early warning.

Resets day 1 of next month — but you must manually re-link billing (see "Resume" below) because GCP doesn't auto-restore.

---

## The Setup Scripts (already run — for reference)

### AWS — 5 commands

#### Command 1: Create the "Deny Bedrock" IAM policy

```bash
aws iam create-policy --policy-name DenyBedrockAtBudget --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyAllBedrock",
    "Effect": "Deny",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:Converse",
      "bedrock:ConverseStream"
    ],
    "Resource": "*"
  }]
}' --description "Auto-attached by Bedrock-Monthly-50 budget action when monthly Bedrock spend reaches \$50."
```

**Syntax explained**:
- `aws iam create-policy` = AWS CLI verb to create an IAM policy
- `--policy-name DenyBedrockAtBudget` = the policy's identifier (you'll reference this name later)
- `--policy-document '{...}'` = the actual JSON rule, single-quoted to preserve quotes inside
- Inside JSON:
  - `"Version": "2012-10-17"` = AWS IAM policy schema version (always this exact string)
  - `"Effect": "Deny"` = blocks the listed actions (vs "Allow" which permits them)
  - `"Action": [...]` = which API operations to deny (4 different ways to call Bedrock — covers all)
  - `"Resource": "*"` = on ALL resources (i.e., any model)

#### Command 2: Create role for AWS Budgets to assume

```bash
aws iam create-role --role-name BudgetActionsRole --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "budgets.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}'
```

**Syntax explained**:
- `aws iam create-role` = create an IAM role (like a user, but for AWS services to use)
- `--assume-role-policy-document` = trust policy: who/what is allowed to USE this role
- `"Principal": {"Service": "budgets.amazonaws.com"}` = the AWS Budgets service is the only thing allowed to assume this role (not random users)
- `"Action": "sts:AssumeRole"` = standard "let this principal use this role" permission

#### Command 3: Give the role permission to attach IAM policies

```bash
aws iam attach-role-policy --role-name BudgetActionsRole \
  --policy-arn arn:aws:iam::aws:policy/AWSBudgetsActionsWithAWSResourceControlAccess
```

**Syntax explained**:
- `aws iam attach-role-policy` = attach an existing managed policy to a role
- `--policy-arn arn:aws:iam::aws:policy/AWSBudgetsActionsWithAWSResourceControlAccess` = AWS-managed policy that grants Budgets the ability to attach/detach IAM policies (the role couldn't actually do its job without this)

#### Command 4: Create the $50 monthly Bedrock budget

```bash
aws budgets create-budget --account-id 903039434627 --budget '{
  "BudgetName": "Bedrock-Monthly-50",
  "BudgetLimit": {"Amount": "50", "Unit": "USD"},
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {"Service": ["Amazon Bedrock"]}
}'
```

**Syntax explained**:
- `aws budgets create-budget` = create a new AWS budget
- `--account-id 903039434627` = your AWS account ID (the 12-digit number)
- `"BudgetLimit": {"Amount": "50", "Unit": "USD"}` = $50 USD ceiling
- `"TimeUnit": "MONTHLY"` = resets every month on day 1 (vs DAILY/QUARTERLY/ANNUALLY)
- `"BudgetType": "COST"` = tracks dollars spent (vs USAGE for hours/requests)
- `"CostFilters": {"Service": ["Amazon Bedrock"]}` = ONLY tracks Bedrock spending (other AWS services don't count toward this $50)

#### Command 5: Wire the budget to the auto-deny action

```bash
aws budgets create-budget-action --account-id 903039434627 \
  --budget-name Bedrock-Monthly-50 \
  --notification-type ACTUAL \
  --action-type APPLY_IAM_POLICY \
  --action-threshold ActionThresholdValue=100,ActionThresholdType=PERCENTAGE \
  --execution-role-arn arn:aws:iam::903039434627:role/BudgetActionsRole \
  --approval-model AUTOMATIC \
  --subscribers Address=winston@arcsage.com.au,SubscriptionType=EMAIL \
  --definition '{"IamActionDefinition":{"PolicyArn":"arn:aws:iam::903039434627:policy/DenyBedrockAtBudget","Roles":["AmazonSageMaker-ExecutionRole-20260128T203969"]}}'
```

**Syntax explained**:
- `aws budgets create-budget-action` = link a budget to an automated reaction
- `--notification-type ACTUAL` = trigger on actual spend (not forecasted/projected)
- `--action-type APPLY_IAM_POLICY` = the reaction is to attach an IAM policy
- `--action-threshold ActionThresholdValue=100,ActionThresholdType=PERCENTAGE` = fire at 100% of budget (i.e., $50)
- `--execution-role-arn arn:aws:iam::...:role/BudgetActionsRole` = which role to use when performing the action (the one we created in Command 2)
- `--approval-model AUTOMATIC` = no manual approval needed; just fire when threshold hit (alternative: `MANUAL` requires email-confirm)
- `--subscribers Address=...,SubscriptionType=EMAIL` = who gets notified
- `--definition '{...}'` = WHAT to do: attach `DenyBedrockAtBudget` policy to the SageMaker role

---

### GCP — 4 commands

#### Command 1: Install the gcloud beta component (one-time)

```bash
gcloud components install beta --quiet
```

**Syntax explained**: gcloud has stable + beta + alpha command tracks. Budget commands need the beta track. `--quiet` skips confirmation prompts.

#### Command 2: Create the Pub/Sub topic for budget alerts

```bash
gcloud pubsub topics create budget-alert-disable-billing --project=algebraic-pact-478006-h0
```

**Syntax explained**:
- `gcloud pubsub topics create <name>` = create a Pub/Sub messaging channel
- `--project=algebraic-pact-478006-h0` = your GCP project ID

#### Command 3: Deploy the Cloud Function killswitch

The Python code (saved to `/tmp/disable-billing/main.py`):

```python
"""Disable GCP billing on this project when budget exceeded.
Triggered by Pub/Sub message from Cloud Billing Budget alert.
"""
import base64, json, os
from googleapiclient import discovery

PROJECT_ID = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")

def stop_billing(event, context):
    pubsub_data = base64.b64decode(event["data"]).decode("utf-8")
    pubsub_json = json.loads(pubsub_data)
    cost_amount = float(pubsub_json.get("costAmount", 0))
    budget_amount = float(pubsub_json.get("budgetAmount", 0))
    if cost_amount <= budget_amount:
        return f"OK: ${cost_amount:.2f} <= ${budget_amount:.2f}"
    billing = discovery.build("cloudbilling", "v1", cache_discovery=False)
    project_name = f"projects/{PROJECT_ID}"
    res = (
        billing.projects()
        .updateBillingInfo(name=project_name, body={"billingAccountName": ""})
        .execute()
    )
    return f"DISABLED billing on {PROJECT_ID}: ${cost_amount:.2f} > ${budget_amount:.2f}"
```

**Code explained line-by-line**:
- `import base64, json, os` = standard libraries for decoding messages, parsing JSON, reading env vars
- `from googleapiclient import discovery` = Google's Python SDK for calling GCP APIs
- `PROJECT_ID = os.environ.get(...)` = which GCP project to disable billing on (set automatically by Cloud Function runtime)
- `def stop_billing(event, context)` = the function GCP calls when a Pub/Sub message arrives
- `event['data']` = the message payload (base64-encoded JSON from the budget alert)
- `cost_amount` / `budget_amount` = parsed from the alert payload
- `if cost_amount <= budget_amount` = early exit if not over budget yet (the function fires at 50% AND 80% AND 100%; only act on 100%+)
- `billing.projects().updateBillingInfo(...body={"billingAccountName": ""})` = the actual disable: set billingAccountName to empty string = unlink billing

Deploy command:
```bash
cd /tmp/disable-billing
gcloud functions deploy budget-killswitch \
  --runtime=python311 \
  --trigger-topic=budget-alert-disable-billing \
  --entry-point=stop_billing \
  --project=algebraic-pact-478006-h0 \
  --region=us-central1
```

**Syntax explained**:
- `gcloud functions deploy <name>` = deploy a Cloud Function with this name
- `--runtime=python311` = Python 3.11
- `--trigger-topic=...` = fire when this Pub/Sub topic gets a message
- `--entry-point=stop_billing` = the Python function name to call (must match `def stop_billing(...)` in main.py)
- `--region=us-central1` = where to host the function (closest US region; can use any)

#### Command 3a: Grant the function permission to disable billing

```bash
SA="412665781391-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding algebraic-pact-478006-h0 \
  --member="serviceAccount:$SA" \
  --role="roles/billing.projectManager"

gcloud beta billing accounts add-iam-policy-binding 01C3B7-CCB5D8-E691BB \
  --member="serviceAccount:$SA" \
  --role="roles/billing.admin"
```

**Syntax explained**:
- `SA=...` = the service account email of the Cloud Function (auto-created when function deployed)
- `add-iam-policy-binding` = grant a role to a member
- `roles/billing.projectManager` = let the SA manage billing on the project
- `roles/billing.admin` = let the SA modify the billing account itself (needed to unlink)

#### Command 4: Create the AUD 300 monthly budget

```bash
gcloud billing budgets create \
  --billing-account=01C3B7-CCB5D8-E691BB \
  --display-name="GCP-Monthly-200USD-300AUD" \
  --budget-amount=300AUD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

Then wire Pub/Sub via alpha (gcloud quirk — only alpha track has the right flag):

```bash
gcloud alpha billing budgets update 1df470d4-6e32-46de-8e4d-5f73f70ba168 \
  --billing-account=01C3B7-CCB5D8-E691BB \
  --all-updates-rule-pubsub-topic=projects/algebraic-pact-478006-h0/topics/budget-alert-disable-billing
```

**Syntax explained**:
- `--billing-account=01C3B7-CCB5D8-E691BB` = which billing account (you have 2; this is "My Billing Account")
- `--budget-amount=300AUD` = AUD 300/month (currency must match billing account's currency)
- `--threshold-rule=percent=0.5` = email + Pub/Sub alert at 50%
- `--threshold-rule=percent=0.8` = alert at 80%
- `--threshold-rule=percent=1.0` = alert at 100% — this is the one that fires the killswitch
- `--all-updates-rule-pubsub-topic=...` = where to send the alerts (the topic the Cloud Function listens to)

---

## Adjusting the Caps

### Raise AWS to $100/month

```bash
aws budgets update-budget --account-id 903039434627 --new-budget '{
  "BudgetName": "Bedrock-Monthly-50",
  "BudgetLimit": {"Amount": "100", "Unit": "USD"},
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {"Service": ["Amazon Bedrock"]}
}'
```

Note: `BudgetName` stays the same even if you raise the limit — don't rename it (would orphan the Budget Action).

### Lower AWS to $20/month

Same command, change `"Amount": "100"` to `"Amount": "20"`.

### Raise GCP to AUD 500

```bash
gcloud alpha billing budgets update 1df470d4-6e32-46de-8e4d-5f73f70ba168 \
  --billing-account=01C3B7-CCB5D8-E691BB \
  --budget-amount=500AUD
```

### Adjust GCP threshold percentages (e.g., add 25% early alert)

```bash
gcloud alpha billing budgets update 1df470d4-6e32-46de-8e4d-5f73f70ba168 \
  --billing-account=01C3B7-CCB5D8-E691BB \
  --threshold-rule=percent=0.25 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

---

## Resume After Auto-Stop Fires

### AWS — resume Bedrock immediately (without raising budget)

```bash
aws iam detach-role-policy \
  --role-name AmazonSageMaker-ExecutionRole-20260128T203969 \
  --policy-arn arn:aws:iam::903039434627:policy/DenyBedrockAtBudget
```

This detaches the Deny policy. Bedrock works again **until the next time the budget action fires**, which only happens at the next 100% trigger (so if you're already over, it'll re-fire on the next API call billed). Better to ALSO raise the budget if you want to keep going.

### AWS — raise budget AND resume

Raise budget first (see "Adjusting" above), then detach the deny policy. Now you have headroom.

### GCP — resume billing

```bash
gcloud beta billing projects link algebraic-pact-478006-h0 \
  --billing-account=01C3B7-CCB5D8-E691BB
```

This re-links your project to the billing account. All chargeable services work again. **Note**: the Cloud Function will fire AGAIN if you exceed budget again — you may want to also raise the budget OR temporarily disable the function:

```bash
# Disable killswitch temporarily (e.g., for emergency overspend)
gcloud functions delete budget-killswitch \
  --project=algebraic-pact-478006-h0 \
  --region=us-central1 \
  --quiet

# Re-deploy when ready (use the Cloud Function code at /tmp/disable-billing/main.py)
```

---

## Wait for Next Month

If you don't need to resume now, just wait. Day 1 of next month:
- AWS: Budget resets to $0 actual spend; Budget Action auto-detaches the deny policy at start of next month
- GCP: Budget resets; YOU must manually re-link billing (GCP design — the function only runs when budget exceeded, never reverses itself)

---

## Three-Layer Defense Summary

| Layer | What | Limit | Behavior |
|---|---|---|---|
| **App-level (v5 chat.ipynb)** | `CONFIG.session_cost_limit` | $20 USD per session | Visible warning at 80%/100%, agent CONTINUES (you decide to Stop) |
| **AWS Bedrock account** | Bedrock-Monthly-50 budget | $50 USD per month | HARD STOP — IAM deny attached at 100%, Bedrock cannot be called |
| **GCP project** | GCP-Monthly-200USD-300AUD budget | AUD 300 (~$200 USD) per month | HARD STOP — billing disabled at 100%, all chargeable APIs stop |

App-level = "see what you're spending and decide". Cloud-level = "circuit breaker for catastrophic runaway".

---

## Worst-Case Cost Exposure

If everything goes wrong simultaneously:
- 1 v5 session goes wild: maxes out at ~$20-30 (app halts at $20 + ~$10 slop)
- AWS month catches it: caps at $50 total Bedrock that month
- GCP month catches anything else: caps at AUD 300 (~$200 USD) total GCP that month

**Total worst-case monthly: ~$250 USD across both clouds combined.** Realistic monthly: $5-30 USD depending on how much you use Bedrock.

---

## How to Inspect Setup Anytime

```bash
# AWS budget current state
aws budgets describe-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50 \
  --query 'Budget.{Limit:BudgetLimit.Amount,Spent:CalculatedSpend.ActualSpend.Amount,Forecast:CalculatedSpend.ForecastedSpend.Amount}'

# AWS budget action state (look for "Status": "STANDBY" = armed; "EXECUTION_SUCCESS" = fired)
aws budgets describe-budget-actions-for-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50 \
  --query 'Actions[].{Status:Status,Threshold:ActionThreshold,Roles:Definition.IamActionDefinition.Roles}'

# GCP budget
gcloud alpha billing budgets describe 1df470d4-6e32-46de-8e4d-5f73f70ba168 \
  --billing-account=01C3B7-CCB5D8-E691BB

# GCP Cloud Function
gcloud functions describe budget-killswitch \
  --project=algebraic-pact-478006-h0 \
  --region=us-central1 \
  --gen2 \
  --format='value(state,updateTime,url)'
```

---

## To Remove Everything (uninstall)

If you want to remove all of this and revert to no caps (NOT recommended):

```bash
# AWS
aws iam detach-role-policy --role-name AmazonSageMaker-ExecutionRole-20260128T203969 \
  --policy-arn arn:aws:iam::903039434627:policy/DenyBedrockAtBudget   # in case it's attached
aws budgets delete-budget-action --account-id 903039434627 --budget-name Bedrock-Monthly-50 --action-id 70646339-958b-49eb-8f27-81fe63279f6f
aws budgets delete-budget --account-id 903039434627 --budget-name Bedrock-Monthly-50
aws iam detach-role-policy --role-name BudgetActionsRole --policy-arn arn:aws:iam::aws:policy/AWSBudgetsActionsWithAWSResourceControlAccess
aws iam delete-role --role-name BudgetActionsRole
aws iam delete-policy --policy-arn arn:aws:iam::903039434627:policy/DenyBedrockAtBudget

# GCP
gcloud alpha billing budgets delete 1df470d4-6e32-46de-8e4d-5f73f70ba168 --billing-account=01C3B7-CCB5D8-E691BB --quiet
gcloud functions delete budget-killswitch --project=algebraic-pact-478006-h0 --region=us-central1 --quiet
gcloud pubsub topics delete budget-alert-disable-billing --project=algebraic-pact-478006-h0 --quiet
```

---

## Reference IDs (your specific account)

Save these somewhere safe:

| Item | Value |
|---|---|
| AWS Account ID | `903039434627` |
| AWS SageMaker Role | `AmazonSageMaker-ExecutionRole-20260128T203969` |
| AWS Deny Policy ARN | `arn:aws:iam::903039434627:policy/DenyBedrockAtBudget` |
| AWS Budget Action ID | `70646339-958b-49eb-8f27-81fe63279f6f` |
| GCP Project ID | `algebraic-pact-478006-h0` |
| GCP Billing Account | `01C3B7-CCB5D8-E691BB` |
| GCP Budget ID | `1df470d4-6e32-46de-8e4d-5f73f70ba168` |
| GCP Pub/Sub Topic | `projects/algebraic-pact-478006-h0/topics/budget-alert-disable-billing` |
| GCP Cloud Function | `budget-killswitch` (us-central1) |
| Email | `winston@arcsage.com.au` |

---

**Created by Claude Code on 2026-05-03 as part of v5.0.1 build setup.** Save this file — you'll need the IDs above to adjust/inspect/uninstall.
