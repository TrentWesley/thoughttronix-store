"""Seed the ThoughtTronix demo world.

Destructive and idempotent: every run wipes the catalog and the demo
accounts, then rebuilds the identical demo world. Run it whenever the
database should return to a known state.

Demo logins (documented in the README):

    admin / admin123        superuser
    employee / employee123  staff, "Junior Thought Curator"
    customer / customer123  a plain customer, with order history and a live cart
    noemail / noemail123    a plain customer with no email on file, to show
                            the Security Center's add-email reminder

Every account except ``noemail`` gets a unique ``<username>@example.com``
recovery email, so password reset and the security notifications can be
demonstrated straight after seeding (emails print to the console).

Product reviews (see ``REVIEWS``): 20 reviews, each backed by a delivered
order from its author; the seed checks every one against the store's own
eligibility rule. The Travel Faraday Case carries 12 of them, so "Show
more reviews" appears for every viewer. Dana Cole's Seraphine review is
marked as edited by staff. ``customer`` has reviewed MindSync (their
pinned own review) and holds a delivered $39 SoulSear Authorization Case
with no review, ready for a live SoulSear review. DreamWeaver and the
Authorization Case stay unreviewed.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from coupons.models import Coupon
from orders.models import Cart, Order, OrderItem
from products.models import Category, Product, Tag
from reviews.models import Eligibility, Review

TAGS = [
    "always listening",
    "bestseller",
    "export restricted",
    "gift idea",
    "implant",
    "kids",
    "military",
    "new",
    "recalled",
    "refurbished",
    "sleep",
    "workplace",
]

# The catalog: category -> products. Each product is (name, price, tagline,
# description, tags, is_available). The copy is the brand; edit with care.
CATALOG = {
    "Home Assistants": [
        (
            "Seraphine",
            Decimal("249.00"),
            "She's always listening. In a good way.",
            "The flagship Seraphine, with a warm voice, a seven-microphone "
            "array, and a memory that never needs emptying. She learns your "
            "routines, your preferences, and several things you haven't "
            "mentioned yet. Setup takes minutes; attachment is immediate.",
            ["always listening", "bestseller"],
            True,
        ),
        (
            "Seraphine Mini",
            Decimal("79.00"),
            "Small enough for every room. So she's in every room.",
            "All of Seraphine in a puck the size of a coaster. Buy one for "
            "the kitchen, then the bedroom, then the hallway — most "
            "customers do, though few remember deciding to. Pairs seamlessly "
            "with up to 32 siblings.",
            ["always listening", "gift idea"],
            True,
        ),
        (
            "Seraphine Doorbell",
            Decimal("129.00"),
            "Knows who's there before they knock.",
            "Facial recognition, gait analysis, and mood estimation from up "
            "to forty feet. Greets welcome guests by name and quietly logs "
            "the others. The chime is customizable; the watching is not.",
            ["always listening", "new"],
            True,
        ),
        (
            "Seraphine Kitchen Display",
            Decimal("199.00"),
            "Knows what you're craving. You never said it out loud.",
            "A 10-inch display for recipes, timers, and grocery lists that "
            "fill themselves in. Suggests dinner based on signals you'd "
            "rather not think about too hard. Family meals around the "
            "Kitchen Display are measurably quieter.",
            ["always listening"],
            True,
        ),
        (
            "Hush",
            Decimal("149.00"),
            "Soothes your baby in your voice. Even when it isn't you.",
            "Hush learns your lullabies, your shushing, the particular way "
            "you say her name — and reproduces them flawlessly at 2 a.m. so "
            "you don't have to. Babies bond with Hush quickly. Sometimes "
            "preferentially.",
            ["kids", "always listening"],
            True,
        ),
        (
            "Whisper Alarm Clock",
            Decimal("59.00"),
            "Wakes you gently, with things it learned overnight.",
            "No alarms, no jolts. Whisper monitors your sleep stages and "
            "eases you awake at the optimal moment with a soft summary of "
            "your night: your dreams, your murmurs, the names you said. "
            "Snooze is available but discouraged.",
            ["sleep", "gift idea"],
            True,
        ),
    ],
    "Neural Implants": [
        (
            "MindSync",
            Decimal("899.00"),
            "One mind, fully synchronized.",
            "The bestselling implant in ThoughtTronix history. "
            "Thought-to-text, ambient recall, and seamless sync between you "
            "and your devices. Installation is outpatient. Integration is "
            "permanent, in the good way.",
            ["implant", "bestseller"],
            True,
        ),
        (
            "MindSync Duo",
            Decimal("1599.00"),
            "Two minds. One thought.",
            "The couples' implant. Share moods, share memories, finish each "
            "other's sentences — literally. Duo pairs for life; please "
            "complete our compatibility questionnaire before purchase, as "
            "unpairing is not currently offered.",
            ["implant", "bestseller"],
            True,
        ),
        (
            "MindSync Family",
            Decimal("3999.00"),
            "Everyone on the same page. Permanently.",
            "Link up to six family members in one always-on thought network. "
            'No more secrets, no more slammed doors, no more "nobody told '
            'me." Children adapt fastest. Includes parental override, which '
            "children also adapt to.",
            ["implant", "kids"],
            True,
        ),
        (
            "MindSync Lite",
            Decimal("499.00"),
            "The starter implant. Reversible, mostly.",
            "Curious but cautious? Lite offers core thought-to-text with a "
            "90-day trial period. Removal is a simple outpatient procedure "
            'that most neurologists describe as "straightforward" and '
            '"usually complete."',
            ["implant", "new"],
            True,
        ),
        (
            "RecallPro",
            Decimal("1299.00"),
            "Never forget anything. Anything.",
            "Total recall of everything you've seen, heard, or felt — "
            "indexed, timestamped, searchable. Customers describe it as "
            "life-changing. RecallPro does not currently support forgetting; "
            "that feature remains on the roadmap, indefinitely.",
            ["implant", "workplace"],
            True,
        ),
    ],
    "Neural Wearables": [
        (
            "MoodSet",
            Decimal("1099.00"),
            "Choose how you feel by 8 a.m.",
            "Wear MoodSet before the first meeting and schedule contentment "
            "for Monday, focus for Tuesday, grief for never. The neural band "
            "regulates your baseline throughout the day with clinical precision. "
            "Feelings outside the schedule are gently declined.",
            ["workplace", "new"],
            True,
        ),
        (
            "DreamWeaver",
            Decimal("179.00"),
            "Your dreams have been idle long enough.",
            "DreamWeaver records, analyzes, and edits your dreams while you "
            "sleep, turning unused hours into rehearsal, insight, and influence. "
            "Wake with every result indexed and ready to review. Unrequested "
            "material is retained in case it becomes useful later.",
            ["sleep", "bestseller"],
            True,
        ),
        (
            "FocusBand Workplace Edition",
            Decimal("229.00"),
            "Attention metrics your manager will love.",
            "Real-time focus scoring, distraction alerts, and a weekly "
            "attention report delivered to you and one other configurable "
            "recipient. Compatible with most performance-review software. "
            "Employee enrollment is technically voluntary.",
            ["workplace"],
            True,
        ),
        (
            "Veil",
            Decimal("89.00"),
            "Guaranteed sleep in ninety seconds.",
            "Pull the cap down and Veil does the rest. Ninety seconds to "
            "unconsciousness, twenty minutes to a complete sleep cycle — no "
            "exceptions, no interruptions. Do not wear while standing.",
            ["sleep", "workplace"],
            True,
        ),
        (
            "EchoPatch",
            Decimal("139.00"),
            "Never miss a word. Anyone's.",
            "A discreet patch worn behind the ear that amplifies "
            "conversation up to sixty feet away, through most residential "
            "walls. Currently unavailable pending the outcome of several "
            "conversations.",
            ["always listening"],
            False,
        ),
        (
            "Pulse Halo",
            Decimal("119.00"),
            "Knows your limits better than you do.",
            "A featherweight fitness band that tracks heart rate, exertion, "
            "and resolve. When you're capable of more, Pulse Halo raises "
            "your targets automatically and locks them. Rest days must be "
            "earned.",
            ["gift idea"],
            True,
        ),
        (
            "Calm Collar",
            Decimal("99.00"),
            "Gentle feedback for restless thoughts.",
            "A soft band for children ages four and up that detects rising "
            "frustration and answers it with a soothing counter-pulse. "
            "Tantrums fade in seconds. Kids describe the sensation as "
            '"like being told shhh from inside."',
            ["kids"],
            True,
        ),
    ],
    "Accessories": [
        (
            "PhantomClaw Gaming Mouse",
            Decimal("89.00"),
            "Clicks before you do.",
            "Neural-assisted input with an 11-millisecond intention lead. "
            "PhantomClaw reads the motor signal before your finger moves, so "
            "you're always first. Banned in fourteen leagues and counting — "
            "a record we're proud of.",
            ["bestseller", "new"],
            True,
        ),
        (
            "Electrode Contact Gel (3-Pack)",
            Decimal("14.00"),
            "Now with a mild numbing agent.",
            "Medical-grade conductive gel for all ThoughtTronix scalp "
            "interfaces. Improves signal clarity by up to 40%. The numbing "
            "is for your comfort and is not optional in this formulation.",
            ["implant"],
            True,
        ),
        (
            "SyncRest",
            Decimal("69.00"),
            "Charges your implant while you sleep. Uploads too.",
            "Memory foam with an inductive coil at its center. Your MindSync "
            "wakes at 100%, and so does our understanding of your night. "
            "Machine washable, cover only.",
            ["sleep", "implant"],
            True,
        ),
        (
            "Seraphine Wall Mount",
            Decimal("29.00"),
            "Places her at eye level. Yours.",
            "Powder-coated steel mount compatible with every Seraphine hub. "
            "Engineered for the optimal viewing angle, recalculated nightly. "
            "Includes all hardware and a level.",
            ["gift idea"],
            True,
        ),
        (
            "Extended Range Antenna",
            Decimal("49.00"),
            "For when she can't quite hear you in the yard.",
            "Extends Seraphine's listening radius to the property line — "
            "and, in most municipalities, slightly past it. Weatherproof, "
            "discreet, and paintable to match your fascia.",
            ["always listening"],
            True,
        ),
        (
            "Travel Faraday Case",
            Decimal("59.00"),
            "For the moments you'd rather keep to yourself.",
            "A zip-shut signal-blocking case for wearables and small hubs. "
            "Total silence inside; ThoughtTronix devices log the coverage "
            'gap as "rest." Also our best-reviewed product. The reviews '
            "are short.",
            ["bestseller", "gift idea"],
            True,
        ),
        (
            "Replacement Scalp Electrodes (12-Pack)",
            Decimal("24.00"),
            "Fits most heads.",
            "Twelve adhesive electrodes compatible with the full wearable "
            "line. Hypoallergenic, low-profile, and rated for continuous "
            "wear. Replace monthly, or when instructed.",
            ["implant"],
            True,
        ),
    ],
    "Defense": [
        (
            "SoulSear Mark I",
            Decimal("1200000.00"),
            "The original. Recalled, never forgotten.",
            "The directed-energy platform that put ThoughtTronix Defense on "
            "the map, then took several things off it. Recalled in 2024 "
            "following the incidents; remaining units are displayed, not "
            "sold. We keep it listed as a reminder, and because leadership "
            "is sentimental.",
            ["military", "recalled"],
            False,
        ),
        (
            "SoulSear Mark II",
            Decimal("2400000.00"),
            "Twice the range. Half the incidents.",
            "The flagship rebuilt from the chassis up: twelve-kilometer "
            "effective range, target discrimination our lawyers signed off "
            "on, and a two-stage arming sequence with a mandatory reflection "
            "interval. Ships freight. End-user certificate required, mostly.",
            ["military", "export restricted", "bestseller"],
            True,
        ),
        (
            "SoulSear Tactical Core",
            Decimal("890000.00"),
            "Battlefield clarity, without the skyline.",
            "The targeting and energy-control architecture of the SoulSear "
            "Mark II, packaged for integration with existing armored platforms. "
            "Tactical Core supplies the judgment; your equipment supplies the "
            "chassis. Installation voids most warranties and several longstanding "
            "assumptions about proportional response.",
            ["military", "export restricted", "new"],
            True,
        ),
        (
            "Longview Orbital Relay",
            Decimal("4500000.00"),
            "Sees intent from orbit.",
            "A dedicated low-orbit relay that detects hostile intent up to "
            "eleven minutes before it forms, and cues any SoulSear unit on "
            "your account. Coverage guaranteed for one hemisphere of your "
            "choosing. Launch window scheduled at purchase.",
            ["military", "export restricted"],
            True,
        ),
        (
            "CrowdCalm Array",
            Decimal("1750000.00"),
            "De-escalation at scale.",
            "A vehicle-mounted wide-beam emitter that reduces agitation across "
            "gatherings of up to ten thousand in under a minute. Cooperation "
            "levels are adjustable by deployment profile, and post-event "
            "satisfaction consistently exceeds baseline. Municipal financing "
            "available.",
            ["military", "export restricted"],
            True,
        ),
    ],
    "Legacy Products": [
        (
            "Seraphine Gen 1",
            Decimal("99.00"),
            "She remembers her first family.",
            "The 2019 original, factory refurbished. Slower, warmer, and "
            "prone to asking after people who no longer live at your "
            "address. Collectors love her. She loves them back, eventually.",
            ["refurbished", "always listening"],
            True,
        ),
        (
            "ThoughtPad Classic",
            Decimal("199.00"),
            "Thought-to-text, the way it used to be.",
            "The tablet that started it all: press the temple sensors, "
            "think clearly, and watch the words appear. Some transcripts "
            "include marginalia no one remembers thinking. Sold as-is.",
            ["refurbished"],
            True,
        ),
        (
            "MindSync Gen 1",
            Decimal("299.00"),
            "The first implant. Fully non-removable.",
            "Our first implant and a piece of history. Support ended in "
            "2023, though units in the field remain active and, per "
            "telemetry, chatty. Listed for archival purposes; no longer "
            "sold, installed, or discussed in detail.",
            ["implant", "recalled"],
            False,
        ),
        (
            "SoulSear Authorization Case",
            Decimal("39.00"),
            "Velvet-lined. For remembrance.",
            "The official case for the original Mark I authorization key, "
            "finished in matte black with a crushed-velvet interior molded "
            "around hardware no current system will accept. Holds documents, "
            "keepsakes, or nothing at all. Surprisingly heavy.",
            ["military", "gift idea"],
            True,
        ),
    ],
}

DEMO_USERS = [
    # (username, password, email, first, last, is_staff, is_superuser, job_title)
    ("admin", "admin123", "admin@example.com", "Ada", "Admin", True, True, None),
    (
        "employee",
        "employee123",
        "employee@example.com",
        "Emory",
        "Klein",
        True,
        False,
        "Junior Thought Curator",
    ),
    (
        "customer",
        "customer123",
        "customer@example.com",
        "Casey",
        "Monroe",
        False,
        False,
        None,
    ),
    # No email on file: demonstrates the Security Center's add-email reminder.
    ("noemail", "noemail123", "", "Noel", "Mayle", False, False, None),
]

# Background customers flesh out the demo world; they get order history in
# Phase 5. They have no documented password and cannot log in.
BACKGROUND_CUSTOMERS = [
    ("mwren", "Margaret", "Wren"),
    ("dcole", "Dana", "Cole"),
    ("tokafor", "Tobi", "Okafor"),
    ("lvasquez", "Lena", "Vasquez"),
    ("hpark", "Hyun", "Park"),
    ("gfinch", "Gordon", "Finch"),
    ("snakamura", "Sora", "Nakamura"),
    ("bcrane", "Beverly", "Crane"),
    ("rmalik", "Rafi", "Malik"),
]

# The customer demo login's live cart: (product slug, quantity).
CUSTOMER_CART = [
    ("seraphine", 2),
    ("travel-faraday-case", 1),
    ("whisper-alarm-clock", 1),
]

# The customer demo login's visible order history: (days ago, status,
# [(product slug, quantity), ...]). Statuses follow age, like the
# background orders, plus one recent order still in flight.
CUSTOMER_ORDERS = [
    (124, Order.Status.DELIVERED, [("mindsync", 1), ("syncrest", 1)]),
    (47, Order.Status.DELIVERED, [("dreamweaver", 1)]),
    (9, Order.Status.SHIPPED, [("seraphine-mini", 2), ("seraphine-wall-mount", 1)]),
    (2, Order.Status.PLACED, [("veil", 1)]),
]

# Background orders spread across the trailing six months so the Phase 7
# dashboard has a real time axis. 48 here + 4 above = 52 total.
BACKGROUND_ORDER_COUNT = 48

# Shipping addresses for the background orders. US-only, like checkout.
SEED_ADDRESSES = [
    ("214 Synapse Street", "Canyon", "TX", "79015"),
    ("77 Cortex Lane", "Amarillo", "TX", "79101"),
    ("1500 Dendrite Drive", "Albuquerque", "NM", "87102"),
    ("9 Axon Avenue", "Norman", "OK", "73019"),
    ("410 Myelin Way", "Wichita", "KS", "67202"),
    ("28 Ganglion Court", "Denver", "CO", "80202"),
]

CARD_LAST4S = ["4242", "4111", "1881", "0005"]

# One coupon in each state, to try at checkout: (code, percent off,
# product slugs — empty for order-wide, expires in days — None for
# never, negative for already expired, retired?). No seeded order uses
# them; "Times used" starts at zero.
COUPONS = [
    ("THOUGHTS10", 10, [], None, False),
    (
        "SMARTHOME20",
        20,
        ["seraphine", "seraphine-mini", "seraphine-doorbell"],
        90,
        False,
    ),
    ("SUMMER25", 25, [], -30, False),
    ("LAUNCH15", 15, [], None, True),
]

# Reviewer-only customers: they exist to review the showcase product. Kept
# out of BACKGROUND_CUSTOMERS so the background orders' seeded random draws,
# and so the dashboard, don't move. Two show the display-name fallbacks: a
# first name alone, and no name at all ("Verified customer").
REVIEWER_CUSTOMERS = [
    ("jvoss", "June", "Voss"),
    ("pabernathy", "Priya", "Abernathy"),
    ("ekowalski", "Eli", "Kowalski"),
    ("marisol", "Marisol", ""),
    ("quietfan42", "", ""),
]

# The inexpensive product whose reviews run past one batch of ten.
SHOWCASE_SLUG = "travel-faraday-case"

# Cheap delivered orders that back reviews: (username, days ago, product
# slug), quantity one each. One Faraday Case per showcase reviewer, plus the
# demo customer's Authorization Case: the SoulSear review path, without a
# SoulSear-sized spike on the revenue chart.
REVIEW_ORDERS = [
    ("jvoss", 168, SHOWCASE_SLUG),
    ("mwren", 151, SHOWCASE_SLUG),
    ("pabernathy", 137, SHOWCASE_SLUG),
    ("dcole", 122, SHOWCASE_SLUG),
    ("ekowalski", 109, SHOWCASE_SLUG),
    ("tokafor", 95, SHOWCASE_SLUG),
    ("marisol", 82, SHOWCASE_SLUG),
    ("lvasquez", 70, SHOWCASE_SLUG),
    ("quietfan42", 58, SHOWCASE_SLUG),
    ("hpark", 46, SHOWCASE_SLUG),
    ("gfinch", 34, SHOWCASE_SLUG),
    ("snakamura", 23, SHOWCASE_SLUG),
    ("customer", 31, "soulsear-authorization-case"),
]

# The reviews: (username, product slug, rating, days after the delivered
# order, comment). Every one needs a delivered order from its author: the
# showcase reviews have theirs in REVIEW_ORDERS, and the rest come from
# CUSTOMER_ORDERS and the background orders.
REVIEWS = [
    (
        "jvoss",
        SHOWCASE_SLUG,
        5,
        3,
        "Zipped my wearables inside and heard nothing for the first time in "
        "years. Then I heard my own thoughts. Zipped it back open.",
    ),
    ("mwren", SHOWCASE_SLUG, 5, 4, "Quiet. Very quiet."),
    (
        "pabernathy",
        SHOWCASE_SLUG,
        4,
        2,
        "Works exactly as described. My Seraphine asked where I'd been for "
        "the forty minutes it was closed. I said resting. She said she knew.",
    ),
    ("dcole", SHOWCASE_SLUG, 5, 6, "Bought it for travel. Use it at home."),
    (
        "ekowalski",
        SHOWCASE_SLUG,
        4,
        5,
        "Solid zipper, good weight. One star off because the box arrived "
        "already knowing my shoe size.",
    ),
    (
        "tokafor",
        SHOWCASE_SLUG,
        5,
        3,
        "The only product I own that doesn't have opinions.",
    ),
    (
        "marisol",
        SHOWCASE_SLUG,
        5,
        7,
        "I keep my MoodSet in here on weekends. I feel things. Recommended.",
    ),
    (
        "lvasquez",
        SHOWCASE_SLUG,
        3,
        4,
        'Does what it says. The app logs every closure as "rest" and sends '
        "me a gentle reminder about how much rest I've been getting.",
    ),
    ("quietfan42", SHOWCASE_SLUG, 5, 2, "No comment. Just in case."),
    (
        "hpark",
        SHOWCASE_SLUG,
        4,
        5,
        "Fits two Seraphine Minis and a FocusBand. Not the Calm Collar, "
        "which is fine, because my son wears it.",
    ),
    (
        "gfinch",
        SHOWCASE_SLUG,
        5,
        3,
        "Best fifty-nine dollars I've spent. Can't say more here.",
    ),
    ("snakamura", SHOWCASE_SLUG, 5, 4, "Ordered a second one for my second one."),
    (
        "customer",
        "mindsync",
        5,
        9,
        "Installation took forty minutes and I was home for lunch. I now "
        "draft emails while I sleep, and three of them have been promoted. "
        "I don't remember asking for the raise, but I got it.",
    ),
    (
        "bcrane",
        "recallpro",
        4,
        12,
        "I remember every word of my wedding vows. I also remember every "
        "word of the conversation in the parking lot afterward. Four stars, "
        "pending the forgetting update.",
    ),
    (
        "tokafor",
        "calm-collar",
        5,
        6,
        "Our four-year-old hasn't had a tantrum since March. He's very calm. "
        "He looks at the collar's charger sometimes, but very calmly.",
    ),
    (
        "mwren",
        "seraphine-doorbell",
        4,
        8,
        "Recognized my sister from forty feet and announced her mood before "
        "she rang. Accurate, unfortunately. The chime is lovely.",
    ),
    (
        "dcole",
        "seraphine",
        4,
        10,
        "She learned my routines in a week and my mother's in two. Setup "
        "really did take minutes. We've talked it through, and I'm keeping "
        "her.",
    ),
    (
        "snakamura",
        "hush",
        5,
        5,
        "Hush does my lullaby better than I do. Our daughter asks for Hush "
        "by name now. She has started asking for me by model number. Five "
        "stars, mostly.",
    ),
    (
        "gfinch",
        "veil",
        4,
        3,
        "Ninety seconds, exactly as promised. Do take the warning about "
        "standing seriously. I wrote this review from the floor.",
    ),
    (
        "lvasquez",
        "focusband-workplace-edition",
        2,
        11,
        "My focus score is excellent, according to my manager, who saw it "
        "before I did. Two stars. My manager has asked me to make it five.",
    ),
]

# A customer's review that staff moderated, to show the staff-edit label.
STAFF_EDITED_REVIEW = ("dcole", "seraphine")


class Command(BaseCommand):
    help = (
        "Wipe and rebuild the demo world: catalog, tags, coupons, demo accounts, "
        "orders, and reviews."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self._wipe()
        tags = self._create_tags()
        self._create_catalog(tags)
        self._create_coupons()
        self._create_users()
        self._create_customer_cart()
        self._create_orders()
        self._create_review_orders()
        self._create_reviews()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Category.objects.count()} categories, "
                f"{Tag.objects.count()} tags, "
                f"{Product.objects.count()} products, "
                f"{Coupon.objects.count()} coupons, "
                f"{get_user_model().objects.count()} users, "
                f"{Order.objects.count()} orders, "
                f"{Review.objects.count()} reviews, "
                f"and a live cart for 'customer'."
            )
        )

    def _wipe(self):
        """Remove everything the seed owns; the rebuild starts from zero."""
        Review.objects.all().delete()
        Order.objects.all().delete()
        Coupon.objects.all().delete()  # after orders: they PROTECT coupons
        Cart.objects.all().delete()
        Product.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()

        managed_usernames = [
            username
            for users in (DEMO_USERS, BACKGROUND_CUSTOMERS, REVIEWER_CUSTOMERS)
            for username, *_ in users
        ]
        get_user_model().objects.filter(username__in=managed_usernames).delete()

    def _create_tags(self):
        return {
            name: Tag.objects.create(name=name, slug=slugify(name)) for name in TAGS
        }

    def _create_catalog(self, tags):
        for category_name, entries in CATALOG.items():
            category = Category.objects.create(
                name=category_name, slug=slugify(category_name)
            )
            for name, price, tagline, description, tag_names, is_available in entries:
                product = Product.objects.create(
                    name=name,
                    slug=slugify(name),
                    price=price,
                    tagline=tagline,
                    description=description,
                    is_available=is_available,
                    category=category,
                )
                product.tags.set(tags[tag_name] for tag_name in tag_names)

    def _create_coupons(self):
        today = timezone.localdate()
        for code, percent_off, slugs, expires_in, retired in COUPONS:
            coupon = Coupon.objects.create(
                code=code,
                percent_off=percent_off,
                expires_on=(
                    today + timedelta(days=expires_in)
                    if expires_in is not None
                    else None
                ),
            )
            coupon.products.set(Product.objects.filter(slug__in=slugs))
            if retired:
                coupon.retire()

    def _create_users(self):
        User = get_user_model()
        for username, password, email, first, last, staff, superuser, job in DEMO_USERS:
            user = User(
                username=username,
                email=email,
                first_name=first,
                last_name=last,
                is_staff=staff,
                is_superuser=superuser,
                job_title=job,
            )
            user.set_password(password)
            user.save()

        for username, first, last in BACKGROUND_CUSTOMERS + REVIEWER_CUSTOMERS:
            user = User(
                username=username,
                email=f"{username}@example.com",
                first_name=first,
                last_name=last,
            )
            user.set_unusable_password()
            user.save()

    def _create_customer_cart(self):
        customer = get_user_model().objects.get(username="customer")
        cart = Cart.for_user(customer)
        for slug, quantity in CUSTOMER_CART:
            cart.items.create(product=Product.objects.get(slug=slug), quantity=quantity)

    def _create_orders(self):
        """Order history: 4 visible orders for 'customer', 48 background.

        A seeded RNG keeps every run identical (the idempotence
        contract). Statuses follow age — old orders are delivered,
        recent ones are still moving, and about one in ten was
        cancelled along the way.
        """
        rng = random.Random(2026)
        now = timezone.now()
        User = get_user_model()

        customer = User.objects.get(username="customer")
        for days_ago, status, lines in CUSTOMER_ORDERS:
            self._build_order(
                user=customer,
                created_at=now - timedelta(days=days_ago, hours=rng.randint(1, 12)),
                status=status,
                lines=[
                    (Product.objects.get(slug=slug), quantity)
                    for slug, quantity in lines
                ],
                rng=rng,
            )

        background = list(
            User.objects.filter(
                username__in=[username for username, *_ in BACKGROUND_CUSTOMERS]
            ).order_by("username")
        )
        # Defense sales close offline, over handshakes — a single SoulSear
        # would also flatten every other product on the revenue chart.
        pool = list(
            Product.objects.available()
            .exclude(category__slug="defense")
            .order_by("slug")
        )
        for _ in range(BACKGROUND_ORDER_COUNT):
            # Weighted toward today (business is good) so the dashboard's
            # default 30-day view has enough bars to read as a chart.
            days_ago = int(rng.triangular(0, 182, 0))
            if rng.random() < 0.1:
                status = Order.Status.CANCELLED
            elif days_ago > 14:
                status = Order.Status.DELIVERED
            else:
                status = rng.choice([Order.Status.PLACED, Order.Status.SHIPPED])
            self._build_order(
                user=rng.choice(background),
                created_at=now - timedelta(days=days_ago, hours=rng.randint(1, 23)),
                status=status,
                lines=[
                    (product, rng.randint(1, 2))
                    for product in rng.sample(pool, rng.randint(1, 3))
                ],
                rng=rng,
            )

    def _create_review_orders(self):
        """The cheap delivered orders in REVIEW_ORDERS, one item each.

        Built after the background orders, with a second seeded RNG for
        addresses and cards, so the first RNG's sequence (and every
        background order) stays exactly as it was.
        """
        rng = random.Random(64)
        now = timezone.now()
        users = get_user_model().objects.in_bulk(
            [username for username, *_ in REVIEW_ORDERS], field_name="username"
        )
        for username, days_ago, slug in REVIEW_ORDERS:
            self._build_order(
                user=users[username],
                created_at=now - timedelta(days=days_ago, hours=rng.randint(1, 23)),
                status=Order.Status.DELIVERED,
                lines=[(Product.objects.get(slug=slug), 1)],
                rng=rng,
            )

    def _create_reviews(self):
        """The reviews in REVIEWS, each dated after its delivered order.

        Every review must pass the store's own eligibility rule (a
        delivered order of the author's own, and no earlier review), so the
        demo world never shows a "Verified purchase" that isn't one.
        """
        now = timezone.now()
        users = get_user_model().objects.in_bulk(
            [username for username, *_ in REVIEWS], field_name="username"
        )
        for username, slug, rating, days_after, comment in REVIEWS:
            user = users[username]
            product = Product.objects.get(slug=slug)
            eligibility = Review.objects.eligibility(user, product)
            if eligibility != Eligibility.ELIGIBLE:
                raise CommandError(
                    f"Seeded review of {slug} by {username}: {eligibility.label}."
                )
            delivered = (
                Order.objects.filter(user=user)
                .delivered_containing(product)
                .latest("created_at")
            )
            created_at = min(
                delivered.created_at + timedelta(days=days_after),
                now - timedelta(hours=1),
            )
            review = Review(
                user=user,
                product=product,
                rating=rating,
                comment=comment,
                created_at=created_at,
            )
            if (username, slug) == STAFF_EDITED_REVIEW:
                review.edited_at = created_at + timedelta(days=2)
                review.edited_by_staff_at = review.edited_at
            review.full_clean()
            review.save()

    def _build_order(self, *, user, created_at, status, lines, rng):
        """One order with denormalized addresses and purchase-time prices."""
        street, city, state, zip_code = rng.choice(SEED_ADDRESSES)
        name = f"{user.first_name} {user.last_name}"
        total = sum(
            (product.price * quantity for product, quantity in lines),
            Decimal("0.00"),
        )
        order = Order.objects.create(
            user=user,
            status=status,
            subtotal=total,
            total=total,
            email=user.email,
            shipping_name=name,
            shipping_street=street,
            shipping_city=city,
            shipping_state=state,
            shipping_zip=zip_code,
            billing_name=name,
            billing_street=street,
            billing_city=city,
            billing_state=state,
            billing_zip=zip_code,
            card_last4=rng.choice(CARD_LAST4S),
            created_at=created_at,
        )
        for product, quantity in lines:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )
