# Deployment Guide: Resume AI Tailor

This project is containerized using Docker, making it easy to deploy locally or to cloud platforms.

## 1. Prerequisites

- **Docker** and **Docker Compose** installed.
- **OpenAI API Key** (for Resume Tailoring).
- **Postgres** (handled by Docker Compose locally, or managed service for cloud).

## 2. Local Deployment (Docker Compose)

The easiest way to run the full stack (Frontend + Backend + Database) is via Docker Compose.

### Steps:
1. **Configure Environment**:
   Ensure you have a `.env` file in the root directory. You can copy the example:
   ```bash
   cp .env.example .env
   ```
   **Critical**: Update `.env` with your actual `OPENAI_API_KEY`.

2. **Build and Run**:
   ```bash
   docker compose up --build -d
   ```
   - `--build`: Rebuilds images to include latest changes.
   - `-d`: Runs in detached mode (background).

3. **Access the App**:
   - **Frontend (UI)**: [http://localhost:5173](http://localhost:5173) (or port 80 depending on mapping)
     - *Note*: The `docker-compose.yml` maps port `5173` to the container's port `80`.
   - **Backend (API)**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

4. **Stop**:
   ```bash
   docker compose down
   ```

## 3. Cloud Deployment (Render / Railway / AWS)

Since the project has `Dockerfile`s for both services, it is compatible with most PaaS providers.

### Option A: Railway / Render (Recommended for ease)
You will typically deploy two services (API and UI) and one Database.

#### 1. Database (PostgreSQL)
- Create a new PostgreSQL database service.
- Copy the `INTERNAL_DATABASE_URL` or connection string.

#### 2. Backend (API)
- **Source**: Connect your GitHub repo.
- **Root Directory**: `app` (Important! The Dockerfile is inside `app/`).
  - *Note*: If your provider doesn't support setting context root easily, you might need to move `Dockerfile` to root or configure "Build Context" to `.`.
  - **Correction**: The `app/Dockerfile` copies `requirements.txt`. If deploying from root repo:
    - Set **Root Directory** to `.`.
    - **Build Command**: `docker build -f app/Dockerfile .` (or let provider detect).
    - *Better approach for PaaS*: Most PaaS expect `Dockerfile` in root. You might need to adjust or specify path.
    - **Environment Variables**:
      - `DATABASE_URL`: (Paste from step 1)
      - `OPENAI_API_KEY`: (Your key)
      - `OPENAI_MODEL`: `gpt-4o-mini`
      - `PORT`: `8000`

#### 3. Frontend (UI)
- **Source**: Connect GitHub repo.
- **Root Directory**: `frontend`
- **Build Command**: `docker build -f frontend/Dockerfile .`
- **Environment Variables**:
  - `VITE_API_URL` (if your frontend needs to know backend URL at build time - though Nginx proxy handles relative `/api` calls).
  - Since we use Nginx proxy (`/api` -> backend), the frontend just talks to itself.
  - **CRITICAL**: For this Docker setup (`nginx.conf`), the Nginx container needs to reach the API.
  - In Docker Compose, `depends_on: api` handles DNS (`http://api:8000`).
  - In **Cloud (Render/Railway)**, services confuse this.
  - **Fix for Cloud**: You likely need to update `nginx.conf` or environment variable to point to the *public* or *private* URL of your deployed Backend service.
  - **Alternative**: Deploy Frontend as a "Static Site" (if using pure Vite build) and point API calls to Backend URL. But our Dockerfile uses Nginx.
  - **Recommended**: Deploy Frontend as a Docker service. Set an env var for the API proxy pass, or use a custom `nginx.conf.template` that substitutes the API URL at runtime.

### Option B: AWS EC2 / VM (Docker Compose)
1. SSH into your instance.
2. Clone repo.
3. Install Docker & Compose.
4. Create `.env`.
5. Run `docker compose up -d`.
6. (Optional) Set up a reverse proxy (Caddy/Traefik) or standard Nginx on host 80/443 to point to container ports.

## 4. AWS EC2 Deployment (Amazon Linux 2023)

We provide a helper script (`ops/setup_ec2.sh`) to automate the environment setup.

### Steps:

1.  **Launch Instance**:
    - Launch an EC2 instance using **Amazon Linux 2023** AMI.
    - Ensure Security Group allows ports: `22` (SSH), `80` (HTTP), `8000` (API).

2.  **Connect**:
    ```bash
    ssh -i your-key.pem ec2-user@your-ip-address
    ```

3.  **Setup Environment**:
    Run the following commands to install Docker and Git:
    ```bash
    # Install Git first to clone repo (or upload setup script manually)
    sudo dnf install -y git
    
    # Clone your repo
    git clone <YOUR_REPO_URL> resume-app
    cd resume-app
    
    # Run Setup Script
    chmod +x ops/setup_ec2.sh
    ./ops/setup_ec2.sh
    ```

4.  **Start Application**:
    *   **Log out** and **Log back in** (to apply Docker permissions).
    *   Create your `.env` file:
        ```bash
        cd resume-app
        cp .env.example .env
        nano .env  # Add your OPENAI_API_KEY
        ```
    *   Run Docker Compose:
        ```bash
        docker compose up --build -d
        ```

5.  **Access**:
    - Frontend: `http://<your-ec2-ip>`
    - API: `http://<your-ec2-ip>:8000/docs`

## 5. Maintenance

- **Backups**: Periodically backup your Postgres data volume (`pg` volume).
- **Updates**: `git pull` -> `docker compose up --build -d`.
