# GQT HRMS — QA & Automated Testing Strategy

## 1. Overview
The platform enforces automated testing at both frontend and backend layers with zero tolerance for flaky tests, test leaks, or unhandled exceptions.

---

## 2. Backend Automated Testing (pytest-django)
* **Configuration:** `backend/pytest.ini`
* **Test Isolation:**
  * Uses `config.settings.test`
  * In-memory isolated SQLite database
  * Fast MD5 password hasher (prevents slow Argon2 CPU delays during test runs)
  * Disabled HTTP rate limiters
* **Execution Command:**
  ```bash
  cd backend
  .\.venv\Scripts\python.exe -m pytest
  ```

---

## 3. Frontend Component & Unit Testing (Vitest)
* **Configuration:** `frontend/vite.config.ts`
* **Environment:** `jsdom` with `@testing-library/react` and `@testing-library/jest-dom`
* **Execution Command:**
  ```bash
  cd frontend
  npm test
  ```

---

## 4. Master Foundation Verification Suite (Windows)
Run all 6 verification checks in one command:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_dev.ps1
```
This executes:
1. Django system checks (`manage.py check`)
2. Django migration consistency (`makemigrations --check --dry-run`)
3. Backend automated pytest suite
4. Frontend TypeScript strict check (`tsc -b --noEmit`)
5. Frontend Vitest component test suite
6. Frontend production build (`tsc -b && vite build`)
