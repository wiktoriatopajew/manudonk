# Import Products to Railway

## Quick Start

To import all 1304 products to your Railway database, run this command in the Railway project terminal:

```bash
python import_to_railway.py
```

This will import all products from `shopify.csv` directly to your PostgreSQL database on Railway.

## What gets imported:
- ✅ 1304 products
- 📁 7 categories (Automobiles, Motorcycles, Trucks, etc.)
- 🏷️ 114 brands
- 🖼️ Product images (URLs)
- 💰 Prices
- 📝 Descriptions

## After import:
Your products will be immediately visible on the website at:
- Homepage: Shows latest products and categories
- Search: `/search` - Browse all products with filters
- Categories: Click any category to see products

## Notes:
- Import takes about 2-3 minutes
- Duplicate products are skipped automatically
- All products get SEO-friendly URLs (slugs)
- Products are automatically categorized by type
