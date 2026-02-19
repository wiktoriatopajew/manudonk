"""
PDF Preview routes - Cached preview with Playwright (Database storage)
"""
import os
import hashlib
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from database.models import get_session, Product, PDFCache

preview_router = APIRouter(prefix="/api/preview", tags=["preview"])


@preview_router.get("/cached-pdf")
async def get_cached_preview(product_id: int, pages: int = 10):
    """
    Generate or serve cached PDF preview of first N pages
    Uses Playwright to open PDF viewer and generate preview
    Stores in database for persistence across restarts
    
    Usage: /api/preview/cached-pdf?product_id=123&pages=10
    """
    # Get product from database
    db = get_session()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.pdf_url:
            raise HTTPException(status_code=404, detail="Product not found or no PDF available")
        
        url = product.pdf_url.split('?')[0]
        # Remove filename if present (e.g., /file.pdf or /file.html)
        import re
        url = re.sub(r'/[^/]*\.(pdf|html?)$', '', url, flags=re.IGNORECASE)
        if not url:
            raise HTTPException(status_code=400, detail="Invalid PDF URL")
        
        if pages < 1 or pages > 20:
            raise HTTPException(status_code=400, detail="Pages must be 1-20")
        
        # Create unique cache key based on URL + pages count
        cache_key = f"{url}_{pages}"
        url_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check database cache first - instant if exists!
        cached = db.query(PDFCache).filter(PDFCache.cache_key == url_hash).first()
        if cached:
            print(f"⚡ [INSTANT] Serving cached PDF from database (no wait!)")
            return StreamingResponse(
                io.BytesIO(cached.pdf_data),
                media_type="application/pdf",
                headers={"Content-Disposition": "inline; filename=preview.pdf"}
            )
        
        # Generate new PDF
        print(f"🔨 [CACHE MISS] Generating preview for: {url}")
        
        try:
            async with async_playwright() as p:
                # Launch browser with performance optimizations
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-web-security']
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={'width': 1200, 'height': 1600},
                    ignore_https_errors=True,
                    bypass_csp=True
                )
                
                page = await context.new_page()
                
                # Try to find PDF viewer URL first
                main_url = url.rstrip('/').split('?')[0]
                print(f"📄 Loading IDRViewer PDF page: {main_url}")
                
                await page.goto(main_url, wait_until="networkidle", timeout=60000)
                
                # Wait for IDRViewer to initialize
                print("⏳ Waiting for IDRViewer to load...")
                await page.wait_for_function("typeof IDRViewer !== 'undefined'", timeout=15000)
                
                # Wait for PDF pages to load
                print("📖 Waiting for PDF pages to load in IDRViewer...")
                await page.wait_for_selector("#idrviewer .page", timeout=10000)
                
                # Wait for canvas elements (actual PDF content)
                print("🎨 Waiting for PDF canvas content...")
                await page.wait_for_function("""
                    () => {
                        const pages = document.querySelectorAll('#idrviewer .page');
                        return pages.length >= 2 && Array.from(pages).some(page => 
                            page.querySelector('canvas, object, iframe, .page-inner')
                        );
                    }
                """, timeout=10000)
                
                # Extra wait for content to fully render
                await page.wait_for_timeout(2000)
                
                print("🖨️ Generating PDF using browser print (Ctrl+P)...")
                
                # Use page.pdf() to simulate Ctrl+P - this captures what user sees
                pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    page_ranges=f"1-{pages}",
                    margin={
                        "top": "0.4in",
                        "bottom": "0.4in", 
                        "left": "0.4in",
                        "right": "0.4in"
                    },
                    scale=0.8  # Slightly smaller to fit more content
                )
                
                await browser.close()
                
                # Save to database
                pdf_cache = PDFCache(
                    product_id=product_id,
                    cache_key=url_hash,
                    pdf_data=pdf_bytes,
                    file_size=len(pdf_bytes)
                )
                db.add(pdf_cache)
                db.commit()
                
                print(f"✅ PDF saved to database cache ({len(pdf_bytes)} bytes)")
                
                return StreamingResponse(
                    io.BytesIO(pdf_bytes),
                    media_type="application/pdf",
                    headers={"Content-Disposition": "inline; filename=preview.pdf"}
                )
                    
        except Exception as e:
            print(f"❌ Error generating preview: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    finally:
        db.close()


@preview_router.get("/page-count/{product_id}")
async def get_page_count(product_id: int):
    """
    Get or fetch page count for a product
    Returns cached value if available, otherwise fetches from PDF viewer
    """
    db = get_session()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Return cached page count if available
        if product.page_count:
            return {"page_count": product.page_count, "cached": True}
        
        # No PDF URL - can't fetch page count
        if not product.pdf_url:
            return {"page_count": None, "error": "No PDF available"}
        
        # Fetch page count from PDF viewer
        url = product.pdf_url.split('?')[0]
        import re
        url = re.sub(r'/[^/]*\.(pdf|html?)$', '', url, flags=re.IGNORECASE)
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-web-security']
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={'width': 1200, 'height': 1600},
                    ignore_https_errors=True,
                    bypass_csp=True
                )
                
                page = await context.new_page()
                main_url = url.rstrip('/').split('?')[0]
                
                print(f"📊 Fetching page count for: {main_url}")
                await page.goto(main_url, wait_until="networkidle", timeout=60000)
                
                # Wait for IDRViewer
                await page.wait_for_function("typeof IDRViewer !== 'undefined'", timeout=15000)
                await page.wait_for_selector("#idrviewer .page", timeout=10000)
                
                # Get total page count from IDRViewer
                page_count = await page.evaluate("""
                    () => {
                        // Try to get from IDRViewer object
                        if (typeof IDRViewer !== 'undefined' && IDRViewer.pagecount) {
                            return IDRViewer.pagecount;
                        }
                        // Fallback: count page elements
                        const pages = document.querySelectorAll('#idrviewer .page');
                        return pages.length;
                    }
                """)
                
                await browser.close()
                
                # Save to database
                if page_count and page_count > 0:
                    product.page_count = page_count
                    db.commit()
                    print(f"✅ Page count saved: {page_count}")
                    return {"page_count": page_count, "cached": False}
                else:
                    return {"page_count": None, "error": "Could not determine page count"}
                    
        except Exception as e:
            print(f"❌ Error fetching page count: {e}")
            return {"page_count": None, "error": str(e)}
    
    finally:
        db.close()
