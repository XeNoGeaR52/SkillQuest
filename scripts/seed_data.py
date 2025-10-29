"""
Seed script to populate the database with sample data.

Run this script after running migrations:
    python -m scripts.seed_data
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Badge, Challenge, DifficultyEnum, User
from app.db.session import async_session_factory


async def seed_database():
    """Seed the database with sample data."""
    async with async_session_factory() as session:
        print("Seeding database...")

        # Check if users already exist
        result = await session.execute(select(User).where(User.username == "alice"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Sample users already exist, skipping user creation...")
            # Get existing users
            result = await session.execute(
                select(User).where(User.username.in_(["alice", "bob", "charlie"]))
            )
            users = list(result.scalars().all())
        else:
            # Create sample users
            users = [
                User(
                    username="alice",
                    email="alice@example.com",
                    password_hash=get_password_hash("password123"),
                    total_xp=0,
                    level=1
                ),
                User(
                    username="bob",
                    email="bob@example.com",
                    password_hash=get_password_hash("password123"),
                    total_xp=0,
                    level=1
                ),
                User(
                    username="charlie",
                    email="charlie@example.com",
                    password_hash=get_password_hash("password123"),
                    total_xp=0,
                    level=1
                ),
            ]

            for user in users:
                session.add(user)
            await session.commit()
            print(f"Created {len(users)} users")

            # Refresh to get IDs
            for user in users:
                await session.refresh(user)

        # Check if challenges already exist
        result = await session.execute(select(Challenge).where(Challenge.title == "Hello World"))
        existing_challenge = result.scalar_one_or_none()

        if existing_challenge:
            print("Sample challenges already exist, skipping challenge creation...")
        else:
            # Create sample challenges
            challenges = [
            Challenge(
                title="Hello World",
                description="Write a program that prints 'Hello, World!' to the console.",
                xp=50,
                difficulty=DifficultyEnum.EASY,
                tags=["beginner", "basics"],
                created_by=users[0].id,
                published=True
            ),
            Challenge(
                title="FizzBuzz",
                description="Write a program that prints numbers from 1 to 100. For multiples of 3, print 'Fizz', for multiples of 5 print 'Buzz', and for multiples of both print 'FizzBuzz'.",
                xp=100,
                difficulty=DifficultyEnum.EASY,
                tags=["logic", "loops"],
                created_by=users[0].id,
                published=True
            ),
            Challenge(
                title="Reverse a String",
                description="Write a function that takes a string and returns it reversed.",
                xp=75,
                difficulty=DifficultyEnum.EASY,
                tags=["strings", "basics"],
                created_by=users[0].id,
                published=True
            ),
            Challenge(
                title="Binary Search",
                description="Implement binary search algorithm to find an element in a sorted array.",
                xp=200,
                difficulty=DifficultyEnum.MEDIUM,
                tags=["algorithms", "search"],
                created_by=users[0].id,
                published=True
            ),
            Challenge(
                title="Balanced Brackets",
                description="Write a function to check if brackets in a string are balanced.",
                xp=150,
                difficulty=DifficultyEnum.MEDIUM,
                tags=["stacks", "strings"],
                created_by=users[0].id,
                published=True
            ),
            Challenge(
                title="Merge Sort",
                description="Implement the merge sort algorithm to sort an array of integers.",
                xp=300,
                difficulty=DifficultyEnum.HARD,
                tags=["algorithms", "sorting"],
                created_by=users[0].id,
                published=True
            ),
            Challenge(
                title="LRU Cache",
                description="Design and implement a Least Recently Used (LRU) cache.",
                xp=400,
                difficulty=DifficultyEnum.HARD,
                tags=["data-structures", "design"],
                created_by=users[0].id,
                published=True
            ),
            ]

            for challenge in challenges:
                session.add(challenge)
            await session.commit()
            print(f"Created {len(challenges)} challenges")

        # Check if badges already exist
        result = await session.execute(select(Badge).where(Badge.name == "First Steps"))
        existing_badge = result.scalar_one_or_none()

        if existing_badge:
            print("Sample badges already exist, skipping badge creation...")
        else:
            # Create sample badges
            badges = [
            Badge(
                name="First Steps",
                description="Complete your first challenge",
                condition={"type": "attempt_count", "count": 1, "status": "passed"},
                icon_url="https://example.com/badges/first-steps.png"
            ),
            Badge(
                name="Getting Started",
                description="Earn your first 100 XP",
                condition={"type": "xp", "threshold": 100},
                icon_url="https://example.com/badges/getting-started.png"
            ),
            Badge(
                name="Rising Star",
                description="Earn 500 XP",
                condition={"type": "xp", "threshold": 500},
                icon_url="https://example.com/badges/rising-star.png"
            ),
            Badge(
                name="Conqueror",
                description="Earn 1000 XP",
                condition={"type": "xp", "threshold": 1000},
                icon_url="https://example.com/badges/conqueror.png"
            ),
            Badge(
                name="Challenge Master",
                description="Complete 10 challenges",
                condition={"type": "attempt_count", "count": 10, "status": "passed"},
                icon_url="https://example.com/badges/challenge-master.png"
            ),
            Badge(
                name="Dedicated",
                description="Complete challenges on 7 different days",
                condition={"type": "consecutive_days", "days": 7},
                icon_url="https://example.com/badges/dedicated.png"
            ),
            ]

            for badge in badges:
                session.add(badge)
            await session.commit()
            print(f"Created {len(badges)} badges")

        print("\n✓ Seed data is ready!")
        print("\nSample user credentials:")
        print("  Username: alice | Password: password123")
        print("  Username: bob   | Password: password123")
        print("  Username: charlie | Password: password123")


if __name__ == "__main__":
    asyncio.run(seed_database())
