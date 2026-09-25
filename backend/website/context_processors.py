def monexa_ui(request):
    user = getattr(request, "user", None)
    org = getattr(user, "organization", None) if user and user.is_authenticated else None
    return {
        "mx_org": org,
        "mx_role": getattr(user, "role", "") if user and user.is_authenticated else "",
    }
