# 🚀 Azure AI Avatar - Deployment Guide

This guide walks you through deploying a production-ready AI avatar system on Azure.

## Prerequisites

### Azure Subscription
- Active Azure subscription with sufficient credits
- Permissions to create resources
- Access to Azure Portal and CLI

### Development Tools
- Azure CLI 2.50+
- .NET 8 SDK (for API)
- Node.js 18+ (for frontend)
- Docker (optional, for containerization)
- Git

### Skills Required
- Basic Azure knowledge
- REST API concepts
- Understanding of authentication (OAuth, JWT)

---

## Phase 1: Azure Resource Setup

### 1.1 Resource Group

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create resource group
az group create \
  --name rg-avatar-prod \
  --location eastus \
  --tags Environment=Production Project=AIAvatar
```

### 1.2 Azure OpenAI Service

```bash
# Create Azure OpenAI resource
az cognitiveservices account create \
  --name openai-avatar-prod \
  --resource-group rg-avatar-prod \
  --kind OpenAI \
  --sku S0 \
  --location eastus \
  --yes

# Get API key
az cognitiveservices account keys list \
  --name openai-avatar-prod \
  --resource-group rg-avatar-prod
```

**Deploy Models via Portal:**
1. Navigate to Azure OpenAI Studio
2. Go to Deployments → Create new deployment
3. Deploy models:
   - `gpt-4-turbo` (name: gpt-4-turbo, capacity: 10K TPM)
   - `gpt-35-turbo` (name: gpt-35-turbo, capacity: 30K TPM)
   - `text-embedding-ada-002` (name: embeddings)

### 1.3 Azure Speech Services

```bash
# Create Speech Services resource
az cognitiveservices account create \
  --name speech-avatar-prod \
  --resource-group rg-avatar-prod \
  --kind SpeechServices \
  --sku S0 \
  --location eastus \
  --yes

# Get keys
az cognitiveservices account keys list \
  --name speech-avatar-prod \
  --resource-group rg-avatar-prod
```

### 1.4 Cosmos DB

```bash
# Create Cosmos DB account
az cosmosdb create \
  --name cosmos-avatar-prod \
  --resource-group rg-avatar-prod \
  --locations regionName=eastus failoverPriority=0 \
  --default-consistency-level Session \
  --enable-automatic-failover true

# Create database
az cosmosdb sql database create \
  --account-name cosmos-avatar-prod \
  --resource-group rg-avatar-prod \
  --name AvatarDB

# Create containers
az cosmosdb sql container create \
  --account-name cosmos-avatar-prod \
  --resource-group rg-avatar-prod \
  --database-name AvatarDB \
  --name Sessions \
  --partition-key-path "/userId" \
  --throughput 400

az cosmosdb sql container create \
  --account-name cosmos-avatar-prod \
  --resource-group rg-avatar-prod \
  --database-name AvatarDB \
  --name Analytics \
  --partition-key-path "/date" \
  --throughput 400
```

### 1.5 Storage Account

```bash
# Create storage account
az storage account create \
  --name storageavatarprod \
  --resource-group rg-avatar-prod \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Create containers
az storage container create \
  --name audio \
  --account-name storageavatarprod \
  --public-access blob

az storage container create \
  --name avatars \
  --account-name storageavatarprod \
  --public-access blob

az storage container create \
  --name recordings \
  --account-name storageavatarprod \
  --public-access off
```

### 1.6 Azure SignalR Service

```bash
# Create SignalR Service
az signalr create \
  --name signalr-avatar-prod \
  --resource-group rg-avatar-prod \
  --location eastus \
  --sku Standard_S1 \
  --unit-count 1 \
  --service-mode Default

# Get connection string
az signalr key list \
  --name signalr-avatar-prod \
  --resource-group rg-avatar-prod
```

### 1.7 App Service Plan & Web App

```bash
# Create App Service Plan
az appservice plan create \
  --name plan-avatar-prod \
  --resource-group rg-avatar-prod \
  --location eastus \
  --sku P1V3 \
  --is-linux

# Create Web App
az webapp create \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod \
  --plan plan-avatar-prod \
  --runtime "DOTNET|8.0"
```

### 1.8 Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app insights-avatar-prod \
  --location eastus \
  --resource-group rg-avatar-prod \
  --application-type web

# Get instrumentation key
az monitor app-insights component show \
  --app insights-avatar-prod \
  --resource-group rg-avatar-prod \
  --query instrumentationKey
```

### 1.9 Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name kv-avatar-prod \
  --resource-group rg-avatar-prod \
  --location eastus \
  --enable-rbac-authorization false

# Store secrets
az keyvault secret set \
  --vault-name kv-avatar-prod \
  --name "AzureOpenAI--ApiKey" \
  --value "YOUR_OPENAI_KEY"

az keyvault secret set \
  --vault-name kv-avatar-prod \
  --name "AzureSpeech--Key" \
  --value "YOUR_SPEECH_KEY"

