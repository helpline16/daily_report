# Login Credentials for Deployed App

## Default Users

The deployed app (accessed via Streamlit link) requires authentication.

### Available Accounts:

1. **Admin Account**
   - Username: `admin`
   - Password: `admin123`

2. **Helpline Account**
   - Username: `helpline16`
   - Password: `helpline@2024`

---

## How to Change Passwords

To change passwords, edit the `src/auth.py` file:

1. Open `src/auth.py`
2. Find the `DEFAULT_USERS` dictionary
3. Update usernames and passwords as needed
4. Commit and push to GitHub
5. Streamlit will automatically redeploy with new credentials

Example:
```python
DEFAULT_USERS = {
    "your_username": hash_password("your_password"),
    "another_user": hash_password("another_password")
}
```

---

## Security Notes

- Passwords are hashed using SHA-256
- Login session persists until logout
- Authentication only applies to deployed app (not local development)
- For production use, consider using Streamlit's built-in authentication or environment variables

---

## Local Development

When running locally (`streamlit run src/app.py`), the app works without login.
Authentication only activates when deployed online.
