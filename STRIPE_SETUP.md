# Stripe Payment Setup Guide

## 1. Create Stripe Account
1. Go to https://stripe.com
2. Click "Start now" and create account
3. Go to Developers → API keys

## 2. Get API Keys
**Test Mode** (for development):
- Publishable key: `pk_test_...`
- Secret key: `sk_test_...`

**Live Mode** (for production):
- Publishable key: `pk_live_...`
- Secret key: `sk_live_...`

## 3. Configure Application
Create `.env` file in project root:
```env
STRIPE_SECRET_KEY=sk_test_your_key_here
DOMAIN=http://localhost:8000
```

For production:
```env
STRIPE_SECRET_KEY=sk_live_your_key_here
DOMAIN=https://yourdomain.com
```

## 4. Setup Webhook (for automatic order creation)
1. Go to Developers → Webhooks
2. Click "Add endpoint"
3. Enter URL: `https://yourdomain.com/api/orders/webhook`
4. Select events: `checkout.session.completed`
5. Copy webhook signing secret: `whsec_...`
6. Add to `.env`:
```env
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
```

## 5. Test Payment
Test card numbers (Test mode only):
- **Success**: 4242 4242 4242 4242
- **Requires authentication**: 4000 0025 0000 3155
- **Declined**: 4000 0000 0000 9995

Use any future expiry date (e.g., 12/34) and any CVC (e.g., 123).

## 6. How it works
1. User clicks "Buy Now" on product page
2. Creates Stripe Checkout session via `/api/orders/create-checkout-session`
3. Redirects to Stripe-hosted payment page (with email collection)
4. User enters email + card details on Stripe
5. After successful payment:
   - Stripe webhook sends event to `/api/orders/webhook`
   - System creates order in database
   - Sends confirmation email
   - Redirects to success page

## 7. Production Checklist
- [ ] Switch to Live mode API keys
- [ ] Update DOMAIN to production URL
- [ ] Configure webhook endpoint on production URL
- [ ] Test full payment flow
- [ ] Enable email notifications
- [ ] Monitor Stripe dashboard for payments

## Features
✅ Secure card payment via Stripe
✅ Email collection during checkout
✅ Automatic order creation via webhook
✅ Email confirmation after purchase
✅ Admin panel shows all orders
✅ No credit card data stored on your server