az keyvault secret set \
  --vault-name kv-avatar-prod \
  --name "CosmosDB--ConnectionString" \
  --value "YOUR_COSMOS_CONNECTION_STRING"
```

---

## Phase 2: Copilot Studio Configuration

### 2.1 Create Copilot

1. Navigate to [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create new copilot:
   - Name: "AI Avatar Assistant"
   - Language: English
   - Environment: Production

### 2.2 Configure Topics

**Greeting Topic:**
```
Trigger phrases:
- Hello
- Hi
- Hey
- Good morning

Response:
Hello! I'm Alex, your AI avatar assistant. I can help you with:
- Product information
- Account support
- Technical assistance
- General inquiries

What can I help you with today?
```

**Fallback Configuration:**
1. Go to System Topics → Fallback
2. Enable "Generative answers"
3. Select Azure OpenAI deployment
4. Set moderation level: Medium

### 2.3 Enable Channels

1. Channels → Direct Line
2. Create new channel
3. Copy Secret Key 1
4. Store in Key Vault:

```bash
az keyvault secret set \
  --vault-name kv-avatar-prod \
  --name "CopilotStudio--DirectLineSecret" \
  --value "YOUR_DIRECT_LINE_SECRET"
```

### 2.4 Custom Actions (Power Automate)

**Example: Get Customer Info**
1. Create Power Automate flow
2. Trigger: When Copilot asks
3. Actions:
   - Parse user input for customer ID
   - Call CRM API
   - Return customer data
4. Register in Copilot Studio

---

## Phase 3: Application Deployment

### 3.1 Configuration

Create `appsettings.Production.json`:

```json
{
  "AzureOpenAI": {
    "Endpoint": "https://openai-avatar-prod.openai.azure.com/",
    "DeploymentName": "gpt-4-turbo"
  },
  "AzureSpeech": {
    "Region": "eastus"
  },
  "SignalR": {
    "ConnectionString": "@Microsoft.KeyVault(SecretUri=https://kv-avatar-prod.vault.azure.net/secrets/SignalR--ConnectionString/)"
  },
  "CosmosDB": {
    "DatabaseName": "AvatarDB"
  },
  "ApplicationInsights": {
    "ConnectionString": "InstrumentationKey=..."
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  }
}
```

### 3.2 Configure Managed Identity

```bash
# Enable system-assigned managed identity
az webapp identity assign \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod

# Get principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod \
  --query principalId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name kv-avatar-prod \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list

# Grant Cosmos DB access
az cosmosdb sql role assignment create \
  --account-name cosmos-avatar-prod \
  --resource-group rg-avatar-prod \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id $PRINCIPAL_ID \
  --scope "/dbs/AvatarDB"
```

### 3.3 Build and Deploy

```bash
# Navigate to your project directory
cd /path/to/avatar-api

# Publish application
dotnet publish -c Release -o ./publish

# Create deployment package
cd publish
zip -r ../deploy.zip .
cd ..

# Deploy to Azure
az webapp deploy \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod \
  --src-path deploy.zip \
  --type zip

# Restart app
az webapp restart \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod
```

### 3.4 Configure App Settings

```bash
# Set Key Vault reference
az webapp config appsettings set \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod \
  --settings \
    AzureOpenAI__ApiKey="@Microsoft.KeyVault(SecretUri=https://kv-avatar-prod.vault.azure.net/secrets/AzureOpenAI--ApiKey/)" \
    AzureSpeech__Key="@Microsoft.KeyVault(SecretUri=https://kv-avatar-prod.vault.azure.net/secrets/AzureSpeech--Key/)" \
    CosmosDB__ConnectionString="@Microsoft.KeyVault(SecretUri=https://kv-avatar-prod.vault.azure.net/secrets/CosmosDB--ConnectionString/)"
```

---

## Phase 4: Frontend Deployment

### 4.1 Static Web App

```bash
# Create Static Web App
az staticwebapp create \
  --name swa-avatar-frontend \
  --resource-group rg-avatar-prod \
  --location eastus \
  --source https://github.com/YOUR_USERNAME/avatar-frontend \
  --branch main \
  --app-location "/" \
  --api-location "api" \
  --output-location "dist"

# Configure custom domain (optional)
az staticwebapp hostname set \
  --name swa-avatar-frontend \
  --resource-group rg-avatar-prod \
  --hostname avatar.yourdomain.com
```

### 4.2 Environment Variables

Create `.env.production`:

```env
VITE_API_URL=https://app-avatar-api-prod.azurewebsites.net
VITE_SIGNALR_URL=https://app-avatar-api-prod.azurewebsites.net/hub/avatar
VITE_AVATAR_RENDERER=uneeq
```

---

## Phase 5: Security & Compliance

### 5.1 Azure AD B2C (Authentication)

```bash
# Create B2C tenant (via Portal)
# Then create application registration

# Configure redirect URIs
az ad app update \
  --id YOUR_APP_ID \
  --web-redirect-uris \
    https://swa-avatar-frontend.azurestaticapps.net/auth/callback \
    https://app-avatar-api-prod.azurewebsites.net/signin-oidc
