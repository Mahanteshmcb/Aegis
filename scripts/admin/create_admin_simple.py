#!/usr/bin/env python
"""
Simple script to create an admin user by directly inserting into the database.
"""
import sqlite3
import hashlib
from passlib.context import CryptContext

# Initialize password context (same as in the backend)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_admin_user():
    # Connect to the database
    db_path = "aegis.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Connecting to database: {db_path}")
    
    # Check if user already exists
    cursor.execute("SELECT id, email FROM users WHERE email = ?", ("admin@aegis.com",))
    result = cursor.fetchone()
    
    if result:
        print(f"Admin user already exists: {result[1]} (ID: {result[0]})")
    else:
        # First, ensure there's a tenant
        cursor.execute("SELECT id FROM tenants LIMIT 1")
        tenant_result = cursor.fetchone()
        
        if not tenant_result:
            print("Creating default tenant...")
            cursor.execute("""
                INSERT INTO tenants (name, created_at, updated_at)
                VALUES (?, datetime('now'), datetime('now'))
            """, ("Default Tenant",))
            conn.commit()
            cursor.execute("SELECT id FROM tenants LIMIT 1")
            tenant_id = cursor.fetchone()[0]
            print(f"  Created tenant with ID: {tenant_id}")
        else:
            tenant_id = tenant_result[0]
            print(f"Using existing tenant with ID: {tenant_id}")
        
        # Hash the password
        hashed_password = hash_password("admin1234")
        
        # Insert admin user
        print("Creating admin user...")
        cursor.execute("""
            INSERT INTO users (email, hashed_password, role, tenant_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """, ("admin@aegis.com", hashed_password, "admin", tenant_id))
        
        conn.commit()
        
        # Verify the user was created
        cursor.execute("SELECT id, email, role FROM users WHERE email = ?", ("admin@aegis.com",))
        user = cursor.fetchone()
        print(f"  Created admin user with ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Role: {user[2]}")
    
    conn.close()
    print("\nYou can now login with:")
    print("  Email: admin@aegis.com")
    print("  Password: admin1234")

if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
