"""
FastAPI Application - Professional Product Catalog
Optimized for 100k+ products with fast loading times
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import func, or_
from database.models import Product, User, Order, Review, get_session, init_db, get_engine, Base
from typing import Optional
from datetime import datetime
import os
import stripe
from dotenv import load_dotenv
from email_utils import send_order_confirmation_email, send_contact_form_email
from cache_manager import cache
import time

# Load environment variables
load_dotenv()

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Import API routes
from api_routes import router as auth_router, orders_router, search_router, newsletter_router, import_router, reviews_router
from email_marketing_routes import email_marketing_router
from tracking_routes import tracking_router
from discount_routes import router as discount_router
from google_merchant import merchant_router
from auth import get_current_user, get_current_admin_user

# Initialize FastAPI app
app = FastAPI(
    title="Professional Product Catalog",
    description="Fast and modern online store with 100k+ products",
    version="2.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Custom Exception Handler - Returns JSON for API routes, HTML for web pages
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Check if this is an API request (starts with /api/)
    is_api_request = request.url.path.startswith("/api/")
    
    # For API requests, always return JSON
    if is_api_request:
        return Response(
            content=f'{{"detail":"{exc.detail}"}}',
            status_code=exc.status_code,
            media_type="application/json"
        )
    
    # For web pages, return HTML templates
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    elif exc.status_code == 401:
        return templates.TemplateResponse(
            "401.html",
            {"request": request},
            status_code=401
        )
    elif exc.status_code == 403:
        return templates.TemplateResponse(
            "403.html",
            {"request": request},
            status_code=403
        )
    elif exc.status_code == 500:
        return templates.TemplateResponse(
            "500.html",
            {"request": request},
            status_code=500
        )
    elif exc.status_code == 503:
        return templates.TemplateResponse(
            "503.html",
            {"request": request},
            status_code=503
        )
    # For other HTTP errors, return JSON
    return Response(
        content=f'{{"detail":"{exc.detail}"}}',
        status_code=exc.status_code,
        media_type="application/json"
    )

# Performance monitoring middleware
@app.middleware("http")
async def add_performance_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))  # milliseconds
    # Log slow requests (over 1 second)
    if process_time > 1.0:
        print(f"⚠️  SLOW REQUEST: {request.method} {request.url.path} took {process_time:.2f}s")
    return response

@app.on_event("startup")
async def startup_event():
    """Initialize database with retry logic for Railway deployment"""
    import time
    from sqlalchemy import text, inspect
    
    max_retries = 10
    retry_delay = 2
    
    print("=" * 50)
    print("🚀 Initializing application...")
    print("=" * 50)
    
    # Retry database connection
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📊 Connecting to database (attempt {attempt}/{max_retries})...")
            engine = get_engine()
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("✅ Database connection established!")
            break
            
        except Exception as e:
            if attempt == max_retries:
                print(f"❌ Failed to connect after {max_retries} attempts: {e}")
                raise
            print(f"⚠️  Connection failed (attempt {attempt}/{max_retries}): {e}")
            print(f"⏳ Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # Initialize database tables
    try:
        print("📊 Creating database tables...")
        init_db()
        print("✅ Database tables ready!")
        
        # Create performance indexes if they don't exist
        print("📈 Checking performance indexes...")
        session = get_session()
        try:
            # Check and create category index for related products
            result = session.execute(text("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = 'products' AND indexname = 'idx_products_category';
            """))
            if result.scalar() == 0:
                print("  📊 Creating index on products.category...")
                session.execute(text("CREATE INDEX idx_products_category ON products(category);"))
                session.commit()
                print("  ✅ Index idx_products_category created")
            else:
                print("  ✓ Index idx_products_category exists")
        except Exception as idx_error:
            print(f"  ⚠️  Index creation skipped: {idx_error}")
            session.rollback()
        finally:
            session.close()
                
    except Exception as e:
        print(f"❌ Table initialization error: {e}")
        import traceback
        traceback.print_exc()
    
    # Create default admin if needed
    try:
        session = get_session()
        user_count = session.query(User).count()
        if user_count == 0:
            print("📝 Creating default admin...")
            admin = User(
                email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
                is_admin=True,
                is_verified=True
            )
            admin.set_password(os.getenv("ADMIN_PASSWORD", "admin123"))
            session.add(admin)
            session.commit()
            print(f"✅ Admin created: {admin.email}")
        session.close()
    except Exception as e:
        print(f"⚠️  Admin creation: {e}")
    
    # Auto-migrate database schema
    try:
        inspector = inspect(engine)
        
        # Get existing columns in products table
        existing_columns = [col['name'] for col in inspector.get_columns('products')]
        
        # List of all expected columns with their definitions
        migrations_needed = []
        
        if 'page_count' not in existing_columns:
            migrations_needed.append(("page_count", "ALTER TABLE products ADD COLUMN page_count INTEGER DEFAULT NULL"))
        
        if 'preview_images' not in existing_columns:
            migrations_needed.append(("preview_images", "ALTER TABLE products ADD COLUMN preview_images TEXT DEFAULT NULL"))
        
        if 'pdf_processed' not in existing_columns:
            migrations_needed.append(("pdf_processed", "ALTER TABLE products ADD COLUMN pdf_processed BOOLEAN DEFAULT FALSE"))
        
        if 'is_featured' not in existing_columns:
            migrations_needed.append(("is_featured", "ALTER TABLE products ADD COLUMN is_featured BOOLEAN DEFAULT FALSE"))
        
        # Execute all migrations
        if migrations_needed:
            print(f"🔄 Running {len(migrations_needed)} migration(s)...")
            with engine.connect() as conn:
                for column_name, sql in migrations_needed:
                    try:
                        conn.execute(text(sql))
                        print(f"  ✅ Added column: {column_name}")
                    except Exception as e:
                        print(f"  ⚠️  Column {column_name}: {e}")
                conn.commit()
            print("✅ All migrations complete!")
        else:
            print("✅ Database schema up to date")
        
        # Create any missing tables (pdf_cache, reviews, etc.)
        existing_tables = inspector.get_table_names()
        for table_name in ['pdf_cache', 'reviews']:
            if table_name not in existing_tables:
                print(f"🔄 Creating {table_name} table...")
                Base.metadata.create_all(bind=engine)
                print(f"✅ {table_name} table created")
                break  # create_all handles all missing tables at once
            
    except Exception as e:
        print(f"⚠️  Migration error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("✅ Application ready!")
    print("=" * 50)


# Include authentication routes
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(search_router)
app.include_router(newsletter_router)
app.include_router(email_marketing_router)
app.include_router(tracking_router)
app.include_router(discount_router)
app.include_router(import_router)
app.include_router(merchant_router)
app.include_router(reviews_router)

# Configuration
# Railway automatically provides RAILWAY_PUBLIC_DOMAIN
railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if railway_domain:
    DOMAIN = f"https://{railway_domain}"
else:
    # Use production domain or localhost
    DOMAIN = os.getenv("DOMAIN", "https://manualbear.com")

# Add custom filter for regex search
import re

def regex_search(text, pattern):
    """Extract text matching regex pattern"""
    if not text:
        return None
    match = re.search(pattern, str(text))
    return match.group(0) if match else None

templates.env.filters['regex_search'] = regex_search


# Helper function to get distinct values
def get_distinct_categories():
    """Get all unique main categories from database (first part before /)"""
    session = get_session()
    try:
        all_categories = session.query(Product.category).distinct().all()
        main_cats = set()
        for (cat,) in all_categories:
            if cat:
                main_cat = cat.split('/')[0] if '/' in cat else cat
                main_cats.add(main_cat)
        return sorted(list(main_cats))
    finally:
        session.close()


def get_distinct_brands(category: Optional[str] = None):
    """Get all unique brands from database, optionally filtered by category"""
    session = get_session()
    try:
        query = session.query(Product.brand).distinct()
        if category:
            # Filter by main category (match start of category field)
            query = query.filter(Product.category.like(f'{category}%'))
        brands = query.order_by(Product.brand).all()
        return [brand[0] for brand in brands if brand[0]]
    finally:
        session.close()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with categories and featured products - CACHED for performance"""
    
    # Try cache first (60 second TTL for homepage)
    cache_key = "homepage_data"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        # Use cached data
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "products": cached_data['products'],
                "categories": cached_data['categories'],
                "page_title": "ManualBear - User Manuals & Service Guides",
                "page_description": "Download PDF user manuals and service guides. Over 1,000+ manuals for vehicles, electronics, and appliances. Instant digital delivery worldwide."
            }
        )
    
    # Cache miss - fetch from database
    session = get_session()
    try:
        # OPTIMIZED: Get main categories with ONE query using SQL expressions
        from sqlalchemy import case, func
        from database.models import DATABASE_URL
        
        # Database-agnostic category splitting
        if DATABASE_URL.startswith("sqlite"):
            # SQLite: use substr and instr to extract first part before '/'
            main_cat_expr = case(
                (func.instr(Product.category, '/') > 0, 
                 func.substr(Product.category, 1, func.instr(Product.category, '/') - 1)),
                else_=Product.category
            )
        else:
            # PostgreSQL: use split_part
            main_cat_expr = func.split_part(Product.category, '/', 1)
        
        # Get main categories and counts in a single query
        category_data = session.query(
            main_cat_expr.label('main_cat'),
            func.count().label('count')
        ).filter(
            Product.category.isnot(None)
        ).group_by(
            'main_cat'
        ).all()
        
        # Convert to list of dicts and sort
        categories = [
            {'name': cat, 'count': count} 
            for cat, count in sorted(category_data, key=lambda x: x[0])
        ]
        
        # Get latest 12 products (4x3 grid) - already optimized with LIMIT
        latest_products = session.query(Product).order_by(Product.id.desc()).limit(12).all()
        
        # Convert to serializable dict for caching
        products_dict = [{
            'id': p.id,
            'title': p.title,
            'brand': p.brand,
            'model': p.model,
            'slug': p.slug,
            'category': p.category,
            'price': float(p.price) if p.price else 0.0,
            'image_url': p.image_url,
            'description': p.description
        } for p in latest_products]
        
        # Cache the data (60 seconds)
        cache.set(cache_key, {
            'products': products_dict,
            'categories': categories
        }, ttl=60)
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "products": latest_products,
                "categories": categories,
                "page_title": "ManualBear - Product Catalog",
                "page_description": "Find user manuals for your products. Over 1,000 manuals available online."
            }
        )
    finally:
        session.close()


@app.get("/cart", response_class=HTMLResponse)
async def cart(request: Request):
    """Shopping cart page"""
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "page_title": "Shopping Cart - ManualBear",
        "page_description": "Review the service manuals in your cart and check out securely with ManualBear."
    })


@app.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    product_type: Optional[str] = None,
    year_from: Optional[str] = None,
    year_to: Optional[str] = None,
    page: int = 1,
    limit: int = 24
):
    """Search products with advanced filters - OPTIMIZED with caching"""
    import time
    start_time = time.time()
    
    # Create cache key from all parameters
    cache_params = f"q={q or ''}&cat={category or ''}&brand={brand or ''}&type={product_type or ''}&yf={year_from or ''}&yt={year_to or ''}&p={page}&l={limit}"
    cache_key = f"search:{cache_params}"
    
    # Try cache first (2 minute TTL for search results)
    cached_result = cache.get(cache_key)
    if cached_result:
        cache_time = time.time() - start_time
        print(f"⚡ Search cache hit: {cache_time:.3f}s")
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                **cached_result
            }
        )
    
    session = get_session()
    try:
        db_start = time.time()
        # Build query
        query = session.query(Product)
        
        # Check if user specified a year in search query (e.g., "Focus 2014")
        year_in_query = None
        
        # Apply search filter - SIMPLIFIED for performance
        if q:
            import re
            from sqlalchemy import func, and_
            
            # Extract year from search query
            year_match = re.search(r'\b(19|20)\d{2}\b', q)
            if year_match:
                year_in_query = int(year_match.group(0))
            
            # Split search term into words for better matching
            search_words = [w.strip() for w in q.lower().split() if len(w.strip()) >= 2]
            
            # Remove year from search words if found
            if year_in_query:
                search_words = [w for w in search_words if w != str(year_in_query)]
            
            # OPTIMIZED: Use simple ILIKE instead of regexp_replace
            word_filters = []
            for word in search_words:
                search_term = f"%{word}%"
                word_filters.append(
                    or_(
                        Product.title.ilike(search_term),
                        Product.model.ilike(search_term),
                        Product.brand.ilike(search_term),
                        Product.category.ilike(search_term)
                    )
                )
            
            # Apply all word filters (AND logic - all words must match)
            if word_filters:
                query = query.filter(and_(*word_filters))
            
        
        # Apply product type filter (NEW)
        if product_type:
            query = query.filter(Product.product_type == product_type)
        
        # Apply year range filter - search in title for year ranges like "2016-2020"
        if year_from and year_from.strip():
            try:
                year_from_int = int(year_from)
                # Match products where:
                # 1. Product.year >= year_from OR
                # 2. Title contains year range that includes year_from (e.g., "2016-2020" includes 2018)
                query = query.filter(
                    or_(
                        Product.year >= year_from_int,
                        Product.title.op('~')(f'\\d{{4}}-\\d{{4}}')  # Has year range in title
                    )
                )
            except ValueError:
                pass
        
        if year_to and year_to.strip():
            try:
                year_to_int = int(year_to)
                query = query.filter(
                    or_(
                        Product.year <= year_to_int,
                        Product.title.op('~')(f'\\d{{4}}-\\d{{4}}')  # Has year range in title
                    )
                )
            except ValueError:
                pass
        
        # Apply category filter
        if category:
            # Filter by main category (match start of category field)
            query = query.filter(Product.category.like(f'{category}%'))
        
        # Apply brand filter
        if brand:
            query = query.filter(Product.brand == brand)
        
        # IMPORTANT: Count total BEFORE loading all (for performance)
        total_count = query.count()
        
        # Apply pagination at SQL level (not in Python!)
        offset = (page - 1) * limit
        products_query = query.order_by(Product.title).limit(limit).offset(offset)
        products = products_query.all()
        
        # Filter by year range if year was specified in search
        # Example: searching "Focus 2014" will find products with "2010-2015" in title
        if year_in_query:
            import re
            filtered_products = []
            for product in products:
                # Check if title contains a year range like "2010-2015"
                range_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', product.title)
                if range_match:
                    year_start = int(range_match.group(1))
                    year_end = int(range_match.group(2))
                    # Include if searched year is within range
                    if year_start <= year_in_query <= year_end:
                        filtered_products.append(product)
                # Also include if product.year matches
                elif product.year and product.year == year_in_query:
                    filtered_products.append(product)
                # Or if title contains the exact year
                elif str(year_in_query) in product.title:
                    filtered_products.append(product)
            
            products = filtered_products
            total_count = len(products)  # Approximate after year filtering
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        
        # Get filters for sidebar
        categories = get_distinct_categories()
        brands = get_distinct_brands(category)
        
        # Build page title for SEO
        page_title = "Search Results"
        if q:
            page_title = f"Search: {q}"
        if product_type:
            page_title += f" - {product_type.title()}"
        if (year_from and year_from.strip()) or (year_to and year_to.strip()):
            year_range = f"{year_from or '...'} - {year_to or '...'}"
            page_title += f" ({year_range})"
        if category:
            page_title += f" - {category}"
        if brand:
            page_title += f" - {brand}"
        
        db_time = time.time() - db_start
        total_time = time.time() - start_time
        
        if total_time > 0.5:
            print(f"⚠️  Slow search: {total_time:.2f}s (DB: {db_time:.2f}s, params: {cache_params[:100]})")
        
        # Convert products to dictionaries for caching (SQLAlchemy objects can't be cached)
        products_dict = [{
            'id': p.id,
            'title': p.title,
            'brand': p.brand,
            'model': p.model,
            'slug': p.slug,
            'category': p.category,
            'price': float(p.price) if p.price else 0.0,
            'image_url': p.image_url,
            'year': p.year,
            'product_type': p.product_type
        } for p in products]
        
        # Prepare response data
        response_data = {
            "products": products_dict,
            "query": q or "",
            "selected_category": category,
            "selected_brand": brand,
            "selected_product_type": product_type,
            "year_from": year_from if year_from and year_from.strip() else None,
            "year_to": year_to if year_to and year_to.strip() else None,
            "categories": categories,
            "brands": brands,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "page_title": page_title,
            "page_description": f"Found {total_count} user manuals. Search over 1,000+ manuals for vehicles, electronics, and appliances."
        }
        
        # Cache the result (2 minutes TTL)
        cache.set(cache_key, response_data, ttl=120)
        
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                **response_data
            }
        )
    finally:
        session.close()


@app.get("/manuals/{slug}", response_class=HTMLResponse)
async def product_detail_by_slug(request: Request, slug: str):
    """Product detail page with SEO-friendly clean URLs - CACHED for performance"""
    import time
    start_time = time.time()
    
    # Try cache first (5 minute TTL for product pages)
    cache_key = f"product:{slug}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        # Use cached data but always fetch fresh reviews
        cache_time = time.time() - start_time
        if cache_time > 0.1:
            print(f"⚡ Cache hit for {slug} took {cache_time:.3f}s (slow)")
        
        # Reviews always fresh (not cached)
        review_session = get_session()
        try:
            product_id = cached_data['product']['id'] if isinstance(cached_data['product'], dict) else cached_data['product'].id
            reviews = review_session.query(Review).filter(
                Review.product_id == product_id,
                Review.approved == True
            ).order_by(Review.created_at.desc()).all()
            review_count = len(reviews)
            avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count else 0
        finally:
            review_session.close()
        
        return templates.TemplateResponse(
            "product.html",
            {
                "request": request,
                "product": cached_data['product'],
                "related_products": cached_data['related_products'],
                "reviews": reviews,
                "review_count": review_count,
                "avg_rating": avg_rating,
                "page_title": cached_data['page_title'],
                "page_description": cached_data['page_description']
            }
        )
    
    # Cache miss - fetch from database
    session = get_session()
    try:
        db_start = time.time()
        # OPTIMIZED: Query by slug (indexed) - should be very fast
        product = session.query(Product).filter(Product.slug == slug).first()
        db_time = time.time() - db_start
        
        if not product:
            # Return nice 404 page instead of JSON error
            return templates.TemplateResponse(
                "404.html",
                {"request": request},
                status_code=404
            )
        
        print(f"🔍 Product query for {slug}: {db_time:.3f}s")
        
        # Generate SEO-optimized title and description
        page_title = f"{product.title} - {product.brand} {product.model} | User Manual"
        page_description = f"Technical documentation for {product.brand} {product.model}. {product.description[:150] if product.description else 'Professional service guide and technical documentation.'}"
        
        # Get related products (same category, limit 4)
        related_start = time.time()
        related_products = session.query(Product).filter(
            Product.category == product.category,
            Product.id != product.id
        ).limit(4).all()
        related_time = time.time() - related_start
        
        print(f"🔗 Related products query: {related_time:.3f}s")
        
        total_time = time.time() - start_time
        if total_time > 0.5:
            print(f"⚠️  SLOW product page load for {slug}: {total_time:.3f}s total")
        
        # Convert to serializable dict for caching
        product_dict = {
            'id': product.id,
            'title': product.title,
            'brand': product.brand,
            'model': product.model,
            'slug': product.slug,
            'category': product.category,
            'price': float(product.price) if product.price else 0.0,
            'image_url': product.image_url,
            'description': product.description,
            'google_drive_link': product.google_drive_link,
            'preview_images': product.preview_images,
            'page_count': product.page_count,
            'year': product.year,
            'product_type': product.product_type
        }
        
        related_dict = [{
            'id': p.id,
            'title': p.title,
            'brand': p.brand,
            'model': p.model,
            'slug': p.slug,
            'price': float(p.price) if p.price else 0.0,
            'image_url': p.image_url
        } for p in related_products]
        
        # Cache the data (5 minutes)
        cache.set(cache_key, {
            'product': product_dict,
            'related_products': related_dict,
            'page_title': page_title,
            'page_description': page_description
        }, ttl=300)
        
        # Reviews always fresh
        reviews = session.query(Review).filter(
            Review.product_id == product.id,
            Review.approved == True
        ).order_by(Review.created_at.desc()).all()
        review_count = len(reviews)
        avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count else 0
        
        return templates.TemplateResponse(
            "product.html",
            {
                "request": request,
                "product": product,
                "related_products": related_products,
                "reviews": reviews,
                "review_count": review_count,
                "avg_rating": avg_rating,
                "page_title": page_title,
                "page_description": page_description
            }
        )
    finally:
        session.close()


# Legacy endpoint for backwards compatibility
@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    """Legacy product detail endpoint - redirects to clean URL"""
    session = get_session()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Redirect to clean URL if slug exists
        if product.slug:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"/manuals/{product.slug}", status_code=301)
        
        # Fallback to old rendering if no slug
        
        # Generate SEO-optimized title and description
        page_title = f"{product.title} - {product.brand} {product.model} | User Manual"
        page_description = f"Technical documentation and service information for {product.brand} {product.model}. Professional quality manual available for purchase."
        
        # Get related products (same category)
        related_products = session.query(Product).filter(
            Product.category == product.category,
            Product.id != product.id
        ).limit(4).all()
        
        # Reviews
        reviews = session.query(Review).filter(
            Review.product_id == product.id,
            Review.approved == True
        ).order_by(Review.created_at.desc()).all()
        review_count = len(reviews)
        avg_rating = round(sum(r.rating for r in reviews) / review_count, 1) if review_count else 0
        
        return templates.TemplateResponse(
            "product.html",
            {
                "request": request,
                "product": product,
                "related_products": related_products,
                "reviews": reviews,
                "review_count": review_count,
                "avg_rating": avg_rating,
                "page_title": page_title,
                "page_description": page_description
            }
        )
    finally:
        session.close()


@app.get("/api/brands")
async def get_brands_api(category: Optional[str] = None):
    """API endpoint to get brands for a category"""
    brands = get_distinct_brands(category)
    return {"brands": brands}


@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, session_id: Optional[str] = None):
    """Success page after payment"""
    session = get_session()
    order = None
    
    if session_id:
        try:
            # Retrieve the Stripe checkout session
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            if checkout_session.payment_status == 'paid':
                # Check if this is a multi-product order
                is_multi = checkout_session.metadata.get('is_multi_product') == 'true'
                
                if is_multi:
                    # Multi-product orders are handled here (webhook doesn't support multi yet)
                    customer_email = checkout_session.customer_details.email if checkout_session.customer_details else None
                    product_ids_str = checkout_session.metadata.get('product_ids', '')
                    product_ids = [int(pid) for pid in product_ids_str.split(',') if pid]
                    session_key = session_id
                    
                    # Check if already processed
                    existing = session.query(Order).filter(
                        Order.paypal_order_id.like(f"{session_key}:%")
                    ).first()
                    
                    if not existing:
                        for product_id in product_ids:
                            product = session.query(Product).filter(Product.id == product_id).first()
                            if product:
                                order_key = f"{session_key}:{product_id}"
                                order = Order(
                                    email=customer_email or "",
                                    product_id=product_id,
                                    price=product.price,
                                    paypal_order_id=order_key,
                                    status="completed"
                                )
                                session.add(order)
                                session.flush()
                                
                                if customer_email:
                                    send_order_confirmation_email(
                                        customer_email,
                                        order.id,
                                        product.title,
                                        order.price
                                    )
                        session.commit()
                else:
                    # Single product - webhook handles this, we just show success
                    pass
                
        except Exception as e:
            print(f"Error in success page: {e}")
    
    session.close()
    
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "page_title": "Thank you for your purchase!",
            "page_description": "Your order has been received"
        }
    )


# Authentication Pages
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "page_title": "Create Account - ManualBear",
        "page_description": "Create a ManualBear account to track your orders and access your manuals."
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "page_title": "Login - ManualBear",
        "page_description": "Log in to your ManualBear account to access your orders and downloads."
    })


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page"""
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Reset password page"""
    return templates.TemplateResponse("reset_password.html", {"request": request})


@app.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, email: str):
    """Email verification page"""
    return templates.TemplateResponse("verify_email.html", {"request": request, "email": email})


# Policy Pages
@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """Privacy policy page"""
    return templates.TemplateResponse("privacy_policy.html", {
        "request": request,
        "page_title": "Privacy Policy - ManualBear",
        "page_description": "How ManualBear collects, uses and protects your personal data. GDPR compliant."
    })


@app.get("/terms-of-service", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    """Terms of service page"""
    return templates.TemplateResponse("terms_of_service.html", {
        "request": request,
        "page_title": "Terms of Service - ManualBear",
        "page_description": "The terms governing use of ManualBear and the purchase of our service manuals."
    })


@app.get("/refund-policy", response_class=HTMLResponse)
async def refund_policy(request: Request):
    """Refund policy page"""
    return templates.TemplateResponse("refund_policy.html", {
        "request": request,
        "page_title": "Return & Refund Policy - ManualBear",
        "page_description": "ManualBear return and refund policy for digital downloads and physical media (USB/DVD)."
    })


@app.get("/about-us", response_class=HTMLResponse)
async def about_us(request: Request):
    """About us page"""
    return templates.TemplateResponse("about_us.html", {
        "request": request,
        "page_title": "About Us - ManualBear",
        "page_description": "ManualBear is an independent technical documentation archive with 1,000+ service and repair manuals."
    })


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Contact page"""
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "page_title": "Contact Us - ManualBear",
        "page_description": "Contact ManualBear support for help with orders, manuals or general questions."
    })


