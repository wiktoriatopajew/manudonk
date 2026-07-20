"""
Google Merchant Feed Generator
Generates XML feed compatible with Google Merchant Center
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, PlainTextResponse
from sqlalchemy.orm import Session
from database.models import Product, get_session
from currency import convert_price, get_market, normalize_market
import xml.etree.ElementTree as ET
from datetime import datetime
import csv
import io

merchant_router = APIRouter(prefix="/feed", tags=["merchant"])

@merchant_router.head("/google-merchant.xml")
async def google_merchant_feed_head():
    """HEAD request support for Google Merchant Center feed validation"""
    from fastapi.responses import Response
    return Response(headers={"Content-Type": "application/xml; charset=UTF-8"})

@merchant_router.get("/google-merchant.xml")
async def generate_google_merchant_feed(page: int = 0):
    """Generate Google Merchant Center Product Feed (XML).
    page=0 returns all products; page=1..4 returns one quarter each (~311 items).
    """

    db_session = get_session()
    PAGE_SIZE = 311

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

        # Get products — paginated when page param is provided
        query = db_session.query(Product).filter(Product.price > 0).order_by(Product.id)
        if page and page > 0:
            products = query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
        else:
            products = query.all()
        
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


@merchant_router.head("/bing-merchant.txt")
async def bing_merchant_feed_head():
    """HEAD request support for Bing/Microsoft Merchant Center feed validation"""
    return Response(headers={"Content-Type": "text/tab-separated-values; charset=UTF-8"})


@merchant_router.get("/bing-merchant.txt")
async def generate_bing_merchant_feed(page: int = 0, market: str = 'US'):
    """Generate Bing / Microsoft Merchant Center Product Feed (tab-separated).
    page=0 returns all products; page=1..4 returns one quarter each (~311 items).
    market selects the country of sale (US/UK/CA/AU) and therefore the currency;
    Microsoft requires one feed per market, priced in that market's currency.
    Columns follow the Microsoft Merchant Center feed spec, which differs from
    Google's: product_category (not google_product_category), pipe-delimited
    product_type, and the bingads_* grouping attributes.
    """
    db_session = get_session()
    PAGE_SIZE = 311
    market = normalize_market(market)
    currency_code = get_market(market)['currency']

    def clean(text):
        """Collapse whitespace and strip tabs/newlines so TSV columns stay intact."""
        if not text:
            return ''
        return ' '.join(str(text).replace('\t', ' ').split())

    try:
        query = db_session.query(Product).filter(Product.price > 0).order_by(Product.id)
        if page and page > 0:
            products = query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
        else:
            products = query.all()

        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

        # Header — Microsoft Merchant Center column names and order
        writer.writerow([
            'id', 'title', 'brand', 'link', 'price', 'description', 'image_link',
            'mpn', 'gtin', 'availability', 'condition', 'product_type',
            'product_category', 'bingads_grouping', 'bingads_label',
            'custom_label_0', 'custom_label_1', 'custom_label_2',
            'custom_label_3', 'custom_label_4'
        ])

        for product in products:
            product_url = (
                f"https://manualbear.com/manuals/{product.slug}" if product.slug
                else f"https://manualbear.com/product/{product.id}"
            )
            # Pin the landing page to this feed's market so the price the
            # shopper lands on always matches the price that was advertised.
            if market != 'US':
                product_url += f"?market={market}"

            title = clean(product.title) or f"{product.brand} {product.model} Service & Repair Manual"

            desc = clean(product.description) or (
                f"Complete technical documentation and service information for "
                f"{product.brand} {product.model}. Delivered as an instant PDF download."
            )
            if len(desc) < 100:
                desc = (
                    f"{desc} Comprehensive service and repair information for "
                    f"{product.brand} {product.model}. Delivered as an instant PDF download."
                )
            desc = desc[:5000]

            if product.image_url:
                image = product.image_url.split(',')[0].strip()
            else:
                image = "https://manualbear.com/static/images/logo.png"

            brand = product.brand or 'Generic'
            mpn = f"{brand}-{product.model}-manual" if brand and product.model else str(product.id)

            # Category is stored as "Cars/Volkswagen"; Microsoft delimits
            # product_type levels with " | " and groups campaigns on the top level.
            segments = [s.strip() for s in (product.category or 'Service Manual').split('/') if s.strip()]
            product_type = ' | '.join(segments)
            grouping = segments[0] if segments else 'Service Manual'

            writer.writerow([
                str(product.id),
                title,
                brand,
                product_url,
                f"{convert_price(product.price, market):.2f} {currency_code}",
                desc,
                image,
                mpn,
                '',
                'In Stock',
                'New',
                product_type,
                'Media > Books > Non-Fiction > Reference Books',
                grouping,
                f"{brand},service manual,repair manual",
                'Technical-Documentation',
                'Service-Manual',
                brand,
                grouping,
                str(product.model or '')
            ])

        content = output.getvalue()
        output.close()

        return PlainTextResponse(content=content, media_type="text/tab-separated-values")

    except Exception as e:
        print(f"Error generating Bing feed: {e}")
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
