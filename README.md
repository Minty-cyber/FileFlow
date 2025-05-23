# Installation Guide

This guide will walk you through setting up FileFlow on your local machine using Docker.

## Prerequisites

Before you begin, ensure you have:
- A computer running Windows 10/11, macOS, or Linux
- Administrative/sudo privileges on your machine
- Internet connection and enough available disk space for downloading Docker and project dependencies

## Step 1: Install Docker

### Windows

1. **Download Docker Desktop**
   - Visit [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - Click "Download for Windows"
   - Run the installer and follow the setup wizard

2. **Enable WSL 2 (if prompted)**
   - Docker Desktop may require Windows Subsystem for Linux 2
   - Follow the prompts to install WSL 2 if needed

3. **Verify Installation**
   ```bash
   docker --version
   docker-compose --version
   ```

### macOS

1. **Download Docker Desktop**
   - Visit [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - Choose the appropriate version for your Mac (Intel or Apple Silicon)
   - Install the .dmg file by dragging Docker to Applications

2. **Start Docker Desktop**
   - Launch Docker Desktop from Applications
   - Complete the initial setup

3. **Verify Installation**
   ```bash
   docker --version
   docker-compose --version
   ```

### Linux (Ubuntu/Debian)

1. **Update package index**
   ```bash
   sudo apt update
   ```

2. **Install required packages**
   ```bash
   sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release
   ```

3. **Add Docker's official GPG key**
   ```bash
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   ```

4. **Add Docker repository**
   ```bash
   echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

5. **Install Docker Engine**
   ```bash
   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
   ```

6. **Add your user to the docker group**
   ```bash
   sudo usermod -aG docker $USER
   ```
   
7. **Log out and back in** for group changes to take effect

8. **Verify Installation**
   ```bash
   docker --version
   docker compose version
   ```

### Linux (CentOS/RHEL/Fedora)

1. **Install Docker using package manager**
   ```bash
   # For CentOS/RHEL
   sudo yum install -y docker docker-compose
   
   # For Fedora
   sudo dnf install -y docker docker-compose
   ```

2. **Start and enable Docker service**
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Add your user to the docker group**
   ```bash
   sudo usermod -aG docker $USER
   ```

4. **Log out and back in** for group changes to take effect

5. **Verify Installation**
   ```bash
   docker --version
   docker-compose --version
   ```

## Step 2: Get the Project

1. **Clone the repository**
   ```bash
   git clone https://github.com/Minty-cyber/FileFlow.git
   cd FileFlow
   ```

   Or download and extract the project files to your desired directory.

2. **Navigate to the project directory**
   ```bash
   cd FileFlow
   ```

## Step 3: Configure Environment (if applicable)

1. **Create and edit configuration**
   -  Create a `.env` file 
   - Open `.env` file in your preferred text editor
   - Update any required configuration values
   - Save the file

## Step 4: Run the Application

1. **Start the application**
   ```bash
   docker compose up
   ```

   This command will:
   - Download required Docker images
   - Build your application containers
   - Start all services defined in `docker-compose.yml`

2. **Run in background (optional)**
   ```bash
   docker compose up -d
   ```
   Use the `-d` flag to run containers in detached mode (in the background).

3. **View logs (if running in background)**
   ```bash
   docker compose logs -f
   ```

## Step 5: Verify Installation

1. **Check running containers**
   ```bash
   docker compose ps
   ```

2. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:8080/docs`
   - You should see a swagger api documentation of the project

## Managing the Application

### Stop the application
```bash
docker compose down
```

### Restart the application
```bash
docker compose restart
```

### Update and rebuild
```bash
docker compose down
docker compose up --build
```

### View application logs
```bash
docker compose logs
```

## Troubleshooting

### Common Issues

**Docker daemon not running**
- **Windows/macOS**: Start Docker Desktop application
- **Linux**: Run `sudo systemctl start docker`

**Permission denied errors**
- Ensure your user is in the docker group
- Log out and back in after adding user to group
- On Linux, you may need to run `newgrp docker`

**Port already in use**
- Check if another application is using the required port
- Stop conflicting services or change port in configuration

**Out of disk space**
- Clean up unused Docker images: `docker system prune`
- Remove unused volumes: `docker volume prune`

### Getting Help

If you encounter issues:
1. Check the project's GitHub issues page
2. Review Docker logs: `docker compose logs`
3. Ensure all prerequisites are met
4. Contact [SUPPORT_CONTACT] for additional support

## Next Steps

Once installation is complete:
- Review the [User Guide](link-to-user-guide)
- Check out the [API Documentation](link-to-api-docs)
- Explore [Configuration Options](link-to-config-docs)
---