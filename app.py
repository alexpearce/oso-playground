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
class UserToken:
    owner: User
    value: str
    #: If True, roles on resources are derived via the owning User
    is_delegate: bool
    scopes: Set[str] = field(default_factory=set)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True)
class Project:
    name: str
    owner: Union[User, Organisation]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


# Placeholder for a Flask/Starlette Request object
@dataclass(frozen=True)
class Request:
    # The scopes defined on the route
    # A token must have these scopes to be access to access the route
    scopes: Set[str] = field(default_factory=set)


def check(actor, action, resource):
    """Helper to convert an Oso exception to a True/False decision."""
    try:
        oso.authorize(actor, action, resource)
    except (ForbiddenError, NotFoundError):
        return False
    return True


def check_request(actor, request):
    """Helper to convert an Oso exception to a True/False decision."""
    try:
        oso.authorize_request(actor, request)
    except (ForbiddenError, NotFoundError):
        return False
    return True


def expect(value, expected):
    ok = "\u001b[32m✔\u001b[0m"
    fail = "\u001b[31m✗\u001b[0m"
    print(f"{ok if value == expected else fail} {expected!s:<5} == {value}")


oso = Oso()
oso.register_class(User)
oso.register_class(UserToken)
oso.register_class(Organisation)
oso.register_class(Project)
# TODO(AP) do we have to register this? so also starlette.Request
oso.register_class(Request)
oso.load_files(["main.polar"])

read_scopes = {"read.project"}
write_scopes = read_scopes | {"create.project", "update.project", "delete.project"}

# Org owner
user = User(name="Dave")
user_token = UserToken(owner=user, value="token_sk_abc123", is_delegate=True, scopes=read_scopes)
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

print("----------------")
print("Token checks")
# A UserToken delegate can do the things the User can do
expect(check(user_token, "create", user_project), True)
# A request with no scopes
expect(check_request(user_token, Request()), True)
# A request with a scope the token does have
expect(check_request(user_token, Request(scopes=set(["read.project"]))), True)
# A request with a scope the token does not have
expect(check_request(user_token, Request(scopes=set(["display.project"]))), False)
