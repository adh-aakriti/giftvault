# giftvault

A personal gift-idea notebook. Save links and notes about people through the year, tag them, give each idea a priority, and see how many days are left until the next occasion.

Built for Individual Assignment 1 (SWD) as one Flask app, and split for Individual Assignment 2 ("Split, Ship and Operate Your Application") into two services and a static UI that run on Azure.

**Live system:** https://aadhikariieu2024ui.z28.web.core.windows.net/

The first request after a quiet period can take up to about a minute. The services scale to zero and the serverless database pauses, so the page shows a "waking up" notice while it retries.

## What it is made of

| Part | What it does | Address on Azure |
|---|---|---|
| UI (`ui/`) | Static page on an Azure Storage static website. It calls both services. | https://aadhikariieu2024ui.z28.web.core.windows.net/ |
| Ideas service (`services/ideas`) | Owns people, ideas, priorities and tags. Own SQL Server database and login. | https://aadhikari-ieu2024-ideas.delightfulglacier-c28718af.francecentral.azurecontainerapps.io/ |
| Occasions service (`services/occasions`) | Owns dates worth remembering and the countdown. Own database and login. Asks Ideas for each person's name and idea count. | https://aadhikari-ieu2024-occasions.delightfulglacier-c28718af.francecentral.azurecontainerapps.io/ |

There is no login. The UI creates a random visitor id, keeps it in the browser's localStorage and sends it as the `X-User-Id` header. Every row is filtered by that id. Each service describes its API in `services/<name>/openapi.yaml`, and `system.yaml` describes the whole system (checked against `system.schema.json` in CI).

If the Ideas service cannot be reached, Occasions still answers reads, marked `degraded: true` with the name and idea count empty, and refuses to create an occasion with 503. ADR-6 gives the reasoning.

## Requirements

Docker with Compose. Nothing else is needed to run or test the system locally. The SQL Server image is `linux/amd64`, so on Apple silicon it runs under emulation and the first start is slower.

## Running locally with compose

```
git clone https://github.com/adh-aakriti/giftvault
cd giftvault
cp .env.example .env
docker compose up --build
```

`.env.example` holds placeholder passwords for local development only. Copy it to `.env` and edit the values if you like. `.env` stays on your machine.

The first start takes a minute or two: SQL Server starts, `db-init` creates the two databases and their logins, then each service applies its migrations and starts.

| Address | What |
|---|---|
| http://localhost:8080 | UI (nginx serving `ui/`) |
| http://localhost:8001/health | Ideas service |
| http://localhost:8002/health | Occasions service |

Stop it with `docker compose down`. Add `-v` to also delete the database volume.

### Running a single service

```
docker compose up --build ideas
docker compose up --build occasions
```

Compose starts SQL Server and `db-init` first, because the service depends on them. Occasions on its own still starts. Its calls to Ideas fail, so reading upcoming occasions comes back degraded and creating an occasion returns 503.

### Configuration

Every setting is an environment variable. Compose sets them for local use, and the deploy workflow sets them on Azure. `system.yaml` lists the full set for each service.

| Variable | Service | Purpose |
|---|---|---|
| `DATABASE_URL` | both | `mssql://<user>:<password>@<host>:1433/<database>`. A secret on Azure. |
| `PORT` | both | Port the container listens on. `8000` in the compose file and on Azure. |
| `UI_ORIGIN` | both | The one origin allowed by CORS. `http://localhost:8080` locally, the storage website on Azure. |
| `IDEAS_URL` | Occasions | Base URL of the Ideas service. `http://ideas:8000` in compose. |
| `DB_CONNECT_RETRY_S` | both | How long to keep retrying the database connection at startup. Default 90 seconds, which covers a paused serverless database resuming. |

The image also carries the git SHA it was built from (`GIT_SHA` build argument). `/health` reports it as `version`.

## Database migrations

Each service keeps numbered SQL files in `services/<name>/migrations/` and applies them itself at startup, in order, each once, recording the file name in a `schema_migrations` table. An applied file is never edited. A new change is a new file. Starting again applies nothing, and each applied file prints `migration applied: <file>` in the service log. For example, `002_add_idea_priority.sql` adds `ideas.priority` with a default, so existing ideas keep their rows. ADR-7 explains the choice and the recovery plan.

