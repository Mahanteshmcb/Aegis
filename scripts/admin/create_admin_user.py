#!/usr/bin/env python
"""
Script to create an admin user for the Aegis application.
Usage: python scripts/admin/create_admin_user.py
"""
import os
import sys

# Set PYTHONPATH to include current directory
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import SessionLocal, engine, Base
from backend import models_db as models, crud, schemas
from datetime import datetime

def main():
    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create or get default tenant
        print("Setting up default tenant...")
        tenant = db.query(models.Tenant).filter(models.Tenant.name == "Default Tenant").first()
        if not tenant:
            tenant = models.Tenant(
                name="Default Tenant",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"  ✓ Created tenant: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"  ✓ Tenant already exists: {tenant.name} (ID: {tenant.id})")
        
        # Step 2: Create admin user
        print("\nCreating admin user...")
        admin_email = "admin@aegis.com"
        admin_password = "admin1234"
        
        # Check if user already exists
        existing_user = db.query(models.User).filter(models.User.email == admin_email).first()
        if existing_user:
            print(f"  ℹ Admin user already exists: {admin_email}")
            print(f"  Password: {admin_password}")
        else:
            # Create user via CRUD
            user_create = schemas.UserCreate(
                email=admin_email,
                password=admin_password,
                role="admin",
                tenant_id=tenant.id
            )
            admin_user = crud.create_user(db, user_create)
            print(f"  ✓ Created admin user: {admin_user.email}")
            print(f"  Password: {admin_password}")
            print(f"  Role: {admin_user.role}")
            print(f"  Tenant ID: {admin_user.tenant_id}")
        
        print("\n✅ Admin user setup complete!")
        print("\nYou can now login with:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
