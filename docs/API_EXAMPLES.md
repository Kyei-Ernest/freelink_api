# FREELINK API Examples

Complete examples for common API workflows.

## Table of Contents
- [Authentication Flow](#authentication-flow)
- [Job Posting Flow](#job-posting-flow)
- [Freelancer Application Flow](#freelancer-application-flow)
- [Contract & Payment Flow](#contract--payment-flow)
- [Error Handling](#error-handling)

---

## Authentication Flow

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "full_name": "John Doe",
    "phone": "+233244123456",
    "country": "Ghana",
    "is_freelancer": true,
    "is_client": false
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_freelancer": true,
  "is_client": false,
  "token": "a1b2c3d4e5f6g7h8i9j0..."
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Response (200 OK):**
```json
{
  "token": "a1b2c3d4e5f6g7h8i9j0...",
  "user": {
    "id": 1,
    "email": "john@example.com",
    "full_name": "John Doe"
  }
}
```

### 3. Use Token in Requests

```bash
# All authenticated requests need the Authorization header
curl -X GET http://localhost:8000/api/profiles/me/ \
  -H "Authorization: Token a1b2c3d4e5f6g7h8i9j0..."
```

---

## Job Posting Flow

### 1. Create a Job (Client Only)

```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Authorization: Token your-client-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build an E-commerce Website",
    "description": "Looking for an experienced developer to build a modern e-commerce platform with payment integration, user authentication, and admin dashboard.",
    "budget": "2500.00",
    "duration": 30,
    "skills_required": ["Python", "Django", "React", "PostgreSQL"]
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "client": "jane@example.com",
  "title": "Build an E-commerce Website",
  "description": "Looking for an experienced developer...",
  "budget": "2500.00",
  "duration": 30,
  "status": "available",
  "skills_required": ["Python", "Django", "React", "PostgreSQL"],
  "created_at": "2026-01-16T12:00:00Z"
}
```

### 2. List Available Jobs (with Filtering)

```bash
# List all available jobs
curl -X GET "http://localhost:8000/api/jobs/?status=available" \
  -H "Authorization: Token your-token"

# Search by keyword
curl -X GET "http://localhost:8000/api/jobs/?search=python" \
  -H "Authorization: Token your-token"

# Order by budget (highest first)
curl -X GET "http://localhost:8000/api/jobs/?ordering=-budget" \
  -H "Authorization: Token your-token"
```

**Response (200 OK):**
```json
{
  "count": 15,
  "next": "http://localhost:8000/api/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Build an E-commerce Website",
      "budget": "2500.00",
      "status": "available"
    }
  ]
}
```

---

## Freelancer Application Flow

### 1. Submit a Proposal (Freelancer Only)

```bash
curl -X POST http://localhost:8000/api/proposals/ \
  -H "Authorization: Token your-freelancer-token" \
  -H "Content-Type: application/json" \
  -d '{
    "job": 1,
    "cover_letter": "I am excited about this project. With 5 years of Django experience and 20+ e-commerce projects, I can deliver a high-quality solution. I propose completing this in 25 days with the following milestones...",
    "proposed_rate": "2000.00",
    "estimated_duration": 25
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "job": 1,
  "freelancer": "john@example.com",
  "cover_letter": "I am excited about this project...",
  "proposed_rate": "2000.00",
  "estimated_duration": 25,
  "status": "submitted",
  "created_at": "2026-01-16T14:00:00Z"
}
```

### 2. Client Reviews Proposals

```bash
# List proposals for a job
curl -X GET "http://localhost:8000/api/proposals/?job=1" \
  -H "Authorization: Token your-client-token"
```

---

## Contract & Payment Flow

### 1. Create Contract (Client)

```bash
curl -X POST http://localhost:8000/api/contracts/contracts/ \
  -H "Authorization: Token your-client-token" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "freelancer_id": 2,
    "agreed_bid": "2000.00",
    "currency": "USD",
    "terms": {
      "deliverables": ["Responsive website", "Admin dashboard", "Documentation"],
      "revisions": 3
    },
    "milestones": [
      {
        "description": "Design mockups and wireframes",
        "amount": "400.00",
        "due_date": "2026-02-01T00:00:00Z"
      },
      {
        "description": "Frontend development",
        "amount": "600.00",
        "due_date": "2026-02-15T00:00:00Z"
      },
      {
        "description": "Backend & payment integration",
        "amount": "600.00",
        "due_date": "2026-02-25T00:00:00Z"
      },
      {
        "description": "Testing & deployment",
        "amount": "400.00",
        "due_date": "2026-03-01T00:00:00Z"
      }
    ]
  }'
```

### 2. Freelancer Accepts Contract

```bash
curl -X PATCH http://localhost:8000/api/contracts/contracts/{contract_id}/accept/ \
  -H "Authorization: Token your-freelancer-token"
```

### 3. Deposit to Escrow (Client)

```bash
curl -X POST http://localhost:8000/api/payments/deposit/ \
  -H "Authorization: Token your-client-token" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "2000.00",
    "currency": "USD"
  }'
```

**Response:**
```json
{
  "authorization_url": "https://checkout.paystack.com/xxx",
  "reference": "ref_123456"
}
```

### 4. Submit Work (Freelancer)

```bash
curl -X PATCH http://localhost:8000/api/contracts/contracts/{contract_id}/submit-work/ \
  -H "Authorization: Token your-freelancer-token"
```

### 5. Leave a Rating

```bash
curl -X POST http://localhost:8000/api/ratings/ \
  -H "Authorization: Token your-client-token" \
  -H "Content-Type: application/json" \
  -d '{
    "job": 1,
    "reviewee": 2,
    "rating": 5,
    "comment": "Excellent work! Delivered on time with great quality. Highly recommended!"
  }'
```

---

## Error Handling

### Common Error Responses

**400 Bad Request** - Validation Error
```json
{
  "email": ["This field is required."],
  "password": ["Password must be at least 8 characters."]
}
```

**401 Unauthorized** - Missing or Invalid Token
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden** - Permission Denied
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found** - Resource Not Found
```json
{
  "detail": "Not found."
}
```

**429 Too Many Requests** - Rate Limited
```json
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}
```

---

## Quick Reference: Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (Delete) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |
