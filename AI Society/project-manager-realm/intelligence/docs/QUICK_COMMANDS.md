# Quick Commands Reference

**Location:** `/Users/venkateshk/Projects/AI Society/project-manager-realm/intelligence/service`

All commands should be run from the `intelligence/service` directory.

---

## 📁 Setup (Do This First)

```bash
# Navigate to service directory
cd /Users/venkateshk/Projects/AI\ Society/project-manager-realm/intelligence/service

# Verify you're in the right place
pwd
# Should show: /Users/venkateshk/Projects/AI Society/project-manager-realm/intelligence/service
```

---

## 🔨 Build Commands

### Build (Using Cache - Fast)
```bash
docker-compose build intelligence
```
**Usage:** Regular builds when you've made code changes  
**Speed:** 30-60 seconds (uses cached layers)  
**Output:** Shows build progress

**Expected Output:**
```
[+] Building 4.0s (15/15) FINISHED
 => [internal] load local bake definitions
 => [6/8] COPY . .
 => [7/8] RUN if [ ! -d /app/app/agents ]...
 => [8/8] RUN useradd -m -u 1000 appuser...
 => naming to docker.io/library/service-intelligence:latest
service-intelligence  Built
```

---

### Build with No Cache (Fresh Build)
```bash
docker-compose build --no-cache intelligence
```
**Usage:** When cache might be stale or for clean rebuild  
**Speed:** 2-5 minutes (rebuilds everything)  
**Output:** Rebuilds all layers from scratch

**Expected Output:**
```
[+] Building 4.6s (16/16) FINISHED
 => [internal] load metadata for docker.io/library/python:3.11-slim
 => [1/8] FROM docker.io/library/python:3.11-slim@sha256:...
 => [2/8] WORKDIR /app
 => [3/8] RUN apt-get update && apt-get install -y...
 => [4/8] COPY requirements.txt .
 => [5/8] RUN pip install --no-cache-dir -r requirements.txt
 => [6/8] COPY . .
 => [7/8] RUN if [ ! -d /app/app/agents ]...
 => [8/8] RUN useradd -m -u 1000 appuser...
 => naming to docker.io/library/service-intelligence:latest
service-intelligence  Built
```

**When to Use:**
- After updating Python version
- After changing base image
- When dependencies seem wrong
- "Try a clean build" troubleshooting

---

## ▶️ Start Commands

### Start All Services
```bash
docker-compose up
```
**Usage:** Start everything (PostgreSQL, Kafka, Intelligence Service, pgAdmin)  
**What Starts:**
- PostgreSQL database (port 5432)
- Kafka broker (port 9092)
- Intelligence Service (port 8003)
- pgAdmin (port 5050)

**Expected Output:**
```
[+] Running 4/4
 ✓ Container intelligence-postgres    Started
 ✓ Container intelligence-kafka       Started
 ✓ Container intelligence-service     Started
 ✓ Container intelligence-pgadmin     Started
```

**Access Points:**
```
Intelligence Service: http://localhost:8003
pgAdmin:             http://localhost:5050
PostgreSQL:          localhost:5432
Kafka:               localhost:9092
```

---

### Start Specific Service
```bash
docker-compose up intelligence
```
**Usage:** Start only Intelligence Service (assumes DB/Kafka already running)  
**Speed:** 3-5 seconds

```bash
docker-compose up postgres
```
**Usage:** Start only PostgreSQL

```bash
docker-compose up kafka
```
**Usage:** Start only Kafka

---

### Start in Background (Detached Mode)
```bash
docker-compose up -d
```
**Usage:** Start services without blocking terminal  
**Benefit:** Terminal stays available for other commands

**To check if running:**
```bash
docker-compose ps
```

---

## 🛑 Stop Commands

### Stop All Services Gracefully
```bash
docker-compose stop
```
**Usage:** Stop running services cleanly  
**Speed:** 10-15 seconds  
**Data:** Preserved (nothing deleted)

**Expected Output:**
```
[+] Stopping 4/4
 ✓ Container intelligence-service    Stopped
 ✓ Container intelligence-kafka      Stopped
 ✓ Container intelligence-postgres   Stopped
 ✓ Container intelligence-pgadmin    Stopped
```

---