@app.post("/contact/send")
async def contact_send(request: Request):
    """Handle contact form submission"""
    from fastapi.responses import JSONResponse
    try:
        data = await request.json()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        subject = str(data.get("subject", "General Enquiry")).strip()
        message = str(data.get("message", "")).strip()

        # Basic validation
        if not name or not email or not message:
            return JSONResponse({"success": False, "error": "Please fill in all required fields."}, status_code=400)
        if len(message) > 5000:
            return JSONResponse({"success": False, "error": "Message is too long."}, status_code=400)
        if "@" not in email or "." not in email:
            return JSONResponse({"success": False, "error": "Please enter a valid email address."}, status_code=400)

        result = send_contact_form_email(name, email, subject or "General Enquiry", message)
        if result:
            return JSONResponse({"success": True})
        else:
            return JSONResponse({"success": False, "error": "Failed to send message. Please email us directly."}, status_code=500)
    except Exception as e:
        print(f"Contact form error: {e}")
        return JSONResponse({"success": False, "error": "An unexpected error occurred."}, status_code=500)


@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    """Frequently asked questions page"""
    return templates.TemplateResponse("faq.html", {
        "request": request,
        "page_title": "FAQ - ManualBear",
        "page_description": "Answers about ordering, delivery, formats and refunds at ManualBear."
    })


