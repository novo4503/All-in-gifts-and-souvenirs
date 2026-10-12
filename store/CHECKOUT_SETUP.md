# Cash-on-delivery checkout setup

The checkout uses the existing `Product` model and a Django session cart. A valid checkout is saved as pending and opens a prefilled WhatsApp Click-to-Chat message. The customer must press Send in WhatsApp; opening the message does not send it or mark it as sent. The cart remains available after WhatsApp opens.

## Database

Apply the new order schema during deployment:

```powershell
python manage.py migrate
```

## Environment configuration

- `DELIVERY_COST`: optional non-negative decimal delivery charge, defaults to `0`.

No WhatsApp API credentials are required. The browser opens `https://wa.me/18762058967` with the order message URL-encoded. WhatsApp works through its app on mobile or WhatsApp Web/Desktop where available. The customer reviews the prefilled message and presses Send to deliver it.

## Checkout behavior

- The session cart contains product IDs and quantities only. Prices and product details are retrieved from the database.
- Checkout values are validated by the server before an order snapshot is created. Invalid data leaves the cart intact.
- WhatsApp message content comes from the saved order and item snapshots, including current database prices and calculated totals.
- Orders remain in notification status `pending` until a separate process confirms delivery; opening Click-to-Chat is not treated as sent.
- The cart and promo code are not cleared when WhatsApp opens.
- The `ISLAND10` promo code is calculated on the server as a 10% subtotal discount.
- Quantities are limited to 99 per product.
- The current `Product` model does not define purchasable options, so order line option snapshots are empty until the catalog model gains such fields.
