"""
Database models for the product catalog
"""
import os
import re
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, Text, Index, Boolean, DateTime, ForeignKey, create_engine, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from passlib.context import CryptContext

Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)  # Consent for marketing communications and ads
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    verification_codes = relationship("VerificationCode", back_populates="user")
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password):
        """Verify password against hash"""
        return pwd_context.verify(password, self.password_hash)


class VerificationCode(Base):
    """Email verification codes"""
    __tablename__ = 'verification_codes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="verification_codes")
    
    @staticmethod
    def generate_code():
        """Generate 6-digit verification code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_valid(self):
        """Check if code is still valid"""
        return not self.used and datetime.utcnow() < self.expires_at


class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    
    @staticmethod
    def generate_token():
        """Generate secure reset token"""
        return secrets.token_urlsafe(48)
    
    def is_valid(self):
        """Check if token is still valid"""
        return not self.used and datetime.utcnow() < self.expires_at


class Newsletter(Base):
    """Newsletter subscriptions"""
    __tablename__ = 'newsletter'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    discount_code = Column(String(50), unique=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    has_purchased = Column(Boolean, default=False)  # For segmentation
    last_reminder_sent = Column(DateTime, nullable=True)  # Track reminder emails
    
    # Relationships
    tracking = relationship("EmailTracking", back_populates="subscriber")


class EmailCampaign(Base):
    """Email marketing campaigns"""
    __tablename__ = 'email_campaigns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # Internal campaign name
    subject = Column(String(255), nullable=False)  # Email subject
    html_content = Column(Text, nullable=False)  # HTML email body
    segment = Column(String(50), default='all')  # all, purchased, not_purchased, active
    status = Column(String(50), default='draft')  # draft, sent, scheduled
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_count = Column(Integer, default=0)  # Number of emails sent
    
    # Relationships
    tracking = relationship("EmailTracking", back_populates="campaign")


class PDFCache(Base):
    """PDF preview cache - persistent storage"""
    __tablename__ = 'pdf_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)  # MD5 hash
    pdf_data = Column(LargeBinary, nullable=False)  # Binary PDF data
    file_size = Column(Integer, nullable=False)  # Size in bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    product = relationship("Product")


class EmailTracking(Base):
    """Track email opens and clicks"""
    __tablename__ = 'email_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('email_campaigns.id'), nullable=True)
    subscriber_id = Column(Integer, ForeignKey('newsletter.id'), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    tracking_token = Column(String(64), unique=True, nullable=False, index=True)
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("EmailCampaign", back_populates="tracking")
    subscriber = relationship("Newsletter", back_populates="tracking")
    
    @staticmethod
    def generate_token():
        """Generate unique tracking token"""
        return secrets.token_urlsafe(48)


class AbandonedCart(Base):
    """Track abandoned carts for recovery emails"""
    __tablename__ = 'abandoned_carts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    product_ids = Column(Text, nullable=False)  # JSON array of product IDs
    total_value = Column(Float, nullable=False)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    recovered = Column(Boolean, default=False)  # True if user completed purchase
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DiscountCode(Base):
    """Discount codes for marketing campaigns"""
    __tablename__ = 'discount_codes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(String(20), nullable=False)  # 'percentage' or 'fixed'
    value = Column(Float, nullable=False)  # Percentage (e.g., 10 for 10%) or fixed amount
    description = Column(String(255))  # Internal note
    expires_at = Column(DateTime, nullable=True)  # NULL = never expires
    max_uses = Column(Integer, nullable=True)  # NULL = unlimited
    used_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))  # Admin email who created it
    
    def is_valid(self):
        """Check if discount code is still valid"""
        if not self.active:
            return False, "Code is inactive"
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False, "Code has expired"
        
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "Code usage limit reached"
        
        return True, "Code is valid"
    
    def calculate_discount(self, total_amount):
        """Calculate discount amount for given total"""
        if self.type == 'percentage':
            return round(total_amount * (self.value / 100), 2)
        else:  # fixed
            return min(self.value, total_amount)  # Don't exceed total amount


class Order(Base):
    """Order model"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Nullable for guest orders
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    email = Column(String(255), nullable=False)
    paypal_order_id = Column(String(255), unique=True)
    status = Column(String(50), default='pending')  # pending, completed, failed
    price = Column(Float, nullable=False)
    download_link = Column(String(500), nullable=True)  # Link to manual set by admin
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    product = relationship("Product")


