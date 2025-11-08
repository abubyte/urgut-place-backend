#!/usr/bin/env python3
"""
Seed script to populate database with dummy data for testing.
Run this script to add categories and shops with the new schema.

Usage:
    python -m app.db.seed_data
"""

from sqlmodel import Session, select
from app.db.session import engine
from app.models.category import Category
from app.models.shop import Shop
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Dummy categories
CATEGORIES = [
    {"name": "Oziq-ovqat", "description": "Oziq-ovqat mahsulotlari"},
    {"name": "Kiyim-kechak", "description": "Kiyim-kechak do'konlari"},
    {"name": "Elektronika", "description": "Elektronika va gadjetlar"},
    {"name": "Uy-ro'zg'or", "description": "Uy-ro'zg'or buyumlari"},
    {"name": "Salomatlik", "description": "Dori-darmon va salomatlik"},
    {"name": "Qurilish", "description": "Qurilish materiallari"},
    {"name": "Avtomobil", "description": "Avtomobil ehtiyot qismlari"},
    {"name": "Kitoblar", "description": "Kitoblar va nashriyotlar"},
]

# Dummy shops data
SHOPS = [
    {
        "name": "Samarqand Non",
        "description": "Eng yangi va mazali nonlar. Har kuni yangi pishiriladi.",
        "category_name": "Oziq-ovqat",
        "seller_phones": ["+998901234567", "+998901234568"],
        "location_lat": 39.6542,
        "location_long": 66.9597,
        "sector": 101,
        "number": 15,
        "sale_type": "retail",
        "logo_url": "https://cdn.urgutplace.test/logos/samarqand-non.png",
        "image_urls": [
            "https://picsum.photos/seed/samarqandnon1/1600/1200",
            "https://picsum.photos/seed/samarqandnon2/1600/1200",
            "https://picsum.photos/seed/samarqandnon3/1600/1200"
        ],
        "social_networks": [
            {"type": "instagram", "url": "https://instagram.com/samarqandnon"},
            {"type": "telegram", "url": "https://t.me/samarqandnon"},
            {"type": "facebook", "url": "https://facebook.com/samarqandnon"}
        ],
        "rating": 4.5,
        "rating_count": 25,
        "like_count": 12,
        "is_featured": True,
    },
    {
        "name": "Moda Do'koni",
        "description": "Eng zamonaviy va chiroyli kiyimlar. Katta tanlov va arzon narxlar.",
        "category_name": "Kiyim-kechak",
        "seller_phones": ["+998902345678"],
        "location_lat": 39.6550,
        "location_long": 66.9600,
        "sector": 203,
        "number": 42,
        "sale_type": "both",
        "logo_url": "https://cdn.urgutplace.test/logos/moda-dokoni.png",
        "image_urls": [
            "https://picsum.photos/seed/modadokoni1/1600/1200",
            "https://picsum.photos/seed/modadokoni2/1600/1200",
            "https://picsum.photos/seed/modadokoni3/1600/1200"
        ],
        "social_networks": [
            {"type": "instagram", "url": "https://instagram.com/modadokon"},
            {"type": "facebook", "url": "https://facebook.com/modadokon"},
            {"type": "telegram", "url": "https://t.me/modadokon"}
        ],
        "rating": 4.8,
        "rating_count": 45,
        "like_count": 30,
        "is_featured": True,
    },
    {
        "name": "Tech Store",
        "description": "Smartfonlar, noutbuklar va boshqa elektronika. Rasmiy kafolat bilan.",
        "category_name": "Elektronika",
        "seller_phones": ["+998903456789", "+998903456790", "+998903456791"],
        "location_lat": 39.6560,
        "location_long": 66.9610,
        "sector": 102,
        "number": 78,
        "sale_type": "retail",
        "logo_url": "https://cdn.urgutplace.test/logos/tech-store.png",
        "image_urls": [
            "https://picsum.photos/seed/techstore1/1600/1200",
            "https://picsum.photos/seed/techstore2/1600/1200",
            "https://picsum.photos/seed/techstore3/1600/1200"
        ],
        "social_networks": [
            {"type": "telegram", "url": "https://t.me/techstore"},
            {"type": "instagram", "url": "https://instagram.com/techstore"}
        ],
        "rating": 4.7,
        "rating_count": 60,
        "like_count": 45,
        "is_featured": False,
    },
    {
        "name": "Uy Ro'zg'or Markazi",
        "description": "Uy uchun kerakli barcha narsalar. Idish-tovoq, mebel va boshqalar.",
        "category_name": "Uy-ro'zg'or",
        "seller_phones": ["+998904567890"],
        "location_lat": 39.6570,
        "location_long": 66.9620,
        "sector": 305,
        "number": 23,
        "sale_type": "wholesale",
        "logo_url": None,
        "image_urls": [
            "https://picsum.photos/seed/uyrozgor1/1600/1200",
            "https://picsum.photos/seed/uyrozgor2/1600/1200",
            "https://picsum.photos/seed/uyrozgor3/1600/1200"
        ],
        "social_networks": [
            {"type": "telegram", "url": "https://t.me/uyrozgor"},
            {"type": "instagram", "url": "https://instagram.com/uyrozgor"}
        ],
        "rating": 4.2,
        "rating_count": 18,
        "like_count": 8,
        "is_featured": False,
    },
    {
        "name": "Sog'liq Aptekasi",
        "description": "Dori-darmonlar va tibbiy buyumlar. Barcha dori vositalari mavjud.",
        "category_name": "Salomatlik",
        "seller_phones": ["+998905678901", "+998905678902"],
        "location_lat": 39.6580,
        "location_long": 66.9630,
        "sector": 110,
        "number": 56,
        "sale_type": "retail",
        "logo_url": "https://cdn.urgutplace.test/logos/sogliq-aptekasi.png",
        "image_urls": [
            "https://picsum.photos/seed/soglikapteka1/1600/1200",
            "https://picsum.photos/seed/soglikapteka2/1600/1200",
            "https://picsum.photos/seed/soglikapteka3/1600/1200"
        ],
        "social_networks": [
            {"type": "instagram", "url": "https://instagram.com/soglikapteka"}
        ],
        "rating": 4.9,
        "rating_count": 35,
        "like_count": 28,
        "is_featured": True,
    },
    {
        "name": "Qurilish Materiallari",
        "description": "Uy qurish uchun barcha materiallar. Sement, g'isht, qum va boshqalar.",
        "category_name": "Qurilish",
        "seller_phones": ["+998906789012"],
        "location_lat": 39.6590,
        "location_long": 66.9640,
        "sector": 420,
        "number": 89,
        "sale_type": "both",
        "logo_url": "https://cdn.urgutplace.test/logos/qurilish-material.png",
        "image_urls": [
            "https://picsum.photos/seed/qurilish1/1600/1200",
            "https://picsum.photos/seed/qurilish2/1600/1200",
            "https://picsum.photos/seed/qurilish3/1600/1200"
        ],
        "social_networks": [
            {"type": "telegram", "url": "https://t.me/qurilishmaterial"}
        ],
        "rating": 4.4,
        "rating_count": 22,
        "like_count": 15,
        "is_featured": False,
    },
    {
        "name": "Avto Servis",
        "description": "Avtomobil ehtiyot qismlari va xizmatlar. Barcha markalar uchun.",
        "category_name": "Avtomobil",
        "seller_phones": ["+998907890123", "+998907890124", "+998907890125", "+998907890126"],
        "location_lat": 39.6600,
        "location_long": 66.9650,
        "sector": 215,
        "number": 112,
        "sale_type": "retail",
        "logo_url": "https://cdn.urgutplace.test/logos/avto-servis.png",
        "image_urls": [
            "https://picsum.photos/seed/avtoservis1/1600/1200",
            "https://picsum.photos/seed/avtoservis2/1600/1200",
            "https://picsum.photos/seed/avtoservis3/1600/1200"
        ],
        "social_networks": [
            {"type": "facebook", "url": "https://facebook.com/avtoservis"},
            {"type": "telegram", "url": "https://t.me/avtoservis"}
        ],
        "rating": 4.6,
        "rating_count": 40,
        "like_count": 25,
        "is_featured": False,
    },
    {
        "name": "Kitoblar Olami",
        "description": "O'zbek va jahon adabiyoti. Darsliklar va ilmiy kitoblar.",
        "category_name": "Kitoblar",
        "seller_phones": ["+998908901234"],
        "location_lat": 39.6610,
        "location_long": 66.9660,
        "sector": 130,
        "number": 34,
        "sale_type": "retail",
        "logo_url": "https://cdn.urgutplace.test/logos/kitoblar-olami.png",
        "image_urls": [
            "https://picsum.photos/seed/kitoblar1/1600/1200",
            "https://picsum.photos/seed/kitoblar2/1600/1200",
            "https://picsum.photos/seed/kitoblar3/1600/1200"
        ],
        "social_networks": [
            {"type": "instagram", "url": "https://instagram.com/kitoblarolami"},
            {"type": "telegram", "url": "https://t.me/kitoblarolami"}
        ],
        "rating": 4.3,
        "rating_count": 15,
        "like_count": 10,
        "is_featured": False,
    },
    {
        "name": "Go'sht Do'koni",
        "description": "Taza go'sht va mol go'shti. Har kuni yangi yetkazib beriladi.",
        "category_name": "Oziq-ovqat",
        "seller_phones": ["+998909012345", "+998909012346"],
        "location_lat": 39.6620,
        "location_long": 66.9670,
        "sector": 307,
        "number": 67,
        "sale_type": "both",
        "logo_url": None,
        "image_urls": [
            "https://picsum.photos/seed/goshtdokoni1/1600/1200",
            "https://picsum.photos/seed/goshtdokoni2/1600/1200",
            "https://picsum.photos/seed/goshtdokoni3/1600/1200"
        ],
        "social_networks": [
            {"type": "telegram", "url": "https://t.me/goshtdokoni"},
            {"type": "instagram", "url": "https://instagram.com/goshtdokoni"}
        ],
        "rating": 4.5,
        "rating_count": 30,
        "like_count": 20,
        "is_featured": False,
    },
    {
        "name": "Zamonaviy Kiyimlar",
        "description": "Yoshlar uchun zamonaviy kiyimlar. Sport va kundalik kiyimlar.",
        "category_name": "Kiyim-kechak",
        "seller_phones": ["+998900123456"],
        "location_lat": 39.6630,
        "location_long": 66.9680,
        "sector": 208,
        "number": 91,
        "sale_type": "retail",
        "logo_url": "https://cdn.urgutplace.test/logos/zamonaviy-kiyimlar.png",
        "image_urls": [
            "https://picsum.photos/seed/zamonaviy1/1600/1200",
            "https://picsum.photos/seed/zamonaviy2/1600/1200",
            "https://picsum.photos/seed/zamonaviy3/1600/1200"
        ],
        "social_networks": [
            {"type": "instagram", "url": "https://instagram.com/zamonaviychimlar"},
            {"type": "telegram", "url": "https://t.me/zamonaviychimlar"}
        ],
        "rating": 4.7,
        "rating_count": 50,
        "like_count": 35,
        "is_featured": True,
    },
]


