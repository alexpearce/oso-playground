# An actor is authorised to perform an action on a resource if a relevant
# permission can be found
allow(actor: Actor, action: String, resource: Resource) if
    has_permission(actor, action, resource);

actor User {}

resource Organisation {
    roles = [
        "owner",
        "member",
    ];
}

# A User has an role in an Organisation if they hold a matching OrganisationRole
has_role(user: User, role_name: String, organisation: Organisation) if
    role in user.organisation_roles and
    role matches { name: role_name, organisation: organisation };

resource Project {
    permissions = [
        "create",
        "read",
        "delete",
    ];
    roles = [
        "owner",
        "member",
    ];

    "create" if "owner";
    "read" if "member";
    "delete" if "owner";

    "member" if "owner";

    # A Project can be owned by an Organisation
    relations = { parent_organisation: Organisation };
    # Organisation Project roles are derived from roles in the owning Organisation
    "owner" if "owner" on "parent_organisation";
    "member" if "member" on "parent_organisation";
}

has_role(user: User, "owner", project: Project) if
    project.owner = user;

has_relation(organisation: Organisation, "parent_organisation", project: Project) if
    project.owner = organisation;
