# Redis Cache Setup Guide

## Overview
This application uses Redis for caching frequently accessed data to improve performance significantly.

## Benefits
- ⚡ **Faster page loads** - Homepage, product pages, and search results are cached
- 🚀 **Reduced database load** - Less queries to PostgreSQL
- 💰 **Lower costs** - Reduced compute usage on Railway
- 📈 **Better scalability** - Can handle more users

## What is Cached?
1. **Homepage** (5 minutes TTL)
   - Categories list
   - Latest products
   
2. **Product Pages** (10 minutes TTL)
   - Product details
   - Related products
   
3. **Search Results** (future implementation)
   - Category listings
   - Brand filters

## Setup on Railway

### Option 1: Railway Redis Plugin (Recommended)
1. Go to your Railway project
2. Click **"New"** → **"Database"** → **"Add Redis"**
3. Railway will automatically set the `REDIS_URL` environment variable
4. Redeploy your application

### Option 2: External Redis Provider

#### Upstash (Free tier available)
1. Go to [upstash.com](https://upstash.com/)
2. Create a free account
3. Create a new Redis database
4. Copy the Redis URL (format: `redis://default:password@hostname:port`)
5. In Railway, add environment variable:
   ```
   REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_HOST.upstash.io:PORT
   ```

#### Redis Cloud (Free tier available)
1. Go to [redis.com/try-free](https://redis.com/try-free/)
2. Create a free account
3. Create a new database
4. Copy the connection string
5. Add to Railway environment variables

## Local Development

### Install Redis locally

**Windows (via WSL or Docker):**
```bash
docker run -d -p 6379:6379 redis
```

**Mac (via Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Set environment variable
Create/update your `.env` file:
```
REDIS_URL=redis://localhost:6379
```

## Testing Cache

### Check if Redis is working
Watch your application logs on startup. You should see:
```
✅ Redis cache connected successfully
```

If Redis is not configured, you'll see:
```
ℹ️ Redis not configured (REDIS_URL not set) - cache disabled
```

### Verify caching is working
1. Visit homepage - first load will be slower (database query)
2. Refresh page - should be much faster (cached)
3. Check Railway logs to see cache hits/misses

## Cache Management

### Clear cache via Python
```python
from cache_manager import cache

# Clear all cache
cache.clear_all()

# Clear specific pattern
cache.clear_pattern("product_detail:*")

# Clear single key
cache.delete("homepage_data")
```

### Clear cache via Redis CLI
```bash
# Railway - use Railway Redis plugin console
# Or connect via redis-cli:
redis-cli -h YOUR_HOST -p YOUR_PORT -a YOUR_PASSWORD
> FLUSHDB  # Clear all keys in current database
```

## Monitoring

### Railway Dashboard
- Monitor Redis memory usage in Railway dashboard
- Free tier: 25 MB (enough for 1000s of cached pages)
- Paid tier: Up to 8 GB

### Cache Stats (future feature)
Add admin dashboard endpoint to show:
- Cache hit rate
- Total cached keys
- Memory usage

## TTL (Time To Live) Settings

Current TTL values can be adjusted in `main.py`:

```python
# Homepage - 5 minutes
cache.set(cache_key, data, ttl=300)

# Product pages - 10 minutes  
cache.set(cache_key, data, ttl=600)
```

Recommended values:
- Homepage: 5-10 minutes (updates frequently)
- Product pages: 10-60 minutes (rarely change)
- Search results: 5-15 minutes (dynamic content)

## Troubleshooting

### Cache not working
1. Check `REDIS_URL` is set correctly
2. Check Railway logs for connection errors
3. Verify Redis service is running

### Stale data showing
1. Reduce TTL values
2. Clear cache manually
3. Add cache invalidation on product updates

### Out of memory
1. Upgrade Redis tier
2. Reduce TTL values
3. Implement LRU eviction policy

## Performance Impact

Expected improvements:
- Homepage: **50-80% faster** (from ~200ms to ~40ms)
- Product pages: **60-90% faster** (from ~150ms to ~30ms)
- Database queries: **70% reduction**

## Future Enhancements

- [ ] Cache search results
- [ ] Add cache warming (pre-populate common queries)
- [ ] Implement cache invalidation on product CRUD operations
- [ ] Add admin cache management UI
- [ ] Monitor cache hit/miss rates
- [ ] Implement Redis Sentinel for high availability
