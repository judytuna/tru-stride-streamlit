import sqlite3
import hashlib
from datetime import datetime
import os

def migrate_database():
    """
    Migrate existing database to add admin features
    """
    print("🔄 Starting database migration...")
    
    conn = sqlite3.connect('horse_gait.db')
    c = conn.cursor()
    
    try:
        # Check if is_admin column exists
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'is_admin' not in columns:
            print("➕ Adding is_admin column...")
            c.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            
        if 'password_hash' not in columns:
            print("➕ Adding password_hash column...")
            c.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            
            # Set default passwords for existing users (they'll need to login with these)
            c.execute("UPDATE users SET password_hash = ? WHERE password_hash IS NULL", 
                     (hashlib.sha256("defaultpass123".encode()).hexdigest(),))
            print("🔑 Set default password 'defaultpass123' for existing users")
        
        # Create default admin user
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        c.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
        admin_exists = c.fetchone()
        
        if not admin_exists:
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
            c.execute("""INSERT INTO users (username, email, created_at, is_admin, password_hash) 
                        VALUES (?, ?, ?, ?, ?)""",
                     (admin_username, f"{admin_username}@horseanalyzer.com", 
                      datetime.now(), 1, password_hash))
            print(f"✅ Created admin user: {admin_username}")
        else:
            # Make existing admin user an actual admin
            c.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (admin_username,))
            print(f"✅ Updated existing user '{admin_username}' to admin")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

def reset_database():
    """
    Nuclear option: Delete and recreate database
    WARNING: This will delete all user data and videos!
    """
    import os
    
    response = input("⚠️  This will DELETE ALL DATA! Type 'YES DELETE' to confirm: ")
    if response != "YES DELETE":
        print("❌ Database reset cancelled")
        return
    
    if os.path.exists('horse_gait.db'):
        os.remove('horse_gait.db')
        print("🗑️  Deleted old database")
    
    # The init_db() function in your main app will create a fresh database
    print("✅ Database reset. Run your app to create fresh database.")

if __name__ == "__main__":
    print("🐎 Horse Gait Analyzer - Database Migration")
    print("\nChoose an option:")
    print("1. Migrate existing database (recommended)")
    print("2. Reset database (deletes all data)")
    print("3. Cancel")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        migrate_database()
    elif choice == "2":
        reset_database()
    else:
        print("❌ Cancelled")