## Running the tests

The tests need a real SQL Server. These are the commands CI runs, for Ideas and then Occasions:

```
export COMPOSE_PROJECT_NAME=giftvault
cp .env.example .env
docker compose run --rm db-init
set -a; . ./.env; set +a

docker run --rm --network giftvault_default \
  -v "$PWD/services/ideas:/app" -w /app \
  -e DATABASE_URL="mssql://ideas_user:${IDEAS_PWD}@sqlserver:1433/ideas" \
  python:3.12-slim \
  sh -c "pip install -q -r requirements-dev.txt && pytest --cov=app --cov-report=term-missing --cov-fail-under=70"

docker run --rm --network giftvault_default \
  -v "$PWD/services/occasions:/app" -w /app \
  -e DATABASE_URL="mssql://occasions_user:${OCCASIONS_PWD}@sqlserver:1433/occasions" \
  python:3.12-slim \
  sh -c "pip install -q -r requirements-dev.txt && pytest --cov=app --cov-report=term-missing --cov-fail-under=70"
```

Each run prints the coverage table with the missing lines and fails below 70%. Tests that need the database skip themselves when `DATABASE_URL` is not set. The cross-seam tests in the Occasions suite replace the Ideas client with a stub that can answer ok, person missing or down. ADR-9 says what is and is not tested.

## How deployment works

Only the pipeline changes anything on Azure. Two workflows in `.github/workflows/` do it:

1. **`ci.yml`** runs on every push and pull request.
   - `lint` runs ruff on both services.
   - `validate` checks `system.yaml` against `system.schema.json` and each `openapi.yaml` against the OpenAPI specification.
   - `test` runs each service's tests against a real SQL Server with the 70% coverage gate.
   - `smoke` starts both real services from compose, creates a person, an idea and an occasion through their APIs, and checks that `/upcoming` returns the name and idea count with `degraded` false.
   - `images` builds both images, and on `main` pushes them to GitHub Container Registry tagged with the commit SHA (`ghcr.io/adh-aakriti/giftvault-ideas:<sha>` and `giftvault-occasions:<sha>`). It needs all four jobs above.
2. **`cd.yml`** runs after CI on `main`. It signs in to Azure with OIDC as a managed identity, points both Container Apps at the images for that SHA, sets their environment variables and database secret, waits until `/health` on both services reports the new SHA, and uploads `ui/` to the storage website with a generated `ui/config.js` that holds the two service addresses.

No Azure password is stored anywhere. The identity has Contributor on the resource group only, and is trusted only for runs on `main` of this repository.

Azure resources, all in the resource group `rg-aadhikari-ieu2024` in France Central, all pay per use:

- Container Apps environment `aadhikari-ieu2024-env` with two apps, `aadhikari-ieu2024-ideas` and `aadhikari-ieu2024-occasions` (minimum 0 and maximum 1 replica, 0.25 vCPU, 0.5 Gi)
- SQL server `aadhikari-ieu2024-sql` with two serverless databases on the free offer, `aadhikari-ieu2024-ideas-db` and `aadhikari-ieu2024-occasions-db`
- storage account `aadhikariieu2024ui` with the static website
- managed identity `aadhikari-ieu2024-github`
- the Log Analytics workspace that Azure creates with the environment

ADR-8 gives the cost model and what scale to zero means for the containers and the database.

## Reproducing the initial Azure setup

These are the commands that were run once, in Azure Cloud Shell (Bash). Passwords are generated into private files and never printed or committed. Replace `<subscription-id>` with your own.

