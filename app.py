from dataclasses import dataclass, field
from typing import Set, Union
import uuid

from oso import ForbiddenError, Oso, NotFoundError


@dataclass(frozen=True)
class Organisation:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True)
class OrganisationRole:
    organisation: Organisation
    name: str


@dataclass(frozen=True)
class User:
    name: str
    organisation_roles: Set[OrganisationRole] = field(default_factory=set)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True)
class Project:
    name: str
    owner: Union[User, Organisation]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


def check(actor, action, resource):
    """Helper to convert an Oso exception to a True/False decision."""
    try:
        oso.authorize(actor, action, resource)
    except (ForbiddenError, NotFoundError):
        return False
    return True


def expect(value, expected):
    print(f"{'✔' if value == expected else '✗'} {expected!s:<5} == {value}")


oso = Oso()
oso.register_class(User)
oso.register_class(Organisation)
oso.register_class(Project)
oso.load_files(["main.polar"])

# Org owner
user = User(name="Dave")
# Org member
user2 = User(name="Daisy")
# No org
user3 = User(name="Duke")
organisation = Organisation(name="Unlimited Ltd.")
user.organisation_roles.add(
    OrganisationRole(organisation=organisation, name="owner")
)
user2.organisation_roles.add(
    OrganisationRole(organisation=organisation, name="member")
)
user_project = Project(name="User project", owner=user)
org_project = Project(name="Organisation project", owner=organisation)

print("Expected == value")
# A User can create personal projects
expect(check(user, "create", user_project), True)
# User can read and delete their own project
expect(check(user, "read", user_project), True)
expect(check(user, "delete", user_project), True)
# User cannot read nor delte a project owned by another User
expect(check(user2, "read", user_project), False)
expect(check(user2, "delete", user_project), False)
# User can read a Project owned by the Organisation they're an owner/member of
expect(check(user, "read", org_project), True)
expect(check(user2, "read", org_project), True)
# User can delete a Project owned by the Organisation they're a owner of
expect(check(user, "delete", org_project), True)
# User cannot delete a Project owned by the Organisation they're a member of
expect(check(user2, "delete", org_project), False)
# User cannot create a Project under a Project unless their are a Project owner
expect(check(user, "create", org_project), True)
expect(check(user2, "create", org_project), False)
# User cannot act on a Project they're not a member of
expect(check(user3, "create", org_project), False)
expect(check(user3, "delete", org_project), False)
