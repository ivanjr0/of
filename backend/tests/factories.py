"""
Factories for generating test data using factory-boy.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from app.models import Content, User, ConversationSession, Message

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for generating User instances"""

    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    is_active = True


class ContentFactory(DjangoModelFactory):
    """Factory for generating Content instances"""

    class Meta:
        model = Content

    name = factory.Faker("sentence", nb_words=5)
    content = factory.Faker("text", max_nb_chars=1000)
    user = factory.SubFactory(UserFactory)
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.Faker("date_time_this_year")
    processed = False
    key_concepts = None
    difficulty_level = None
    estimated_study_time = None
    is_deleted = False


class ProcessedContentFactory(ContentFactory):
    """Factory for generating processed Content instances"""

    processed = True
    key_concepts = factory.LazyFunction(lambda: fake.words(nb=5))
    difficulty_level = factory.Faker(
        "random_element", elements=["beginner", "intermediate", "advanced", "expert"]
    )
    estimated_study_time = factory.Faker("random_int", min=10, max=120)


class ConversationSessionFactory(DjangoModelFactory):
    """Factory for generating ConversationSession instances"""

    class Meta:
        model = ConversationSession

    user = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence", nb_words=4)
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.Faker("date_time_this_year")
    is_deleted = False


class MessageFactory(DjangoModelFactory):
    """Factory for generating Message instances"""

    class Meta:
        model = Message

    session = factory.SubFactory(ConversationSessionFactory)
    role = factory.Faker("random_element", elements=["user", "assistant"])
    content = factory.Faker("text", max_nb_chars=300)
    timestamp = factory.Faker("date_time_this_year")
    token_count = factory.Faker("random_int", min=10, max=500)