@app.get("/shipping-policy", response_class=HTMLResponse)
async def shipping_policy(request: Request):
    """Shipping policy page"""
    return templates.TemplateResponse("shipping_policy.html", {
        "request": request,
        "page_title": "Shipping & Delivery Policy - ManualBear",
        "page_description": "ManualBear delivery options, costs and processing times for digital and physical orders."
    })


@app.get("/payment-policy", response_class=HTMLResponse)
async def payment_policy(request: Request):
    """Payment policy page"""
    return templates.TemplateResponse("payment_policy.html", {
        "request": request,
        "page_title": "Payment Policy - ManualBear",
        "page_description": "Accepted payment methods, currency and security at ManualBear (Stripe, PCI-DSS Level 1)."
    })


# Admin Panel
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard"""
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_alt(request: Request):
    """Admin dashboard (alternative path)"""
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})


@app.get("/admin/newsletter", response_class=HTMLResponse)
async def admin_newsletter(request: Request):
    """Admin newsletter management"""
    return templates.TemplateResponse("admin/newsletter.html", {"request": request})


@app.get("/admin/email-templates", response_class=HTMLResponse)
async def admin_email_templates(request: Request):
    """Email campaign templates preview"""
    return templates.TemplateResponse("admin/email_templates.html", {"request": request})


@app.get("/admin/import-monitor", response_class=HTMLResponse)
async def admin_import_monitor(request: Request):
    """Bulk import progress monitor"""
    return templates.TemplateResponse("admin/import_monitor.html", {"request": request})


@app.get("/admin/cache-manager", response_class=HTMLResponse)
async def admin_cache_manager(request: Request):
    """PDF cache manager"""
    return templates.TemplateResponse("admin/cache_manager.html", {"request": request})


@app.get("/api/admin/cache-stats")
async def get_cache_stats():
    """Get cache statistics from database"""
    db = get_session()
    try:
        from database.models import PDFCache
        
        # Count total cached files
        count = db.query(PDFCache).count()
        
        # Calculate total size
        total_size = db.query(PDFCache).with_entities(PDFCache.file_size).all()
        total_bytes = sum(size[0] for size in total_size)
        
        # Format size
        if total_bytes < 1024:
            size_str = f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            size_str = f"{total_bytes / 1024:.1f} KB"
        elif total_bytes < 1024 * 1024 * 1024:
            size_str = f"{total_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{total_bytes / (1024 * 1024 * 1024):.1f} GB"
        
        return {"count": count, "size": size_str}
    finally:
        db.close()


@app.post("/api/admin/cache-clear")
async def clear_cache():
    """Clear all cache files from database"""
    db = get_session()
    try:
        from database.models import PDFCache
        
        # Count before delete
        count = db.query(PDFCache).count()
        
        # Delete all cache entries
        db.query(PDFCache).delete()
        db.commit()
        
        return {"success": True, "deleted": count}
    except Exception as e:
        db.rollback()
        print(f"Error clearing cache: {e}")
        return {"success": False, "deleted": 0}
    finally:
        db.close()


@app.get("/my-orders", response_class=HTMLResponse)
async def my_orders_page(request: Request):
    """User orders page"""
    return templates.TemplateResponse("my_orders.html", {"request": request})


# PDF Processing Endpoints (Admin only)
@app.post("/api/admin/process-pdfs")
async def process_pdfs_endpoint(
    product_id: Optional[int] = None,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Process PDFs: Download from pdf_url and upload to Google Drive
    Admin only endpoint
    
    Args:
        product_id: Specific product ID to process (optional)
        limit: Max number of products to process (optional)
    """
    try:
        from railway_pdf_processor import RailwayPDFProcessor
        
        processor = RailwayPDFProcessor()
        results = {"status": "processing", "products": []}
        
        if product_id:
            # Process single product
            success = processor.process_product(product_id)
            processor.close()
            
            return {
                "status": "completed",
                "product_id": product_id,
                "success": success
            }
        else:
            # Process all pending (with limit)
            session = processor.session
            query = session.query(Product).filter(
                Product.pdf_url.isnot(None),
                Product.google_drive_link.is_(None)
            )
            
            if limit:
                query = query.limit(limit)
            
            products = query.all()
            
            if not products:
                processor.close()
                return {
                    "status": "completed",
                    "message": "No products need processing",
                    "count": 0
                }
            
            success_count = 0
            failed_count = 0
            
            for product in products:
                if processor.process_product(product.id):
                    success_count += 1
                    results["products"].append({
                        "id": product.id,
                        "title": product.title,
                        "status": "success"
                    })
                else:
                    failed_count += 1
                    results["products"].append({
                        "id": product.id,
                        "title": product.title,
                        "status": "failed"
                    })
            
            processor.close()
            
            return {
                "status": "completed",
                "total": len(products),
                "successful": success_count,
                "failed": failed_count,
                "products": results["products"]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """Robots.txt for SEO - tells search engines how to crawl the site"""
    content = f"""User-agent: *
Allow: /
Allow: /search
Allow: /manuals/
Allow: /static/images/

Disallow: /api/
Disallow: /admin/
Disallow: /cart
Disallow: /checkout
Disallow: /login
Disallow: /register

# Crawl-delay for polite crawling
Crawl-delay: 1

# Sitemap location
Sitemap: {DOMAIN}/sitemap.xml
"""
    return content


@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    """
    Dynamic sitemap for SEO - optimized for large product catalogs
    Google recommends max 50,000 URLs per sitemap
    """
    session = get_session()
    try:
        # Get products count
        total_products = session.query(func.count(Product.id)).filter(Product.slug.isnot(None)).scalar()
        
        # Limit to 50,000 products (Google's recommendation)
        # Prioritize newer products
        products = session.query(Product.slug).filter(
            Product.slug.isnot(None)
        ).order_by(Product.id.desc()).limit(50000).all()
        
        # Start XML
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Homepage
        xml_content.append('  <url>')
        xml_content.append(f'    <loc>{DOMAIN}/</loc>')
        xml_content.append(f'    <lastmod>{today}</lastmod>')
        xml_content.append('    <changefreq>daily</changefreq>')
        xml_content.append('    <priority>1.0</priority>')
        xml_content.append('  </url>')
        
        # Search page
        xml_content.append('  <url>')
        xml_content.append(f'    <loc>{DOMAIN}/search</loc>')
        xml_content.append(f'    <lastmod>{today}</lastmod>')
        xml_content.append('    <changefreq>daily</changefreq>')
        xml_content.append('    <priority>0.9</priority>')
        xml_content.append('  </url>')
        
        # Product pages - only slugs to save memory
        for (slug,) in products:
            xml_content.append(f'  <url><loc>{DOMAIN}/manuals/{slug}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
        
        xml_content.append('</urlset>')
        
        return Response(
            content='\n'.join(xml_content),
            media_type="application/xml",
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
