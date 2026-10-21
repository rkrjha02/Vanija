"""Insert fake products into the database for development."""

import asyncio
import sys

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.data.models import Product

PRODUCTS = [
    # Phones
    Product(id="PHN001", name="Samsung Galaxy M15", category="phone", brand="Samsung",
            price=8999, stock=25, description="Budget phone with 6000mAh battery and Super AMOLED display.",
            specs={"ram_gb": 4, "storage_gb": 128, "battery_mah": 6000, "camera_mp": 50}),
    Product(id="PHN002", name="Xiaomi Redmi Note 13", category="phone", brand="Xiaomi",
            price=11999, stock=30, description="Mid-range phone with AMOLED display and 108MP camera.",
            specs={"ram_gb": 6, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 108}),
    Product(id="PHN003", name="Realme Narzo 70 Pro", category="phone", brand="Realme",
            price=14999, stock=15, description="Performance phone with Dimensity 7050 and 120Hz AMOLED.",
            specs={"ram_gb": 8, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 50}),
    Product(id="PHN004", name="Samsung Galaxy A35", category="phone", brand="Samsung",
            price=22999, stock=20, description="Mid-premium with OIS camera and IP67 water resistance.",
            specs={"ram_gb": 8, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 50}),
    Product(id="PHN005", name="OnePlus Nord CE4", category="phone", brand="OnePlus",
            price=24999, stock=18, description="Fast charging 100W SUPERVOOC with Snapdragon 7 Gen 3.",
            specs={"ram_gb": 8, "storage_gb": 256, "battery_mah": 5500, "camera_mp": 50}),
    Product(id="PHN006", name="OnePlus 12R", category="phone", brand="OnePlus",
            price=39999, stock=10, description="Flagship killer with Snapdragon 8 Gen 2 and 5500mAh.",
            specs={"ram_gb": 8, "storage_gb": 256, "battery_mah": 5500, "camera_mp": 50}),
    Product(id="PHN007", name="Samsung Galaxy S24", category="phone", brand="Samsung",
            price=69999, stock=8, description="Flagship with Galaxy AI, Snapdragon 8 Gen 3, and titanium frame.",
            specs={"ram_gb": 8, "storage_gb": 256, "battery_mah": 4000, "camera_mp": 50}),
    Product(id="PHN008", name="Xiaomi 14", category="phone", brand="Xiaomi",
            price=59999, stock=0, description="Leica camera phone with Snapdragon 8 Gen 3.",
            specs={"ram_gb": 12, "storage_gb": 512, "battery_mah": 4610, "camera_mp": 50}),

    # Laptops
    Product(id="LAP001", name="Acer Aspire Lite AL15-41", category="laptop", brand="Acer",
            price=32999, stock=12, description="Entry-level laptop with Ryzen 5 and full HD IPS display.",
            specs={"ram_gb": 8, "storage_gb": 512, "display_inch": 15.6, "processor": "AMD Ryzen 5 5500U"}),
    Product(id="LAP002", name="Lenovo IdeaPad Slim 3", category="laptop", brand="Lenovo",
            price=38999, stock=15, description="Thin and light with 12th Gen Intel and rapid charge.",
            specs={"ram_gb": 8, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel Core i5-1235U"}),
    Product(id="LAP003", name="HP Pavilion 15", category="laptop", brand="HP",
            price=52999, stock=10, description="All-rounder with backlit keyboard and B&O audio.",
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel Core i5-1340P"}),
    Product(id="LAP004", name="ASUS VivoBook Pro 15", category="laptop", brand="ASUS",
            price=62999, stock=7, description="Creator laptop with OLED display and H-series processor.",
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel Core i7-13620H"}),
    Product(id="LAP005", name="Lenovo IdeaPad Gaming 3", category="laptop", brand="Lenovo",
            price=58999, stock=9, description="Budget gaming laptop with RTX 3050 and 120Hz display.",
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "AMD Ryzen 5 7535HS"}),
    Product(id="LAP006", name="HP Victus 16", category="laptop", brand="HP",
            price=76999, stock=5, description="Gaming laptop with RTX 4060 and 144Hz display.",
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 16.1, "processor": "Intel Core i7-13700H"}),

    # Headphones
    Product(id="HPH001", name="boAt Rockerz 450", category="headphone", brand="boAt",
            price=999, stock=50, description="Wireless on-ear headphones with 15-hour battery life.",
            specs={"battery_hours": 15, "noise_cancelling": False, "connectivity": "Bluetooth 5.0"}),
    Product(id="HPH002", name="JBL Tune 520BT", category="headphone", brand="JBL",
            price=3499, stock=35, description="On-ear wireless with JBL Pure Bass and 57-hour battery.",
            specs={"battery_hours": 57, "noise_cancelling": False, "connectivity": "Bluetooth 5.3"}),
    Product(id="HPH003", name="Sony WH-CH720N", category="headphone", brand="Sony",
            price=7999, stock=20, description="Over-ear with active noise cancelling and 35-hour battery.",
            specs={"battery_hours": 35, "noise_cancelling": True, "connectivity": "Bluetooth 5.2"}),
    Product(id="HPH004", name="Samsung Galaxy Buds FE", category="headphone", brand="Samsung",
            price=4999, stock=0, description="True wireless earbuds with ANC and IPX2 water resistance.",
            specs={"battery_hours": 21, "noise_cancelling": True, "connectivity": "Bluetooth 5.2"}),
    Product(id="HPH005", name="Sony WH-1000XM5", category="headphone", brand="Sony",
            price=24999, stock=6, description="Premium noise cancelling headphones with 30-hour battery and LDAC.",
            specs={"battery_hours": 30, "noise_cancelling": True, "connectivity": "Bluetooth 5.3"}),
]


async def seed():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(select(Product).limit(1))
        if result.scalar_one_or_none() is not None:
            print("Products already exist, skipping seed.")
            await engine.dispose()
            return

        session.add_all(PRODUCTS)
        await session.commit()
        print(f"Inserted {len(PRODUCTS)} products.")

    await engine.dispose()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
