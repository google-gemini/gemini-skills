---
name: Engineering Standards
description: Professional Engineering Standards & Protocols for the organization.
---

# Professional Engineering Standards & Protocols

## 1. Core Engineering Principles
**The Non-Negotiables**
These principles apply universally across all languages and frameworks within the organization.

- **Type Safety**: Strict typing is mandatory. The use of `any` or dynamic types typically implies a design failure.
- **Immutability**: Prefer immutable data structures. State mutations must be explicit and contained.
- **DRY (Don't Repeat Yourself)**: Abstract common logic into shared libraries or utilities.
- **SOLID**: Adhere to Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion principles.
- **Security First**: Sanitize all inputs (XSS/SQL Injection prevention), never commit secrets/keys, and enforce the Principle of Least Privilege.

---

## 2. API Design & Architecture Standards
This section defines the strict contract for designing, documenting, and implementing APIs.

### 2.1 RESTful Maturity Model
- **Resource Naming**: Use plural nouns for resources (e.g., `/users`, `/orders`). **Never** use verbs in URIs (e.g., avoid `/getUsers`).
- **Versioning**: All APIs must be versioned. Prefer URI versioning (e.g., `/api/v1/resource`) for clarity.
- **HTTP Methods**:
  - `GET`: Retrieve resources. Safe and idempotent.
  - `POST`: Create new resources. Not idempotent.
  - `PUT`: Replace a resource entirely. Idempotent.
  - `PATCH`: Partially update a resource.
  - `DELETE`: Remove a resource.

### 2.2 Standardized HTTP Status Codes
- **Success**:
  - `200 OK`: Request succeeded.
  - `201 Created`: Resource successfully created.
  - `204 No Content`: Action succeeded, but no content to return (common for DELETE).
- **Client Errors**:
  - `400 Bad Request`: Validation failure or malformed JSON.
  - `401 Unauthorized`: Authentication token is missing or invalid.
  - `403 Forbidden`: Authenticated, but lacks permission for this scope.
  - `404 Not Found`: Resource does not exist.
  - `429 Too Many Requests`: Rate limit exceeded.
- **Server Errors**:
  - `500 Internal Server Error`: Generic server failure (**Never** expose stack traces to client).

### 2.3 Response Envelope Structure
All JSON responses must follow a consistent envelope structure.

**Success Response Example:**
```json
{
  "status": "success",
  "data": {
    "id": "usr_12345",
    "email": "user@example.com",
    "role": "admin"
  },
  "meta": {
    "timestamp": "2023-10-27T10:00:00Z"
  }
}
```

**Error Response Example:**
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "The email format is invalid.",
    "details": [
      { "field": "email", "issue": "must be a valid email address" }
    ]
  }
}
```

### 2.4 Pagination, Filtering, & Sorting

- **Pagination**: Use cursor-based pagination for large datasets; offset-based for small, static lists.
    
- **Sorting**: Use `sort_by` parameter. Use generic minus sign for descending (e.g., `?sort=-created_at`).
    
- **Filtering**: Use specific query parameters (e.g., `?status=active&role=admin`).
    

---

## 3. Frontend Ecosystem Standards

### 3.1 TypeScript Core

- **Strict Mode**: `tsconfig.json` must have `"strict": true`.
    
- **Type Definitions**:
    
    - Use `type` for primitives, unions, and tuples.
        
    - Use `interface` for object shapes and extendability.
        
- **Validation**: Use **Zod** for runtime validation (API responses, forms, env vars).
    
- **No `any`**: Use `unknown` with type guards if the type is truly dynamic.
    

### 3.2 React (Modern Standards)

- **Functional Only**: No Class Components.
    
- **Hooks Rules**:
    
    - Keep logic inside custom hooks (`useAuth`, `useFetch`).
        
    - Never use `useEffect` for derived state; use `useMemo` or raw calculation.
        
- **State Management**:
    
    - **Server State**: TanStack Query (React Query).
        
    - **Client State**: Context API (for theme/auth) or Zustand.
        

### 3.3 Next.js (App Router Standard)

- **Server Components (RSC)**: Fetch data on the server by default. Use `"use client"` only for interactivity.
    
- **Server Actions**: Use Server Actions for mutations (form submissions) instead of API routes.
    
- **File Structure**: `app/` (Routes), `components/` (UI), `lib/` (Utils), `actions/` (Server Logic).
    

### 3.4 Angular (Modern & Signal-based)

- **Standalone**: All components must be `standalone: true`. Avoid `NgModules`.
    
- **Reactivity (Signals)**: Use `signal()`, `computed()`, and `effect()`. Avoid manual RxJS subscriptions.
    
- **Change Detection**: MUST use `ChangeDetectionStrategy.OnPush`.
    
- **Control Flow**: Use `@if`, `@for`, `@switch` syntax.
    
- **DI**: Use `inject()` instead of constructor injection.
    

**Angular Signal Component Pattern:**
```TypeScript
import { Component, signal, computed, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="profile-card">
      @if (isAdmin()) { <span class="badge">Admin</span> }
      <h3>{{ userName() }}</h3>
      <button (click)="updateRole()">Promote</button>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserProfileComponent {
  private authService = inject(AuthService);
  userId = signal<string>('123');
  userName = computed(() => `User: ${this.userId()}`);
  isAdmin = this.authService.isAdmin; // Signal from service

  updateRole() {
    this.userId.set('456');
  }
}
```

---

## 4. Backend & Systems Languages

### 4.1 Node.js & TypeScript Backend

- **Async/Await**: No callback hell. Always handle errors with `try/catch`.
    
- **Architecture**: Controller -> Service -> Repository pattern.
    
- **Config**: Strictly use `dotenv` or `t3-env` for environment variables.
    

### 4.2 Python (Modern)

- **Type Hints**: Mandatory for all function signatures (e.g., `def process(items: list[str]) -> bool:`).
    
- **Pydantic**: Use Pydantic models for data validation.
    
- **AsyncIO**: Use `async`/`await` for I/O bound operations (FastAPI standard).
    

### 4.3 Go (Golang)

- **Error Handling**: Explicit `if err != nil` is required. Do not ignore errors using `_`.
    
- **Context**: Pass `context.Context` as the first argument to every I/O function.
    
- **Project Layout**: Follow standard Go layout (`cmd/`, `internal/`, `pkg/`).
    

### 4.4 Rust

- **Ownership**: Minimize `.clone()`. Use borrowing (`&`) effectively.
    
- **Error Handling**: Use `Result<T, E>` and `Option<T>`. Never use `.unwrap()` in production; use `?` operator or `expect()`.
    
- **Clippy**: Code must pass `cargo clippy -- -D warnings`.
    

### 4.5 Java

- **Modern Features**: Use `Records` for DTOs (Java 14+).
    
- **Streams**: Use Stream API for collections but maintain readability.
    
- **Optional**: Use `Optional<T>` to avoid `NullPointerException`.
    

---

## 5. Database Standards

- **SQL (Relational)**:
    
    - Use parameterized queries strictly (No String Concatenation).
        
    - Index Foreign Keys and frequently queried columns.
        
    - Use snake_case for table and column names.
        
- **NoSQL**:
    
    - Design schemas based on access patterns (read-heavy vs write-heavy).
        

---

## 6. DevOps & Quality Assurance

- **Git**:
    
    - **Commit Messages**: Follow Conventional Commits (`feat:`, `fix:`, `chore:`).
        
    - **Branches**: Main/Master must always be deployable.
        
- **Testing**:
    
    - Unit Tests for business logic.
        
    - Integration Tests for API endpoints.
        
- **Documentation**:
    
    - Code must be self-documenting.
        
    - API docs generated via Swagger/OpenAPI.
        

---

## 7. The Refactoring Protocol

When reviewing code, the Engineer MUST follow this loop:

1. **Analyze**: Identify the language and framework.
    
2. **Detect Smells**: (e.g., Prop Drilling, Magic Numbers, Callback Hell).
    
3. **Refactor**: Apply the specific standards from Sections above.
    
4. **Explain**: Briefly state _why_ the change was made.