```
# 1. Select the subscription
az account set --subscription "<subscription-id>"
az account show -o table

# 2. Providers (one-off, takes a few minutes)
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Sql
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.ManagedIdentity

# 3. Allowed regions for this subscription (France Central was chosen)
az policy assignment list --query "[?contains(displayName,'Allowed resource deployment regions')].parameters.listOfAllowedLocations.value" -o json

# 4. Resource group and the UI storage account (static website)
PREFIX="aadhikari-ieu2024"; LOCATION="francecentral"; RG="rg-$PREFIX"
UI_STORAGE="$(echo "$PREFIX" | tr -d '-')ui"
az group create --name "$RG" --location "$LOCATION"
az storage account create --name "$UI_STORAGE" --resource-group "$RG" --location "$LOCATION" --sku Standard_LRS --kind StorageV2
az storage blob service-properties update --account-name "$UI_STORAGE" --static-website --index-document index.html
az storage account show --name "$UI_STORAGE" --resource-group "$RG" --query "primaryEndpoints.web" -o tsv

# 5. SQL server and two serverless databases on the free offer
SQL_SERVER="$PREFIX-sql"; SQL_ADMIN="sqladmin"
SQL_ADMIN_PWD="$(openssl rand -base64 24 | tr -d '/+=')Aa1!"
echo "$SQL_ADMIN_PWD" > ~/.sqladmin_pwd && chmod 600 ~/.sqladmin_pwd
az sql server create --name "$SQL_SERVER" --resource-group "$RG" --location "$LOCATION" --admin-user "$SQL_ADMIN" --admin-password "$SQL_ADMIN_PWD"
az sql server firewall-rule create --resource-group "$RG" --server "$SQL_SERVER" --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
az sql db create --resource-group "$RG" --server "$SQL_SERVER" --name "$PREFIX-ideas-db" --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1 --min-capacity 0.5 --backup-storage-redundancy Local --use-free-limit true --free-limit-exhaustion-behavior AutoPause
az sql db create --resource-group "$RG" --server "$SQL_SERVER" --name "$PREFIX-occasions-db" --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1 --min-capacity 0.5 --backup-storage-redundancy Local --use-free-limit true --free-limit-exhaustion-behavior AutoPause

# 6. sqlcmd (not installed in Cloud Shell)
mkdir -p ~/bin && cd ~/bin && curl -sL https://github.com/microsoft/go-sqlcmd/releases/latest/download/sqlcmd-linux-amd64.tar.bz2 | tar xj && cd ~
export PATH="$HOME/bin:$PATH"

# 7. One contained user per database, able to run migrations in its own database only
SQL_HOST="$SQL_SERVER.database.windows.net"
IDEAS_PWD="$(openssl rand -base64 24 | tr -d '/+=')Aa1!"
OCCASIONS_PWD="$(openssl rand -base64 24 | tr -d '/+=')Aa1!"
echo "$IDEAS_PWD" > ~/.ideas_pwd; echo "$OCCASIONS_PWD" > ~/.occasions_pwd
chmod 600 ~/.ideas_pwd ~/.occasions_pwd
sqlcmd -S "$SQL_HOST" -d "$PREFIX-ideas-db" -U "$SQL_ADMIN" -P "$SQL_ADMIN_PWD" -Q "CREATE USER ideas_user WITH PASSWORD = '$IDEAS_PWD'; ALTER ROLE db_ddladmin ADD MEMBER ideas_user; ALTER ROLE db_datareader ADD MEMBER ideas_user; ALTER ROLE db_datawriter ADD MEMBER ideas_user;"
sqlcmd -S "$SQL_HOST" -d "$PREFIX-occasions-db" -U "$SQL_ADMIN" -P "$SQL_ADMIN_PWD" -Q "CREATE USER occasions_user WITH PASSWORD = '$OCCASIONS_PWD'; ALTER ROLE db_ddladmin ADD MEMBER occasions_user; ALTER ROLE db_datareader ADD MEMBER occasions_user; ALTER ROLE db_datawriter ADD MEMBER occasions_user;"

# 8. Container Apps environment and the two apps, started on a placeholder image
az extension add --name containerapp --upgrade -y
ENV="$PREFIX-env"
az containerapp env create --name "$ENV" --resource-group "$RG" --location "$LOCATION"
IDEAS_URL_DB="mssql://ideas_user:$(cat ~/.ideas_pwd)@$SQL_HOST:1433/$PREFIX-ideas-db"
az containerapp create --name "$PREFIX-ideas" --resource-group "$RG" --environment "$ENV" --image mcr.microsoft.com/k8se/quickstart:latest --target-port 80 --ingress external --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi --secrets "database-url=$IDEAS_URL_DB"
OCC_URL_DB="mssql://occasions_user:$(cat ~/.occasions_pwd)@$SQL_HOST:1433/$PREFIX-occasions-db"
az containerapp create --name "$PREFIX-occasions" --resource-group "$RG" --environment "$ENV" --image mcr.microsoft.com/k8se/quickstart:latest --target-port 80 --ingress external --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi --secrets "database-url=$OCC_URL_DB"

# 9. The pipeline's identity (managed identity trusted through OIDC)
SUB="<subscription-id>"
az identity create --name "$PREFIX-github" --resource-group "$RG" --location "$LOCATION"
PRINCIPAL_ID="$(az identity show --name "$PREFIX-github" --resource-group "$RG" --query principalId -o tsv)"
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal --role Contributor --scope "/subscriptions/$SUB/resourceGroups/$RG"
az identity federated-credential create --name github-main --identity-name "$PREFIX-github" --resource-group "$RG" --issuer https://token.actions.githubusercontent.com --subject "repo:adh-aakriti/giftvault:ref:refs/heads/main" --audiences api://AzureADTokenExchange
# GitHub may send the subject with numeric ids, so a second credential covers that form
az identity federated-credential create --name github-main-id --identity-name "$PREFIX-github" --resource-group "$RG" --issuer https://token.actions.githubusercontent.com --subject "repo:adh-aakriti@208366594/giftvault@1378591685:ref:refs/heads/main" --audiences api://AzureADTokenExchange

# 10. Reader access for the professors
az role assignment create --assignee amartini@faculty.ie.edu --role Reader --scope "/subscriptions/$SUB/resourceGroups/$RG"
az role assignment create --assignee bserra@faculty.ie.edu --role Reader --scope "/subscriptions/$SUB/resourceGroups/$RG"

# 11. GitHub secrets and variables (values read from Azure and the private files, never printed)
gh auth login
REPO="adh-aakriti/giftvault"
gh secret set AZURE_CLIENT_ID --repo "$REPO" --body "$(az identity show --name "$PREFIX-github" --resource-group "$RG" --query clientId -o tsv)"
gh secret set AZURE_TENANT_ID --repo "$REPO" --body "$(az account show --query tenantId -o tsv)"
gh secret set AZURE_SUBSCRIPTION_ID --repo "$REPO" --body "$(az account show --query id -o tsv)"
gh secret set IDEAS_DB_PASSWORD --repo "$REPO" --body "$(cat ~/.ideas_pwd)"
gh secret set OCCASIONS_DB_PASSWORD --repo "$REPO" --body "$(cat ~/.occasions_pwd)"
gh variable set PREFIX --repo "$REPO" --body "$PREFIX"
gh variable set RESOURCE_GROUP --repo "$REPO" --body "$RG"
gh variable set UI_STORAGE --repo "$REPO" --body "aadhikariieu2024ui"
gh auth logout
```