### Stop & Remove Containers
```bash
docker-compose down
```
**Usage:** Stop and remove all containers (but keep volumes/data)  
**Speed:** 10-15 seconds  
**Data:** Database data persists (stored in volumes)

**Expected Output:**
```
[+] Running 1/0
 ✓ Network intelligence_default  Removed
```

---

### Stop & Remove Everything (Including Data)
```bash
docker-compose down -v
```
**Usage:** Complete cleanup (removes volumes too)  
**⚠️ WARNING:** Deletes all database data!  
**Use Case:** Fresh start, clean slate

**Data Lost:**
- All conversations deleted
- All messages deleted
- All workspaces deleted

---

### Stop Single Service
```bash
docker-compose stop intelligence
```
**Usage:** Stop just the Intelligence Service

---

## 📋 View Logs

### View Logs Live (Follow Mode)
```bash
docker-compose logs -f intelligence
```
**Usage:** Watch logs in real-time as they happen  
**Exit:** Press `Ctrl+C` to stop following

**What You See:**
```
intelligence-service  | {"message": "gemini_generate_start"...
intelligence-service  | {"message": "prompt_rendered"...
intelligence-service  | {"message": "gemini_generate_success"...
```

---

### View Live Logs with Last N Lines
```bash
docker-compose logs -f --tail 50 intelligence
```
**Usage:** Show last 50 lines and follow  
**Default:** Shows last 100 lines  
**Options:** `--tail 20`, `--tail 100`, `--tail 200`

---

### View All Service Logs Live
```bash
docker-compose logs -f
```
**Usage:** View all services together (color-coded)  
**Output:** Mix of PostgreSQL, Kafka, and Intelligence logs

---

### View Logs with Timestamps
```bash
docker-compose logs -f -t intelligence
```
**Usage:** Add timestamps to each log line

**Example:**
```
2026-01-08T16:30:45.123456Z intelligence-service | {"message": "gemini_generate_start"...
2026-01-08T16:30:50.456789Z intelligence-service | {"message": "gemini_generate_success"...
```

---

