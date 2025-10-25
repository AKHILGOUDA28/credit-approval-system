# Credit Approval System (Backend Assignment)

## Overview
A Django REST + PostgreSQL backend system for credit and loan approval, fully dockerized.

## Features
- Register new customers
- Calculate credit eligibility and score
- Create and manage loans
- View single or all loans per customer
- Dockerized setup (runs with one command)

## Tech Stack
- Python 3.11
- Django 4.2
- Django REST Framework
- PostgreSQL (Docker)
- Pandas (for optional Excel ingestion)

## Run Instructions
```bash
docker-compose up --build

## 🧩 API Endpoints

| HTTP Method | Endpoint | Description |
|--------------|-----------|-------------|
| **POST** | `/register` | Register a new customer |
| **POST** | `/check-eligibility` | Check loan eligibility |
| **POST** | `/create-loan` | Create and approve a new loan |
| **GET** | `/view-loan/<loan_id>` | View details of a loan |
| **GET** | `/view-loans/<customer_id>` | View all loans for a customer |

---

### 🔹 `/register`
**Method:** `POST`  
Registers a new customer and calculates approved limit.