After that:

- Merge to `main`. CI runs, then `cd.yml` replaces the placeholder image and sets the ingress port to 8000.
- The first deploy cannot pull a new package while it is private. Make both GHCR packages (`giftvault-ideas` and `giftvault-occasions`) public in their GitHub package settings, then re-run the failed job.
- From then on, only the pipeline changes anything.

To read the logs of a service: `az containerapp logs show --name aadhikari-ieu2024-ideas --resource-group rg-aadhikari-ieu2024 --follow`.

## Using it

1. Open the live URL (or http://localhost:8080 locally) and add a person.
2. Open that person and save an idea: a link, a note, or both, with optional comma-separated tags and a priority from 1 to 3.
3. Add an occasion for them, ticking "every year" for a birthday.
4. "Coming up" lists the occasions by how soon they are, with how many ideas are saved for each person.

## Project structure

```
ui/                       Static page, config.js for the service addresses
services/ideas/           Ideas service
services/occasions/       Occasions service
  app/                    Code, one module per concern
  migrations/             Numbered SQL files applied at startup
  tests/                  pytest suite
  openapi.yaml            API description
  Dockerfile
  requirements.txt        Runtime dependencies
  requirements-dev.txt    Test dependencies
db/init.sql               Local only: creates the two databases and logins
docker-compose.yml        Local stack: SQL Server, db-init, both services, UI
system.yaml               Description of the whole system
system.schema.json        Schema that system.yaml is checked against (provided)
.github/workflows/        ci.yml and cd.yml
.env.example              Placeholder settings for local use
ADR.md                    Architecture decision record
AI_USAGE.md               AI usage log
```
