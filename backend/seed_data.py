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
            price=8999, stock=25,
            short_description="Budget phone with long battery life and AMOLED display",
            description="An affordable everyday phone with a 6000mAh battery that lasts two days on a single charge. Features a Super AMOLED display for clear viewing and a 50MP main camera. Good choice for students or anyone who needs a reliable phone without spending much.",
            tags=["budget", "long-battery", "students", "first-phone", "everyday-use"],
            specs={"ram_gb": 4, "storage_gb": 128, "battery_mah": 6000, "camera_mp": 50}),
    Product(id="PHN002", name="Xiaomi Redmi Note 13", category="phone", brand="Xiaomi",
            price=11999, stock=30,
            short_description="Mid-range phone with 108MP camera and AMOLED display",
            description="A well-rounded mid-range phone with a 108MP main camera for detailed photos and a bright AMOLED display. The 5000mAh battery and 33W fast charging keep it going through a full day. Suited for people who want a good camera phone without paying flagship prices.",
            tags=["camera", "mid-range", "photography", "social-media", "everyday-use", "students"],
            specs={"ram_gb": 6, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 108}),
    Product(id="PHN003", name="Realme Narzo 70 Pro", category="phone", brand="Realme",
            price=14999, stock=15,
            short_description="Performance mid-range phone with 120Hz AMOLED and fast processor",
            description="Built for speed with a MediaTek Dimensity 7050 processor and 120Hz AMOLED display for smooth scrolling and gaming. 8GB RAM handles multitasking well. A solid pick for gamers and heavy users who want flagship-level performance at a mid-range price.",
            tags=["gaming", "performance", "multitasking", "smooth-display", "mid-range"],
            specs={"ram_gb": 8, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 50}),
    Product(id="PHN004", name="Samsung Galaxy A35", category="phone", brand="Samsung",
            price=22999, stock=20,
            short_description="Water-resistant mid-premium phone with OIS camera",
            description="A durable mid-premium phone with IP67 water and dust resistance. The 50MP camera has optical image stabilisation for steady photos and videos. Gets regular Samsung software updates for 4 years. Good for professionals who want reliability and a clean camera without flagship pricing.",
            tags=["water-resistant", "durable", "camera", "professional", "reliable", "outdoor"],
            specs={"ram_gb": 8, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 50}),
    Product(id="PHN005", name="OnePlus Nord CE4", category="phone", brand="OnePlus",
            price=24999, stock=18,
            short_description="Fast-charging phone with 100W SUPERVOOC and Snapdragon processor",
            description="Charges from zero to full in about 30 minutes with 100W SUPERVOOC. Powered by Snapdragon 7 Gen 3 for fast app launches and smooth multitasking. The 5500mAh battery lasts a full day of heavy use. Ideal for busy professionals and heavy users who can't afford downtime.",
            tags=["fast-charging", "professional", "heavy-use", "multitasking", "productivity"],
            specs={"ram_gb": 8, "storage_gb": 256, "battery_mah": 5500, "camera_mp": 50}),
    Product(id="PHN006", name="OnePlus 12R", category="phone", brand="OnePlus",
            price=39999, stock=10,
            short_description="Flagship-level phone with Snapdragon 8 Gen 2 at a lower price",
            description="Delivers flagship performance with a Snapdragon 8 Gen 2 processor and 5500mAh battery with 100W charging. The 120Hz AMOLED display is bright and responsive. A strong choice for power users, mobile gamers, and anyone who wants top-tier performance without paying full flagship price.",
            tags=["flagship-killer", "gaming", "power-user", "fast-charging", "premium"],
            specs={"ram_gb": 8, "storage_gb": 256, "battery_mah": 5500, "camera_mp": 50}),
    Product(id="PHN007", name="Samsung Galaxy S24", category="phone", brand="Samsung",
            price=69999, stock=8,
            short_description="Flagship phone with Galaxy AI, titanium frame, and pro camera",
            description="Samsung's flagship with on-device Galaxy AI features including live translation and photo editing. Built with a titanium frame and Gorilla Glass Armor for durability. Snapdragon 8 Gen 3 handles anything. For professionals, photographers, and anyone who wants the best Samsung experience.",
            tags=["flagship", "AI", "premium", "photography", "professional", "gift"],
            specs={"ram_gb": 8, "storage_gb": 256, "battery_mah": 4000, "camera_mp": 50}),
    Product(id="PHN008", name="Xiaomi 14", category="phone", brand="Xiaomi",
            price=59999, stock=0,
            short_description="Compact flagship with Leica camera system and Snapdragon 8 Gen 3",
            description="A compact flagship co-engineered with Leica for professional-grade photography. The Snapdragon 8 Gen 3 and 12GB RAM deliver top-tier performance in a phone that fits comfortably in one hand. For photography enthusiasts and users who prefer a smaller, powerful phone.",
            tags=["flagship", "camera", "photography", "compact", "Leica", "premium"],
            specs={"ram_gb": 12, "storage_gb": 512, "battery_mah": 4610, "camera_mp": 50}),

    # Laptops
    Product(id="LAP001", name="Acer Aspire Lite AL15-41", category="laptop", brand="Acer",
            price=32999, stock=12,
            short_description="Affordable everyday laptop with Ryzen 5 and full HD display",
            description="An entry-level laptop with AMD Ryzen 5 5500U processor and 512GB SSD for quick boot times. The 15.6-inch full HD IPS display is comfortable for long reading and browsing sessions. Suitable for students, basic office work, and web browsing.",
            tags=["budget", "students", "online-classes", "office-work", "browsing", "portable"],
            specs={"ram_gb": 8, "storage_gb": 512, "display_inch": 15.6, "processor": "AMD Ryzen 5 5500U"}),
    Product(id="LAP002", name="Lenovo IdeaPad Slim 3", category="laptop", brand="Lenovo",
            price=38999, stock=15,
            short_description="Thin and light laptop with 12th Gen Intel and rapid charge",
            description="A slim 1.6kg laptop that is easy to carry between home and office. 12th Gen Intel Core i5 handles everyday productivity, video calls, and light multitasking. Rapid charge gets you two hours of use from a 15-minute charge. Great for commuters, students, and remote workers.",
            tags=["portable", "lightweight", "commuting", "work-from-home", "students", "office-work"],
            specs={"ram_gb": 8, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel Core i5-1235U"}),
    Product(id="LAP003", name="HP Pavilion 15", category="laptop", brand="HP",
            price=52999, stock=10,
            short_description="Well-rounded laptop with 16GB RAM, backlit keyboard, and premium audio",
            description="A versatile all-rounder with 16GB RAM for comfortable multitasking across many browser tabs and apps. Features a backlit keyboard for working in dim lighting and B&O tuned speakers for better audio. Suits professionals, content viewers, and anyone who wants a step up from basic laptops.",
            tags=["productivity", "work-from-home", "multitasking", "professional", "audio", "all-rounder"],
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel Core i5-1340P"}),
    Product(id="LAP004", name="ASUS VivoBook Pro 15", category="laptop", brand="ASUS",
            price=62999, stock=7,
            short_description="Creator laptop with OLED display and high-performance processor",
            description="Built for creative work with a vivid OLED display that shows accurate colours for photo and video editing. The Intel Core i7 H-series processor handles rendering and heavy creative software. A strong choice for graphic designers, video editors, and content creators.",
            tags=["creative", "video-editing", "photo-editing", "OLED", "design", "content-creation"],
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel Core i7-13620H"}),
    Product(id="LAP005", name="Lenovo IdeaPad Gaming 3", category="laptop", brand="Lenovo",
            price=58999, stock=9,
            short_description="Budget gaming laptop with RTX 3050 and 120Hz display",
            description="An affordable entry into PC gaming with an NVIDIA RTX 3050 GPU and 120Hz display for smooth gameplay. The Ryzen 5 7535HS processor and 16GB RAM also handle streaming, recording, and everyday tasks. Good for casual to mid-level gamers and students who want one laptop for both gaming and studies.",
            tags=["gaming", "budget-gaming", "students", "streaming", "casual-gaming"],
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "AMD Ryzen 5 7535HS"}),
    Product(id="LAP006", name="HP Victus 16", category="laptop", brand="HP",
            price=76999, stock=5,
            short_description="Mid-range gaming laptop with RTX 4060 and 144Hz display",
            description="A capable gaming laptop with NVIDIA RTX 4060 for running modern games at high settings. The 144Hz 16.1-inch display gives smooth visuals and the i7-13700H processor handles both gaming and heavy productivity tasks. For serious gamers and users who need GPU power for 3D work or machine learning.",
            tags=["gaming", "high-performance", "AAA-games", "3D-work", "machine-learning", "GPU"],
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 16.1, "processor": "Intel Core i7-13700H"}),

    # Headphones
    Product(id="HPH001", name="boAt Rockerz 450", category="headphone", brand="boAt",
            price=999, stock=50,
            short_description="Budget wireless on-ear headphones with 15-hour battery",
            description="Lightweight wireless on-ear headphones at an affordable price. 15 hours of battery life covers a full day of listening. Padded ear cushions and an adjustable headband keep them comfortable. Good for daily commuting, casual music listening, and video calls on a budget.",
            tags=["budget", "commuting", "everyday-use", "music", "casual", "students"],
            specs={"battery_hours": 15, "noise_cancelling": False, "connectivity": "Bluetooth 5.0"}),
    Product(id="HPH002", name="JBL Tune 520BT", category="headphone", brand="JBL",
            price=3499, stock=35,
            short_description="On-ear wireless headphones with JBL Pure Bass and 57-hour battery",
            description="JBL's Pure Bass sound delivers rich, deep low-end for music lovers. The 57-hour battery means you can go weeks without charging. Lightweight and foldable for easy carrying. A reliable mid-range option for commuters, gym-goers, and anyone who listens to music for hours daily.",
            tags=["music", "bass", "long-battery", "commuting", "gym", "travel"],
            specs={"battery_hours": 57, "noise_cancelling": False, "connectivity": "Bluetooth 5.3"}),
    Product(id="HPH003", name="Sony WH-CH720N", category="headphone", brand="Sony",
            price=7999, stock=20,
            short_description="Over-ear noise-cancelling headphones with 35-hour battery",
            description="Lightweight over-ear headphones with Sony's active noise cancellation for blocking out background noise. 35 hours of battery life and multipoint connection lets you switch between phone and laptop. Ideal for work-from-home, office use, commuting, and focused study sessions.",
            tags=["noise-cancellation", "work-from-home", "office", "commuting", "focus", "study"],
            specs={"battery_hours": 35, "noise_cancelling": True, "connectivity": "Bluetooth 5.2"}),
    Product(id="HPH004", name="Samsung Galaxy Buds FE", category="headphone", brand="Samsung",
            price=4999, stock=0,
            short_description="True wireless earbuds with ANC and water resistance",
            description="Compact true wireless earbuds with active noise cancellation and IPX2 splash resistance. 21 hours total battery with the case. Pairs seamlessly with Samsung phones and supports ambient sound mode for awareness. Suited for commuting, gym workouts, and hands-free calls.",
            tags=["earbuds", "wireless", "gym", "commuting", "compact", "Samsung-ecosystem"],
            specs={"battery_hours": 21, "noise_cancelling": True, "connectivity": "Bluetooth 5.2"}),
    Product(id="HPH005", name="Sony WH-1000XM5", category="headphone", brand="Sony",
            price=24999, stock=6,
            short_description="Premium wireless noise-cancelling over-ear headphones",
            description="Sony's flagship headphones with industry-leading noise cancellation and 30-hour battery. LDAC codec support delivers high-resolution audio over Bluetooth. Speak-to-chat pauses music automatically when you talk. For frequent travellers, audiophiles, and professionals who need distraction-free listening.",
            tags=["premium", "noise-cancellation", "travel", "audiophile", "professional", "work-from-home"],
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