### View Past Logs (Not Live)
```bash
docker-compose logs intelligence
```
**Usage:** Show all logs (doesn't follow)  
**Output:** Entire log history for service

---

### View Logs for Single Line Events
```bash
docker-compose logs -f intelligence | grep "error"
```
**Usage:** Live logs filtered for "error"  
**Exit:** Press `Ctrl+C`

**Other Filters:**
```bash
docker-compose logs -f intelligence | grep "gemini"
docker-compose logs -f intelligence | grep "success"
docker-compose logs -f intelligence | grep "clarification"
```

---

### View Logs with Color
```bash
docker-compose logs -f --no-log-prefix intelligence
```
**Usage:** Remove timestamp/service prefix for cleaner output

---

## 🔄 Common Workflows

### Full Restart (Clean State)
```bash
# 1. Stop everything
docker-compose stop

# 2. Start everything
docker-compose up

# 3. Watch logs
docker-compose logs -f intelligence
```

**Time:** ~20 seconds

---

### Rebuild & Restart
```bash
# 1. Rebuild
docker-compose build intelligence

# 2. Stop old container
docker-compose stop intelligence

# 3. Start new container
docker-compose up -d intelligence

# 4. Check logs
docker-compose logs -f intelligence
```

**Time:** 1-2 minutes

---

### Clean Rebuild & Restart
```bash
# 1. Clean build
docker-compose build --no-cache intelligence

# 2. Stop
docker-compose stop intelligence

# 3. Start
docker-compose up -d intelligence

# 4. Tail logs
docker-compose logs -f --tail 20 intelligence
```

**Time:** 3-5 minutes

---

### Debug Service Issues
```bash
# 1. Check if running
docker-compose ps

# 2. View recent logs
docker-compose logs --tail 50 intelligence

# 3. Watch live logs
docker-compose logs -f intelligence

# 4. Filter for errors
docker-compose logs -f intelligence | grep -i error

# 5. If still broken, clean restart
docker-compose stop intelligence
docker-compose build --no-cache intelligence
docker-compose up intelligence
```

---

## 🧹 Maintenance Commands

### Check Status of All Services
```bash
docker-compose ps
```
**Expected Output:**
```
NAME                           STATUS              PORTS
intelligence-service          Up 5 minutes        0.0.0.0:8003->8003/tcp
intelligence-postgres         Up 5 minutes        0.0.0.0:5432->5432/tcp
intelligence-kafka            Up 5 minutes        0.0.0.0:9092->9092/tcp
intelligence-pgadmin          Up 5 minutes        0.0.0.0:5050->5050/tcp
```

---

### Check Disk Usage
```bash
docker system df
```
**Usage:** See how much space Docker is using

---

### Clean Up Unused Images/Containers
```bash
docker system prune
```
**Usage:** Remove stopped containers and unused images  
**⚠️ WARNING:** Removes data from other projects too!

---

### View Service Configuration
```bash
docker-compose config
```
**Usage:** See resolved docker-compose configuration

---

## 🧪 Test Commands

### Test Clarification Agent
```bash
curl -X POST 'http://localhost:8003/api/v1/agents/clarify?user_description=Build%20a%20mobile%20app&project_context=Fintech' | jq .
```

### Test PRD Generator
```bash
curl -X POST 'http://localhost:8003/api/v1/agents/generate-prd' \
  -H 'Content-Type: application/json' \
  -d '{"requirement_description":"Build mobile app","clarification_answers":[]}' | jq .
```

### Test Analysis Agent
```bash
curl -X POST 'http://localhost:8003/api/v1/agents/analyze' \
  -H 'Content-Type: application/json' \
  -d '{"requirements":{"title":"Mobile App"},"analysis_depth":"standard"}' | jq .
```

### Check Health Endpoint
```bash
curl -s http://localhost:8003/health | jq .
```

### View Database via pgAdmin
```
URL: http://localhost:5050
Email: admin@example.com
Password: admin
```

---

## ⚡ Quick Copy-Paste Commands

**Start everything:**
```bash
cd /Users/venkateshk/Projects/AI\ Society/project-manager-realm/intelligence/service && docker-compose up
```

**Stop everything:**
```bash
cd /Users/venkateshk/Projects/AI\ Society/project-manager-realm/intelligence/service && docker-compose stop
```

**View logs live:**
```bash
cd /Users/venkateshk/Projects/AI\ Society/project-manager-realm/intelligence/service && docker-compose logs -f intelligence
```

**Rebuild & restart:**
```bash
cd /Users/venkateshk/Projects/AI\ Society/project-manager-realm/intelligence/service && docker-compose build intelligence && docker-compose restart intelligence && docker-compose logs -f intelligence
```

**Clean rebuild & restart:**
```bash
cd /Users/venkateshk/Projects/AI\ Society/project-manager-realm/intelligence/service && docker-compose build --no-cache intelligence && docker-compose restart intelligence && sleep 3 && docker-compose logs -f intelligence
```

---

## 📝 Notes

### Directory Structure
```
/Users/venkateshk/Projects/AI Society/project-manager-realm/
  └── intelligence/service/
       ├── docker-compose.yml          (Main config)
       ├── docker-compose.override.yml (Dev overrides)
       ├── .env                        (Environment variables)
       ├── Dockerfile                  (Intelligence service image)
       ├── requirements.txt            (Python dependencies)
       └── app/                        (Service code)
```

### Key Ports
```
Intelligence Service: 8003
pgAdmin:             5050
PostgreSQL:          5432
Kafka:               9092
```

### Environment File (.env)
```
DATABASE_URL=postgresql+asyncpg://intelligence:dev_password@localhost:5432/intelligence
KAFKA_BROKERS=localhost:9092
GEMINI_API_KEY=<your-key>
```

### Common Issues

**"Port already in use"**
```bash
# Kill process on port 8003
lsof -ti:8003 | xargs kill -9

# Then restart
docker-compose up
```

**"Connection refused"**
```bash
# Services might not be ready yet
# Wait 10 seconds and try again
sleep 10
docker-compose logs intelligence
```

**"Database connection failed"**
```bash
# PostgreSQL might not be fully initialized
# Restart database
docker-compose stop postgres
docker-compose up postgres
# Wait 30 seconds
sleep 30
docker-compose up intelligence
```

---

**Last Updated:** January 8, 2026  
**Status:** Current & Tested  
**All Services:** ✅ Running
