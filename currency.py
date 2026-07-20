"""
Multi-market currency support.

Single source of truth for market -> currency -> price, shared by the product
pages, the Stripe checkout and the Bing/Google feeds. Prices are derived from
the USD price stored on the product via a fixed per-market multiplier and then
rounded to a .99 ending, so a market's price never drifts between what the feed
advertises and what the site charges.
"""
import math

DEFAULT_MARKET = 'US'

# multiplier is applied to the stored USD price, then rounded up to .99.
# Adjust these by hand if exchange rates move far enough to hurt margin —
# they are deliberately not tied to a live FX feed, because a price that moves
# between the feed crawl and the customer's visit gets the product disapproved.
MARKETS = {
    'US': {'currency': 'USD', 'symbol': '$',   'multiplier': 1.00, 'countries': ('US',), 'language': 'en'},
    'UK': {'currency': 'GBP', 'symbol': '£',   'multiplier': 0.79, 'countries': ('GB', 'UK'), 'language': 'en'},
    'CA': {'currency': 'CAD', 'symbol': 'CA$', 'multiplier': 1.37, 'countries': ('CA',), 'language': 'en'},
    'AU': {'currency': 'AUD', 'symbol': 'A$',  'multiplier': 1.52, 'countries': ('AU',), 'language': 'en'},
}

# ISO country -> market, derived from the table above.
COUNTRY_TO_MARKET = {
    country: market
    for market, cfg in MARKETS.items()
    for country in cfg['countries']
}

# Symbol per ISO code, for rendering an amount that has already been charged
# (receipts, emails, order history) where the market is no longer in play.
CURRENCY_SYMBOLS = {cfg['currency']: cfg['symbol'] for cfg in MARKETS.values()}

# Headers set by common CDNs/hosts, in order of preference.
_GEO_HEADERS = ('cf-ipcountry', 'x-vercel-ip-country', 'x-appengine-country', 'x-country-code')


def get_market(market_key):
    """Return the config for a market key, falling back to the default."""
    return MARKETS.get((market_key or '').upper(), MARKETS[DEFAULT_MARKET])


def normalize_market(market_key):
    """Return a valid market key, falling back to the default."""
    key = (market_key or '').upper()
    return key if key in MARKETS else DEFAULT_MARKET


def convert_price(usd_price, market_key):
    """Convert a stored USD price into the market's currency, ending in .99."""
    cfg = get_market(market_key)
    raw = float(usd_price or 0)
    if raw <= 0:
        return 0.0
    # A 1.0 multiplier means the stored price is already this market's price —
    # leave it exactly as-is rather than re-rounding it up to the next .99.
    if cfg['multiplier'] == 1.0:
        return round(raw, 2)
    raw *= cfg['multiplier']
    base = math.floor(raw)
    charmed = base + 0.99
    if charmed < raw:
        charmed = base + 1.99
    return max(0.99, round(charmed, 2))


def format_price(usd_price, market_key):
    """Human-readable price for templates, e.g. '£13.99'."""
    cfg = get_market(market_key)
    return f"{cfg['symbol']}{convert_price(usd_price, market_key):.2f}"


def format_amount(amount, currency_code):
    """Render an amount that was actually charged, e.g. '£13.99 GBP'.

    Always includes the ISO code: a bare '$' is ambiguous between USD, CAD and
    AUD, and a receipt is exactly where that ambiguity causes support tickets.
    """
    code = (currency_code or 'USD').upper()
    symbol = CURRENCY_SYMBOLS.get(code, '')
    return f"{symbol}{float(amount or 0):.2f} {code}"


def resolve_market(request):
    """Work out which market a visitor belongs to.

    Precedence: explicit ?market= (used by feed landing URLs so the advertised
    price is guaranteed to match) > saved cookie > CDN geo header > default.
    """
    explicit = request.query_params.get('market')
    if explicit and explicit.upper() in MARKETS:
        return explicit.upper()

    cookie = request.cookies.get('market')
    if cookie and cookie.upper() in MARKETS:
        return cookie.upper()

    for header in _GEO_HEADERS:
        country = request.headers.get(header)
        if country and country.upper() in COUNTRY_TO_MARKET:
            return COUNTRY_TO_MARKET[country.upper()]

    return DEFAULT_MARKET


def market_context(request):
    """Template context describing the visitor's market."""
    key = resolve_market(request)
    cfg = get_market(key)
    return {
        'market': key,
        'currency': cfg['currency'],
        'currency_symbol': cfg['symbol'],
        'markets': MARKETS,
        'currency_symbols': CURRENCY_SYMBOLS,
    }
