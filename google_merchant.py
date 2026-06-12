"""
Google Merchant Feed Generator
Generates XML feed compatible with Google Merchant Center
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database.models import Product, get_session
import xml.etree.ElementTree as ET
from datetime import datetime

merchant_router = APIRouter(prefix="/feed", tags=["merchant"])

@merchant_router.get("/google-merchant.xml")
async def generate_google_merchant_feed():
    """Generate Google Merchant Center Product Feed (XML)"""
    
    db_session = get_session()
    
    try:
        # Create RSS feed
        rss = ET.Element('rss', {
            'version': '2.0',
            'xmlns:g': 'http://base.google.com/ns/1.0'
        })
        
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = 'ManualBear - Technical Documentation & Service Information'
        ET.SubElement(channel, 'link').text = 'https://manualbear.com'
        ET.SubElement(channel, 'description').text = 'Comprehensive library of technical documentation and service information for vehicles, motorcycles, and equipment'
        
        # Get all active products
        products = db_session.query(Product).filter(
            Product.price > 0  # Only products with price
        ).all()
        
        for product in products:
            item = ET.SubElement(channel, 'item')

            # Slug fallback
            product_url = f"https://manualbear.com/manuals/{product.slug}" if product.slug else f"https://manualbear.com/product/{product.id}"

            # Required fields
            ET.SubElement(item, 'g:id').text = str(product.id)
            ET.SubElement(item, 'g:title').text = product.title or f"{product.brand} {product.model} Service & Repair Documentation"
            
            desc = product.description or f"Complete technical documentation and service information for {product.brand} {product.model}."
            if len(desc) < 100:
                desc = f"{desc} Comprehensive service and repair information for {product.brand} {product.model}. Delivered as an instant PDF download."
            ET.SubElement(item, 'g:description').text = desc[:5000]

            ET.SubElement(item, 'g:link').text = product_url

            # Image — take the first URL from comma-separated list
            if product.image_url:
                first_img = product.image_url.split(',')[0].strip()
                ET.SubElement(item, 'g:image_link').text = first_img
            else:
                ET.SubElement(item, 'g:image_link').text = "https://manualbear.com/static/images/logo.png"

            ET.SubElement(item, 'g:condition').text = 'new'
            ET.SubElement(item, 'g:availability').text = 'in stock'
            ET.SubElement(item, 'g:price').text = f"{product.price:.2f} USD"

            # Mark identifier_exists as false (no EAN/GTIN codes)
            ET.SubElement(item, 'g:identifier_exists').text = 'no'

            # Custom label — document type for internal GMC reporting
            ET.SubElement(item, 'g:custom_label_0').text = 'Technical-Documentation'
            ET.SubElement(item, 'g:custom_label_1').text = 'Service-Manual'

            # Category mapping - use Media > Books categories for technical documentation
            if product.category:
                category_name = product.category
                if 'Cars' in category_name or 'Automotive' in category_name:
                    ET.SubElement(item, 'g:google_product_category').text = 'Media > Books > Non-Fiction > Reference Books'
                elif 'Motorcycle' in category_name:
                    ET.SubElement(item, 'g:google_product_category').text = 'Media > Books > Non-Fiction > Reference Books'
                elif 'Truck' in category_name:
                    ET.SubElement(item, 'g:google_product_category').text = 'Media > Books > Non-Fiction > Reference Books'
                elif 'Construction' in category_name:
                    ET.SubElement(item, 'g:google_product_category').text = 'Media > Books > Non-Fiction > Reference Books'
                else:
                    ET.SubElement(item, 'g:google_product_category').text = 'Media > Books > Non-Fiction > Reference Books'

                ET.SubElement(item, 'g:product_type').text = category_name

            # Brand and model
            ET.SubElement(item, 'g:brand').text = product.brand or 'Generic'
            ET.SubElement(item, 'g:mpn').text = f"{product.brand}-{product.model}-manual" if product.brand and product.model else str(product.id)
            
        # Convert to string
        xml_string = ET.tostring(rss, encoding='unicode', method='xml')
        
        # Add XML declaration
        xml_output = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'
        
        return Response(content=xml_output, media_type="application/xml")
        
    except Exception as e:
        print(f"Error generating feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()


@merchant_router.get("/google-merchant-stats")
async def get_feed_stats():
    """Get statistics about products in the feed"""
    db_session = get_session()
    
    try:
        total_products = db_session.query(Product).filter(Product.price > 0).count()
        
        # Count by category
        categories = {}
        products = db_session.query(Product).filter(Product.price > 0).all()
        for p in products:
            cat = p.category or 'Uncategorized'
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_products": total_products,
            "feed_url": "https://manualbear.com/feed/google-merchant.xml",
            "categories": categories,
            "last_generated": datetime.now().isoformat()
        }
    finally:
        db_session.close()
