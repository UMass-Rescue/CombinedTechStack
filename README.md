# Combined Server, Client, and Microservices

This repository contains the combined code for the frontend, server, and both training+prediction microservices.

## Setup

The setup of the new combined repository is very simple. First, delete any existing containers and volumes
from any previous installations of the server or microservices.

To run this repository, follow the following steps:

### Installation Step 1: Install Docker

Install Docker Desktop and ensure that Docker is running on your computer.

[Install Docker Desktop Here](https://www.docker.com/products/docker-desktop)

Now, open the root folder of this repository in the command line.

### Installation Step 2: Build Project Containers

Run the command `docker-compose build`

## Running the Application

### Start Application

Run the command `docker-compose up`

### Stop Application

Run the command `docker-compose down`

## API Access

If you would like to interact with the API, download the collection on Postman for easy testing

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/12863615-83efc5d6-55dd-46f7-a2b4-ff972d5e244d?action=collection%2Ffork&collection-url=entityId%3D12863615-83efc5d6-55dd-46f7-a2b4-ff972d5e244d%26entityType%3Dcollection%26workspaceId%3D0882ea33-df4c-4df8-87c2-056554e228b7#?env%5BCombined%20Tech%20Stack%20Development%20Environment%5D=W3sia2V5IjoiYXV0aF90b2tlbiIsInZhbHVlIjoiIiwiZW5hYmxlZCI6dHJ1ZX0seyJrZXkiOiJhcGlfa2V5IiwidmFsdWUiOiIiLCJlbmFibGVkIjp0cnVlfSx7ImtleSI6ImJhc2VVcmwiLCJ2YWx1ZSI6Imh0dHA6Ly9sb2NhbGhvc3Q6NTAwMCIsImVuYWJsZWQiOnRydWV9XQ==)