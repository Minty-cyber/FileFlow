# FileFlow
This project is a full backend chat system that involves group chat messaging and private chat messaging. It uses:
- `Postgres` with `Alembic` for the `User Authentication` and `RBAC`
- `MonogoDB` with `Beanie` for the Chat and Messaging database,
- `Redis` for `PubSub` and `Caching` and maintaing messages during `offline state`,
- `uv` for package management,
- `docker` for containerisation
- `pytest` for unit testing 

# Installation Guide

This guide will walk you through setting up FileFlow on your local machine using Docker.

## Prerequisites

Before you begin, ensure you have:
- Have docker and python installed
- A thirst for programming.

## Get the Project

1. **Clone the repository**
   ```bash
   git clone https://github.com/Minty-cyber/FileFlow.git
   ```

2. **Navigate to the project directory**
   ```bash
   cd FileFlow
   ```

## Step 3: Configure Environment (if applicable)

1. **Create and edit configuration**
   -  Create a `.env` file 
   - Copy the contents of the  `.env.exmaple` and paste it in your `.env`
   

## Run the Application

**Start and build the application**
   ```bash
   docker compose up --build
   ```
**View logs (if running in background)**
   ```bash
   docker compose logs -f
   ```

**Access the application**
   - Open your web browser
   - Navigate to `http://localhost:8080/docs`
   - You should see a swagger api documentation of the project