```

### 5.2 API Management (Optional)

```bash
# Create APIM instance
az apim create \
  --name apim-avatar-prod \
  --resource-group rg-avatar-prod \
  --publisher-email admin@company.com \
  --publisher-name "Company Name" \
  --sku-name Developer

# Import API
az apim api import \
  --resource-group rg-avatar-prod \
  --service-name apim-avatar-prod \
  --path /avatar \
  --specification-format OpenApi \
  --specification-url https://app-avatar-api-prod.azurewebsites.net/swagger/v1/swagger.json
```

### 5.3 Configure CORS

```bash
az webapp cors add \
  --name app-avatar-api-prod \
  --resource-group rg-avatar-prod \
  --allowed-origins \
    https://swa-avatar-frontend.azurestaticapps.net \
    https://avatar.yourdomain.com
```

---

## Phase 6: Monitoring & Alerting

### 6.1 Application Insights Queries

**Average Response Time:**
```kusto
requests
| where timestamp > ago(1h)
| summarize avg(duration) by bin(timestamp, 5m)
| render timechart
```

**Error Rate:**
```kusto
requests
| where timestamp > ago(1h)
| summarize ErrorRate = 100.0 * countif(success == false) / count() by bin(timestamp, 5m)
| render timechart
```

### 6.2 Alerts

```bash
# Create alert for high error rate
az monitor metrics alert create \
  --name alert-avatar-error-rate \
  --resource-group rg-avatar-prod \
  --scopes /subscriptions/YOUR_SUB_ID/resourceGroups/rg-avatar-prod/providers/Microsoft.Web/sites/app-avatar-api-prod \
  --condition "avg requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group YOUR_ACTION_GROUP_ID

# Create alert for high latency
az monitor metrics alert create \
  --name alert-avatar-latency \
  --resource-group rg-avatar-prod \
  --scopes /subscriptions/YOUR_SUB_ID/resourceGroups/rg-avatar-prod/providers/Microsoft.Web/sites/app-avatar-api-prod \
  --condition "avg requests/duration > 2000" \
  --window-size 5m \
  --evaluation-frequency 1m
```

---

## Phase 7: Testing

### 7.1 Health Check

```bash
# API health
curl https://app-avatar-api-prod.azurewebsites.net/api/avatar/health

# Expected: {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### 7.2 Load Testing

```bash
# Install Azure Load Testing CLI
az extension add --name load

# Run load test
az load test create \
  --name load-test-avatar \
  --resource-group rg-avatar-prod \
  --load-test-config-file loadtest.yaml
```

**loadtest.yaml:**
```yaml
version: 1.0
testName: Avatar API Load Test
testPlan: jmeter-test.jmx
engineInstances: 1
duration: 300
rampUpTime: 60
targetThroughput: 100
```

---

## Phase 8: CI/CD Pipeline

### 8.1 GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Avatar API

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0'

      - name: Restore dependencies
        run: dotnet restore

      - name: Build
        run: dotnet build --configuration Release --no-restore

      - name: Test
        run: dotnet test --no-build --verbosity normal

      - name: Publish
        run: dotnet publish -c Release -o ./publish

      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: app-avatar-api-prod
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: ./publish
```

---

## Cost Optimization Tips

1. **Use consumption tiers** where possible
2. **Enable auto-scaling** with aggressive scale-down
3. **Cache common responses** in Redis
4. **Use GPT-3.5 Turbo** for simple queries
5. **Implement response streaming** for better UX
6. **Set up lifecycle policies** for blob storage
7. **Monitor and optimize** OpenAI token usage

---

## Troubleshooting

### Issue: High latency

**Solution:**
- Enable Application Insights profiler
- Check OpenAI response times
- Verify network connectivity
- Review database query performance

### Issue: Authentication failures

**Solution:**
- Verify Key Vault permissions
- Check managed identity configuration
- Review AAD B2C settings
- Validate JWT tokens

### Issue: SignalR disconnections

**Solution:**
- Increase SignalR capacity
- Enable sticky sessions
- Check firewall rules
- Review CORS configuration

---

## Next Steps

1. **Production Testing**: User acceptance testing
2. **Performance Tuning**: Optimize based on real usage
3. **Feature Enhancement**: Add new capabilities
4. **Multi-region**: Deploy to additional regions
5. **Analytics**: Set up business intelligence dashboards

---

**Deployment Checklist:**

- [ ] All Azure resources created
- [ ] Secrets stored in Key Vault
- [ ] Managed identities configured
- [ ] Application deployed and running
- [ ] Copilot Studio configured
- [ ] Frontend deployed
- [ ] Authentication working
- [ ] Monitoring and alerts set up
- [ ] Load testing completed
- [ ] CI/CD pipeline configured
- [ ] Documentation updated
- [ ] Team trained

---

**Last Updated**: 2025-11-17
