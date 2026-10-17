"""Marketing copy templates and formatting helpers for BabuJeeStore."""

from typing import Optional, List, Dict


TEMPLATES: Dict[str, str] = {
    "promotional": (
        "🔥 SPECIAL OFFER: {product_name} 🔥\n\n"
        "{description}\n\n"
        "💰 Special Price: {price} {discount_text}\n\n"
        "⚡ Limited stock available. Grab yours before it's gone!\n\n"
        "👉 Shop Now: {product_url}\n\n"
        "{hashtags}"
    ),
    "new_arrival": (
        "✨ JUST DROPPED at BabuJeeStore! ✨\n\n"
        "Introducing {product_name} – the newest addition to our collection.\n\n"
        "{description}\n\n"
        "🏷️ Available now for {price}.\n\n"
        "🚚 Fast shipping & guaranteed quality.\n\n"
        "🔗 Order directly here: {product_url}\n\n"
        "{hashtags}"
    ),
    "benefit_driven": (
        "Looking for {product_name}? We've got you covered! 🌟\n\n"
        "{description}\n\n"
        "Why our customers love it:\n"
        "✅ Premium Quality\n"
        "✅ Best Value for Money ({price})\n"
        "✅ Fast & Reliable Delivery\n\n"
        "👇 Don't miss out, order today:\n"
        "{product_url}\n\n"
        "{hashtags}"
    ),
    "flash_sale": (
        "🚨 24-HOUR FLASH SALE 🚨\n\n"
        "Get {product_name} for ONLY {price}! {discount_text}\n\n"
        "{description}\n\n"
        "⏳ Deal ends soon – don't wait!\n"
        "🛒 Tap the link to secure yours now: {product_url}\n\n"
        "{hashtags}"
    )
}

DEFAULT_HASHTAGS = [
    "#BabuJeeStore",
    "#OnlineShopping",
    "#Deals",
    "#ShopOnline",
    "#BestPrice",
    "#Trending"
]


def format_marketing_copy(
    product_name: str,
    price: str,
    product_url: str,
    description: str,
    discount_percent: Optional[int] = None,
    style: str = "promotional",
    custom_hashtags: Optional[List[str]] = None
) -> str:
    """
    Format a high-converting Facebook product post caption.
    
    Args:
        product_name: The name/title of the product.
        price: Formatted price string (e.g. '$29.99' or 'Rs. 2,500').
        product_url: Direct product link to your website.
        description: Brief product highlight/features.
        discount_percent: Optional discount number (e.g. 20 for 20% OFF).
        style: Template style: 'promotional', 'new_arrival', 'benefit_driven', 'flash_sale'.
        custom_hashtags: Optional extra hashtags.
    """
    template = TEMPLATES.get(style, TEMPLATES["promotional"])
    
    discount_text = f"({discount_percent}% OFF!)" if discount_percent else ""
    
    tags = list(DEFAULT_HASHTAGS)
    if custom_hashtags:
        for t in custom_hashtags:
            clean_tag = t.strip()
            if not clean_tag.startswith("#"):
                clean_tag = f"#{clean_tag}"
            if clean_tag not in tags:
                tags.append(clean_tag)
                
    hashtags_str = " ".join(tags[:8])
    
    return template.format(
        product_name=product_name,
        price=price,
        discount_text=discount_text,
        description=description.strip(),
        product_url=product_url,
        hashtags=hashtags_str
    )