class Product(Base):
    """Product model with fields optimized for 100k+ products"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True, index=True)  # Auto-detected from title/model
    product_type = Column(String(50), nullable=True, index=True)  # vehicles, electronics, publications, other
    slug = Column(String(300), unique=True, index=True, nullable=True)
    image_url = Column(Text, nullable=True)  # URL to product image(s), comma-separated for multiple images
    
    # PDF delivery system
    pdf_url = Column(String(500), nullable=True)  # Original PDF download URL from CSV
    google_drive_link = Column(String(500), nullable=True)  # Permanent Google Drive link
    page_count = Column(Integer, nullable=True)  # Number of pages in the manual
    preview_images = Column(Text, nullable=True)  # JSON array of preview image paths
    pdf_processed = Column(Boolean, default=False)  # Flag if PDF was processed
    is_featured = Column(Boolean, default=False)  # Featured product flag
    
    # Create composite indexes for faster filtering
    __table_args__ = (
        Index('idx_category_brand', 'category', 'brand'),
        Index('idx_title_search', 'title'),
        Index('idx_year_type', 'year', 'product_type'),
    )
    
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'brand': self.brand,
            'model': self.model,
            'slug': self.slug,
            'image_url': self.image_url,
            'google_drive_link': self.google_drive_link,
            'preview_images': self.preview_images,
            'pdf_processed': self.pdf_processed
        }
    
    @staticmethod
    def generate_slug(title, brand, model, product_id=None):
        """
        Generate SEO-friendly slug from product details
        Example: ford-f150-2012-repair-manual
        """
        # Combine title parts
        slug_parts = [brand, model]
        
        # Remove brand and model from title to avoid duplication
        title_clean = title.lower()
        for part in [brand.lower(), model.lower()]:
            title_clean = title_clean.replace(part, '')
        
        # Add remaining title words (limit to important words)
        title_words = [w for w in title_clean.split() if len(w) > 3][:3]
        slug_parts.extend(title_words)
        
        # Create slug
        slug_text = ' '.join(slug_parts)
        
        # Transliterate and clean
        slug = slug_text.lower()
        # Remove Polish characters
        slug = slug.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e')
        slug = slug.replace('ł', 'l').replace('ń', 'n').replace('ó', 'o')
        slug = slug.replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
        
        # Remove special characters and replace spaces with hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        slug = slug.strip('-')
        
        # Limit length
        if len(slug) > 100:
            slug = slug[:100].rsplit('-', 1)[0]
        
        # Add ID suffix for uniqueness if provided
        if product_id:
            slug = f"{slug}-{product_id}"
        
        return slug
    
    def generate_and_set_slug(self):
        """Generate and set slug for this product"""
        if not self.slug:
            self.slug = self.generate_slug(self.title, self.brand, self.model, self.id)


# Database setup
# Priority: DATABASE_PUBLIC_URL (reliable) > DATABASE_URL (internal) > SQLite
# Use public URL for better stability on Railway
DATABASE_URL = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL", "sqlite:///./database/products.db")

print(f"🔗 Database: {DATABASE_URL[:60]}...")  # Log connection string (first 60 chars)

# PostgreSQL URLs from Railway use postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


# Global engine instance (created once)
_engine = None

def get_engine():
    """Get or create database engine with connection pooling"""
    global _engine
    if _engine is None:
        # SQLite needs check_same_thread, PostgreSQL doesn't
        if DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            _engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
        else:
            # PostgreSQL with optimized connection pooling
            _engine = create_engine(
                DATABASE_URL,
                pool_size=20,  # Increased from 10
                max_overflow=40,  # Increased from 20
                pool_pre_ping=True,  # Test connections before using
                pool_recycle=300,  # Recycle connections after 5 minutes (faster)
                echo=False,
                connect_args={
                    "connect_timeout": 30,  # 30 second connection timeout for Railway
                }
            )
    return _engine


# Global session factory (created once)
_SessionLocal = None

def get_session():
    """Get database session from reusable session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal()


def init_db():
    """Initialize database - create all tables and add missing columns"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration: Add missing columns if they don't exist
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Check if products table exists
    if 'products' in inspector.get_table_names():
        existing_columns = {col['name'] for col in inspector.get_columns('products')}
        
        # Define required columns with their SQL types
        required_columns = {
            'year': 'INTEGER',
            'product_type': 'VARCHAR(50)',
            'page_count': 'INTEGER'
        }
        
        # Add missing columns
        with engine.connect() as conn:
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    try:
                        # PostgreSQL syntax
                        if DATABASE_URL.startswith("postgresql"):
                            conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}"))
                        # SQLite syntax
                        else:
                            conn.execute(text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"✅ Added missing column: {col_name}")
                    except Exception as e:
                        # Column might already exist or other error
                        print(f"⚠️  Could not add column {col_name}: {e}")
            
            # Add indexes if they don't exist
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_year ON products(year)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_product_type ON products(product_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_year_type ON products(year, product_type)"))
                conn.commit()
                print("✅ Indexes verified/created")
            except Exception as e:
                print(f"⚠️  Index creation: {e}")
    
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
