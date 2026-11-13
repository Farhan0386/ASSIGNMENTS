# Lab 4: Secure Connect and Communication Platform

**Student Name:** Farhan Hussain  
**Roll Number:** 2501730002  
**Program:** B.Tech CSE (AI/ML) - 3rd Semester, Section C  
**Course:** Web Dev III (Unit - 4)  
**Evaluation Marks:** 2.5

---

## 1. Project Overview

The **Secure Connect and Communication Platform** is a server-side Node.js and Express.js application demonstrating core backend security, stateless authentication, role-based access control (RBAC), event-driven logging, and real-time bidirectional communication without relying on pre-built authentication or chat frameworks.

---

## 2. Learning Objectives and Concepts Covered

- **Authentication and Authorization:** Custom signup and login workflows with input validation and credential verification.
- **Password Security:** One-way salted password hashing using `bcrypt`.
- **Stateless Session Management:** Generating and verifying signed JSON Web Tokens (`jsonwebtoken`) containing user identity and role metadata.
- **Protected Routes and RBAC:** Middleware guarding private endpoints (`403 Forbidden` when unauthenticated) and restricting administrative routes by user role.
- **Notes CRUD API:** Full Create, Read, Update, and Delete operations scoped strictly to the authenticated note owner.
- **Real-Time Communication:** Room-based WebSocket messaging (`general` room) using `Socket.IO`.
- **Event-Driven Architecture:** Decoupled audit logging for user and note lifecycle events via Node.js native `EventEmitter`.
- **Environment Configuration:** Managing server ports and JWT secrets securely via `dotenv`.

---

## 3. Technology Stack

- **Runtime:** Node.js
- **Web Framework:** Express.js
- **Authentication:** `jsonwebtoken` (JWT) and `bcrypt`
- **Real-Time Engine:** `socket.io` and `socket.io-client`
- **Configuration:** `dotenv`
- **Data Persistence:** In-memory store / MongoDB-compatible schema models (`User`, `Note`)

---

## 4. Folder Structure

```text
SeAssignement-4-cure Connect and Communication Platform/
├── config/
│   └── db.js                   # Database configuration module
├── events/
│   └── appEvents.js            # Node.js EventEmitter listeners for audit logs
├── middleware/
│   └── authMiddleware.js       # JWT verification and RBAC role authorization
├── models/
│   ├── User.js                 # User schema (username, email, hashed password, role)
│   └── Note.js                 # Note schema (title, content, owner, timestamps)
├── routes/
│   ├── authRoutes.js           # /api/auth/signup and /api/auth/login endpoints
│   └── noteRoutes.js           # Protected /api/notes CRUD and admin RBAC endpoints
├── screenshots/
│   ├── server-socket-output.jpg
│   └── api-test-output.png
├── .env                        # Environment variables (excluded from Git)
├── .gitignore                  # Ignores node_modules/ and .env
├── package.json                # Project dependencies and metadata
├── server.js                   # Express and Socket.IO HTTP server entry point
└── test.js                     # Automated offline API and Socket.IO test suite
```

---

## 5. Setup and Installation

### Install dependencies

```bash
npm install
```

### Configure environment variables

Create a `.env` file in the root directory:

```env
PORT=5000
MONGO_URI=mongodb://127.0.0.1:27017/secure_connect
JWT_SECRET=super_secret_webdev3_key_2026
```

### Start the server

Run in Terminal 1:

```bash
node server.js
```

Expected console output:

```text
[server] listening on http://localhost:5000
```

### Run the automated verification test

Run in Terminal 2:

```bash
node test.js
```

---

## 6. API Documentation

### Authentication Endpoints (`/api/auth`)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/signup` | No | Registers a new user with a bcrypt-hashed password (`201 Created`) |
| `POST` | `/api/auth/login` | No | Verifies credentials and issues a signed JWT (`200 OK`) |

### Sample signup request and response

Request (`POST /api/auth/signup`):

```json
{
  "username": "victor",
  "email": "victor@example.com",
  "password": "123456"
}
```

Response (`201 Created`):

```json
{
  "message": "User registered",
  "id": "5e432b20898239475f143f12",
  "username": "victor",
  "email": "victor@example.com"
}
```

### Sample login request and response

Request (`POST /api/auth/login`):

```json
{
  "email": "victor@example.com",
  "password": "123456"
}
```

Response (`200 OK`):

```json
{
  "message": "Login successful",
  "token": "<JWT_TOKEN>"
}
```

### Protected Notes Endpoints (`/api/notes`)

All `/api/notes` routes require `Authorization: Bearer <JWT_TOKEN>` or a token cookie. Unauthenticated requests are rejected with `403 Forbidden`:

```json
{
  "message": "No token provided"
}
```

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `POST` | `/api/notes` | `user`, `admin` | Creates a new note linked to `req.user.id` (`201 Created`) |
| `GET` | `/api/notes` | `user`, `admin` | Retrieves all notes owned by the authenticated user (`200 OK`) |
| `PUT` | `/api/notes/:id` | `user`, `admin` | Updates a specific note owned by the user (`200 OK`) |
| `DELETE` | `/api/notes/:id` | `user`, `admin` | Deletes a specific note owned by the user (`200 OK`) |
| `GET` | `/api/notes/admin/all` | `admin` only | RBAC-restricted route to view all users' notes |

---

## 7. Event-Driven and Real-Time Architecture

### Node.js EventEmitter (`events/appEvents.js`)

The application emits and logs asynchronous lifecycle events without blocking HTTP responses:

- `user:registered` -> `[event] New user registered: <username> (<email>)`
- `user:loggedIn` -> `[event] User logged in: <username>`
- `note:created` -> `[event] Note created (<noteId>) by user <ownerId>`

### Socket.IO Events (`server.js`)

- `connection`: Logs the connected client socket ID (`User connected: <socket.id>`).
- `joinRoom`: Subscribes a socket to a chat room (`<socket.id> joined room general`).
- `chatMessage`: Broadcasts messages to all clients in the target room (`[general] <username>: <message>`).
- `disconnect`: Logs client disconnection (`User disconnected: <socket.id>`).

---

## 8. Execution Output Screenshots

### Server console, EventEmitter logs, and real-time Socket.IO chat

![Server and Socket.IO output](screenshots/server-socket-output.jpg)

### Signup, login JWT, 403 route protection, and Notes CRUD verification

![API test output](screenshots/api-test-output.png)

---

## Quick Final Check Before Pushing to GitHub

Make sure your folder structure matches the image paths in this README:

1. The `screenshots/` folder exists in the root directory.
2. Inside `screenshots/`, the images are named `server-socket-output.jpg` and `api-test-output.png`.
3. Run `git status` to verify that `node_modules/` and `.env` are ignored by `.gitignore`.