def create_categories(session: Session):
    """Create categories if they don't exist."""
    print("Creating categories...")
    for cat_data in CATEGORIES:
        existing = session.exec(
            select(Category).where(Category.name == cat_data["name"])
        ).first()
        
        if not existing:
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"]
            )
            session.add(category)
            print(f"  ✓ Created category: {cat_data['name']}")
        else:
            print(f"  - Category already exists: {cat_data['name']}")
    
    session.commit()
    print("Categories created!\n")


def create_shops(session: Session):
    """Create shops with dummy data."""
    print("Creating shops...")
    
    # Get category mapping
    categories = session.exec(select(Category)).all()
    category_map = {cat.name: cat.id for cat in categories}
    
    for shop_data in SHOPS:
        existing = session.exec(
            select(Shop).where(Shop.name == shop_data["name"])
        ).first()

        category_id = category_map.get(shop_data["category_name"])
        if not category_id:
            print(f"  ✗ Category not found: {shop_data['category_name']}")
            continue

        if existing:
            existing.description = shop_data["description"]
            existing.category_id = category_id
            existing.seller_phones = shop_data["seller_phones"]
            existing.location_lat = shop_data["location_lat"]
            existing.location_long = shop_data["location_long"]
            existing.sector = shop_data["sector"]
            existing.number = shop_data["number"]
            existing.sale_type = shop_data["sale_type"]
            existing.logo_url = shop_data["logo_url"]
            existing.social_networks = shop_data["social_networks"]
            existing.image_urls = shop_data.get("image_urls", [])
            existing.is_featured = shop_data["is_featured"]
            existing.updated_at = datetime.utcnow()
            print(f"  • Updated shop: {shop_data['name']}")
            continue

        shop = Shop(
            name=shop_data["name"],
            description=shop_data["description"],
            category_id=category_id,
            seller_phones=shop_data["seller_phones"],
            location_lat=shop_data["location_lat"],
            location_long=shop_data["location_long"],
            sector=shop_data["sector"],
            number=shop_data["number"],
            sale_type=shop_data["sale_type"],
            logo_url=shop_data["logo_url"],
            social_networks=shop_data["social_networks"],
            rating=shop_data["rating"],
            rating_count=shop_data["rating_count"],
            like_count=shop_data["like_count"],
            is_featured=shop_data["is_featured"],
            expiration_months=12,
            expires_at=datetime.utcnow() + relativedelta(months=12),
            is_active=True,
        )

        shop.image_urls = shop_data.get("image_urls", [])
        session.add(shop)
        print(f"  ✓ Created shop: {shop_data['name']}")
    
    session.commit()
    print("Shops created!\n")


def main():
    """Main function to seed the database."""
    print("=" * 50)
    print("Starting database seeding...")
    print("=" * 50)
    print()
    
    try:
        with Session(engine) as session:
            create_categories(session)
            create_shops(session)
        
        print("=" * 50)
        print("Database seeding completed successfully!")
        print("=" * 50)
    except Exception as e:
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()

